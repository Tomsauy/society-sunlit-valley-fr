"""Lecture du SNBT des quêtes FTB : juste assez pour en tirer tâches et objets."""
from __future__ import annotations

import re

_BLANC = " \t\r\n,"
_NU = re.compile(r"[^\s,{}\[\]:\"']+")
_TYPE = re.compile(r"[BIL];")


class ErreurSNBT(ValueError):
    pass


def lire(texte: str):
    valeur, _ = _valeur(texte, _sauter(texte, 0))
    return valeur


def _sauter(t: str, i: int) -> int:
    while i < len(t) and t[i] in _BLANC:
        i += 1
    return i


def _attendre(t: str, i: int) -> None:
    if i >= len(t):
        raise ErreurSNBT("fin de texte inattendue")


def _valeur(t: str, i: int):
    _attendre(t, i)
    c = t[i]
    if c == "{":
        return _compose(t, i + 1)
    if c == "[":
        return _liste(t, i + 1)
    if c in "\"'":
        return _chaine(t, i)
    m = _NU.match(t, i)
    if not m:
        raise ErreurSNBT(f"caractère inattendu {c!r} en {i}")
    return m.group(0), m.end()


def _chaine(t: str, i: int):
    fin, i, morceaux = t[i], i + 1, []
    while i < len(t) and t[i] != fin:
        if t[i] == "\\" and i + 1 < len(t):
            morceaux.append(t[i + 1])
            i += 2
        else:
            morceaux.append(t[i])
            i += 1
    _attendre(t, i)
    return "".join(morceaux), i + 1


def _compose(t: str, i: int):
    d = {}
    i = _sauter(t, i)
    _attendre(t, i)
    while t[i] != "}":
        if t[i] in "\"'":
            cle, i = _chaine(t, i)
        else:
            m = _NU.match(t, i)
            if not m:
                raise ErreurSNBT(f"clé attendue en {i}")
            cle, i = m.group(0), m.end()
        i = _sauter(t, i)
        _attendre(t, i)
        if t[i] != ":":
            raise ErreurSNBT(f"« : » attendu en {i}")
        d[cle], i = _valeur(t, _sauter(t, i + 1))
        i = _sauter(t, i)
        _attendre(t, i)
    return d, i + 1


def _liste(t: str, i: int):
    liste = []
    i = _sauter(t, i)
    _attendre(t, i)
    if _TYPE.match(t, i):
        i = _sauter(t, i + 2)
    _attendre(t, i)
    while t[i] != "]":
        valeur, i = _valeur(t, i)
        liste.append(valeur)
        i = _sauter(t, i)
        _attendre(t, i)
    return liste, i + 1
