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
check("cas nominal", validate(en, ok) == [])
check("clé manquante", ("missing", "b") in validate(en, {"a": "Salut %s", "item.mod.x": "Ble"}))
check("clé en trop", ("extra", "z") in validate(en, {**ok, "z": "?"}))
check("token perdu", ("tokens", "a") in validate(en, {**ok, "a": "Salut"}))
check("valeur vide", ("empty", "b") in validate(en, {**ok, "b": "  "}))
check("non traduit", ("untranslated", "b") in validate({"b": "Sprinkler"}, {"b": "Sprinkler"}))
check("identique légitime court", validate({"b": "OK"}, {"b": "OK"}) == [])
check("EN vide → FR vide ok", validate({"b": ""}, {"b": ""}) == [])
check("EN vide → FR rempli refusé", ("should_be_empty", "b") in validate({"b": ""}, {"b": "Texte"}))
# La politique sans accents est levée depuis le 29/08/2026 : un nom accentué est correct.
check("accents autorisés sur un nom", validate({"item.mod.x": "Wheat"}, {"item.mod.x": "Blé"}) == [])
check("accents autorisés sur une phrase",
      validate({"item.mod.downgrade": "Caps slots at 64 items"},
               {"item.mod.downgrade": "Limite les emplacements à un maximum de 64 objets"}) == [])
print("Tous les tests passent.")
