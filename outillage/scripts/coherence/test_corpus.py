"""Le corpus reconstitué comme le jeu fusionne les langues."""
import unittest

from coherence import corpus as corpus_mod
from coherence.fabrique import ESPACE, PACK, ecrire, pack_et_espace


class TestFusion(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.c = corpus_mod.charger(self.pack, self.espace)

    def test_ordre_vanilla_jar_projet(self):
        self.assertEqual((self.c.fr["block.minecraft.stone"], self.c.origine_fr["block.minecraft.stone"]),
                         ("Roche", "vanilla"))
        self.assertEqual(self.c.origine_fr["block.furniture.table"], "jar")
        self.assertEqual(self.c.origine_fr["item.society.bac"], "projet")
        self.assertEqual(self.c.fr_base.get("item.society.bac"), None)

    def test_anglais_vide_remplace_par_le_reconstitue(self):
        # Point de vigilance 3 : objet KubeJS sans displayName.
        self.assertEqual(self.c.en["item.society.cle_rouge"], "")
        self.assertEqual(self.c.anglais("item.society.cle_rouge"), "Red Key")
        self.assertEqual(self.c.anglais("item.society.inconnue"), "")

    def test_cle_definie_dans_deux_fichiers(self):
        # Point de vigilance 1 : valeur déterministe, doublon visible, aucun double compte.
        self.assertEqual(self.c.fr["block.furniture.sofa"], "Canapé")
        self.assertEqual(self.c.ns_projet["block.furniture.sofa"], "society")
        self.assertEqual(self.c.doublons(), {"block.furniture.sofa": {"furniture": "Sofa", "society": "Canapé"}})
        cles = [cle for cle, _ in self.c.textes_projet()]
        self.assertEqual(cles.count("block.furniture.sofa"), 1)
        self.assertNotIn("_comment", cles)  # clé de commentaire : jamais affichée

    def test_temoins_et_version(self):
        self.assertEqual(self.c.temoins[("society", "item.society.oubliee")], {"ko_kr": "잊힌"})
        self.assertEqual(self.c.version, "4.1.5")

    def test_texte_d_une_cle(self):
        self.assertEqual(self.c.texte("item.society.bac"), "Bac d'expédition")


class TestEntreesManquantes(unittest.TestCase):

    def test_json_illisible(self):
        dossier, pack, espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(dossier.cleanup)
        ecrire(pack, {"kubejs/assets/society/lang/fr_fr.json": '{"a": "b",}'})
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "fr_fr.json"):
            corpus_mod.charger(pack, espace)

    def test_fichier_de_l_espace_absent(self):
        """Le français et l'anglais de Mojang, l'anglais reconstitué : sans eux, des contrôles se videraient sans
        bruit. Chacun est requis, et l'erreur le nomme."""
        for chemin in corpus_mod.FICHIERS_REQUIS:
            with self.subTest(fichier=chemin):
                dossier, pack, espace = pack_et_espace(PACK, ESPACE)
                self.addCleanup(dossier.cleanup)
                (espace / chemin).unlink()
                with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, f"{chemin} introuvable"):
                    corpus_mod.charger(pack, espace)
        self.assertEqual(sorted(corpus_mod.FICHIERS_REQUIS), ["references/mc_en_us.json", "references/mc_fr_fr.json",
                                                              "society-corrected-en.json"])

    def test_arborescence_du_fork_sans_jars(self):
        # Point de vigilance 4 : message clair, pas de trace de pile.
        dossier, pack, espace = pack_et_espace(PACK, {})
        self.addCleanup(dossier.cleanup)
        (espace / "extracted" / ".garde").unlink()
        (espace / "extracted").rmdir()
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "--instantane"):
            corpus_mod.charger(pack, espace)


if __name__ == "__main__":
    unittest.main()
