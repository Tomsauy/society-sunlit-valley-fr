"""Déterminants et prépositions devant les %s."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options

ARGUMENTS = {"tooltip.society.gatcha_machine": [["nom_objet"]], "item.society.saison": [["saison"]],
             "msg.nombre": [["autre"]], "msg.ordre": [["autre"], ["nom_objet"]], "msg.elision": [["nom_objet"]]}
FR = {
    "tooltip.society.gatcha_machine": "Clic droit avec un %s pour acheter une capsule",
    "item.society.saison": "Cet arbre ne porte des fruits qu'en %s !",
    "msg.nombre": "Le %s est prêt",
    "msg.ordre": "%1$s donne le %2$s",
    "msg.elision": "Utilise l'%s",
    "msg.inconnu": "Pose la %s ici",
    "msg.table": "Pose la %s ici",
    "msg.pourcent": "Gagne 5%%s de plus",
}


def constats(gabarits=None):
    c = Corpus(arguments=ARGUMENTS)
    for cle, fr in FR.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = "x %s", fr, "projet"
    config = Config(espace=Path("."), gabarits=gabarits or {"msg.table": [["autre"]]})
    return {(x.cle, x.statut) for x in CONTROLES["gabarits"](c, None, config, Options())}


class TestGabarits(unittest.TestCase):

    def test_constats(self):
        self.assertEqual(constats(), {
            ("tooltip.society.gatcha_machine", BLOQUANT), ("item.society.saison", BLOQUANT),
            ("msg.ordre", BLOQUANT), ("msg.elision", BLOQUANT), ("msg.inconnu", SIGNALE)})

    def test_determinant_apres_elision(self):
        c = Corpus(arguments={"msg.alimentation": [["nom_objet"]]})
        textes = {"msg.alimentation": "Nécessite l'alimentation d'un %s", "msg.inconnue": "Branche-le à l'aide d'une %s"}
        for cle, fr in textes.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = "x %s", fr, "projet"
        config = Config(espace=Path("."))
        resultat = {(x.cle, x.statut) for x in CONTROLES["gabarits"](c, None, config, Options())}
        self.assertEqual(resultat, {("msg.alimentation", BLOQUANT), ("msg.inconnue", SIGNALE)})


if __name__ == "__main__":
    unittest.main()
