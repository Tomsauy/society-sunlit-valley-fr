"""Livres, journal, quêtes, boutiques et essences dans le corpus."""
import unittest

from coherence import corpus as corpus_mod
from coherence.fabrique import ESPACE, PACK_COMPLET, ecrire, pack_et_espace


class TestSources(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK_COMPLET, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.c = corpus_mod.charger(self.pack, self.espace)

    def test_champs_des_livres_et_leurs_objets(self):
        champs = {ch.pointeur: ch for ch in self.c.livres}
        self.assertEqual(sorted(champs), ["/name", "/pages/0/text", "/pages/1/text"])
        self.assertEqual(champs["/name"].fr, "Chèvre")
        self.assertEqual(champs["/name"].cle, "almanac/entries/animals/goat.json#/name")
        self.assertEqual(champs["/pages/0/text"].objets, ("minecraft:goat", "society:large_goat_milk"))
        self.assertEqual(self.c.texte("almanac/entries/animals/goat.json#/pages/1/text"), "Une chèvre.")

    def test_livre_sans_francais(self):
        ecrire(self.pack, {"patchouli_books/almanac/en_us/entries/animals/cow.json": {"name": "Cow"}})
        c = corpus_mod.charger(self.pack, self.espace)
        self.assertEqual(next(ch.fr for ch in c.livres if ch.fichier.endswith("cow.json")), "")

    def test_journal(self):
        self.assertIn("- Added a thing", self.c.journal_en)
        self.assertIn("- Ajout d'une chose", self.c.journal_fr)

    def test_quetes(self):
        (quete,) = self.c.quetes
        self.assertEqual(quete.identifiant, "86A3F527E1A973E")
        self.assertEqual(quete.chapitre, "tools")
        self.assertEqual(quete.icone, "constructionwand:core_angel")
        self.assertIn("ftbquests.chapter.tools.quest86A3F527E1A973E.description1", quete.cles)
        (tache,) = quete.taches
        self.assertEqual(tache.cle_titre,
                         "ftbquests.chapter.tools.quest86A3F527E1A973E.task.9153904729612208527.title")
        self.assertIn("constructionwand:core_destruction", tache.objets)

    def test_boutiques_sans_nbt(self):
        self.assertEqual(self.c.vendus, {"society:pig_race_ticket"})

    def test_essences_activees(self):
        self.assertEqual(self.c.essences, ["leaves_type.autumnity.maple", "wood_type.atmospheric.rosewood"])

    def test_journal_fr_manquant_avec_anglais_leve(self):
        # Résidu 1 : notre changelog est facultatif dans le code, mais pas quand l'anglais existe.
        (self.pack / "config/fancymenu/assets/changelog_fr_fr.markdown").unlink()
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "changelog_fr_fr.markdown"):
            corpus_mod.charger(self.pack, self.espace)

    def test_journal_absent_des_deux_cotes_reste_legitime(self):
        (self.pack / "config/fancymenu/assets/changelog_en_us.markdown").unlink()
        (self.pack / "config/fancymenu/assets/changelog_fr_fr.markdown").unlink()
        c = corpus_mod.charger(self.pack, self.espace)
        self.assertEqual((c.journal_en, c.journal_fr), ("", ""))

    def test_everycomp_toml_manquant_avec_essences_dans_le_corpus_leve(self):
        # Résidu 1 : sans le toml, `_essences` ne peut plus dire si Every Compat est présent ; le corpus
        # le sait déjà par les clés wood_type./leaves_type. que le jar de la mod y a mises.
        (self.pack / "config/everycomp-entries.toml").unlink()
        ecrire(self.espace, {"extracted/everycomp-1.0/everycomp/en_us.json": {"leaves_type.minecraft.oak": "Oak"}})
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "everycomp-entries.toml"):
            corpus_mod.charger(self.pack, self.espace)

    def test_everycomp_toml_manquant_sans_essences_reste_legitime(self):
        (self.pack / "config/everycomp-entries.toml").unlink()
        c = corpus_mod.charger(self.pack, self.espace)
        self.assertEqual(c.essences, [])

    def test_snbt_illisible(self):
        ecrire(self.pack, {"config/ftbquests/quests/chapters/casse.snbt": "{ quests: ["})
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "casse.snbt"):
            corpus_mod.charger(self.pack, self.espace)


if __name__ == "__main__":
    unittest.main()
