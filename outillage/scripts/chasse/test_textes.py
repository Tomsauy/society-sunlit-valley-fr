"""Inventaire des textes de la chasse et témoins (spec 3 §3, §5)."""
import json
import tempfile
import unittest
from pathlib import Path

from chasse.textes import inventaire, lignes_du_journal, temoins, unite_de
from coherence.corpus import ChampLivre, Corpus


def corpus_d_essai():
    c = Corpus()
    valeurs = {
        "block.minecraft.stone": ("Stone", "Roche", "vanilla"),
        "item.society.apple": ("Apple", "Pomme", "projet"),
        "item.society.vide": ("Empty", "", "projet"),
        "_comment": ("", "Objets", "projet"),
        "item.society.morte": ("Dead", "Morte", "projet"),
        "item.society.sans_anglais": ("", "Sans anglais", "projet"),
        "wood_type.atmospheric.aspen": ("", "Tremble", "projet"),
        "ftbquests.chapter.welcome.quest1.title": ("Hi", "Salut", "projet"),
        "block.create.cog": ("Cogwheel", "Roue dentée", "jar"),
    }
    for cle, (en, fr, origine) in valeurs.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
    c.ns_projet.update({"item.society.apple": "society", "ftbquests.chapter.welcome.quest1.title": "ftbquestlocalizer",
                        "wood_type.atmospheric.aspen": "everycomp"})
    c.livres = [ChampLivre("almanac/e.json", "/name", "Goat", "Chèvre", ()), ChampLivre("almanac/e.json", "/text", "A", "", ())]
    c.journal_en = "^^^\n## 4.1.5\n---\n- Added x\n- Fixed y\n"
    c.journal_fr = "^^^\nUn café\n## 4.1.5\n---\n- Ajout de x\n- Correction de y\n"
    return c


class TestInventaire(unittest.TestCase):

    def test_ce_qui_compte(self):
        textes, exclus = inventaire(corpus_d_essai(), {"block.create.cog": "create"}, frozenset({"item.society.morte"}))
        ids = [t.id for t in textes]
        self.assertEqual(ids, ["almanac/e.json#/name", "block.create.cog", "ftbquests.chapter.welcome.quest1.title",
                               "item.society.apple", "journal#3", "journal#5", "journal#6", "wood_type.atmospheric.aspen"])
        self.assertEqual(exclus, {"mojang": 1, "vide": 2, "commentaire": 1, "morte": 1, "sans anglais": 1})
        par_id = {t.id: t for t in textes}
        self.assertEqual(par_id["ftbquests.chapter.welcome.quest1.title"].unite, "quetes:welcome")
        self.assertEqual(par_id["wood_type.atmospheric.aspen"].unite, "everycomp")
        self.assertEqual((par_id["block.create.cog"].origine, par_id["block.create.cog"].unite), ("jar", "create"))
        self.assertEqual((par_id["journal#5"].en, par_id["journal#5"].fr), ("- Added x", "- Ajout de x"))

    def test_journal_apparie_par_rang(self):
        self.assertEqual(lignes_du_journal("## A\n- a\n- b\n", "## A\n\n- a'\n"), [(1, "## A", "## A"), (3, "- a", "- a'")])

    def test_unite(self):
        self.assertEqual(unite_de("block_type.everycomp.stairs", "everycomp"), "everycomp")
        self.assertEqual(unite_de("item.quark.x", "quark"), "quark")

    def test_temoins(self):
        with tempfile.TemporaryDirectory() as d:
            ns = Path(d) / "extracted" / "create-6" / "create"
            ns.mkdir(parents=True)
            (ns / "es_es.json").write_text(json.dumps({"block.create.cog": "Engranaje", "x": ""}), encoding="utf-8")
            c = corpus_d_essai()
            c.temoins[("society", "item.society.apple")] = {"ko_kr": "사과", "zh_cn": ""}
            t = temoins(c, d)
            self.assertEqual(t, {"block.create.cog": {"es_es": "Engranaje"}, "item.society.apple": {"ko_kr": "사과"}})


if __name__ == "__main__":
    unittest.main()
