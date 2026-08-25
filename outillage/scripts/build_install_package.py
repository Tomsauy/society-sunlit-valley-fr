#!/usr/bin/env python3
"""Génère dist/Society_FR_installation.zip — le paquet remis aux joueurs. Relançable.

Contenu du paquet, tel qu'il se décompresse sur le dossier de l'instance :
  kubejs/assets/<mod>/lang/fr_fr.json      chargés automatiquement par KubeJS
  patchouli_books/<livre>/fr_fr/           livres-guides (livre externe : aucun
                                           pack de ressources ne peut les fournir)
  config/fancymenu/assets/changelog_fr_fr.markdown
                                           journal des modifications du menu titre,
                                           choisi par le layout via la langue du jeu
  optionnel/Society_FR.zip                 même chose que les lang, en pack de
                                           ressources, pour qui ne veut pas toucher
                                           à kubejs/ (ne couvre pas les livres)
  Installer-Windows.bat, LISEZ-MOI.txt
"""
import json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
DEST = ROOT / "dist" / "Society_FR_installation.zip"

# Le .bat reste sans accents : l'encodage de la console Windows n'est pas garanti.
BAT = """@echo off
setlocal
echo.
echo   Traduction francaise -- Society: Sunlit Valley {version}
echo.
set "SRC=%~dp0"
set "DEST=%~1"
if "%DEST%"=="" (
  echo   Glissez le dossier de votre instance sur ce fichier, ou lancez :
  echo     Installer-Windows.bat "C:\\Users\\vous\\curseforge\\minecraft\\Instances\\Society"
  echo.
  pause
  exit /b 1
)
if not exist "%DEST%\\kubejs" (
  echo   ERREUR : "%DEST%" ne contient pas de dossier kubejs.
  echo   Ce n'est pas le dossier de l'instance du modpack.
  echo.
  pause
  exit /b 1
)
echo   Installation vers %DEST%
xcopy "%SRC%kubejs" "%DEST%\\kubejs" /E /I /Y >nul || goto :err
xcopy "%SRC%patchouli_books" "%DEST%\\patchouli_books" /E /I /Y >nul || goto :err
xcopy "%SRC%config" "%DEST%\\config" /E /I /Y >nul || goto :err
echo.
echo   OK. Dans le jeu : Options ^> Langue ^> Francais (France).
echo.
pause
exit /b 0
:err
echo   ECHEC de la copie. Verifiez que le jeu est ferme.
pause
exit /b 1
"""

LISEZMOI = """Traduction française — Society: Sunlit Valley {version}
(traduction communautaire non officielle)

INSTALLATION SUR WINDOWS
1. Repérez le dossier de votre instance : celui qui contient kubejs/,
   patchouli_books/ et config/.
     CurseForge   C:\\Users\\<vous>\\curseforge\\minecraft\\Instances\\<nom du pack>
     Prism        %APPDATA%\\PrismLauncher\\instances\\<nom>\\.minecraft
     Modrinth     %APPDATA%\\com.modrinth.theseus\\profiles\\<nom>
     Officiel     %APPDATA%\\.minecraft
   Depuis CurseForge : bouton « ... » sur le pack, puis « Open Folder ».
2. Fermez le jeu, puis au choix :
     - faites glisser le dossier de l'instance SUR Installer-Windows.bat ;
     - ou copiez à la main les dossiers kubejs, patchouli_books et config de
       cette archive dans l'instance. Windows demande quoi faire : choisissez
       « Remplacer les fichiers dans la destination ». Les dossiers sont
       fusionnés, rien d'autre n'est supprimé.
3. Lancez le jeu : Options > Langue > Français (France). C'est tout —
   KubeJS charge kubejs/assets/<mod>/lang/fr_fr.json tout seul, il n'y a
   AUCUN pack de ressources à activer.

INSTALLATION SUR MACOS / LINUX
Même principe, en fusionnant (le /. final compte) :
  cp -R kubejs/. "/chemin/instance/kubejs/"
  cp -R patchouli_books/. "/chemin/instance/patchouli_books/"
  cp -R config/. "/chemin/instance/config/"
Sur macOS, ne glissez pas les dossiers dans le Finder : il REMPLACE le dossier
kubejs au lieu de le fusionner, et les scripts du pack sont perdus.

ALTERNATIVE — pack de ressources
DOSSIER test-infobulles/ — NE PAS INSTALLER PAR DEFAUT
Correctif experimental d'un defaut du pack : six infobulles affichent un carre a
la place d'un retour a la ligne, dans toutes les langues. Voir le LISEZ-MOI de ce
dossier. Il touche un script du pack, pas la traduction.

Pour ne pas toucher au dossier kubejs : copiez optionnel/Society_FR.zip dans
resourcepacks/, puis dans le jeu Options > Packs de ressources, activez-le et
placez-le tout en haut. Copiez quand même patchouli_books/ : les livres-guides
sont des livres externes, aucun pack de ressources ne peut les fournir.

EN MULTIJOUEUR
Rien à installer sur le serveur : quêtes, dialogues et messages du serveur sont
transmis sous forme de clés, que votre client traduit lui-même. Il suffit que le
serveur tourne sur la même version du modpack.

IMPORTANT
- Traduction faite pour la version {version} du modpack. Sur une autre version,
  les textes ajoutés depuis resteront en anglais.
- Les noms d'objets sont volontairement SANS ACCENTS : la recherche d'EMI ne
  gère pas les accents, taper « ble » doit pouvoir trouver « Ble ». Tout le
  reste (quêtes, dialogues, descriptions, livres) est accentué normalement.
- Si vous repérez un texte encore en anglais, signalez-le : certains objets
  créés par les scripts du pack n'ont aucune source anglaise et ne se
  détectent qu'en jouant.
"""

BAT_TEST = """@echo off
chcp 65001 >nul
setlocal
set "DEST=%~1"
if "%DEST%"=="" (
  echo.
  echo   Glissez le dossier de votre instance SUR ce fichier.
  echo.
  pause & exit /b 1
)
if not exist "%DEST%\\kubejs\\client_scripts" (
  echo   ERREUR : "%DEST%" ne contient pas kubejs\\client_scripts.
  pause & exit /b 1
)
set "DOSSIER=%DEST%\\kubejs\\client_scripts\\tooltips"
for %%F in ("%~dp0kubejs\\client_scripts\\tooltips\\*.js") do (
  if exist "%DOSSIER%\\%%~nxF" (
    if not exist "%DOSSIER%\\%%~nxF.avant-test" copy "%DOSSIER%\\%%~nxF" "%DOSSIER%\\%%~nxF.avant-test" >nul
  )
  copy /Y "%%F" "%DOSSIER%\\%%~nxF" >nul || goto :err
)
echo.
echo   Correctif de test installe.
echo   L'original est sauvegarde en addTooltips.js.avant-test
echo   Pour revenir en arriere : renommez-le en addTooltips.js
echo.
pause & exit /b 0
:err
echo   ECHEC de la copie.
pause & exit /b 1
"""

LISEZMOI_TEST = """\ufeffCorrectif de test — infobulles sur plusieurs lignes

CE DOSSIER N'EST PAS DE LA TRADUCTION. Ne l'installez que pour tester.

LE PROBLEME
Six infobulles du pack affichent un carre a la place d'un retour a la ligne :
jeton de surplus, cisailles magiques, cristal ensoleille, extractinateur, terre
riche, arroseur. Une infobulle Minecraft est une liste de composants, un par
ligne : un saut de ligne dans le texte n'en cree pas, il arrive jusqu'a la police
qui n'a pas de glyphe et affiche son carre.

Le defaut touche TOUTES les langues, l'anglais compris. Il vient du pack, pas de
la traduction.

LE CORRECTIF
Les fichiers d'infobulles concernes gagnent un helper qui decoupe le texte avant de l'ajouter, une ligne
par composant — le meme principe que le pack applique deja aux peluches dans
addAdvancedTooltips.js.

INSTALLER
Glissez le dossier de votre instance sur Installer-le-test.bat. L'original est
sauvegarde sous le meme nom suivi de .avant-test.

REVENIR EN ARRIERE
Renommez chaque fichier .avant-test en retirant ce suffixe.

POURQUOI CE N'EST PAS DANS L'INSTALLATION NORMALE
Ce fichier appartient au pack et Chakyl le modifie souvent. L'ecraser a chaque
mise a jour annulerait ses corrections sans qu'on s'en apercoive. Le vrai remede
est un signalement amont, ou la correction profite a toutes les langues.
"""

def main() -> None:
    version = json.loads((REPO / "pakku.json").read_text())["version"]
    langs = sorted((REPO / "kubejs" / "assets").glob("*/lang/fr_fr.json"))
    books = sorted(p for b in (REPO / "patchouli_books").iterdir()
                   if (b / "fr_fr").is_dir() for p in (b / "fr_fr").rglob("*") if p.is_file())
    changelog = REPO / "config" / "fancymenu" / "assets" / "changelog_fr_fr.markdown"
    rp = REPO / "resourcepacks" / "Society_FR.zip"
    for f in (changelog, rp):
        if not f.exists():
            raise SystemExit(f"ERREUR : {f} manquant — lancer build_fr_resourcepack.py ?")

    DEST.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(DEST, "w", zipfile.ZIP_DEFLATED) as z:
        for f in langs:
            z.write(f, f"kubejs/assets/{f.parents[1].name}/lang/fr_fr.json")
        for f in books:
            z.write(f, str(f.relative_to(REPO)))
        z.write(changelog, str(changelog.relative_to(REPO)))
        z.write(rp, "optionnel/Society_FR.zip")
        z.writestr("Installer-Windows.bat",
                   BAT.format(version=version).replace("\n", "\r\n"))
        # tous les fichiers d'infobulles portant le correctif, pas un seul :
        # le pack en compte quatre, et deux ont ete corriges.
        patches = sorted(
            f for f in (REPO / "kubejs/client_scripts/tooltips").glob("*.js")
            if "ajouterLignes" in f.read_text(encoding="utf-8")
        )
        if patches:
            for f in patches:
                z.write(f, f"test-infobulles/{f.relative_to(REPO)}")
            z.writestr("test-infobulles/Installer-le-test.bat",
                       BAT_TEST.replace("\n", "\r\n"))
            z.writestr("test-infobulles/LISEZ-MOI.txt",
                       LISEZMOI_TEST.replace("\n", "\r\n"))
        z.writestr("LISEZ-MOI.txt",
                   "\ufeff" + LISEZMOI.format(version=version).replace("\n", "\r\n"))

    print(f"écrit {DEST.relative_to(ROOT)} — version {version} : "
          f"{len(langs)} fichiers lang, {len(books)} fichiers de livres, "
          f"1 changelog, {DEST.stat().st_size // 1024} Ko")

if __name__ == "__main__":
    main()
