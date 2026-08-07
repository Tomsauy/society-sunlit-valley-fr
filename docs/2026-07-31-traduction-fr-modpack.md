# Traduction française intégrale de Society: Sunlit Valley — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire une traduction française complète, cohérente et validée mécaniquement de tout le texte visible du modpack (Society, quêtes, overrides, mods sans FR, livres Patchouli), livrée en overrides kubejs sur la branche `traduction-fr` + resource pack zip.

**Architecture:** Pipeline en 5 phases (inventaire déterministe → glossaire avec checkpoint utilisateur → traduction de masse par workflows → réconciliation/relecture → livrables). Les scripts Python déterministes vivent dans `fr-workspace/scripts/`, les workflows multi-agents traduisent par unités avec contexte, un validateur mécanique garantit clés/placeholders/politique accents.

**Tech Stack:** Python 3 (stdlib uniquement), outil Workflow (multi-agents), git, zipfile/urllib.

**Spec:** `docs/specs/2026-07-31-traduction-fr-modpack-design.md` (lire en premier)

## Global Constraints

- Racine projet : `/Users/thomas/IAPersoProjects/SunlitValley/` (notée `ROOT` ci-dessous). Repo du pack : `ROOT/society-sunlit-valley/` (noté `REPO`), branche `traduction-fr`.
- Dans `REPO`, ne committer QUE des fichiers fonctionnels : `kubejs/assets/*/lang/fr_fr.json`, `patchouli_books/*/fr_fr/**`, `resourcepacks/Society_FR.zip`, et (Tâche 14 uniquement) des scripts kubejs modifiés + leurs clés `en_us.json`. Jamais de scripts pipeline ni de docs dans `REPO`.
- Tout fichier de travail va dans `ROOT/fr-workspace/` ; les scripts pipeline dans `ROOT/fr-workspace/scripts/`.
- Aucune PR upstream, jamais (politique anti-IA du projet upstream).
- La traduction FR communautaire existante du repo (fichiers `fr_fr.json` de kubejs et `patchouli_books/*/fr_fr/`) est REMPLACÉE, jamais lue comme référence.
- Les `fr_fr.json` embarqués dans les JARs des mods sont conservés et servent de référence de glossaire.
- Codes intouchables dans toute traduction : `%s`, `%1$s`, `§x`, `$(...)` (Patchouli), `\n`, `{0}`, `%%`, marqueur `🌐`. Le validateur (Tâche 8) est la loi.
- Politique accents : décidée en Tâche 5 (vérification EMI). Si EMI est sensible aux accents → clés `item.*` et `block.*` sans accents, français accentué partout ailleurs.
- Registre : tutoiement chaleureux (quêtes, dialogues), impersonnel type Minecraft FR (interface). Capitalisation française (« Houe dorée », pas « Houe Dorée »).
- JSON produits : UTF-8, `ensure_ascii=False`, indentation 2, clés triées, newline final.
- Workflows : ≤15 agents par invocation ; plusieurs invocations successives pour les gros volumes.
- Python : stdlib uniquement (json, zipfile, urllib, hashlib, re, pathlib).

---

## Vue d'ensemble des tâches

| # | Tâche | Phase |
|---|---|---|
| 1 | Setup : workspace, git racine, .gitignore | — |
| 2 | Script téléchargement des JARs | 1 |
| 3 | Script extraction des lang des JARs | 1 |
| 4 | Script inventaire + unités de traduction | 1 |
| 5 | Vérification EMI → décision accents | 1 |
| 6 | Scan des chaînes en dur du pack | 1 |
| 7 | Références vanilla Minecraft FR | 2 |
| 8 | Validateur de traduction (TDD) | 3 (outil) |
| 9 | Candidats glossaire | 2 |
| 10 | Workflow glossaire + guide de style | 2 |
| 11 | ✋ CHECKPOINT utilisateur : glossaire + volumes | 2 |
| 12 | Générateur de lots + applicateur de traductions | 3 |
| 13 | Vagues de traduction (Society → overrides → quêtes → mods → Patchouli) | 3 |
| 14 | Conversion opportuniste des chaînes en dur KubeJS | 3 |
| 15 | Réconciliation globale EN→FR (inclut FR des JARs) | 4 |
| 16 | Relecture qualité intégrale | 4 |
| 17 | Build du resource pack zip | 5 |
| 18 | Rapport final + handoff test en jeu | 5 |

Structure des fichiers créés :

```
ROOT/
├── docs/
│   ├── specs/2026-07-31-traduction-fr-modpack-design.md   (existant)
│   ├── plans/2026-07-31-traduction-fr-modpack.md          (ce fichier)
│   └── RAPPORT-TRADUCTION-FR.md                           (T18)
└── fr-workspace/
    ├── scripts/
    │   ├── download_jars.py        (T2)
    │   ├── extract_langs.py        (T3)
    │   ├── build_inventory.py      (T4)
    │   ├── scan_hardcoded.py       (T6)
    │   ├── fetch_vanilla_refs.py   (T7)
    │   ├── validate_translation.py (T8)
    │   ├── test_validate.py        (T8)
    │   ├── glossary_candidates.py  (T9)
    │   ├── make_batches.py         (T12)
    │   ├── apply_translations.py   (T12)
    │   ├── reconcile.py            (T15)
    │   └── build_fr_resourcepack.py(T17)
    ├── jars/            (cache JARs, T2)
    ├── extracted/       (langs extraites, T3)
    ├── references/      (vanilla EN/FR, T7)
    ├── inventaire.json  (T4)
    ├── DECISION-ACCENTS.md (T5)
    ├── hardcoded-candidates.json (T6)
    ├── glossaire-candidats.json (T9)
    ├── glossaire.json + GLOSSAIRE.md + STYLE.md (T10)
    ├── batches/         (lots, T12)
    ├── out/             (sorties d'agents, T13)
    └── divergences.json (T15)
```

---

### Task 1: Setup — workspace, git racine, branche

**Files:**
- Create: `ROOT/.gitignore`, `ROOT/fr-workspace/scripts/` (dossier)
- Modify: rien dans REPO (vérifier seulement la branche)

**Interfaces:**
- Produces: dépôt git à la racine (versionne docs/ et fr-workspace/scripts/), branche `traduction-fr` active dans REPO.

- [ ] **Step 1: Créer l'arborescence et le .gitignore racine**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
mkdir -p fr-workspace/scripts fr-workspace/out fr-workspace/batches
cat > .gitignore <<'EOF'
society-sunlit-valley/
fr-workspace/jars/
fr-workspace/extracted/
fr-workspace/references/
fr-workspace/out/
fr-workspace/batches/
fr-workspace/emi-check/
node_modules/
.DS_Store
EOF
```

- [ ] **Step 2: Initialiser git à la racine** (décision du plan : versionne specs, plans, scripts et glossaire — le repo du pack imbriqué est ignoré ; réversible par `rm -rf ROOT/.git`)

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git init -b main
git add .gitignore docs/
git commit -m "chore: init projet traduction FR (spec + plan)"
```

- [ ] **Step 3: Vérifier la branche du repo du pack**

```bash
cd society-sunlit-valley && git status --short && git branch --show-current
```
Attendu : arbre propre, branche `traduction-fr` (elle existe déjà ; sinon `git checkout -b traduction-fr master`).

---

### Task 2: Script de téléchargement des JARs

**Files:**
- Create: `ROOT/fr-workspace/scripts/download_jars.py`

**Interfaces:**
- Consumes: `REPO/pakku-lock.json` (`{"projects": [{"files": [{"file_name", "url", "hashes": {"sha1"}}]}]}`)
- Produces: `ROOT/fr-workspace/jars/*.jar` (cache vérifié par sha1) + `jars/_failed.json` (liste `[nom, erreur]`). Option CLI `--limit N`.

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Télécharge les JARs listés dans pakku-lock.json. Cache + reprise (sha1)."""
import hashlib, json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
JARS = ROOT / "fr-workspace" / "jars"

def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    JARS.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    lock = json.loads((REPO / "pakku-lock.json").read_text())
    todo, cached, failed = [], 0, []
    for proj in lock["projects"]:
        for f in proj.get("files", []):
            url, name = f.get("url"), f.get("file_name", "")
            if not url or not name.endswith(".jar"):
                continue
            dest, want = JARS / name, (f.get("hashes") or {}).get("sha1")
            if dest.exists() and (not want or sha1(dest) == want):
                cached += 1
                continue
            todo.append((url, dest, want))
    todo = todo[:limit] if limit else todo
    print(f"{cached} en cache, {len(todo)} à télécharger")
    for url, dest, want in todo:
        try:
            req = urllib.request.Request(url.replace(" ", "%20"),
                                         headers={"User-Agent": "sunlit-fr-pipeline"})
            dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            if want and sha1(dest) != want:
                dest.unlink()
                failed.append([dest.name, "sha1 mismatch"])
            else:
                print("ok", dest.name)
        except Exception as e:
            failed.append([dest.name, str(e)])
    (JARS / "_failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1))
    print(f"échecs: {len(failed)}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Tester sur un échantillon**

Run: `python3 fr-workspace/scripts/download_jars.py --limit 3`
Attendu : 3 jars dans `fr-workspace/jars/`, `_failed.json` vide (`[]`), exit 0.

- [ ] **Step 3: Run complet** (~366 mods, prévoir plusieurs minutes ; relançable)

Run: `python3 fr-workspace/scripts/download_jars.py`
Attendu : exit 0. Si échecs (URLs mortes), consigner `_failed.json` — ces mods passeront en « non analysés » dans l'inventaire (T4) et au rapport final (T18), ne pas bloquer.

- [ ] **Step 4: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/download_jars.py && git commit -m "feat: script téléchargement JARs (cache sha1)"
```

---

### Task 3: Script d'extraction des fichiers lang des JARs

**Files:**
- Create: `ROOT/fr-workspace/scripts/extract_langs.py`

**Interfaces:**
- Consumes: `ROOT/fr-workspace/jars/*.jar`
- Produces: `ROOT/fr-workspace/extracted/<jar_stem>/<namespace>/<locale>.json` pour locales {en_us, fr_fr, ko_kr, zh_cn, pt_br, th_th, es_es}. Gère les jars imbriqués `META-INF/jarjar/*.jar`.

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Extrait assets/<ns>/lang/<locale>.json de chaque JAR (y compris jarjar imbriqués)."""
import io, json, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JARS = ROOT / "fr-workspace" / "jars"
OUT = ROOT / "fr-workspace" / "extracted"
LOCALES = {"en_us", "fr_fr", "ko_kr", "zh_cn", "pt_br", "th_th", "es_es"}
PAT = re.compile(r"^assets/([^/]+)/lang/([a-z]{2}_[a-z]{2})\.json$")

def harvest(zf: zipfile.ZipFile, store: dict) -> None:
    for name in zf.namelist():
        m = PAT.match(name)
        if m and m.group(2) in LOCALES:
            try:
                data = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue
            if isinstance(data, dict) and data:
                store.setdefault(m.group(1), {}).setdefault(m.group(2), {}).update(
                    {k: v for k, v in data.items() if isinstance(v, str)})
        elif name.startswith("META-INF/jarjar/") and name.endswith(".jar"):
            try:
                harvest(zipfile.ZipFile(io.BytesIO(zf.read(name))), store)
            except Exception:
                pass

def main() -> None:
    count = 0
    for jar in sorted(JARS.glob("*.jar")):
        store: dict = {}
        try:
            harvest(zipfile.ZipFile(jar), store)
        except zipfile.BadZipFile:
            print("BAD ZIP:", jar.name)
            continue
        for ns, locs in store.items():
            for loc, data in locs.items():
                dest = OUT / jar.stem / ns / f"{loc}.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
                count += 1
    print(f"{count} fichiers lang extraits")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run et contrôle visuel**

Run: `python3 fr-workspace/scripts/extract_langs.py && ls fr-workspace/extracted | head && find fr-workspace/extracted -name en_us.json | wc -l`
Attendu : plusieurs centaines de fichiers ; vérifier qu'un mod connu (ex. `create-*`) a `en_us.json` ET `fr_fr.json`.

- [ ] **Step 3: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/extract_langs.py && git commit -m "feat: extraction des lang des JARs (jarjar inclus)"
```

---

### Task 4: Inventaire et unités de traduction

**Files:**
- Create: `ROOT/fr-workspace/scripts/build_inventory.py`

**Interfaces:**
- Consumes: `extracted/` (T3), `REPO/kubejs/assets/*/lang/en_us.json`, `REPO/kubejs/assets/society/lang/en_us_template.json` + `en_us.json`, `REPO/kubejs/assets/ftbquestlocalizer/lang/en_us.json`, `REPO/patchouli_books/*/en_us/**/*.json`, `jars/_failed.json`
- Produces: `ROOT/fr-workspace/inventaire.json` :

```json
{
  "units": [
    {"id": "society", "kind": "society", "namespace": "society",
     "en": {"clé": "valeur EN", "...": "..."},
     "jar_fr_partial": null,
     "witnesses": {"ko_kr": "chemin ou null", "zh_cn": "chemin ou null"},
     "target": "kubejs/assets/society/lang/fr_fr.json"},
    {"id": "mod:<ns>", "kind": "mod|mod_delta", "namespace": "<ns>", "...": "idem"},
    {"id": "override:<ns>", "kind": "override", "...": "idem"},
    {"id": "quests", "kind": "quests", "...": "idem"},
    {"id": "patchouli:<book>/<relpath>", "kind": "patchouli",
     "en": {"<json-pointer>": "texte EN"}, "target": "patchouli_books/<book>/fr_fr/<relpath>"}
  ],
  "skipped": [{"namespace": "<ns>", "reason": "fr_complet|sans_texte"}],
  "unanalyzed": ["mods dont le jar a échoué au téléchargement"],
  "stats": {"units": 0, "keys_total": 0, "par_kind": {}}
}
```

Règles (de la spec) : namespace avec `en_us` extrait + pas de `fr_fr` extrait → `mod` ; `fr_fr` incomplet (clés manquantes vs en_us) → `mod_delta` avec `en` = delta seulement et `jar_fr_partial` = le fr existant ; `fr_fr` complet → `skipped`. Tout `kubejs/assets/<ns>/lang/en_us.json` → unité `override` (toutes ses clés, priorité sur le jar : les retirer du delta du mod correspondant). Society : union template + en_us.json. Patchouli : champs `name`, `text`, `description`, `title`, `subtitle`, `landing_text` extraits récursivement avec json-pointer (`pages/3/text`).

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Construit inventaire.json : unités de traduction, skips, stats."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
EXT = ROOT / "fr-workspace" / "extracted"
PATCHOULI_FIELDS = {"name", "text", "description", "title", "subtitle", "landing_text"}

def load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}

def pointers(obj, prefix=""):
    """Extrait récursivement les champs textuels patchouli → {pointer: texte}."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.strip() in PATCHOULI_FIELDS and isinstance(v, str) and v.strip():
                out[f"{prefix}{k}"] = v
            else:
                out.update(pointers(v, f"{prefix}{k}/"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(pointers(v, f"{prefix}{i}/"))
    return out

def main() -> None:
    units, skipped = [], []
    # -- namespaces extraits des jars, fusionnés multi-jars --
    ns_map: dict = {}
    for jar_dir in EXT.iterdir() if EXT.exists() else []:
        for ns_dir in jar_dir.iterdir():
            entry = ns_map.setdefault(ns_dir.name, {})
            for loc_file in ns_dir.glob("*.json"):
                entry.setdefault(loc_file.stem, {}).update(load(loc_file))
    override_ns = set()
    # -- overrides kubejs (prioritaires) --
    for lang_dir in sorted((REPO / "kubejs" / "assets").glob("*/lang")):
        ns = lang_dir.parent.name
        en = load(lang_dir / "en_us.json")
        if ns in {"society", "ftbquestlocalizer"} or not en:
            continue
        override_ns.add(ns)
        wit = {loc: str(lang_dir / f"{loc}.json") if (lang_dir / f"{loc}.json").exists() else None
               for loc in ("ko_kr", "zh_cn")}
        units.append({"id": f"override:{ns}", "kind": "override", "namespace": ns,
                      "en": en, "jar_fr_partial": None, "witnesses": wit,
                      "target": f"kubejs/assets/{ns}/lang/fr_fr.json"})
    # -- mods --
    for ns, locs in sorted(ns_map.items()):
        en, fr = locs.get("en_us", {}), locs.get("fr_fr", {})
        todo = {k: v for k, v in en.items() if k not in fr}
        if ns in override_ns:  # les clés overridées sont déjà couvertes par l'unité override
            ov = load(REPO / "kubejs" / "assets" / ns / "lang" / "en_us.json")
            todo = {k: v for k, v in todo.items() if k not in ov}
        if not en:
            continue
        if not todo:
            skipped.append({"namespace": ns, "reason": "fr_complet" if fr else "sans_texte"})
            continue
        kind = "mod_delta" if fr else "mod"
        wit = {loc: locs.get(loc) and f"extracted:{ns}:{loc}" for loc in ("ko_kr", "zh_cn")}
        units.append({"id": f"mod:{ns}", "kind": kind, "namespace": ns,
                      "en": todo, "jar_fr_partial": fr or None, "witnesses": wit,
                      "target": f"kubejs/assets/{ns}/lang/fr_fr.json"})
    # -- society (template ∪ en_us) --
    sdir = REPO / "kubejs" / "assets" / "society" / "lang"
    sen = {**load(sdir / "en_us.json"), **load(sdir / "en_us_template.json")}
    units.append({"id": "society", "kind": "society", "namespace": "society",
                  "en": sen, "jar_fr_partial": None,
                  "witnesses": {"ko_kr": str(sdir / "ko_kr.json"), "zh_cn": str(sdir / "zh_cn.json")},
                  "target": "kubejs/assets/society/lang/fr_fr.json"})
    # -- quêtes --
    qdir = REPO / "kubejs" / "assets" / "ftbquestlocalizer" / "lang"
    units.append({"id": "quests", "kind": "quests", "namespace": "ftbquestlocalizer",
                  "en": load(qdir / "en_us.json"), "jar_fr_partial": None,
                  "witnesses": {"ko_kr": str(qdir / "ko_kr.json"), "zh_cn": str(qdir / "zh_cn.json")},
                  "target": "kubejs/assets/ftbquestlocalizer/lang/fr_fr.json"})
    # -- patchouli --
    for book_dir in sorted((REPO / "patchouli_books").iterdir()):
        for f in sorted((book_dir / "en_us").rglob("*.json")):
            en = pointers(json.loads(f.read_text()))
            if not en:
                continue
            rel = f.relative_to(book_dir / "en_us")
            ko = book_dir / "ko_kr" / rel
            units.append({"id": f"patchouli:{book_dir.name}/{rel}", "kind": "patchouli",
                          "namespace": book_dir.name, "en": en, "jar_fr_partial": None,
                          "witnesses": {"ko_kr": str(ko) if ko.exists() else None, "zh_cn": None},
                          "target": f"patchouli_books/{book_dir.name}/fr_fr/{rel}"})
    failed = load(ROOT / "fr-workspace" / "jars" / "_failed.json") or []
    stats = {"units": len(units),
             "keys_total": sum(len(u["en"]) for u in units),
             "par_kind": {}}
    for u in units:
        k = stats["par_kind"].setdefault(u["kind"], {"units": 0, "keys": 0})
        k["units"] += 1
        k["keys"] += len(u["en"])
    inv = {"units": units, "skipped": skipped,
           "unanalyzed": [f[0] for f in failed], "stats": stats}
    (ROOT / "fr-workspace" / "inventaire.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(stats, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run et contrôles de cohérence**

Run: `python3 fr-workspace/scripts/build_inventory.py`
Contrôles attendus : `society` ≈ 2000+ clés (union template+en_us), `quests` = 1659, nombre d'overrides ≈ 66+2, des unités `mod` en nombre comparable au modèle coréen (~100), `create` absent des units (fr complet dans le JAR → skipped).

- [ ] **Step 3: Contrôle anti-régression sur un cas connu**

Run: `python3 -c "import json; inv=json.load(open('fr-workspace/inventaire.json')); u=[x for x in inv['units'] if x['id']=='quests'][0]; print(len(u['en']))"`
Attendu : `1659`.

- [ ] **Step 4: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/build_inventory.py && git commit -m "feat: inventaire des unités de traduction"
```

---

### Task 5: Vérification EMI → décision accents

**Files:**
- Create: `ROOT/fr-workspace/DECISION-ACCENTS.md`

**Interfaces:**
- Produces: décision documentée `accent_free_prefixes` = `[]` (EMI insensible aux accents) OU `["item.", "block.", "entity."]` (EMI sensible → politique hybride). Consommée par T8 (validateur), T10 (STYLE.md) et T13 (prompts).

- [ ] **Step 1: Inspecter le code de recherche d'EMI**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/fr-workspace
mkdir -p emi-check && cd emi-check
unzip -o -q ../jars/emi-*.jar -d emi-jar
# localiser les classes de recherche
find emi-jar -path "*emi*search*" -name "*.class" | head -20
# chercher une normalisation Unicode dans ces classes
for f in $(find emi-jar -path "*search*" -name "*.class"); do
  if strings "$f" | grep -qiE "java/text/Normalizer|NFKD|NFD"; then echo "NORMALISATION TROUVÉE: $f"; fi
done
# contre-vérification sur tout le jar (au cas où la normalisation vit ailleurs)
for f in $(find emi-jar -name "*.class"); do
  strings "$f" | grep -qiE "java/text/Normalizer" && echo "$f"
done
```

- [ ] **Step 2: Trancher et documenter**

Interprétation : si `java/text/Normalizer` apparaît dans le chemin de recherche (classes `*search*` ou appelées par elles) → EMI plie les accents, `accent_free_prefixes = []`. Sinon → politique hybride, `accent_free_prefixes = ["item.", "block.", "entity."]`. En cas de doute (résultat ambigu), appliquer l'hybride (choix validé par l'utilisateur en brainstorming). Écrire `fr-workspace/DECISION-ACCENTS.md` :

```markdown
# Décision accents (spec §Phase 1.5)
- Version EMI inspectée : <nom exact du jar>
- Méthode : recherche de java/text/Normalizer dans les classes de recherche (strings sur .class)
- Résultat : <trouvé dans X / non trouvé>
- Décision : accent_free_prefixes = <[] ou ["item.", "block.", "entity."]>
```

- [ ] **Step 3: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/DECISION-ACCENTS.md && git commit -m "docs: décision politique accents (vérification EMI)"
```

---

### Task 6: Scan des chaînes en dur du pack

**Files:**
- Create: `ROOT/fr-workspace/scripts/scan_hardcoded.py`

**Interfaces:**
- Produces: `ROOT/fr-workspace/hardcoded-candidates.json` : `[{"file": "chemin relatif REPO", "line": 12, "text": "littéral anglais", "kind": "kubejs|fancymenu|dialog"}]`. Consommé par T14 (conversion) et T18 (rapport). Best-effort assumé.

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Repère le texte anglais littéral dans kubejs/, config/fancymenu/, Dialog. Best-effort."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
out = []
JS_PAT = re.compile(
    r"(?:Text\.of|Component\.literal|\.tooltip|\.displayName|\.formattedText|\.name)"
    r"\s*\(\s*['\"]([A-Z][^'\"]{3,120})['\"]")
for js in (REPO / "kubejs").rglob("*.js"):
    for i, line in enumerate(js.read_text(errors="ignore").splitlines(), 1):
        for m in JS_PAT.finditer(line):
            out.append({"file": str(js.relative_to(REPO)), "line": i,
                        "text": m.group(1), "kind": "kubejs"})
FM_KEYS = {"label", "text", "title", "tooltip", "description"}
def walk(obj, f):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FM_KEYS and isinstance(v, str) and re.search(r"[A-Za-z]{4}", v) \
               and not v.startswith(("%", "{", "fancymenu.", "society.")):
                out.append({"file": f, "line": 0, "text": v, "kind": "fancymenu"})
            else:
                walk(v, f)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, f)
for jf in (REPO / "config" / "fancymenu").rglob("*.json"):
    try:
        walk(json.loads(jf.read_text(errors="ignore")), str(jf.relative_to(REPO)))
    except Exception:
        pass
dedup = {(o["file"], o["line"], o["text"]): o for o in out}
(ROOT / "fr-workspace" / "hardcoded-candidates.json").write_text(
    json.dumps(list(dedup.values()), ensure_ascii=False, indent=1) + "\n")
print(f"{len(dedup)} candidats")
```

- [ ] **Step 2: Run et échantillonnage manuel**

Run: `python3 fr-workspace/scripts/scan_hardcoded.py && python3 -c "import json; c=json.load(open('fr-workspace/hardcoded-candidates.json')); print(len(c)); [print(x['file'], repr(x['text'])) for x in c[:15]]"`
Attendu : liste plausible (tooltips, labels de menus) ; les faux positifs (IDs, clés déjà localisées) seront filtrés à la main en T14.

- [ ] **Step 3: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/scan_hardcoded.py && git commit -m "feat: scan des chaînes en dur du pack"
```

---

### Task 7: Références vanilla Minecraft (EN + FR officiels)

**Files:**
- Create: `ROOT/fr-workspace/scripts/fetch_vanilla_refs.py`

**Interfaces:**
- Produces: `ROOT/fr-workspace/references/mc_en_us.json` et `mc_fr_fr.json` (traduction officielle Mojang 1.20.1). Consommés par T9/T10 (glossaire).

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Récupère en_us (client.jar) et fr_fr (assets Mojang) officiels de Minecraft 1.20.1."""
import io, json, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fr-workspace" / "references"

def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "sunlit-fr-pipeline"})
    return urllib.request.urlopen(req, timeout=180).read()

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    man = json.loads(get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"))
    meta = json.loads(get(next(v["url"] for v in man["versions"] if v["id"] == "1.20.1")))
    client = zipfile.ZipFile(io.BytesIO(get(meta["downloads"]["client"]["url"])))
    (OUT / "mc_en_us.json").write_bytes(client.read("assets/minecraft/lang/en_us.json"))
    idx = json.loads(get(meta["assetIndex"]["url"]))
    h = idx["objects"]["minecraft/lang/fr_fr.json"]["hash"]
    (OUT / "mc_fr_fr.json").write_bytes(get(f"https://resources.download.minecraft.net/{h[:2]}/{h}"))
    en = json.loads((OUT / "mc_en_us.json").read_text())
    fr = json.loads((OUT / "mc_fr_fr.json").read_text())
    print(f"vanilla en_us: {len(en)} clés, fr_fr: {len(fr)} clés")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run**

Run: `python3 fr-workspace/scripts/fetch_vanilla_refs.py`
Attendu : ~5000+ clés dans chaque fichier ; vérifier `python3 -c "import json; print(json.load(open('fr-workspace/references/mc_fr_fr.json'))['item.minecraft.golden_apple'])"` → « Pomme dorée ».

- [ ] **Step 3: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/fetch_vanilla_refs.py && git commit -m "feat: références vanilla Minecraft EN/FR"
```

---

### Task 8: Validateur de traduction (TDD)

**Files:**
- Create: `ROOT/fr-workspace/scripts/validate_translation.py`
- Test: `ROOT/fr-workspace/scripts/test_validate.py`

**Interfaces:**
- Produces: `validate(en: dict, fr: dict, accent_free_prefixes: tuple = ()) -> list[tuple[str, str]]` — liste d'erreurs `(code, clé)` avec codes `missing`, `extra`, `empty`, `tokens`, `accents`, `untranslated`. Et `tokens(s: str) -> list[str]`. Importé par T12 (apply), T13, T15, T16. CLI : `python3 validate_translation.py <en.json> <fr.json> [--accent-free item.,block.,entity.]`.

- [ ] **Step 1: Écrire les tests d'abord**

```python
#!/usr/bin/env python3
"""Tests du validateur. Run: python3 fr-workspace/scripts/test_validate.py"""
from validate_translation import tokens, validate

def check(name, cond):
    print(("OK  " if cond else "FAIL"), name)
    assert cond, name

# tokens
check("percent simple", tokens("Hello %s!") == ["%s"])
check("percent indexé", tokens("%1$s eats %2$s") == ["%1$s", "%2$s"])
check("codes couleur", tokens("§aGreen§r txt") == ["§a", "§r"])
check("patchouli", tokens("$(l)Stats$()") == ["$()", "$(l)"])
check("newline littéral", tokens(r"line\nnext") == [r"\n"])
# validate
en = {"a": "Hi %s", "b": "Plain", "item.mod.x": "Wheat"}
ok = {"a": "Salut %s", "b": "Simple", "item.mod.x": "Ble"}
check("cas nominal", validate(en, ok, ("item.",)) == [])
check("clé manquante", ("missing", "b") in validate(en, {"a": "Salut %s", "item.mod.x": "Ble"}, ()))
check("clé en trop", ("extra", "z") in validate(en, {**ok, "z": "?"}, ()))
check("token perdu", ("tokens", "a") in validate(en, {**ok, "a": "Salut"}, ()))
check("valeur vide", ("empty", "b") in validate(en, {**ok, "b": "  "}, ()))
check("accent interdit", ("accents", "item.mod.x") in validate(en, {**ok, "item.mod.x": "Blé"}, ("item.",)))
check("accent autorisé hors préfixe", validate(en, {**ok, "b": "Été"}, ("item.",)) == [])
check("non traduit", ("untranslated", "b") in validate({"b": "Sprinkler"}, {"b": "Sprinkler"}, ()))
check("identique légitime court", validate({"b": "OK"}, {"b": "OK"}, ()) == [])
print("Tous les tests passent.")
```

- [ ] **Step 2: Vérifier que les tests échouent**

Run: `cd fr-workspace/scripts && python3 test_validate.py`
Attendu : `ModuleNotFoundError: No module named 'validate_translation'`.

- [ ] **Step 3: Écrire le validateur**

```python
#!/usr/bin/env python3
"""Validation mécanique d'une traduction : clés, placeholders, accents, non-traduit."""
import json, re, sys

TOKEN = re.compile(r"%(?:\d+\$)?[sdfeu]|%%|§.|\$\([^)]*\)|\\n|\{\d+\}")
ACCENTS = re.compile("[àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇœŒæÆ]")
WORD = re.compile(r"[A-Za-z]{4,}")

def tokens(s: str) -> list:
    return sorted(TOKEN.findall(s))

def validate(en: dict, fr: dict, accent_free_prefixes: tuple = ()) -> list:
    errors = []
    for k, v in en.items():
        if k not in fr:
            errors.append(("missing", k))
            continue
        t = fr[k]
        if not isinstance(t, str) or not t.strip():
            errors.append(("empty", k))
            continue
        if tokens(v) != tokens(t):
            errors.append(("tokens", k))
        if accent_free_prefixes and k.startswith(tuple(accent_free_prefixes)) and ACCENTS.search(t):
            errors.append(("accents", k))
        if t == v and len(WORD.findall(v)) >= 1 and len(v) > 3:
            errors.append(("untranslated", k))
    errors.extend(("extra", k) for k in fr if k not in en)
    return errors

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pfx = ()
    if "--accent-free" in sys.argv:
        pfx = tuple(sys.argv[sys.argv.index("--accent-free") + 1].split(","))
    en = json.load(open(args[0]))
    fr = json.load(open(args[1]))
    errs = validate(en, fr, pfx)
    for code, key in errs:
        print(f"{code}\t{key}")
    print(f"{len(errs)} erreur(s)", file=sys.stderr)
    sys.exit(1 if errs else 0)
```

Note : le code `untranslated` est un *avertissement fort* — des mots identiques EN/FR existent (« Portion », « Total », noms propres du glossaire). T12/T13 le traitent comme non-bloquant si la valeur figure dans la liste des termes gardés en anglais du glossaire, bloquant sinon.

- [ ] **Step 4: Vérifier que les tests passent**

Run: `cd fr-workspace/scripts && python3 test_validate.py`
Attendu : `Tous les tests passent.` — sinon corriger le validateur (pas les tests) jusqu'à passage.

- [ ] **Step 5: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/validate_translation.py fr-workspace/scripts/test_validate.py
git commit -m "feat: validateur mécanique de traduction (TDD)"
```

---

### Task 9: Candidats glossaire

**Files:**
- Create: `ROOT/fr-workspace/scripts/glossary_candidates.py`

**Interfaces:**
- Consumes: `inventaire.json` (T4), `extracted/` (T3, fr complets des jars), `references/mc_*.json` (T7)
- Produces: `ROOT/fr-workspace/glossaire-candidats.json` : `[{"en": "Shipping Bin", "occurrences": 12, "namespaces": ["society", "..."], "vanilla_fr": null, "jar_fr": {"create": "..."}, "witness_ko": "배송 상자", "sample_keys": ["item.society.x"]}]`. Consommé par T10.

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Détecte les termes candidats au glossaire : valeurs EN partagées, noms Society, vocab vanilla."""
import json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "fr-workspace"

def main() -> None:
    inv = json.loads((WS / "inventaire.json").read_text())
    mc_en = json.loads((WS / "references" / "mc_en_us.json").read_text())
    mc_fr = json.loads((WS / "references" / "mc_fr_fr.json").read_text())
    vanilla = {v: mc_fr[k] for k, v in mc_en.items() if k in mc_fr}
    # index valeur EN → occurrences dans les unités à traduire
    occ = defaultdict(lambda: {"namespaces": set(), "keys": [], "count": 0, "witness_ko": None})
    ko_cache = {}
    for u in inv["units"]:
        ko = None
        w = u["witnesses"].get("ko_kr")
        if w and not w.startswith("extracted:"):
            ko = ko_cache.setdefault(w, json.loads(Path(w).read_text()) if Path(w).exists() else {})
        for k, v in u["en"].items():
            if len(v) > 60 or not re.search(r"[A-Za-z]", v):
                continue
            e = occ[v]
            e["namespaces"].add(u["namespace"])
            e["count"] += 1
            if len(e["keys"]) < 3:
                e["keys"].append(k)
            if ko and k in ko and not e["witness_ko"]:
                e["witness_ko"] = ko[k]
    # fr des jars complets (référence)
    jar_fr_index = defaultdict(dict)
    for jar_dir in (WS / "extracted").iterdir():
        for ns_dir in jar_dir.iterdir():
            en_f, fr_f = ns_dir / "en_us.json", ns_dir / "fr_fr.json"
            if en_f.exists() and fr_f.exists():
                en_d, fr_d = json.loads(en_f.read_text()), json.loads(fr_f.read_text())
                for k, v in en_d.items():
                    if k in fr_d and v != fr_d[k]:
                        jar_fr_index[v][ns_dir.name] = fr_d[k]
    cands = []
    for v, e in occ.items():
        multi = len(e["namespaces"]) >= 2
        society_name = "society" in e["namespaces"] and any(
            k.startswith(("item.", "block.")) for k in e["keys"])
        if not (multi or society_name or v in vanilla or v in jar_fr_index):
            continue
        cands.append({"en": v, "occurrences": e["count"],
                      "namespaces": sorted(e["namespaces"]),
                      "vanilla_fr": vanilla.get(v),
                      "jar_fr": jar_fr_index.get(v, {}),
                      "witness_ko": e["witness_ko"],
                      "sample_keys": e["keys"]})
    cands.sort(key=lambda c: -c["occurrences"])
    (WS / "glossaire-candidats.json").write_text(
        json.dumps(cands, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(cands)} candidats")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run et contrôle**

Run: `python3 fr-workspace/scripts/glossary_candidates.py && python3 -c "import json; c=json.load(open('fr-workspace/glossaire-candidats.json')); print(len(c)); [print(x['en'], '→ vanilla:', x['vanilla_fr'], '| jars:', x['jar_fr']) for x in c[:10]]"`
Attendu : quelques centaines de candidats ; les termes vanilla (« Wheat »…) montrent leur `vanilla_fr`.

- [ ] **Step 3: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/glossary_candidates.py && git commit -m "feat: extraction des candidats glossaire"
```

---

### Task 10: Workflow glossaire + guide de style

**Files:**
- Create: `ROOT/fr-workspace/glossaire.json`, `ROOT/fr-workspace/GLOSSAIRE.md`, `ROOT/fr-workspace/STYLE.md` (produits par workflow + script de fusion inline)

**Interfaces:**
- Consumes: `glossaire-candidats.json` (T9), `DECISION-ACCENTS.md` (T5)
- Produces: `glossaire.json` : `{"entries": [{"en": "...", "fr": "...", "keep_english": false, "rationale": "..."}], "keep_english_terms": ["Create", "Society", "..."]}` ; `GLOSSAIRE.md` (lisible, pour checkpoint) ; `STYLE.md` (guide complet). Consommés par T13, T15, T16.

- [ ] **Step 1: Préparer les segments** — découper `glossaire-candidats.json` en ~10 segments équilibrés (`fr-workspace/batches/gloss-XX.json`) via une commande inline :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 - <<'EOF'
import json, math
from pathlib import Path
c = json.loads(Path("fr-workspace/glossaire-candidats.json").read_text())
n = max(1, math.ceil(len(c) / 10))
Path("fr-workspace/batches").mkdir(exist_ok=True)
for i in range(0, len(c), n):
    Path(f"fr-workspace/batches/gloss-{i//n:02d}.json").write_text(
        json.dumps(c[i:i+n], ensure_ascii=False, indent=1))
print("segments:", math.ceil(len(c)/n))
EOF
```

- [ ] **Step 2: Lancer le workflow glossaire** (invocation Workflow ; agents ≤ 12). Script :

```js
export const meta = {
  name: 'glossaire-fr',
  description: 'Propose les traductions FR des termes du glossaire + guide de style',
  phases: [{ title: 'Recherche SDV' }, { title: 'Glossaire' }, { title: 'Style' }],
}
phase('Recherche SDV')
const sdv = await agent(`Recherche web : terminologie OFFICIELLE française de Stardew Valley.
Trouve les traductions officielles FR de : Shipping Bin, Perfection, quality (normal/argent/or/iridium),
saisons, Greenhouse, Sprinkler, Scarecrow, Junimo, Community Center, Fertilizer, forageables,
Luck, Energy, Artisan Goods, Preserves Jar, Keg, Coop, Barn, Fish Pond.
Retourne un JSON {terme_en: terme_fr_officiel} + notes sur les termes non traduits officiellement.`,
  { label: 'sdv-fr', schema: { type: 'object', properties: { terms: { type: 'object' }, notes: { type: 'string' } }, required: ['terms'] } })
phase('Glossaire')
const results = await parallel(args.segments.map(seg => () =>
  agent(`Tu établis le glossaire FR du modpack Minecraft "Society: Sunlit Valley"
(ferme/commerce, esprit Stardew Valley, public familial).
Lis le fichier ${seg} : candidats [{en, occurrences, namespaces, vanilla_fr, jar_fr, witness_ko, sample_keys}].
Pour CHAQUE candidat propose la traduction FR canonique. Règles de priorité STRICTES :
1. vanilla_fr non nul → reprendre EXACTEMENT vanilla_fr.
2. jar_fr non vide → reprendre la traduction du jar (si plusieurs jars divergent, choisis la plus naturelle et note-le).
3. Terminologie officielle Stardew Valley FR : ${JSON.stringify(sdv.terms)}.
4. Sinon traduis toi-même : fidèle, naturel, capitalisation française (majuscule initiale seule).
keep_english=true UNIQUEMENT pour : noms propres de mods (Create, Botania…), marques du pack
(Society, Sunlit Valley), termes iconiques intraduisibles sans trahir l'esprit du jeu.
Indice : witness_ko montre ce que le traducteur coréen a fait (s'il a gardé l'anglais, c'est un signal fort).
Écris ta sortie dans ${seg.replace('gloss-', 'gloss-out-')} avec le tool Write :
{"entries": [{"en", "fr", "keep_english", "rationale"}]} (rationale ≤ 15 mots).
Retourne {"written": "<chemin>", "count": N}.`,
    { label: seg, phase: 'Glossaire', schema: { type: 'object', properties: { written: { type: 'string' }, count: { type: 'number' } }, required: ['written', 'count'] } })))
phase('Style')
const style = await agent(`Rédige fr-workspace/STYLE.md (tool Write) : guide de style FR du modpack
Society: Sunlit Valley. Sections OBLIGATOIRES, avec exemples chacune :
1. Registre : tutoiement chaleureux dans quêtes/dialogues (esprit Stardew Valley), impersonnel/infinitif
   type Minecraft FR pour l'interface. 2. Capitalisation française ("Houe dorée" jamais "Houe Dorée").
3. Politique accents : lis fr-workspace/DECISION-ACCENTS.md et intègre sa décision.
4. Typographie : accents sur majuscules (É), apostrophe droite ', pas d'espace insécable (police Minecraft),
   espace simple avant ! et ?. 5. Codes intouchables : %s %1$s §x $(...) \\n {0} 🌐.
6. Faux-amis du domaine (crop→culture, can→arrosoir/bidon selon contexte, mill→moulin…).
Retourne {"written": "fr-workspace/STYLE.md"}.`,
  { label: 'style', schema: { type: 'object', properties: { written: { type: 'string' } }, required: ['written'] } })
return { segments: results.filter(Boolean).length, style: style.written, sdvNotes: sdv.notes }
```

Invocation : `Workflow({script: <ci-dessus>, args: {segments: ["fr-workspace/batches/gloss-00.json", "..."]}})` avec la liste réelle des segments du Step 1.

- [ ] **Step 3: Fusionner les sorties en glossaire.json**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 - <<'EOF'
import json
from pathlib import Path
entries, seen = [], set()
for f in sorted(Path("fr-workspace/batches").glob("gloss-out-*.json")):
    for e in json.loads(f.read_text())["entries"]:
        if e["en"] not in seen:
            seen.add(e["en"]); entries.append(e)
keep = sorted({e["en"] for e in entries if e.get("keep_english")})
gl = {"entries": entries, "keep_english_terms": keep}
Path("fr-workspace/glossaire.json").write_text(json.dumps(gl, ensure_ascii=False, indent=1) + "\n")
md = ["# Glossaire FR — Society: Sunlit Valley", "", "## Termes gardés en anglais", ""]
md += [f"- **{t}**" for t in keep]
md += ["", "## Traductions imposées", "", "| EN | FR | Justification |", "|---|---|---|"]
md += [f"| {e['en']} | {e['fr']} | {e.get('rationale','')} |" for e in entries if not e.get("keep_english")]
Path("fr-workspace/GLOSSAIRE.md").write_text("\n".join(md) + "\n")
print(len(entries), "entrées,", len(keep), "gardées en anglais")
EOF
```

- [ ] **Step 4: Vérification de cohérence interne du glossaire** — deux entrées FR identiques pour des EN différents sont légitimes ; une entrée EN avec deux FR est impossible par construction (dédup). Contrôle rapide : `python3 -c "import json; g=json.load(open('fr-workspace/glossaire.json')); print(len(g['entries']))"`.

- [ ] **Step 5: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/glossaire.json fr-workspace/GLOSSAIRE.md fr-workspace/STYLE.md
git commit -m "feat: glossaire maître + guide de style"
```

---

### Task 11: ✋ CHECKPOINT utilisateur — glossaire, style, volumes

**Files:** aucun nouveau (présentation)

**Interfaces:**
- Consumes: `GLOSSAIRE.md`, `STYLE.md`, `inventaire.json`, `DECISION-ACCENTS.md`
- Produces: validation utilisateur explicite. BLOQUANT : ne pas lancer T12+ sans elle.

- [ ] **Step 1: Envoyer les documents** via SendUserFile : `GLOSSAIRE.md`, `STYLE.md`, `DECISION-ACCENTS.md`.

- [ ] **Step 2: Présenter la synthèse** dans la conversation : stats de l'inventaire (unités et clés par kind), résultat EMI/accents, liste des termes gardés en anglais, 10 exemples de traductions imposées, mods non analysés (jars en échec), estimation du volume de la traduction de masse.

- [ ] **Step 3: Attendre la validation.** Amendements demandés → éditer `glossaire.json`/`STYLE.md` directement, re-committer, re-présenter. Ne passer à T12 qu'après un accord explicite.

---

### Task 12: Générateur de lots + applicateur de traductions

**Files:**
- Create: `ROOT/fr-workspace/scripts/make_batches.py`, `ROOT/fr-workspace/scripts/apply_translations.py`

**Interfaces:**
- `make_batches.py [--kinds society,override,quests,mod,mod_delta,patchouli]` : lit `inventaire.json`, écrit `fr-workspace/batches/tr-<kind>-NNN.json` :
  `{"unit_id", "kind", "namespace", "target", "en": {...≤200 clés...}, "context_sample": {...30 paires...}, "jar_fr_partial": {...}, "witness_ko": {...clés du lot...}, "out": "fr-workspace/out/<unit_id_slug>-NNN.json"}`. Unité ≤200 clés = 1 lot ; sinon tranches de 200.
- `apply_translations.py <batch.json>...` : lit chaque batch + son `out` (`{"translations": {...}}`), valide via `validate_translation.validate` (accent_free selon `DECISION-ACCENTS.md`, `untranslated` toléré si valeur ∈ `keep_english_terms`), fusionne dans `REPO/<target>` (kind patchouli : reconstruit le fichier depuis `en_us` + pointers). Exit 1 avec rapport si erreurs.

- [ ] **Step 1: Écrire make_batches.py**

```python
#!/usr/bin/env python3
"""Découpe l'inventaire en lots de traduction ≤200 clés avec contexte."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "fr-workspace"
CHUNK = 200

def main() -> None:
    kinds = None
    if "--kinds" in sys.argv:
        kinds = set(sys.argv[sys.argv.index("--kinds") + 1].split(","))
    inv = json.loads((WS / "inventaire.json").read_text())
    (WS / "batches").mkdir(exist_ok=True)
    made = []
    for u in inv["units"]:
        if kinds and u["kind"] not in kinds:
            continue
        items = sorted(u["en"].items())
        ctx = dict(items[:30])
        ko = {}
        w = u["witnesses"].get("ko_kr")
        if w and not str(w).startswith("extracted:") and w and Path(w).exists():
            ko = json.loads(Path(w).read_text())
        slug = re.sub(r"[^a-z0-9]+", "_", u["id"].lower())
        for n, i in enumerate(range(0, len(items), CHUNK)):
            chunk = dict(items[i:i + CHUNK])
            batch = {"unit_id": u["id"], "kind": u["kind"], "namespace": u["namespace"],
                     "target": u["target"], "en": chunk, "context_sample": ctx,
                     "jar_fr_partial": u["jar_fr_partial"],
                     "witness_ko": {k: ko[k] for k in chunk if k in ko},
                     "out": f"fr-workspace/out/{slug}-{n:03d}.json"}
            p = WS / "batches" / f"tr-{u['kind']}-{slug}-{n:03d}.json"
            p.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n")
            made.append(str(p.relative_to(ROOT)))
    print(json.dumps(made, indent=1))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Écrire apply_translations.py**

```python
#!/usr/bin/env python3
"""Applique les sorties d'agents aux fichiers cibles du repo, après validation."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_translation import validate

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

def accent_prefixes() -> tuple:
    txt = (WS / "DECISION-ACCENTS.md").read_text()
    return ("item.", "block.", "entity.") if '["item.", "block.", "entity."]' in txt else ()

def set_pointer(obj, pointer: str, value: str) -> None:
    parts = pointer.split("/")
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value

def main() -> None:
    gl = json.loads((WS / "glossaire.json").read_text())
    keep = set(gl["keep_english_terms"])
    pfx = accent_prefixes()
    all_errors = {}
    for batch_path in sys.argv[1:]:
        b = json.loads(Path(batch_path).read_text())
        out_p = ROOT / b["out"]
        if not out_p.exists():
            all_errors[batch_path] = [("no_output", b["out"])]
            continue
        tr = json.loads(out_p.read_text())["translations"]
        errs = [e for e in validate(b["en"], tr, pfx)
                if not (e[0] == "untranslated" and b["en"][e[1]] in keep)]
        if errs:
            all_errors[batch_path] = errs
            continue
        target = REPO / b["target"]
        if b["kind"] == "patchouli":
            src = REPO / b["target"].replace("/fr_fr/", "/en_us/")
            doc = json.loads(src.read_text())
            for ptr, val in tr.items():
                set_pointer(doc, ptr, val)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(doc, ensure_ascii=False, indent=4) + "\n")
        else:
            cur = json.loads(target.read_text()) if target.exists() else {}
            cur.update(tr)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print("appliqué:", b["target"], f"({len(tr)} clés)")
    if all_errors:
        print(json.dumps({k: v[:20] for k, v in all_errors.items()}, ensure_ascii=False, indent=1))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Note (première vague d'un `target`) : les `fr_fr.json` communautaires existants sont REMPLACÉS — avant la première application sur un target de kind ≠ patchouli, `apply` fusionne dans le fichier existant. Pour respecter la spec, la première étape de chaque vague T13 supprime le fichier cible existant (`git rm` les fr_fr.json des unités de la vague) AVANT d'appliquer.

- [ ] **Step 3: Test sur un mini-lot fabriqué à la main**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
mkdir -p fr-workspace/out
cat > fr-workspace/batches/tr-test-000.json <<'EOF'
{"unit_id": "test", "kind": "mod", "namespace": "testns",
 "target": "kubejs/assets/testns/lang/fr_fr.json",
 "en": {"item.testns.pie": "Apple Pie %s"}, "context_sample": {},
 "jar_fr_partial": null, "witness_ko": {}, "out": "fr-workspace/out/test-000.json"}
EOF
echo '{"translations": {"item.testns.pie": "Tarte aux pommes %s"}}' > fr-workspace/out/test-000.json
python3 fr-workspace/scripts/apply_translations.py fr-workspace/batches/tr-test-000.json
cat society-sunlit-valley/kubejs/assets/testns/lang/fr_fr.json
# nettoyage
rm -rf society-sunlit-valley/kubejs/assets/testns fr-workspace/batches/tr-test-000.json fr-workspace/out/test-000.json
```
Attendu : « appliqué: … (1 clés) », fichier créé avec la traduction, puis nettoyé. Refaire le même test avec `"Tarte %d"` dans out → exit 1, erreur `tokens`.

- [ ] **Step 4: Commit (racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/make_batches.py fr-workspace/scripts/apply_translations.py
git commit -m "feat: générateur de lots + applicateur avec validation"
```

---

### Task 13: Vagues de traduction

**Files:**
- Modify: `REPO/kubejs/assets/*/lang/fr_fr.json`, `REPO/patchouli_books/*/fr_fr/**` (créés/remplacés)

**Interfaces:**
- Consumes: batches (T12), `glossaire.json`, `STYLE.md`, `apply_translations.py`
- Produces: tous les fichiers FR du périmètre, committés par vague dans REPO.

Ordre des vagues (une vague = un kind ; grosses vagues découpées en invocations Workflow de ≤15 lots) :
1. `society` — 2. `override` — 3. `quests` — 4. `mod` + `mod_delta` — 5. `patchouli`

- [ ] **Step 1: Générer les lots de la vague** (exemple vague 1) :

Run: `python3 fr-workspace/scripts/make_batches.py --kinds society`

- [ ] **Step 2: Purger les cibles de la vague** (remplacement, pas fusion — spec) :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
# pour chaque target distinct de la vague (lister via les batch files) :
git rm -q --ignore-unmatch kubejs/assets/society/lang/fr_fr.json
# vague patchouli : git rm -r --ignore-unmatch patchouli_books/*/fr_fr
```

- [ ] **Step 3: Lancer le workflow de traduction** sur les lots de la vague (≤15 par invocation, invocations successives jusqu'à épuisement). Script générique :

```js
export const meta = {
  name: 'traduire-lots-fr',
  description: 'Traduit des lots EN→FR avec glossaire et style',
  phases: [{ title: 'Traduire' }],
}
const outs = await parallel(args.batches.map(b => () =>
  agent(`Tu es traducteur professionnel EN→FR d'un modpack Minecraft façon Stardew Valley.
AVANT TOUT lis ces trois fichiers (tool Read) :
1. ${args.root}/fr-workspace/STYLE.md (règles de style, registre, accents — OBLIGATOIRES)
2. ${args.root}/fr-workspace/GLOSSAIRE.md (traductions imposées + termes à garder en anglais)
3. ${args.root}/${b} (ton lot : {unit_id, kind, en, context_sample, jar_fr_partial, witness_ko, out})
Puis traduis CHAQUE clé de "en" :
- Respect ABSOLU du glossaire ; termes keep_english laissés tels quels.
- Codes intouchables, à recopier à l'identique : %s %1$s §x $(...) \\n {0} %%  et le marqueur 🌐.
- kind=quests/dialog : tutoiement chaleureux. Interface : impersonnel type Minecraft FR.
- jar_fr_partial non nul : aligne ton style sur ces traductions existantes du mod.
- witness_ko : témoin d'interprétation (si le sens EN est ambigu, le choix coréen éclaire le sens, jamais le style).
- context_sample : contexte du mod, pour cohérence interne.
- Ne traduis JAMAIS une clé absente de "en", n'en invente aucune.
Écris (tool Write) dans le fichier "out" du lot : {"translations": {"clé": "traduction", ...}}
avec TOUTES les clés de "en". Retourne {"unit_id", "out", "count"}.`,
    { label: b, schema: { type: 'object', properties: { unit_id: { type: 'string' }, out: { type: 'string' }, count: { type: 'number' } }, required: ['unit_id', 'out', 'count'] } })))
return { done: outs.filter(Boolean).length, failed: args.batches.length - outs.filter(Boolean).length }
```

Invocation : `Workflow({script, args: {root: "/Users/thomas/IAPersoProjects/SunlitValley", batches: [<≤15 chemins relatifs de batch>]}})`.

- [ ] **Step 4: Appliquer + valider la vague**

Run: `python3 fr-workspace/scripts/apply_translations.py fr-workspace/batches/tr-society-*.json`
Attendu : exit 0. Si exit 1 : pour chaque lot en erreur, relancer UN agent de correction (même prompt + la liste exacte des erreurs `(code, clé)` en tête), puis re-appliquer. Deux échecs consécutifs sur le même lot → le traduire inline (moi) et consigner.

- [ ] **Step 5: Committer la vague dans REPO**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
git add kubejs/assets/*/lang/fr_fr.json patchouli_books/*/fr_fr
git commit -m "trad(fr): vague society — retraduction intégrale"
```

- [ ] **Step 6: Répéter Steps 1-5 pour chaque vague** (`override`, `quests`, `mod,mod_delta`, `patchouli`) avec le message de commit adapté (`trad(fr): vague overrides`, `trad(fr): vague quêtes`, `trad(fr): vague mods`, `trad(fr): vague patchouli`). Vague `mod` : plusieurs dizaines d'invocations Workflow successives — suivre l'avancement en cochant ici :
  - [ ] Vague 1 society appliquée + committée
  - [ ] Vague 2 overrides appliquée + committée
  - [ ] Vague 3 quêtes appliquée + committée
  - [ ] Vague 4 mods appliquée + committée
  - [ ] Vague 5 patchouli appliquée + committée

---

### Task 14: Conversion opportuniste des chaînes en dur KubeJS

**Files:**
- Modify: scripts `REPO/kubejs/**/*.js` concernés, `REPO/kubejs/assets/society/lang/en_us.json` + `fr_fr.json`

**Interfaces:**
- Consumes: `hardcoded-candidates.json` (T6), glossaire
- Produces: littéraux convertis en `Text.translate('society.hardcoded.<slug>')` + clés ajoutées aux deux langues. Commit dédié.

- [ ] **Step 1: Trier les candidats à la main** — parcourir `hardcoded-candidates.json`, éliminer les faux positifs (IDs, texte déjà localisé, texte non visible en jeu). Garder une liste courte et sûre (candidats `kubejs` dont le littéral s'affiche réellement : tooltips, messages, noms).

- [ ] **Step 2: Convertir chaque littéral retenu** — pour un littéral `"Some Tooltip"` dans `kubejs/client_scripts/foo.js` :
  1. Choisir un slug : `society.hardcoded.some_tooltip`.
  2. Remplacer dans le script : `Text.of('Some Tooltip')` → `Text.translate('society.hardcoded.some_tooltip')` (Edit ; adapter à l'appel réel : `.tooltip(Text.translate(...))` etc.).
  3. Ajouter `"society.hardcoded.some_tooltip": "Some Tooltip"` dans `kubejs/assets/society/lang/en_us.json` et sa traduction dans `fr_fr.json`.
  Les candidats `fancymenu` ne sont PAS convertis (leurs layouts ne supportent pas les clés lang de façon fiable) : ils restent recensés pour le rapport (T18).

- [ ] **Step 3: Vérifier la syntaxe JS** — pas de test runner KubeJS hors jeu : contrôle par `node --check` :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
for f in $(git diff --name-only -- 'kubejs/**/*.js'); do node --check "$f" && echo "OK $f"; done
```
Attendu : OK pour chaque fichier modifié. (`node --check` valide la syntaxe, pas l'API KubeJS — l'exécution réelle est vérifiée au test en jeu, T18.)

- [ ] **Step 4: Commit dédié (REPO)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
git add kubejs
git commit -m "trad(fr): conversion des littéraux KubeJS en clés de lang (en_us + fr_fr) — à vérifier en jeu"
```

---

### Task 15: Réconciliation globale EN→FR

**Files:**
- Create: `ROOT/fr-workspace/scripts/reconcile.py`

**Interfaces:**
- Consumes: tous les `fr_fr.json` produits (REPO), `extracted/` (fr des JARs), `glossaire.json`, `inventaire.json`
- Produces: `fr-workspace/divergences.json` : `[{"en": "...", "variants": {"trad A": [["fichier", "clé"]], "trad B": [...]}}]` ; puis application des arbitrages. Garantit « 1 chaîne EN = 1 traduction FR » (sauf `keep_distinct` justifié).

- [ ] **Step 1: Écrire reconcile.py**

```python
#!/usr/bin/env python3
"""Détecte les chaînes EN identiques traduites différemment ; applique les arbitrages."""
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

def collect():
    """en_value → {fr_value → [(source, clé)]}. Sources: fichiers produits + jars fr complets."""
    index = defaultdict(lambda: defaultdict(list))
    inv = json.loads((WS / "inventaire.json").read_text())
    en_by_target = defaultdict(dict)
    for u in inv["units"]:
        if u["kind"] != "patchouli":
            en_by_target[u["target"]].update(u["en"])
    for target, en in en_by_target.items():
        fp = REPO / target
        if not fp.exists():
            continue
        fr = json.loads(fp.read_text())
        for k, v in en.items():
            if k in fr and len(v) <= 60:
                index[v][fr[k]].append([target, k])
    for jar_dir in (WS / "extracted").iterdir():
        for ns_dir in jar_dir.iterdir():
            en_f, fr_f = ns_dir / "en_us.json", ns_dir / "fr_fr.json"
            if not (en_f.exists() and fr_f.exists()):
                continue
            en_d, fr_d = json.loads(en_f.read_text()), json.loads(fr_f.read_text())
            for k, v in en_d.items():
                if k in fr_d and len(v) <= 60:
                    index[v][fr_d[k]].append([f"jar:{ns_dir.name}", k])
    return index

def detect():
    div = [{"en": en, "variants": {fr: locs for fr, locs in variants.items()}}
           for en, variants in collect().items() if len(variants) > 1]
    (WS / "divergences.json").write_text(json.dumps(div, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(div)} divergences")

def apply_choices(choices_path: str):
    """choices: [{"en", "chosen_fr", "keep_distinct": false}] — applique chosen_fr partout
    dans les fichiers PRODUITS ; pour les sources jar:<ns>, ajoute un override ciblé."""
    choices = json.loads(Path(choices_path).read_text())
    div = {d["en"]: d for d in json.loads((WS / "divergences.json").read_text())}
    edits = defaultdict(dict)
    for c in choices:
        if c.get("keep_distinct"):
            continue
        for fr, locs in div[c["en"]]["variants"].items():
            if fr == c["chosen_fr"]:
                continue
            for src, key in locs:
                if src.startswith("jar:"):
                    edits[f"kubejs/assets/{src[4:]}/lang/fr_fr.json"][key] = c["chosen_fr"]
                else:
                    edits[src][key] = c["chosen_fr"]
    for target, kv in edits.items():
        fp = REPO / target
        cur = json.loads(fp.read_text()) if fp.exists() else {}
        cur.update(kv)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print("réconcilié:", target, len(kv), "clés")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_choices(sys.argv[2])
    else:
        detect()
```

- [ ] **Step 2: Détecter**

Run: `python3 fr-workspace/scripts/reconcile.py`
Attendu : `divergences.json` produit ; en lire 5 à la main pour vérifier le format.

- [ ] **Step 3: Arbitrer par workflow** (lots de ~40 divergences par agent, ≤15 agents par invocation) :

```js
export const meta = {
  name: 'arbitrage-divergences-fr',
  description: 'Choisit la traduction FR canonique pour chaque chaîne EN divergente',
  phases: [{ title: 'Arbitrer' }],
}
const outs = await parallel(args.slices.map((s, i) => () =>
  agent(`Lis ${args.root}/fr-workspace/GLOSSAIRE.md puis ${s} (divergences [{en, variants}]).
Pour CHAQUE divergence choisis LA traduction canonique parmi les variantes (ou une meilleure
si toutes sont fautives — rare). keep_distinct=true SEULEMENT si la même chaîne EN a
légitimement deux sens selon le contexte (ex. "Charge" nom vs verbe) — justifie en ≤10 mots.
Priorité : glossaire > traduction du jar officiel > majorité > naturel.
Écris (tool Write) ${s.replace('.json', '-choix.json')} :
[{"en", "chosen_fr", "keep_distinct", "why"}]. Retourne {"count": N}.`,
    { label: `arb-${i}`, schema: { type: 'object', properties: { count: { type: 'number' } }, required: ['count'] } })))
return { done: outs.filter(Boolean).length }
```

Préparation des tranches et fusion des choix (inline) :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 - <<'EOF'
import json
from pathlib import Path
d = json.loads(Path("fr-workspace/divergences.json").read_text())
for i in range(0, len(d), 40):
    Path(f"fr-workspace/batches/div-{i//40:03d}.json").write_text(
        json.dumps(d[i:i+40], ensure_ascii=False, indent=1))
print((len(d) + 39) // 40, "tranches")
EOF
# après le workflow :
python3 - <<'EOF'
import json
from pathlib import Path
allc = []
for f in sorted(Path("fr-workspace/batches").glob("div-*-choix.json")):
    allc += json.loads(f.read_text())
Path("fr-workspace/choix-reconciliation.json").write_text(json.dumps(allc, ensure_ascii=False, indent=1))
print(len(allc), "choix")
EOF
```

- [ ] **Step 4: Appliquer + re-valider**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 fr-workspace/scripts/reconcile.py --apply fr-workspace/choix-reconciliation.json
python3 fr-workspace/scripts/reconcile.py   # re-détection
```
Attendu à la re-détection : seules les divergences `keep_distinct` restent. Puis re-valider tous les fichiers touchés avec `validate_translation.py` (les remplacements peuvent casser un placeholder si `chosen_fr` vient d'un contexte différent) :
`for b in fr-workspace/batches/tr-*.json; do python3 fr-workspace/scripts/apply_translations.py "$b" 2>/dev/null || echo "REVALIDER: $b"; done` — toute erreur → correction inline.

- [ ] **Step 5: Commit (REPO + racine)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
git add kubejs/assets && git commit -m "trad(fr): réconciliation globale — 1 chaîne EN = 1 traduction FR"
cd .. && git add fr-workspace/scripts/reconcile.py && git commit -m "feat: réconciliation EN→FR"
```

---

### Task 16: Relecture qualité intégrale

**Files:**
- Modify: fichiers FR produits (corrections)

**Interfaces:**
- Consumes: fichiers FR produits, `STYLE.md`, `GLOSSAIRE.md`
- Produces: corrections appliquées + re-validation mécanique. Workflow par lots de fichiers.

- [ ] **Step 1: Lister les fichiers produits**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
git diff --name-only master...traduction-fr -- 'kubejs/assets/*/lang/fr_fr.json' 'patchouli_books/*/fr_fr' > ../fr-workspace/produced-files.txt
wc -l ../fr-workspace/produced-files.txt
```

- [ ] **Step 2: Workflow de relecture** (1 agent par fichier ≤400 clés, sinon 1 agent par moitié ; ≤15 agents par invocation, invocations successives) :

```js
export const meta = {
  name: 'relecture-fr',
  description: 'Relecture qualité des traductions FR produites',
  phases: [{ title: 'Relire' }],
}
const outs = await parallel(args.files.map(f => () =>
  agent(`Relecteur FR natif, exigeant. Lis ${args.root}/fr-workspace/STYLE.md et
${args.root}/fr-workspace/GLOSSAIRE.md, puis le fichier ${args.root}/society-sunlit-valley/${f}
et sa source EN (${f.includes('patchouli') ? 'le fichier en_us correspondant (remplace /fr_fr/ par /en_us/)' : 'en_us.json du même dossier, ou fr-workspace/extracted pour les mods'}).
Traque : fautes d'orthographe/grammaire/accords, anglicismes, calques, contresens vs l'EN,
tutoiement/vouvoiement incohérent, violations du glossaire, capitalisation anglaise.
NE MODIFIE PAS les codes %s §x $(...) \\n. NE change PAS un choix terminologique conforme au glossaire.
Écris (tool Write) ${args.root}/fr-workspace/out/review-<basename>.json :
{"file": "${f}", "corrections": [{"key": "...", "fr": "texte corrigé", "reason": "≤10 mots"}]}
([] si rien à corriger). Retourne {"file", "count"}.`,
    { label: f, schema: { type: 'object', properties: { file: { type: 'string' }, count: { type: 'number' } }, required: ['file', 'count'] } })))
return { reviewed: outs.filter(Boolean).length, corrections: outs.filter(Boolean).reduce((a, o) => a + o.count, 0) }
```

- [ ] **Step 3: Appliquer les corrections** (inline) :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 - <<'EOF'
import json
from pathlib import Path
REPO = Path("society-sunlit-valley")
n = 0
for rf in Path("fr-workspace/out").glob("review-*.json"):
    r = json.loads(rf.read_text())
    fp = REPO / r["file"]
    if r["file"].startswith("patchouli_books"):
        continue  # corrections patchouli : appliquer à la main (pointers), rares
    cur = json.loads(fp.read_text())
    for c in r["corrections"]:
        if c["key"] in cur:
            cur[c["key"]] = c["fr"]; n += 1
    fp.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
print(n, "corrections appliquées")
EOF
```
Les `review-*.json` de fichiers patchouli sont appliqués à la main (Edit sur les champs pointés), puis re-vérifier chaque fichier corrigé avec `apply_translations.py` sur ses batches (comme T15 Step 4).

- [ ] **Step 4: Commit (REPO)**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley/society-sunlit-valley
git add kubejs/assets patchouli_books && git commit -m "trad(fr): relecture qualité intégrale"
```

---

### Task 17: Build du resource pack

**Files:**
- Create: `ROOT/fr-workspace/scripts/build_fr_resourcepack.py`
- Create: `REPO/resourcepacks/Society_FR.zip` (généré)

**Interfaces:**
- Consumes: `REPO/kubejs/assets/*/lang/fr_fr.json`
- Produces: zip avec `pack.mcmeta` (pack_format 15) + `assets/<ns>/lang/fr_fr.json`. Ne contient PAS les patchouli (chargés depuis le dossier du pack, pas du resource pack).

- [ ] **Step 1: Écrire le script**

```python
#!/usr/bin/env python3
"""Génère resourcepacks/Society_FR.zip depuis les overrides kubejs. Relançable."""
import json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"

def main() -> None:
    dest = REPO / "resourcepacks" / "Society_FR.zip"
    files = sorted((REPO / "kubejs" / "assets").glob("*/lang/fr_fr.json"))
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps(
            {"pack": {"pack_format": 15,
                      "description": "Traduction FR non officielle — Society: Sunlit Valley"}},
            ensure_ascii=False, indent=2))
        for f in files:
            z.write(f, f"assets/{f.parents[1].name}/lang/fr_fr.json")
    print(f"écrit {dest.name}: {len(files)} fichiers lang")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run + vérification**

Run: `python3 fr-workspace/scripts/build_fr_resourcepack.py && unzip -l society-sunlit-valley/resourcepacks/Society_FR.zip | head`
Attendu : `pack.mcmeta` + N fichiers lang, N = nombre de namespaces traduits.

- [ ] **Step 3: Commits**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add fr-workspace/scripts/build_fr_resourcepack.py && git commit -m "feat: build du resource pack FR"
cd society-sunlit-valley
git add resourcepacks/Society_FR.zip && git commit -m "trad(fr): resource pack Society_FR.zip"
```

Note : `.gitignore` du REPO contient `resourcepacks/*` avec exception `!/resourcepacks/sunlit_overrides.zip` — ajouter l'exception `!/resourcepacks/Society_FR.zip` au `.gitignore` du REPO dans ce commit (`git add .gitignore`).

- [ ] **Step 4: Vérifier l'exception .gitignore**

Run: `cd society-sunlit-valley && git check-ignore resourcepacks/Society_FR.zip; echo "exit=$?"`
Attendu : `exit=1` (non ignoré).

---

### Task 18: Rapport final + handoff test en jeu

**Files:**
- Create: `ROOT/docs/RAPPORT-TRADUCTION-FR.md`

**Interfaces:**
- Consumes: `inventaire.json`, `divergences.json`, `hardcoded-candidates.json`, `jars/_failed.json`, stats des vagues
- Produces: rapport final envoyé à l'utilisateur + instructions de test.

- [ ] **Step 1: Générer les statistiques**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 - <<'EOF'
import json
from pathlib import Path
inv = json.loads(Path("fr-workspace/inventaire.json").read_text())
div = json.loads(Path("fr-workspace/divergences.json").read_text())
hc = json.loads(Path("fr-workspace/hardcoded-candidates.json").read_text())
print(json.dumps({"stats": inv["stats"], "skipped": len(inv["skipped"]),
                  "unanalyzed": inv["unanalyzed"], "divergences_restantes": len(div),
                  "hardcoded_recensés": len(hc)}, ensure_ascii=False, indent=1))
EOF
```

- [ ] **Step 2: Rédiger `docs/RAPPORT-TRADUCTION-FR.md`** avec les sections : Vue d'ensemble (chiffres du Step 1) ; Ce qui est traduit (par kind, nb clés) ; Ce qui ne l'est pas et pourquoi (mods fr-complets skippés, jars non téléchargés, chaînes en dur des mods, candidats fancymenu non convertis, textures avec texte — inventaire best-effort, explicitement non exhaustif) ; Choix terminologiques majeurs (extraits de GLOSSAIRE.md) ; Divergences keep_distinct et leur justification ; Maintenance (procédure delta : relancer T2→T4, `make_batches` ne produit que les clés nouvelles, re-vague T13) ; Comment tester (langue fr_fr dans Minecraft, points de contrôle : noms d'items Society, une quête, un écran EMI, recherche « ble »/« blé » selon la politique accents, un livre patchouli).

- [ ] **Step 3: Envoyer et committer**

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
git add docs/RAPPORT-TRADUCTION-FR.md && git commit -m "docs: rapport final de traduction"
```
Puis SendUserFile du rapport + message de synthèse avec les instructions de test en jeu. Les retours de test utilisateur (contresens repérés en jeu, réglages de style) sont traités comme corrections ponctuelles : Edit du fichier concerné + re-run `build_fr_resourcepack.py` + commit.

---

## Self-Review (fait à l'écriture du plan)

1. **Couverture spec** : Phase 1 → T2-T6 ; Phase 2 → T7, T9, T10, T11 (checkpoint) ; Phase 3 → T8, T12, T13, T14 ; Phase 4 → T15 (réconciliation + FR des jars, spec §Phase 4.2), T16 ; Phase 5 → T17, T18. Politique accents → T5 + T8 + STYLE.md. Témoins ko/zh → T4 (witnesses), T9 (witness_ko), T13 (prompt). Patchouli → T4 (pointers), T13 vague 5, T12 (apply). Chaînes en dur → T6 + T14 + rapport. Maintenance delta → rapport T18. ✓
2. **Placeholders** : aucun TBD ; tous les scripts sont complets ; les prompts d'agents sont écrits en entier. ✓
3. **Cohérence des interfaces** : `validate(en, fr, accent_free_prefixes)` défini T8, consommé T12/T15 ; format batch défini T12 Step 1 et consommé T13 (prompt) et T12 (apply) ; `divergences.json` défini T15 Step 1, consommé T15 Step 3-4 ; chemins `fr-workspace/…` constants. ✓
