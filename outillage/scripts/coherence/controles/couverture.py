"""Contrôle couverture : rien d'affiché en anglais faute de français, rien de vide, pas de doublon.

Les clés vides et les objets sans anglais sont les deux pièges de chaque version (CLAUDE.md) :
une clé présente mais vide, un objet KubeJS dont seul l'anglais reconstitué dit le nom.
"""
from __future__ import annotations

from ..corpus import affichee
from ..modele import BLOQUANT, SIGNALE, Constat

NOM = "couverture"
SANS_ANGLAIS = "objet sans anglais : reconstituer son anglais (society-corrected-en.json), puis traduire"
BLANC_SANS_TEMOIN = ("texte vide, sans anglais ni traduction témoin : une ligne blanche voulue se déclare par une "
                     "exception motivée (spec 2 §7)")


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for cle in sorted(set(corpus.en) | set(corpus.reconstitue)):
        en = corpus.anglais(cle)
        # Vanilla : les manques de Mojang ne s'affichent pas en jeu, sauf surcharge française du projet ;
        # block_type : contrôle everycomp.
        if (not en.strip() or not affichee(cle)
                or (corpus.origine_en.get(cle) == "vanilla" and corpus.origine_fr.get(cle) != "projet")
                or cle.startswith("block_type.")):
            continue
        fr = corpus.fr.get(cle)
        if fr is None:
            constats.append(Constat(NOM, cle, BLOQUANT, attendu=en, detail="anglais sans français"))
        elif not fr.strip():
            constats.append(Constat(NOM, cle, BLOQUANT, attendu=en, detail="français vide face à un anglais renseigné"))
    for (ns, cle), langues in sorted(corpus.temoins.items()):
        if ns in config.mods_retires or cle in corpus.fr or not affichee(cle):
            continue
        if cle.startswith("ftbquests.") and not corpus.anglais(cle):
            continue  # ancien format de quête : la clé n'existe plus en anglais
        constats.append(Constat(NOM, cle, BLOQUANT, preuve=f"kubejs/assets/{ns}/lang",
                                detail=f"présente dans les témoins ({', '.join(sorted(langues))}), absente du français"))
    for cle, valeurs in corpus.doublons().items():
        constats.append(Constat(NOM, cle, SIGNALE, actuel=" | ".join(f"{ns} : {v}" for ns, v in sorted(valeurs.items())),
                                detail="clé définie dans plusieurs fichiers avec des valeurs différentes"))
    for champ in corpus.livres:
        if champ.en.strip() and not champ.fr.strip():
            constats.append(Constat(NOM, champ.cle, BLOQUANT, attendu=champ.en, detail="champ de livre sans français"))
    return constats + _sans_anglais(corpus, config)


def _sans_anglais(corpus, config) -> list:
    """Piège n° 2 de CLAUDE.md : une clé du projet ou des témoins sans anglais effectif — ni anglais, ni anglais
    reconstitué — et sans français s'affiche sous le nom que KubeJS tire de l'identifiant ; aucune règle ne la
    voit, faute d'anglais à comparer. Ne sont pas relevés : un blanc voulu (l'anglais et le français sont vides, et
    les témoins existent et sont vides ; sans témoin, le blanc bloque jusqu'à son exception, spec 2 §7), une clé
    des témoins absente du français, que la règle des témoins
    relève déjà, un mod retiré, une ancienne quête."""
    temoins = {}
    for (ns, cle), langues in corpus.temoins.items():
        temoins.setdefault(cle, []).append((ns, langues))
    projet = {cle for cle, origine in corpus.origine_en.items() if origine == "projet"}
    constats = []
    for cle in sorted(projet | set(temoins)):
        if (not affichee(cle) or cle.startswith("ftbquests.") or corpus.anglais(cle).strip()
                or (corpus.fr.get(cle) or "").strip()):
            continue
        espaces = [ns for ns, _ in temoins.get(cle, ())]
        if espaces and all(ns in config.mods_retires for ns in espaces):
            continue
        if cle not in corpus.fr:
            if espaces:
                continue  # la règle des témoins la relève
            detail = SANS_ANGLAIS
        elif not temoins.get(cle):
            detail = BLANC_SANS_TEMOIN  # sans témoin, un blanc n'est plus présumé voulu
        elif not any(v.strip() for _, langues in temoins[cle] for v in langues.values()):
            continue  # blanc voulu : l'anglais, les témoins et le français sont vides
        else:
            detail = SANS_ANGLAIS
        constats.append(Constat(NOM, cle, BLOQUANT, detail=detail))
    return constats
