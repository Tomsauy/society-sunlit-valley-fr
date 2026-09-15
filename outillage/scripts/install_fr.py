#!/usr/bin/env python3
"""Installe la traduction FR dans une instance de jeu Society: Sunlit Valley.

Usage : python3 install_fr.py <chemin-instance-de-jeu> [--dry-run] [--resourcepack]

L'instance cible est le dossier contenant kubejs/, patchouli_books/, resourcepacks/
(souvent .minecraft/ ou le dossier d'instance du launcher).

Méthode par défaut — copie directe (recommandée) :
  kubejs/assets/<mod>/lang/fr_fr.json  → chargés automatiquement par KubeJS, rien à activer
  patchouli_books/<livre>/fr_fr/       → livres-guides
  config/fancymenu/assets/changelog_fr_fr.markdown → journal du menu titre, choisi
                                       par le layout selon la langue du jeu
  Cette méthode REMPLACE les anciennes traductions FR communautaires du pack.

Option --resourcepack : installe à la place le zip dans resourcepacks/ (à activer dans le jeu).
  Utile pour une instance dont on ne veut pas modifier le dossier kubejs.
  Attention : ne couvre pas les livres Patchouli (toujours copiés en direct).

Une sauvegarde .bak-fr est faite avant tout remplacement.

Ce que la traduction ne porte plus est RETIRE de l'instance. Le script tient pour
cela un relevé de ce qu'il a posé, `.traduction-fr.json` à la racine de l'instance :
au passage suivant, ce qui y figurait sans figurer dans la nouvelle installation
s'en va. Sans ce relevé, un fichier abandonné survit indéfiniment — c'est ainsi
qu'une instance a gardé les alias de recherche EMI après leur suppression, et a
continué de les servir au jeu.
"""
import json, shutil, sys
from datetime import date
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2]
SRC_REPO = SRC_ROOT / "society-sunlit-valley"
RELEVE = ".traduction-fr.json"

# Ce que des versions antérieures du script posaient sans jamais le reprendre. Les
# instances installées avant le relevé n'ont aucune autre trace de ces fichiers.
RESIDUS_CONNUS = ("kubejs/assets/emi/aliases/society_fr.json",)


def lire_releve(dest: Path) -> list:
    f = dest / RELEVE
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("pose", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def retirer(cible: Path, racine: Path) -> None:
    """Défait une pose : la sauvegarde reprend sa place, sinon le fichier s'en va.

    Remettre le .bak-fr est le point important — pour un fichier de langue, cette
    sauvegarde est la traduction d'origine du pack, que notre pose recouvrait. La
    supprimer sans la rendre laisserait le namespace sans aucun français.
    """
    for suffixe in (".bak-fr", ".json.bak-fr"):
        sauvegarde = (cible.with_name(cible.name + suffixe) if suffixe == ".bak-fr"
                      else cible.with_suffix(suffixe))
        if sauvegarde.exists():
            if cible.exists():
                shutil.rmtree(cible) if cible.is_dir() else cible.unlink()
            shutil.move(str(sauvegarde), str(cible))
            return
    if cible.is_dir():
        shutil.rmtree(cible)
    elif cible.exists():
        cible.unlink()
    # Un dossier vidé par ce retrait n'a plus de raison d'être. On s'arrête un cran
    # avant les dossiers structurels de l'instance — kubejs/, config/,
    # patchouli_books/ — qui lui appartiennent et non à la traduction : retirer le
    # dernier fichier posé ne doit pas emporter le dossier qui l'accueillait.
    parent = cible.parent
    while parent.parent != racine and racine in parent.parents \
            and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def a_retirer(dest: Path, pose: list) -> list:
    """Ce que le passage précédent avait posé et que celui-ci ne pose plus."""
    garde = set(pose)
    anciens = [c for c in lire_releve(dest) if c not in garde]
    residus = [c for c in RESIDUS_CONNUS
               if c not in garde and (dest / c).exists() and c not in anciens]
    return [c for c in anciens + residus if (dest / c).exists()]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    use_rp = "--resourcepack" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    dest = Path(args[0]).expanduser().resolve()
    if not dest.is_dir():
        sys.exit(f"ERREUR : {dest} n'existe pas")

    problems = []
    if not (dest / "kubejs").is_dir():
        problems.append("pas de dossier kubejs/ — est-ce bien l'instance du modpack ?")
    src_ver = json.loads((SRC_REPO / "pakku.json").read_text())["version"]
    dest_pakku = dest / "pakku.json"
    if dest_pakku.exists():
        dv = json.loads(dest_pakku.read_text()).get("version")
        if dv != src_ver:
            problems.append(f"versions différentes : traduction faite pour {src_ver}, instance en {dv}")
    if problems:
        print("⚠ Avertissements :")
        for p in problems:
            print("  -", p)
        if not dry:
            r = input("Continuer quand même ? [o/N] ").strip().lower()
            if r not in ("o", "oui", "y", "yes"):
                sys.exit("Annulé.")

    lang_files = sorted((SRC_REPO / "kubejs" / "assets").glob("*/lang/fr_fr.json"))
    books = [(b.name, b / "fr_fr", dest / "patchouli_books" / b.name / "fr_fr")
             for b in sorted((SRC_REPO / "patchouli_books").iterdir()) if (b / "fr_fr").is_dir()]
    changelog = Path("config/fancymenu/assets/changelog_fr_fr.markdown")

    pose = [changelog.as_posix()]
    pose += [f"patchouli_books/{name}/fr_fr" for name, _, _ in books]
    if use_rp:
        pose.append("resourcepacks/Society_FR.zip")
    else:
        pose += [f"kubejs/assets/{f.parents[1].name}/lang/fr_fr.json" for f in lang_files]
    obsoletes = a_retirer(dest, sorted(pose))

    print(f"\nInstallation vers : {dest}")
    if use_rp:
        zip_src = SRC_REPO / "resourcepacks" / "Society_FR.zip"
        print(f"  1. {zip_src.name} → resourcepacks/  ({zip_src.stat().st_size // 1024} Ko) [à activer dans le jeu]")
    else:
        print(f"  1. {len(lang_files)} fichiers de langue → kubejs/assets/<mod>/lang/fr_fr.json  [chargés automatiquement]")
    for name, src, _ in books:
        print(f"  2. livre « {name} » → patchouli_books/{name}/fr_fr/  ({len(list(src.rglob('*.json')))} fichiers)")
    print(f"  3. {changelog.name} → {changelog.parent}/  [journal du menu titre]")
    if obsoletes:
        print(f"  4. {len(obsoletes)} fichiers retirés — la traduction ne les porte plus :")
        for c in obsoletes:
            rendue = " (sauvegarde restaurée)" if (
                (dest / c).with_suffix(".json.bak-fr").exists()
                or (dest / f"{c}.bak-fr").exists()) else ""
            print(f"       {c}{rendue}")
    if dry:
        print("\n(--dry-run : rien n'a été écrit)")
        return

    if use_rp:
        zip_src = SRC_REPO / "resourcepacks" / "Society_FR.zip"
        zip_dst = dest / "resourcepacks" / "Society_FR.zip"
        zip_dst.parent.mkdir(parents=True, exist_ok=True)
        if zip_dst.exists():
            shutil.copy2(zip_dst, zip_dst.with_suffix(".zip.bak-fr"))
        shutil.copy2(zip_src, zip_dst)
    else:
        for f in lang_files:
            ns = f.parents[1].name
            dst = dest / "kubejs" / "assets" / ns / "lang" / "fr_fr.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not dst.with_suffix(".json.bak-fr").exists():
                shutil.copy2(dst, dst.with_suffix(".json.bak-fr"))
            shutil.copy2(f, dst)

    dst_changelog = dest / changelog
    dst_changelog.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_REPO / changelog, dst_changelog)

    for name, src, dst in books:
        if dst.exists():
            bak = dst.with_name("fr_fr.bak-fr")
            if bak.exists():
                shutil.rmtree(bak)
            shutil.move(str(dst), str(bak))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)

    for c in obsoletes:
        retirer(dest / c, dest)
    (dest / RELEVE).write_text(json.dumps(
        {"version": src_ver, "date": date.today().isoformat(),
         "mode": "resourcepack" if use_rp else "copie directe", "pose": sorted(pose)},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("\n✓ Installé. Dans le jeu :")
    if use_rp:
        print("  - Options → Packs de ressources → activer « Society_FR » (tout en haut de la pile)")
    print("  - Options → Langue → Français (France)")
    print("  - Les livres Patchouli et les fichiers de langue sont chargés automatiquement.")

    print()
    print("  Le mod Accent Fold est vivement conseillé : sans lui, la recherche")
    print("  d'objets fonctionne, mais il faut taper les accents — « Blé », pas")
    print("  « ble ». Avec lui, les deux marchent.")
    print("  Le jar se prend sur https://github.com/Tomsauy/accent-fold.")

if __name__ == "__main__":
    main()
