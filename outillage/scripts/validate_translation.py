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
        if not v.strip():
            if isinstance(t, str) and not t.strip():
                continue
            errors.append(("should_be_empty", k))
            continue
        if not isinstance(t, str) or not t.strip():
            errors.append(("empty", k))
            continue
        if tokens(v) != tokens(t):
            errors.append(("tokens", k))
        # la politique accents ne vise que les NOMS (cherchables dans EMI) : clé à 3 segments
        # dont la valeur est un libellé court, pas une phrase de tooltip
        is_name = k.count(".") == 2 and len(v.split()) <= 6 and not v.rstrip().endswith((".", "!", "?"))
        if (accent_free_prefixes and k.startswith(tuple(accent_free_prefixes))
                and is_name and ACCENTS.search(t)):
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
