"""Formes interdites et passe LanguageTool."""
import http.server
import json
import threading
import unittest
import urllib.parse
from pathlib import Path

from coherence.config import Config, charger_config
from coherence.controles import CONTROLES
from coherence.controles.orthographe import LanguageToolIndisponible, languagetool
from coherence.corpus import Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options

ESPACE = Path(__file__).resolve().parents[2]


def formes(textes, formes_interdites):
    c = Corpus()
    c.fr.update(textes)
    c.origine_fr.update({cle: "projet" for cle in textes})
    config = Config(espace=Path("."), formes_interdites=formes_interdites)
    return {x.cle: x for x in CONTROLES["orthographe"](c, None, config, Options())}


class FauxLanguageTool(http.server.BaseHTTPRequestHandler):
    """Comme LanguageTool (Java), compte ses décalages en unités UTF-16 : un émoji en vaut deux."""
    def do_POST(self):
        champs = urllib.parse.parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
        texte = champs["text"][0]
        i = texte.find("alpins")
        decalage = len(texte[:i].encode("utf-16-le")) // 2
        matches = [{"offset": decalage, "length": 6, "message": "Accord", "rule": {"id": "AGREEMENT"},
                    "replacements": [{"value": "alpin"}]}] if i >= 0 else []
        corps = json.dumps({"matches": matches}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args):
        pass


class TestOrthographe(unittest.TestCase):

    def test_formes_interdites_jars_compris(self):
        c = Corpus()
        c.fr.update({"block.a.x": "Planches de pallisandre", "block.minecraft.y": "Echange", "a.z": "Tout les jours"})
        c.origine_fr.update({"block.a.x": "jar", "block.minecraft.y": "vanilla", "a.z": "projet"})
        formes = [{"forme": "pallisandre", "juste": "palissandre", "source": "contre-analyse"},
                  {"forme": "Echange", "juste": "Échange", "source": "contre-analyse"},
                  {"forme": "tout les", "juste": "tous les", "source": "contre-analyse"}]
        config = Config(espace=Path("."), formes_interdites=formes)
        constats = {x.cle: x for x in CONTROLES["orthographe"](c, None, config, Options())}
        self.assertEqual(sorted(constats), ["a.z", "block.a.x"])
        self.assertEqual(constats["block.a.x"].attendu, "Planches de palissandre")
        self.assertEqual(constats["a.z"].attendu, "Tous les jours")
        self.assertEqual(constats["a.z"].statut, BLOQUANT)
        self.assertEqual(constats["a.z"].objet, "tout les")  # la forme, comme la règle d'un constat LanguageTool

    def test_forme_sensible_a_la_casse(self):
        """Une forme à « casse » ne vise que ce qu'elle écrit, et se remplace telle qu'écrite : « N'importe le »
        après une virgule devient « peu importe le » ; « le village n'importe le sel » est juste."""
        c = formes({"a.faux": "Pluie au printemps, N'importe le reste de l'année",
                    "a.juste": "Le village n'importe le sel qu'en hiver."},
                   [{"forme": "N'importe le", "juste": "peu importe le", "casse": True}])
        self.assertEqual(sorted(c), ["a.faux"])
        self.assertEqual(c["a.faux"].attendu, "Pluie au printemps, peu importe le reste de l'année")

    def test_formes_du_depot_fautives_partout(self):
        """Les formes interdites du dépôt sont fautives dans tout contexte : « malgré tout les autres » et « le
        village n'importe le sel » sont justes ; « alors tout les autres », « N'importe le reste » et « un cable »
        ne le sont pas."""
        c = formes({"a.juste1": "Elle aime malgré tout les autres.",
                    "a.juste2": "Le village n'importe le sel qu'en hiver.",
                    "a.faux1": "Quand un bloc est placé, alors tout les autres seront placés.",
                    "a.faux2": "Pluie au printemps, N'importe le reste de l'année",
                    "a.faux3": "Connecte-les ensemble, ou utilise un cable."},
                   charger_config(ESPACE).formes_interdites)
        self.assertEqual(sorted(c), ["a.faux1", "a.faux2", "a.faux3"])
        self.assertEqual(c["a.faux1"].attendu, "Quand un bloc est placé, alors tous les autres seront placés.")
        self.assertEqual(c["a.faux2"].attendu, "Pluie au printemps, peu importe le reste de l'année")
        self.assertEqual(c["a.faux3"].attendu, "Connecte-les ensemble, ou utilise un câble.")

    def test_languagetool(self):
        serveur = http.server.HTTPServer(("127.0.0.1", 0), FauxLanguageTool)
        threading.Thread(target=serveur.serve_forever, daemon=True).start()
        self.addCleanup(serveur.server_close)
        self.addCleanup(serveur.shutdown)
        url = f"http://127.0.0.1:{serveur.server_port}/v2/check"
        (c,) = languagetool([("a.b", "Bonjour"), ("block.meadow.pine_stairs", "Escalier §2alpins")], url)
        self.assertEqual((c.cle, c.objet, c.statut, c.attendu), ("block.meadow.pine_stairs", "AGREEMENT", SIGNALE, "alpin"))
        self.assertIn("« alpins »", c.detail)

    def test_languagetool_apres_des_emojis(self):
        """Les émojis d'un texte du lot (🌼, deux unités UTF-16 chacun) ne décalent pas les textes suivants."""
        serveur = http.server.HTTPServer(("127.0.0.1", 0), FauxLanguageTool)
        threading.Thread(target=serveur.serve_forever, daemon=True).start()
        self.addCleanup(serveur.server_close)
        self.addCleanup(serveur.shutdown)
        url = f"http://127.0.0.1:{serveur.server_port}/v2/check"
        textes = [("a.b", "🌼" * 10 + " Printemps"), ("block.meadow.pine_stairs", "Escalier alpins"),
                  ("c.d", "Au revoir")]
        (c,) = languagetool(textes, url)
        self.assertEqual(c.cle, "block.meadow.pine_stairs")
        self.assertIn("« alpins »", c.detail)

    def test_languagetool_injoignable(self):
        with self.assertRaises(LanguageToolIndisponible):
            languagetool([("a.b", "Bonjour")], "http://127.0.0.1:9/v2/check")


if __name__ == "__main__":
    unittest.main()
