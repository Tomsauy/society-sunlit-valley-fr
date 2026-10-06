"""Injection d'erreurs (spec §12, critère 2) : au moins 100 erreurs par classe, toutes détectées.

Chaque classe copie le corpus figé de la contre-analyse, injecte ses erreurs sur des clés que le
contrôle ne signalait pas (ou sur des clés créées pour l'occasion), relance le contrôle et exige un
constat sur chaque clé touchée. Graine fixe : 20260928.
"""
from __future__ import annotations

import copy
import random
import re
import unittest
from pathlib import Path

from compare_accents import plier
from validate_translation import TOKEN

from coherence.config import charger_config
from coherence.controles import CONTROLES
from coherence.controles import references as ref
from coherence.controles.accents import exemptes as exemptes_accents, formes_uniques, homographes
from coherence.controles.anglais_residuel import exemptes, lexique
from coherence.controles.casse import metiers_et_boutiques
from coherence.controles.decisions import valeur_decidee
from coherence.controles.nombres import nombres_en, nombres_fr
from coherence.corpus import charger
from coherence.modele import Options
from coherence.police import lignes
from coherence.registre import CLE_OBJET, Registre
from coherence.regles_derivees import Familles
from coherence.texte import contient, jetons, meme_casse, mots, sans_codes

ESPACE = Path(__file__).resolve().parents[2]
FIGE = ESPACE / "instantane" / "contre-analyse-c31accf2c.json.gz"
MINIMUM, ECHANTILLON = 100, 150
MOT = re.compile(r"[^\W\d_]+")
AVEC_REGISTRE = {"casse", "homonymes", "references", "terminologie"}
APRES_DETERMINANT = re.compile(r"\b(?:le|la|les|un|une|des|du|ton|ta|tes|ce|cette|ces) (\w+)")


def lancer(controle, corpus, config) -> set:
    registre = Registre(corpus, config) if controle in AVEC_REGISTRE else None
    return {c.cle for c in CONTROLES[controle](corpus, registre, config, Options())}


def ajouter(corpus, cle, fr, modele=""):
    """Crée une clé du projet, dans le namespace de `modele`."""
    corpus.fr[cle], corpus.origine_fr[cle] = fr, "projet"
    corpus.ns_projet[cle] = corpus.ns_projet.get(modele, "society")
    return cle


# Dérivés que Mojang nomme d'un autre nom que leur base : « Oak Fence Gate », un portillon, ne cite pas « Oak Fence ».
DERIVES = {("fence", "gate"), ("glass", "pane"), ("window", "pane"), ("rose", "bush")}
ECHANTILLON_INDEPENDANT = 400


def noms_cites(suite, motifs, est_un_nom) -> list:
    """Spec §6, étape 1, sans le code du contrôle : les noms citables de l'anglais (`suite`, ses mots), le plus long
    d'abord, sans chevauchement. Un nom ne se cite pas lui-même en entier ; « Light Blue » et « Light Gray » sont une
    seule couleur de teinture (« Light Blue Curtain » ne cite pas « Blue Curtain ») ; un dérivé que Mojang renomme
    n'est pas sa base."""
    i, trouves = 0, []
    while i < len(suite):
        if i and suite[i - 1] == mots("light")[0] and suite[i] in mots("blue gray"):
            i += 1
            continue
        for k in range(min(8, len(suite) - i), 0, -1):
            m = tuple(suite[i:i + k])
            derive = i + k < len(suite) and (m[-1], suite[i + k]) in DERIVES
            if m in motifs and not derive and not (est_un_nom and i == 0 and k == len(suite)):
                trouves.append(m)
                i += k
                break
        else:
            i += 1
    return trouves


def propres(config, registre, corpus) -> set:
    """Les mots que casse exempte, aux mêmes sources que le contrôle : ceux des termes gardés et des noms des PNJ, et
    ceux des métiers, des boutiques et de majuscules.json, dont la majuscule est juste (STYLE §2, décision du
    29/09/2026) : « Oeuf d'apparition de Ribbit Pêcheur » ne serait pas une erreur injectée. Un métier juste après
    « de » dans un nom (« Chapeau de Fermier »), que casse relève, est écarté aussi : la classe ne l'injecte pas."""
    termes = config.termes_gardes() + registre.noms_de_pnj() + metiers_et_boutiques(corpus) + list(config.majuscules)
    return {m for t in termes for m in t.split()}


@unittest.skipUnless(FIGE.exists(), "révision figée absente (tâche 25)")
class TestMutations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.corpus = charger(ESPACE.parent, ESPACE, instantane=FIGE)
        cls.config = charger_config(ESPACE)

    def detecter(self, controle, muter, regles=None):
        corpus, config = copy.deepcopy(self.corpus), copy.deepcopy(self.config)
        config.regles.update(regles or {})
        avant = lancer(controle, corpus, config)
        touchees = set(muter(corpus, config, avant, random.Random(20260928)))
        manquees = sorted(touchees - lancer(controle, corpus, config))
        self.assertGreaterEqual(len(touchees), MINIMUM, f"{controle} : trop peu d'erreurs injectées")
        self.assertEqual(manquees, [], f"{controle} : {len(manquees)} sur {len(touchees)} non détectées")

    def test_accent_retire(self):
        def muter(corpus, config, avant, rng):
            formes = {pli: forme.lower() for pli, forme in formes_uniques(config).items()}
            gardes, homs = exemptes_accents(config), homographes(corpus, config, formes)
            candidates = []
            for cle, fr in corpus.textes_projet():
                dans_un_nom = bool(CLE_OBJET.match(cle))
                visibles = MOT.findall(sans_codes(fr))  # un mot caché dans un code ne compte pas
                mot = next((m for m in visibles if formes.get(plier(m)) == m.lower() and plier(m) not in gardes
                            and (dans_un_nom or plier(m) not in homs)
                            and len(re.findall(rf"(?<!\w){re.escape(m)}(?!\w)", fr)) == visibles.count(m)), None)
                if mot and cle not in avant:
                    candidates.append((cle, fr, mot))
            for cle, fr, mot in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = re.sub(rf"(?<!\w){re.escape(mot)}(?!\w)", meme_casse(mot, plier(mot)), fr)
                yield cle
        self.detecter("accents", muter)

    def test_nom_cite_remplace(self):
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            index, liens = ref._index(registre), ref._liens(corpus)
            autres = [n for n in registre.noms.values() if registre.citable(n)]
            candidates = []
            for cle, en, fr, ns in ref._textes(corpus):
                if cle in avant or "#" in cle:
                    continue
                for _, noms in ref._citations(jetons(en), index, cle in registre.noms):
                    noms = [n for n in noms if n.cle != cle]
                    vise = ref._resoudre(cle, ns, noms, liens, {}, set()) if noms else None
                    if vise and re.search(re.escape(vise.fr), fr, re.I):
                        candidates.append((cle, fr, vise))
                        break
            for i, (cle, fr, vise) in enumerate(rng.sample(candidates, min(len(candidates), ECHANTILLON))):
                if i % 2:  # un synonyme : la tête du nom change
                    nouveau = "Machin" + (" " + vise.fr.split(" ", 1)[1] if " " in vise.fr else "")
                else:      # le nom d'un autre objet
                    nouveau = rng.choice(autres).fr
                mute = re.sub(re.escape(vise.fr), lambda m: nouveau, fr, flags=re.I)
                if not contient(mute, vise.fr):
                    corpus.fr[cle] = mute
                    yield cle
        self.detecter("references", muter)

    def test_nom_cite_remplace_selection_independante(self):
        """La même erreur, sur une population que le contrôle ne choisit pas : la sélection ne passe ni par _citations
        ni par _resoudre. Un texte que lit le contrôle est retenu quand son anglais cite, au sens de la spec §6, un nom
        citable du registre dont tous les porteurs ont le même français, et que son français contient ce nom ; le nom y
        est remplacé par celui d'un autre objet ou par un synonyme.

        « Citer » suit la spec §6 (voir noms_cites). Les erreurs sont indépendantes : le nom affiché d'un porteur que
        cite un texte muté ne change pas, sans quoi le texte muté redeviendrait conforme au nom muté.

        La règle « même mod » est retirée (fiche du 30/09 : meme-mod) : un nom d'un seul mot venu d'un autre mod peut
        être muté comme un autre ; un matériau se déclare par une exception ou dans mots_generiques.json."""
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            candidates = []
            for cle, en, fr, _ in ref._textes(corpus):
                if cle in avant:
                    continue
                cites = noms_cites(mots(en), registre.par_anglais, cle in registre.noms)
                tous = {n.cle for m in cites for n in registre.par_anglais[m]}
                for m in cites:
                    noms = [n for n in registre.par_anglais[m] if n.cle != cle]
                    if noms and len({mots(n.fr) for n in noms}) == 1 and re.search(re.escape(noms[0].fr), fr, re.I):
                        candidates.append((cle, fr, noms[0], tous))
                        break
            autres = [n for n in registre.noms.values() if registre.citable(n)]
            mutees, gardes = set(), set()
            for i, (cle, fr, vise, tous) in enumerate(rng.sample(candidates, min(len(candidates), ECHANTILLON_INDEPENDANT))):
                if cle in gardes or tous & mutees:
                    continue
                if i % 2:  # un synonyme : la tête du nom change
                    nouveau = "Machin" + (" " + vise.fr.split(" ", 1)[1] if " " in vise.fr else "")
                else:      # le nom d'un autre objet
                    nouveau = rng.choice(autres).fr
                mute = re.sub(re.escape(vise.fr), lambda m: nouveau, fr, flags=re.I)
                if not contient(mute, vise.fr):
                    if "#" in cle:
                        corpus.champ(cle).fr = mute
                    else:
                        corpus.fr[cle] = mute
                    gardes |= tous
                    mutees.add(cle)
            return mutees
        self.detecter("references", muter)

    def test_famille_cassee(self):
        def muter(corpus, config, avant, rng):
            f = Familles(corpus, config)
            justes = sorted(c for c in f.membres if c not in avant and corpus.fr.get(c) and f.attendu(c) == corpus.fr[c])
            for cle in rng.sample(justes, min(len(justes), ECHANTILLON)):
                fr = corpus.fr[cle]
                variantes = [v for v in (fr.replace("d'", "de ", 1), fr[:-1] if fr[-1] in "es" else fr + "e",
                                         fr.replace(" de ", " du ", 1)) if v != fr]
                corpus.fr[cle] = rng.choice(variantes)
                yield cle
        self.detecter("familles", muter)

    def test_code_supprime(self):
        def muter(corpus, config, avant, rng):
            candidates = [(c, fr) for c, fr in corpus.textes_projet()
                          if c not in avant and corpus.anglais(c) and TOKEN.search(fr)]
            for cle, fr in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                m = rng.choice(list(TOKEN.finditer(fr)))
                corpus.fr[cle] = fr[:m.start()] + fr[m.end():]
                yield cle
        self.detecter("codes", muter)

    def test_vouvoiement(self):
        tutoiement = re.compile(r"\b(tu|ton|ta|tes)\b")
        vous = {"tu": "vous", "ton": "votre", "ta": "votre", "tes": "vos"}

        def muter(corpus, config, avant, rng):
            candidates = [(c, fr) for c, fr in corpus.textes_projet() if c not in avant and tutoiement.search(fr)
                          and (corpus.ns_projet.get(c, "").startswith("society")
                               or corpus.ns_projet.get(c) in ("dialog", "ftbquestlocalizer"))]
            for cle, fr in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = tutoiement.sub(lambda m: vous[m.group(1)], fr, count=1)
                yield cle
        self.detecter("conventions", muter)

    def test_determinant_devant_un_nom_d_objet(self):
        determinants = ("le ", "la ", "un ", "une ", "l'", "du ", "au ", "ce ", "cette ", "son ", "sa ", "ton ",
                        "ta ", "mon ", "ma ")
        deja = re.compile(r"(?i)(?:\b(?:le|la|les|un|une|du|des|au|aux|ce|cet|cette|ces|mon|ma|mes|ton|ta|tes"
                          r"|son|sa|ses|de la)\s+|\b[ld]')$")

        def muter(corpus, config, avant, rng):
            modeles = []
            for cle, types in sorted({**corpus.arguments, **config.gabarits}.items()):
                m = re.search(r"%(?:1\$)?s", corpus.fr.get(cle, ""))
                if types and "nom_objet" in types[0] and m and corpus.origine_fr.get(cle) == "projet":
                    modeles.append((cle, corpus.fr[cle], m))
            assert modeles, "aucun gabarit dont le premier argument est un nom d'objet"
            for i in range(MINIMUM + 20):
                cle, fr, m = modeles[i % len(modeles)]
                debut = deja.sub("", fr[:m.start()])
                if debut and not debut.endswith((" ", "(", "«", '"')):
                    debut += " "
                mutant = ajouter(corpus, f"{cle}.mutant{i}", debut + determinants[i % len(determinants)] + fr[m.start():], cle)
                corpus.arguments[mutant] = [["nom_objet"]]
                yield mutant
        self.detecter("gabarits", muter)

    def test_essence_retiree(self):
        def muter(corpus, config, avant, rng):
            retirees = [e for e in corpus.essences if corpus.fr.get(e) and e not in avant]
            for essence in retirees:
                del corpus.fr[essence]
                yield essence
            for i in range(max(0, MINIMUM + 10 - len(retirees))):
                corpus.essences.append(f"wood_type.mutant.essence{i}")
                yield f"wood_type.mutant.essence{i}"
        self.detecter("everycomp", muter)

    def test_nom_de_boutique_allonge(self):
        def muter(corpus, config, avant, rng):
            touchees = set()
            for ident in sorted(corpus.vendus):
                ns, _, chemin = ident.partition(":")
                cle = next((c for c in (f"item.{ns}.{chemin}", f"block.{ns}.{chemin}") if corpus.fr.get(c)), None)
                if cle and cle not in avant and corpus.origine_fr.get(cle) == "projet":
                    while lignes(corpus.fr[cle]) <= 2:
                        corpus.fr[cle] += " extraordinaire"
                    touchees.add(cle)
            for i in range(max(0, MINIMUM + 10 - len(touchees))):
                corpus.vendus.add(f"mutant:objet{i}")
                touchees.add(ajouter(corpus, f"item.mutant.objet{i}", "Appât pour poisson-chat des cavernes géant"))
            return touchees
        self.detecter("largeur", muter)

    def test_script_amont_modifie(self):
        def muter(corpus, config, avant, rng):
            for chemin in [c for c in config.scripts_patches if c not in avant]:
                corpus.scripts_amont[chemin] = "f" * 40
                yield chemin
            for i in range(MINIMUM):
                chemin = f"kubejs/mutant/script{i}.js"
                config.scripts_patches[chemin] = {"base": f"{i:040d}", "motif": "mutation"}
                corpus.scripts_amont[chemin] = f"{i + 1:040d}"
                yield chemin
        self.detecter("scripts_patches", muter)

    def test_valeur_decidee_alteree(self):
        def muter(corpus, config, avant, rng):
            conformes = sorted(c for c, d in config.provenance.get("cles", {}).items()
                               if c not in avant and valeur_decidee(d) is not None and corpus.fr.get(c) == valeur_decidee(d))
            for cle in rng.sample(conformes, min(len(conformes), ECHANTILLON)):
                corpus.fr[cle] += " (modifié)"
                yield cle
        self.detecter("decisions", muter)

    def test_forme_interdite_reintroduite(self):
        def muter(corpus, config, avant, rng):
            textes = [(c, fr) for c, fr in corpus.textes_projet() if c not in avant]
            formes = config.formes_interdites
            assert formes, "formes_interdites.json est vide"
            for i in range(MINIMUM + 20):
                cle, fr = textes[rng.randrange(len(textes))]
                yield ajouter(corpus, f"{cle}.mutant{i}", f"{fr} {formes[i % len(formes)]['forme']}", cle)
        self.detecter("orthographe", muter)

    def test_majuscule_interne_ajoutee(self):
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            exemptes = propres(config, registre, corpus)
            candidates = []
            for nom in registre.noms.values():
                trouves = list(MOT.finditer(nom.fr))
                if CLE_OBJET.match(nom.cle) and nom.origine != "vanilla" and nom.cle not in avant and len(trouves) >= 2:
                    m = trouves[-1]
                    if len(m.group(0)) > 1 and m.group(0).islower() and m.group(0).capitalize() not in exemptes:
                        candidates.append((nom.cle, nom.fr, m.start(), m.end(), m.group(0)))
            for cle, fr, debut, fin, mot in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = fr[:debut] + mot.capitalize() + fr[fin:]
                yield cle
        self.detecter("casse", muter)

    def test_majuscule_en_corps_de_phrase(self):
        """Spec 2 §14 : casse_textes active, un nom d'objet cité en minuscules en corps de phrase, sans mise en valeur,
        reçoit une majuscule : chaque texte ainsi touché est relevé."""
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            exemptes = {m.lower() for t in config.termes_gardes() + metiers_et_boutiques(corpus) + list(config.majuscules)
                        + registre.noms_de_pnj() for m in MOT.findall(t)}
            par_premier = {}
            for nom in {n.fr.lower() for n in registre.noms.values()
                        if CLE_OBJET.match(n.cle) and n.origine != "vanilla" and len(n.fr) > 3 and MOT.findall(n.fr)
                        and MOT.findall(n.fr)[0].lower() not in exemptes}:
                par_premier.setdefault(MOT.findall(nom)[0], []).append(nom)
            candidates = []
            for cle, fr in corpus.textes_projet():
                if cle in avant or cle in registre.noms or re.search(r"[§&$%<>]", fr) or len(fr) > 300:
                    continue
                for m in APRES_DETERMINANT.finditer(fr):
                    i = m.start(1)
                    if any(fr.startswith(n, i) and not fr[i + len(n):i + len(n) + 1].isalnum()
                           for n in par_premier.get(m.group(1), ())):
                        candidates.append((cle, fr, i))
                        break
            for cle, fr, i in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = fr[:i] + fr[i].upper() + fr[i + 1:]
                yield cle
        self.detecter("casse", muter, regles={"casse_textes": True})

    def test_mot_anglais_recopie(self):
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            seuls, _ = exemptes(config, registre)
            exclus = lexique(corpus, config) | seuls
            candidates = []
            for cle, fr in corpus.textes_projet():  # le contrôle regarde les mots recopiés dans les noms
                if cle in avant or not CLE_OBJET.match(cle):
                    continue
                deja = set(mots(fr))
                etrangers = [w for w in re.findall(r"[A-Za-z]{4,}", corpus.anglais(cle))
                             if len(mots(w)[0]) >= 4 and mots(w)[0] not in exclus and mots(w)[0] not in deja]
                if etrangers:
                    candidates.append((cle, fr, etrangers[0]))
            for cle, fr, mot in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = f"{fr} {mot}"
                yield cle
        self.detecter("anglais_residuel", muter)

    def test_terme_impose_remplace_par_un_synonyme(self):
        def muter(corpus, config, avant, rng):
            registre = Registre(corpus, config)
            candidates = []
            for terme in (t for t in config.termes_imposes if t.get("interdits")):
                anglais = re.compile(rf"\b(?:{terme['anglais']})\b", re.I)
                filtre = re.compile(terme["cles"]) if terme.get("cles") else None
                formes = terme["francais"] if isinstance(terme["francais"], list) else [terme["francais"]]
                portee = terme.get("portee", "tout")
                for cle, fr in corpus.textes_projet():
                    est_nom = cle in registre.noms
                    if (cle in avant or (filtre and not filtre.search(cle)) or (portee == "noms" and not est_nom)
                            or (portee == "textes" and est_nom) or not anglais.search(corpus.anglais(cle))):
                        continue
                    forme = next((f for f in formes if re.search(re.escape(f), fr, re.I)), None)
                    if forme:
                        candidates.append((cle, fr, forme, formes, terme["interdits"]))
            touchees = set()
            for i, (cle, fr, forme, formes, interdits) in enumerate(rng.sample(candidates, min(len(candidates), ECHANTILLON))):
                mute = re.sub(re.escape(forme), lambda m: interdits[i % len(interdits)], fr, flags=re.I)
                if cle not in touchees and not any(contient(mute, f) for f in formes):
                    corpus.fr[cle] = mute
                    touchees.add(cle)
            return touchees
        self.detecter("terminologie", muter)

    def test_nombre_change(self):
        """Spec 3 §5 : un nombre de l'anglais changé dans le français (« 3 » devient « 4 »), là où il n'y figure
        qu'une fois, est relevé."""
        def muter(corpus, config, avant, rng):
            candidates = []
            for cle, fr in corpus.textes_projet():
                if cle in avant:
                    continue
                en, nombres = nombres_en(corpus.anglais(cle)), nombres_fr(fr)
                entier = next((n for n in en if n.isdigit() and nombres.count(n) == 1
                               and len(re.findall(rf"(?<!\d){n}(?!\d)", fr)) == 1), None)
                if entier:
                    candidates.append((cle, fr, entier))
            for cle, fr, entier in rng.sample(candidates, min(len(candidates), ECHANTILLON)):
                corpus.fr[cle] = re.sub(rf"(?<!\d){entier}(?!\d)", str(int(entier) + 1), fr)
                yield cle
        self.detecter("nombres", muter, regles={"nombres": True})


if __name__ == "__main__":
    unittest.main()
