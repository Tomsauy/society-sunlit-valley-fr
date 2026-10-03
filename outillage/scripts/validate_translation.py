#!/usr/bin/env python3
"""Validation mécanique d'une traduction : clés, placeholders, non-traduit.

Le contrôle d'accents a disparu : la politique s'est inversée, tout le français est
accentué, noms d'objets compris. La recherche en jeu tient désormais du mod Accent
Fold, pas d'un alias — ce script ne le vérifie pas.
"""
import json, re, sys

# Codes qui doivent se retrouver à l'identique : printf (%s, %1$s, %.1f, %%), couleurs Minecraft (§a)
# et FTB (&6), macros Patchouli (liens compris), balises <lt…>, nom du joueur (@i), gabarits de
# construction (${…}), sauts de ligne réels ou écrits \n, jetons FTB ({0}, {@pagebreak}, {image:…}).
# Faux positif assumé : « &x » et « @i » collés à un mot (« cause&effect ») comptent aussi comme codes,
# car un code FTB suit souvent une lettre (« récompenses&r ») ; un tel constat se couvre par une exception motivée.
# Partagé avec le vérificateur (coherence/controles/codes.py) : ne pas le recopier ailleurs.
TOKEN = re.compile(
    r"%(?:\d+\$)?(?:\.\d+)?[sdfeu]|%%|§.|&[0-9a-fk-or]|\$\([^)]*\)|</?lt\w+[^>]*>|@i\b"
    r"|\$\{[^}]*\}|\\n|\n|\{\d+\}|\{@\w+\}|\{image:[^}]*\}"
)
WORD = re.compile(r"[A-Za-z]{4,}")

def tokens(s: str) -> list:
    return sorted(TOKEN.findall(s))

def validate(en: dict, fr: dict) -> list:
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
        if t == v and len(WORD.findall(v)) >= 1 and len(v) > 3:
            errors.append(("untranslated", k))
    errors.extend(("extra", k) for k in fr if k not in en)
    return errors

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    en = json.load(open(args[0]))
    fr = json.load(open(args[1]))
    errs = validate(en, fr)
    for code, key in errs:
        print(f"{code}\t{key}")
    print(f"{len(errs)} erreur(s)", file=sys.stderr)
    sys.exit(1 if errs else 0)
