"""Non-régression (spec §12, critère 1) : chaque constat vérifié de la contre-analyse qui relève
d'une règle est retrouvé par son contrôle.

Corpus : l'instantané complet de la révision de la contre-analyse (c31accf2c). Le test retrouve le défaut, pas
une présence : les exceptions s'appliquent avant la comparaison (la dette, non), si bien qu'un faux positif
couvert ne tient aucune ligne ; et quand la colonne « objet » d'une étiquette est remplie (la règle
LanguageTool, ou l'objet du constat quand la clé en porte plusieurs du même contrôle), le constat retrouvé doit
avoir cet objet. Les lignes « orthographe:languagetool » exigent un serveur LanguageTool local (variable LT_URL,
par exemple http://localhost:8081/v2/check) ; sans lui, elles sont sautées et le test le dit.
"""
from __future__ import annotations

import csv
import os
import unittest
from pathlib import Path

from coherence import rapport
from coherence.config import charger_config
from coherence.controles import CONTROLES
from coherence.corpus import charger
from coherence.modele import Options
from coherence.registre import Registre

ESPACE = Path(__file__).resolve().parents[2]
FIGE = ESPACE / "instantane" / "contre-analyse-c31accf2c.json.gz"
ETIQUETTES = ESPACE / "coherence" / "etiquettes-contre-analyse.tsv"
COLONNES = ["ligne", "cle", "controle", "objet", "motif"]
LT_URL = os.environ.get("LT_URL", "")
HORS_REGLE = {"semantique", "arbitrage", "sans objet"}
LIGNES_DU_TSV = 738


def cle_du_tsv(cle: str) -> str:
    """La clé du TSV dans la forme du vérificateur : « patchouli_books/<livre>/fr_fr/<fichier>#pages/0/text »
    devient « <livre>/<fichier>#/pages/0/text » (un livre sans pointeur : « <livre>/<fichier> »)."""
    if not cle.startswith("patchouli_books/"):
        return cle
    _, livre, _, reste = cle.split("/", 3)
    fichier, _, pointeur = reste.partition("#")
    return f"{livre}/{fichier}#/{pointeur.strip()}" if pointeur else f"{livre}/{fichier}"


def trouves(options) -> dict:
    """(étiquette, clé) -> objets des constats que les exceptions ne couvrent pas, sur la révision figée (la dette
    ne s'applique pas) ; un champ de livre vaut aussi pour son fichier."""
    corpus = charger(ESPACE.parent, ESPACE, instantane=FIGE)
    config = charger_config(ESPACE)
    registre = Registre(corpus, config)
    constats = []
    for verifier in CONTROLES.values():
        constats += verifier(corpus, registre, config, options)
    resultat = rapport.appliquer(constats, config.exceptions, [], corpus.texte, list(CONTROLES))
    objets = {}
    for c in resultat.bloquants + resultat.signales:
        etiquette = f"{c.controle}:languagetool" if c.detail.startswith("LanguageTool") else c.controle
        for cle in {c.cle, c.cle.split("#")[0]}:
            objets.setdefault((etiquette, cle), set()).add(c.objet)
    return objets


@unittest.skipUnless(FIGE.exists() and ETIQUETTES.exists(), "révision figée ou étiquettes absentes (tâche 25)")
class TestConstatsVerifies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(ETIQUETTES, encoding="utf-8") as f:
            lecteur = csv.DictReader(f, delimiter="\t")
            cls.colonnes, cls.etiquettes = lecteur.fieldnames, list(lecteur)
        options = Options(languagetool=bool(LT_URL), url_languagetool=LT_URL or Options().url_languagetool,
                          toutes_regles=True)
        cls.trouves = trouves(options)

    def test_chaque_ligne_est_etiquetee(self):
        self.assertEqual(self.colonnes, COLONNES)
        self.assertEqual(sorted(int(e["ligne"]) for e in self.etiquettes), list(range(1, LIGNES_DU_TSV + 1)))
        for e in self.etiquettes:
            self.assertIn(e["controle"], set(CONTROLES) | HORS_REGLE | {"orthographe:languagetool"}, e)
            if e["controle"] in HORS_REGLE:
                self.assertTrue(e["motif"].strip(), f"ligne {e['ligne']} : un motif est requis")
                self.assertFalse(e["objet"], f"ligne {e['ligne']} : une ligne hors règle n'a pas d'objet")
            if e["controle"].endswith(":languagetool"):
                self.assertTrue(e["objet"], f"ligne {e['ligne']} : une ligne LanguageTool nomme sa règle")

    def test_chaque_constat_de_regle_est_retrouve(self):
        manques, sautees = [], 0
        for e in self.etiquettes:
            if e["controle"] in HORS_REGLE:
                continue
            if e["controle"].endswith(":languagetool") and not LT_URL:
                sautees += 1
                continue
            objets, objet = self.trouves.get((e["controle"], e["cle"])), e.get("objet") or ""
            if objets is None or (objet and objet not in objets):
                manques.append(f"ligne {e['ligne']} [{e['controle']}{' ' + objet if objet else ''}] {e['cle']}")
        if sautees:
            print(f"\n{sautees} lignes LanguageTool sautées : LT_URL non défini")
        self.assertEqual(manques, [], f"{len(manques)} constats vérifiés non retrouvés")


if __name__ == "__main__":
    unittest.main()
