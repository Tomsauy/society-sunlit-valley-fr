"""Lecture du SNBT des quêtes."""
import unittest

from coherence import snbt

QUETE = """{
	quests: [
		{
			id: "086A3F527E1A973E"
			icon: "constructionwand:core_angel"
			description: [
				"{ftbquests.chapter.tools.quest86A3F527E1A973E.description1}"
				""
			]
			tasks: [{
				id: "7F0933DA244DC98F"
				item: {
					Count: 1
					id: "itemfilters:or"
					tag: { items: [ { Count: 1b, id: "constructionwand:core_destruction" } ] }
				}
				title: "{ftbquests.chapter.tools.quest86A3F527E1A973E.task.9153904729612208527.title}"
				type: "item"
			}]
			x: 2.5d
		}
	]
}"""


class TestSNBT(unittest.TestCase):

    def test_quete_complete(self):
        q = snbt.lire(QUETE)["quests"][0]
        self.assertEqual(q["id"], "086A3F527E1A973E")
        self.assertEqual(q["tasks"][0]["item"]["tag"]["items"][0]["id"],
                         "constructionwand:core_destruction")
        self.assertEqual(q["x"], "2.5d")
        self.assertEqual(q["description"][1], "")

    def test_virgules_et_tableaux_types(self):
        self.assertEqual(snbt.lire('{a: [I; 1, 2], b: "x\\"y"}'), {"a": ["1", "2"], "b": 'x"y'})

    def test_texte_tronque(self):
        with self.assertRaises(snbt.ErreurSNBT):
            snbt.lire('{a: "x"')


if __name__ == "__main__":
    unittest.main()
