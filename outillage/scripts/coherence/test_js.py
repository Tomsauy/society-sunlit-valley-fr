"""Lecture des scripts KubeJS : infobulles, arguments des gabarits."""
import unittest

from coherence import js

SOURCE = """
// commentaire : n'importe quoi ( sans parenthèse fermante
ItemEvents.tooltip((tooltip) => {
  /* bloc ' " */
  tooltip.add("simplerecall:recall_potion", Text.translatable("tooltip.society.recall_potion").gray());
  tooltip.add(["whimsy_deco:phone", "whimsy_deco:blue_phone"], Text.translatable("tooltip.society.phone"));
  ajouterLignes("society:gatcha", Text.translatable("tooltip.society.gatcha_machine",
      Text.translatable("item.numismatics.sun")), (t) => t.gray());
  tooltip.addAdvanced("society:loupe", (item, advanced, text) => {
    text.add(1, Text.translatable("tooltip.society.loupe", `x(${item.count})`));
  });
  player.tell(Text.translatable("item.society.enriched_bone_meal.tree_fruit_season",
      Text.translatable("desc.sereneseasons.autumn").gold()));
  player.tell(Text.translatable("message.society.count", count, stack.getHoverName()));
});
"""


class TestAnalyse(unittest.TestCase):

    def setUp(self):
        self.sources = [js.sans_commentaires(SOURCE)]

    def test_arguments_de_premier_niveau(self):
        self.assertEqual(js.arguments('"a", f(1, [2, 3]), "x,y"'), ['"a"', "f(1, [2, 3])", '"x,y"'])

    def test_infobulles(self):
        bulles = js.infobulles(self.sources)
        self.assertEqual(bulles["tooltip.society.recall_potion"], {"simplerecall:recall_potion"})
        self.assertEqual(bulles["tooltip.society.phone"], {"whimsy_deco:phone", "whimsy_deco:blue_phone"})
        self.assertEqual(bulles["tooltip.society.gatcha_machine"], {"society:gatcha"})
        self.assertEqual(bulles["tooltip.society.loupe"], {"society:loupe"})
        self.assertNotIn("item.numismatics.sun", bulles)

    def test_types_des_arguments(self):
        args = js.arguments_gabarits(self.sources)
        self.assertEqual(args["tooltip.society.gatcha_machine"], [["nom_objet"]])
        self.assertEqual(args["item.society.enriched_bone_meal.tree_fruit_season"], [["saison"]])
        self.assertEqual(args["message.society.count"], [["autre"], ["nom_objet"]])
        self.assertNotIn("tooltip.society.phone", args)

    def test_hors_clone_git(self):
        """M3 : l'échec de git (hors d'un clone, ou sans origin/master) se distingue d'un amont sans script : None."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(js.blobs_amont(Path(d)))


if __name__ == "__main__":
    unittest.main()
