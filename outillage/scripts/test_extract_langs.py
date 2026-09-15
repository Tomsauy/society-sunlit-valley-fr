"""L'extracteur de langues, et surtout ce qu'il retire.

Écrire est facile ; oublier d'effacer est le défaut qui a laissé 86 clés d'un mod
retiré du pack traîner dans le corpus jusqu'à passer pour des lacunes.
"""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import extract_langs


class BaseTemporaire(unittest.TestCase):
    """Chaque test travaille sur ses propres dossiers jars/ et extracted/."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        racine = Path(self.tmp.name)
        self.jars = racine / "jars"
        self.out = racine / "extracted"
        self.jars.mkdir()
        self.out.mkdir()
        self._jars_avant, self._out_avant = extract_langs.JARS, extract_langs.OUT
        extract_langs.JARS, extract_langs.OUT = self.jars, self.out
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self._restaurer)

    def _restaurer(self):
        extract_langs.JARS, extract_langs.OUT = self._jars_avant, self._out_avant

    def ecrire_jar(self, nom, ns, locales):
        with zipfile.ZipFile(self.jars / f"{nom}.jar", "w") as z:
            for loc, data in locales.items():
                z.writestr(f"assets/{ns}/lang/{loc}.json", json.dumps(data))

    def extraits(self):
        return sorted(p.relative_to(self.out).as_posix()
                      for p in self.out.rglob("*.json"))


class TestElaguer(BaseTemporaire):

    def fabriquer(self, *chemins):
        for c in chemins:
            p = self.out / c
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}")
        return [self.out / c for c in chemins]

    def test_retire_ce_que_la_passe_n_a_pas_ecrit(self):
        garde, perime = self.fabriquer("mod-1.0/ns/en_us.json",
                                       "vieux-0.9/ns/en_us.json")
        retires = extract_langs.elaguer({garde})
        self.assertTrue(garde.exists())
        self.assertFalse(perime.exists())
        self.assertEqual([p.as_posix() for p in retires], ["vieux-0.9/ns/en_us.json"])

    def test_retire_les_dossiers_devenus_vides(self):
        garde, _ = self.fabriquer("mod-1.0/ns/en_us.json", "vieux-0.9/ns/en_us.json")
        extract_langs.elaguer({garde})
        self.assertFalse((self.out / "vieux-0.9").exists())
        self.assertTrue((self.out / "mod-1.0" / "ns").is_dir())

    def test_une_langue_abandonnee_s_en_va_sans_emporter_le_mod(self):
        garde, _ = self.fabriquer("mod-1.0/ns/en_us.json", "mod-1.0/ns/ko_kr.json")
        extract_langs.elaguer({garde})
        self.assertEqual(self.extraits(), ["mod-1.0/ns/en_us.json"])

    def test_ne_retire_rien_quand_tout_est_recouvert(self):
        gardes = self.fabriquer("a-1.0/ns/en_us.json", "b-2.0/ns/fr_fr.json")
        self.assertEqual(extract_langs.elaguer(set(gardes)), [])
        self.assertEqual(len(self.extraits()), 2)


class TestMain(BaseTemporaire):

    def test_un_jar_retire_emporte_son_extrait(self):
        self.ecrire_jar("emixx-forge-1.5.1", "emixx", {"en_us": {"a": "A"}})
        self.ecrire_jar("emi-1.1.24", "emi", {"en_us": {"b": "B"}})
        extract_langs.main()
        self.assertEqual(self.extraits(),
                         ["emi-1.1.24/emi/en_us.json", "emixx-forge-1.5.1/emixx/en_us.json"])

        # 4.1.5 : EMI++ sort du pack. Son extrait ne doit pas lui survivre.
        (self.jars / "emixx-forge-1.5.1.jar").unlink()
        extract_langs.main()
        self.assertEqual(self.extraits(), ["emi-1.1.24/emi/en_us.json"])

    def test_une_montee_de_version_ne_laisse_pas_l_ancienne(self):
        self.ecrire_jar("mod-1.0", "ns", {"en_us": {"a": "A"}})
        extract_langs.main()
        (self.jars / "mod-1.0.jar").unlink()
        self.ecrire_jar("mod-2.0", "ns", {"en_us": {"a": "A2"}})
        extract_langs.main()
        self.assertEqual(self.extraits(), ["mod-2.0/ns/en_us.json"])

    def test_le_contenu_reste_juste(self):
        self.ecrire_jar("mod-1.0", "ns", {"en_us": {"b": "B", "a": "A"}})
        extract_langs.main()
        d = json.loads((self.out / "mod-1.0/ns/en_us.json").read_text(encoding="utf-8"))
        self.assertEqual(d, {"a": "A", "b": "B"})


if __name__ == "__main__":
    unittest.main()
