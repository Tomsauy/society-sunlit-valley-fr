"""L'instantané : même rapport sans jars ni scripts."""
import shutil
import unittest

from coherence import corpus as corpus_mod
from coherence.fabrique import ESPACE, PACK_COMPLET, ecrire, pack_et_espace


def copier_le_francais(pack, fork):
    """Ne garde que ce que contient le fork : le français du projet."""
    motifs = ("kubejs/assets/*/lang/fr_fr.json", "patchouli_books/*/fr_fr/**/*.json",
              "config/fancymenu/assets/changelog_fr_fr.markdown")
    for motif in motifs:
        for chemin in pack.glob(motif):
            cible = fork / chemin.relative_to(pack)
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(chemin, cible)


class TestInstantane(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK_COMPLET, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.base = self.pack.parent
        self.chemin = self.base / "instantane" / "4.1.5.json.gz"

    def test_parite_clone_et_fork(self):
        complet = corpus_mod.charger(self.pack, self.espace)
        corpus_mod.ecrire_instantane(complet, self.chemin)
        fork = self.base / "fork"
        copier_le_francais(self.pack, fork)
        depuis = corpus_mod.charger(fork, self.base / "vide", instantane=self.chemin)
        self.assertEqual(depuis, complet)

    def test_octets_reproductibles(self):
        complet = corpus_mod.charger(self.pack, self.espace)
        corpus_mod.ecrire_instantane(complet, self.chemin)
        premier = self.chemin.read_bytes()
        corpus_mod.ecrire_instantane(complet, self.chemin)
        self.assertEqual(self.chemin.read_bytes(), premier)

    def test_instantane_absent(self):
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "introuvable"):
            corpus_mod.charger(self.pack, self.espace, instantane=self.base / "rien.json.gz")

    def test_version_differente(self):
        corpus_mod.ecrire_instantane(corpus_mod.charger(self.pack, self.espace), self.chemin)
        ecrire(self.pack, {"pakku.json": {"version": "4.1.6"}})
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "4.1.5.*4.1.6"):
            corpus_mod.charger(self.pack, self.espace, instantane=self.chemin)

    def test_version_declaree_par_l_espace_du_fork(self):
        corpus_mod.ecrire_instantane(corpus_mod.charger(self.pack, self.espace), self.chemin)
        fork = self.base / "fork"
        copier_le_francais(self.pack, fork)
        ecrire(self.base / "outillage", {"version-du-pack.txt": "4.1.6\n"})
        with self.assertRaisesRegex(corpus_mod.CorpusIncomplet, "4.1.6"):
            corpus_mod.charger(fork, self.base / "outillage", instantane=self.chemin)

    def test_instantane_complet(self):
        complet = corpus_mod.charger(self.pack, self.espace)
        corpus_mod.ecrire_instantane(complet, self.chemin, complet=True)
        depuis = corpus_mod.charger(self.base / "nulle-part", self.base / "vide", instantane=self.chemin)
        self.assertEqual(depuis, complet)


if __name__ == "__main__":
    unittest.main()
