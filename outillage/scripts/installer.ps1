<#
.SYNOPSIS
  Installe la traduction française de Society: Sunlit Valley dans une instance de jeu.

.DESCRIPTION
  Pendant Windows d'install_fr.py, sans Python : il tourne depuis le paquet
  décompressé (dist/Society_FR_installation.zip), dont il prend les fichiers à côté
  de lui. Installer-Windows.bat le lance ; on peut aussi l'appeler directement :

    powershell -ExecutionPolicy Bypass -File .\installer.ps1 "C:\...\Instances\Society" [-DryRun] [-SansAccentFold]

  (« .\installer.ps1 » tout court est refusé par la politique d'exécution de Windows.)

  Il pose les fichiers de langue (kubejs/assets/<mod>/lang/fr_fr.json), les livres
  (patchouli_books/<livre>/fr_fr/), le journal du menu titre et le mod Accent Fold
  (mods/). Une sauvegarde .bak-fr est faite avant tout remplacement.

  Ce que la traduction ne porte plus est RETIRÉ, exactement comme le fait
  install_fr.py : le relevé .traduction-fr.json, à la racine de l'instance, liste ce
  qui a été posé ; au passage suivant, ce qui y figurait sans figurer dans la
  nouvelle installation s'en va, et sa sauvegarde reprend sa place. Les deux
  installeurs lisent et écrivent le même relevé, on peut passer de l'un à l'autre.

  Écrit pour Windows PowerShell 5.1 (présent sur tout Windows 10 et 11) : ni
  opérateurs de PowerShell 7, ni BOM dans les fichiers écrits (Python ne lirait plus
  le relevé). Ce fichier-ci, en revanche, DOIT garder son BOM : sans lui, PowerShell
  5.1 le lit en ANSI et ses accents deviennent illisibles.
#>
param(
    [Parameter(Position = 0)] [string] $Instance,
    [switch] $DryRun,
    [switch] $SansAccentFold,
    [switch] $Oui
)

$ErrorActionPreference = 'Stop'
$Src = $PSScriptRoot
# PowerShell ignore la casse des noms de variables : $NomReleve et non $Releve, que
# le contenu du relevé, écrit en fin de script, écraserait.
$NomReleve = '.traduction-fr.json'
# Ce que des versions antérieures posaient sans jamais le reprendre (voir install_fr.py).
$ResidusConnus = @('kubejs/assets/emi/aliases/society_fr.json')
$Utf8 = New-Object System.Text.UTF8Encoding $false

function Natif([string] $racine, [string] $relatif) {
    Join-Path $racine ($relatif -replace '/', [IO.Path]::DirectorySeparatorChar)
}

function Lire-Releve([string] $dest) {
    $f = Join-Path $dest $NomReleve
    if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { return @() }
    try {
        $d = [IO.File]::ReadAllText($f, $Utf8) | ConvertFrom-Json
        if ($null -eq $d.pose) { return @() }
        return @($d.pose | ForEach-Object { [string] $_ })
    } catch { return @() }
}

function A-Retirer([string] $dest, [string[]] $pose) {
    $garde = @{}; foreach ($p in $pose) { $garde[$p] = $true }
    $anciens = @(Lire-Releve $dest | Where-Object { -not $garde.ContainsKey($_) })
    $residus = @($ResidusConnus | Where-Object {
        -not $garde.ContainsKey($_) -and (Test-Path -LiteralPath (Natif $dest $_)) -and ($anciens -notcontains $_) })
    return @(($anciens + $residus) | Where-Object { Test-Path -LiteralPath (Natif $dest $_) })
}

function Supprimer([string] $chemin) {
    if (Test-Path -LiteralPath $chemin -PathType Container) { Remove-Item -LiteralPath $chemin -Recurse -Force }
    elseif (Test-Path -LiteralPath $chemin) { Remove-Item -LiteralPath $chemin -Force }
}

# Défait une pose : la sauvegarde reprend sa place, sinon le fichier s'en va. Mêmes
# noms de sauvegarde qu'install_fr.py : <nom>.bak-fr, ou <nom sans extension>.json.bak-fr.
function Retirer([string] $cible, [string] $racine) {
    $nom = Split-Path $cible -Leaf
    $parent = Split-Path $cible -Parent
    $sansExt = [IO.Path]::GetFileNameWithoutExtension($nom)
    foreach ($sauvegarde in @((Join-Path $parent ($nom + '.bak-fr')), (Join-Path $parent ($sansExt + '.json.bak-fr')))) {
        if (Test-Path -LiteralPath $sauvegarde) {
            Supprimer $cible
            Move-Item -LiteralPath $sauvegarde -Destination $cible
            return
        }
    }
    Supprimer $cible
    # Les dossiers vidés partent, jusqu'aux dossiers de l'instance exclus (kubejs/,
    # config/, patchouli_books/, mods/) : ils appartiennent à l'instance.
    $racine = [IO.Path]::GetFullPath($racine).TrimEnd('\', '/')
    $dossier = [IO.Path]::GetFullPath($parent).TrimEnd('\', '/')
    while ($true) {
        $haut = [IO.Path]::GetDirectoryName($dossier)
        if ($null -eq $haut -or $haut.TrimEnd('\', '/') -eq $racine) { break }
        if (-not $dossier.StartsWith($racine + [IO.Path]::DirectorySeparatorChar)) { break }
        if (-not (Test-Path -LiteralPath $dossier -PathType Container)) { break }
        if (@(Get-ChildItem -LiteralPath $dossier -Force).Count -gt 0) { break }
        Remove-Item -LiteralPath $dossier -Force
        $dossier = $haut
    }
}

function Version-De([string] $fichierPakku) {
    try { return ([IO.File]::ReadAllText($fichierPakku, $Utf8) | ConvertFrom-Json).version } catch { return $null }
}

# --- l'instance -----------------------------------------------------------------
if (-not $Instance) {
    Write-Host ''
    Write-Host '  Traduction française de Society: Sunlit Valley'
    Write-Host '  Collez le chemin du dossier de votre instance (celui qui contient kubejs),'
    Write-Host '  ou glissez ce dossier sur Installer-Windows.bat.'
    $Instance = (Read-Host '  Dossier de l''instance').Trim('"', ' ')
}
# Lancé par « powershell -File », un chemin terminé par \ avant son guillemet
# ("C:\...\minecraft\") arrive mal découpé : Windows lit \" comme un guillemet
# littéral, et le reste de la ligne se colle au chemin (« ...\minecraft" -DryRun »).
# On recoupe : le chemin s'arrête au guillemet, les options qui suivent comptent.
if ($Instance -match '^([^"]*)"(.*)$') {
    $Instance = $Matches[1]
    foreach ($mot in ($Matches[2] -split '\s+')) {
        switch ($mot) {
            '-DryRun' { $DryRun = $true }
            '-SansAccentFold' { $SansAccentFold = $true }
            '-Oui' { $Oui = $true }
        }
    }
}
if ($Instance) {
    $Instance = $Instance.Trim()
    if ($Instance.Length -gt 3) { $Instance = $Instance.TrimEnd('\', '/') }
}
if (-not $Instance -or -not (Test-Path -LiteralPath $Instance -PathType Container)) {
    Write-Host "ERREUR : le dossier « $Instance » n'existe pas."
    exit 1
}
$Dest = (Resolve-Path -LiteralPath $Instance).ProviderPath

$versionSrc = (Get-Content -LiteralPath (Join-Path $Src 'version.txt') -Raw -Encoding UTF8).Trim()
$problemes = @()
if (-not (Test-Path -LiteralPath (Join-Path $Dest 'kubejs') -PathType Container)) {
    $problemes += "pas de dossier kubejs — est-ce bien l'instance du modpack ?"
}
$pakku = Join-Path $Dest 'pakku.json'
if (Test-Path -LiteralPath $pakku) {
    $vi = Version-De $pakku
    if ($vi -and $vi -ne $versionSrc) {
        $problemes += "versions différentes : traduction faite pour $versionSrc, instance en $vi"
    }
}
if ($problemes.Count -gt 0) {
    Write-Host 'Avertissements :'
    foreach ($p in $problemes) { Write-Host "  - $p" }
    if (-not $DryRun -and -not $Oui) {
        $r = (Read-Host 'Continuer quand même ? [o/N]').Trim().ToLower()
        if (@('o', 'oui', 'y', 'yes') -notcontains $r) { Write-Host 'Annulé.'; exit 1 }
    }
}

# --- ce que le paquet pose --------------------------------------------------------
$langues = @(Get-ChildItem -LiteralPath (Join-Path $Src 'kubejs/assets') -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'lang/fr_fr.json') } |
    Sort-Object Name | ForEach-Object { $_.Name })
$livres = @()
if (Test-Path -LiteralPath (Join-Path $Src 'patchouli_books')) {
    $livres = @(Get-ChildItem -LiteralPath (Join-Path $Src 'patchouli_books') -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'fr_fr') -PathType Container } |
        Sort-Object Name | ForEach-Object { $_.Name })
}
$changelog = 'config/fancymenu/assets/changelog_fr_fr.markdown'
$jar = $null
if (-not $SansAccentFold -and (Test-Path -LiteralPath (Join-Path $Src 'mods'))) {
    $jar = Get-ChildItem -LiteralPath (Join-Path $Src 'mods') -Filter 'accentfold-*.jar' | Sort-Object Name | Select-Object -Last 1
}

$pose = @($changelog)
$pose += $livres | ForEach-Object { "patchouli_books/$_/fr_fr" }
$pose += $langues | ForEach-Object { "kubejs/assets/$_/lang/fr_fr.json" }
if ($jar) { $pose += "mods/$($jar.Name)" }
$pose = @($pose | Sort-Object { $_ } -CaseSensitive)
$obsoletes = A-Retirer $Dest $pose

# Une autre version d'Accent Fold dans mods/ ferait planter Forge (deux fois le même
# mod) : elle est mise de côté, renommée en .bak-fr, que Forge ne charge pas.
$autresJars = @()
if ($jar -and (Test-Path -LiteralPath (Join-Path $Dest 'mods'))) {
    $autresJars = @(Get-ChildItem -LiteralPath (Join-Path $Dest 'mods') -Filter 'accentfold-*.jar' |
        Where-Object { $_.Name -ne $jar.Name -and $obsoletes -notcontains "mods/$($_.Name)" })
}

Write-Host ''
Write-Host "Installation vers : $Dest"
Write-Host "  1. $($langues.Count) fichiers de langue -> kubejs/assets/<mod>/lang/fr_fr.json  [chargés automatiquement]"
foreach ($l in $livres) { Write-Host "  2. livre « $l » -> patchouli_books/$l/fr_fr/" }
Write-Host "  3. changelog_fr_fr.markdown -> config/fancymenu/assets/  [journal du menu titre]"
if ($jar) { Write-Host "  4. mod $($jar.Name) -> mods/  [recherche sans accents]" }
foreach ($a in $autresJars) { Write-Host "     autre version mise de côté : mods/$($a.Name) -> $($a.Name).bak-fr" }
if ($obsoletes.Count -gt 0) {
    if ($obsoletes.Count -eq 1) { $accord = 'fichier retiré — la traduction ne le porte plus' }
    else { $accord = 'fichiers retirés — la traduction ne les porte plus' }
    Write-Host "  5. $($obsoletes.Count) $accord :"
    foreach ($c in $obsoletes) { Write-Host "       $c" }
}
if ($DryRun) {
    Write-Host ''
    Write-Host '(-DryRun : rien n''a été écrit)'
    exit 0
}

# --- la pose ----------------------------------------------------------------------
function Copier-Fichier([string] $de, [string] $vers, [bool] $sauvegarder) {
    $dossier = Split-Path $vers -Parent
    if (-not (Test-Path -LiteralPath $dossier)) { New-Item -ItemType Directory -Path $dossier -Force | Out-Null }
    if ($sauvegarder -and (Test-Path -LiteralPath $vers) -and -not (Test-Path -LiteralPath ($vers + '.bak-fr'))) {
        Copy-Item -LiteralPath $vers -Destination ($vers + '.bak-fr') -Force
    }
    Copy-Item -LiteralPath $de -Destination $vers -Force
}

foreach ($l in $langues) {
    Copier-Fichier (Natif $Src "kubejs/assets/$l/lang/fr_fr.json") (Natif $Dest "kubejs/assets/$l/lang/fr_fr.json") $true
}
Copier-Fichier (Natif $Src $changelog) (Natif $Dest $changelog) $false
foreach ($l in $livres) {
    $dst = Natif $Dest "patchouli_books/$l/fr_fr"
    if (Test-Path -LiteralPath $dst) {
        $bak = $dst + '.bak-fr'
        if (Test-Path -LiteralPath $bak) { Remove-Item -LiteralPath $bak -Recurse -Force }
        Move-Item -LiteralPath $dst -Destination $bak
    }
    $parent = Split-Path $dst -Parent
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath (Natif $Src "patchouli_books/$l/fr_fr") -Destination $dst -Recurse
}
foreach ($a in $autresJars) {
    $bak = $a.FullName + '.bak-fr'
    if (Test-Path -LiteralPath $bak) { Remove-Item -LiteralPath $bak -Force }
    Move-Item -LiteralPath $a.FullName -Destination $bak
}
if ($jar) { Copier-Fichier $jar.FullName (Natif $Dest "mods/$($jar.Name)") $false }

foreach ($c in $obsoletes) { Retirer (Natif $Dest $c) $Dest }

$contenuReleve = [ordered]@{
    version = $versionSrc
    date    = (Get-Date -Format 'yyyy-MM-dd')
    mode    = 'copie directe'
    pose    = $pose
}
[IO.File]::WriteAllText((Join-Path $Dest $NomReleve), ($contenuReleve | ConvertTo-Json -Depth 3) + "`n", $Utf8)

Write-Host ''
Write-Host 'OK, installé. Dans le jeu :'
Write-Host '  - Options -> Langue -> Français (France)'
Write-Host '  - Les fichiers de langue et les livres sont chargés automatiquement.'
if ($jar) { Write-Host '  - Accent Fold est installé : « ble » trouve « Blé » dans les recherches.' }
exit 0
