import { test, expect } from "vitest";
import { parseLang } from "./parse-lang.js";

test("JSON standard", () => {
  const r = parseLang('{"a":"b"}');
  expect(r.data).toEqual({ a: "b" });
  expect(r.tolerated).toBe(false);
});

test("commentaires // tolérés — cas réel de vintagedelight", () => {
  const r = parseLang('{\r\n  "creativetab.vintage_tab": "Vintage Tab",\r\n  //Blocks\r\n  "block.vintagedelight.cheese_mold": "Cheese Mold"\r\n}');
  expect(r.data["block.vintagedelight.cheese_mold"]).toBe("Cheese Mold");
  expect(r.tolerated).toBe(true);
});

test("une URL dans une valeur n'est pas prise pour un commentaire", () => {
  const r = parseLang('{"lien":"https://exemple.fr/page"}');
  expect(r.data.lien).toBe("https://exemple.fr/page");
});

test("JSON réellement invalide renvoie null", () => {
  const r = parseLang('{"a":"b"\n"c":"d"}');
  expect(r.data).toBe(null);
});

test("BOM en tête", () => {
  expect(parseLang('﻿{"a":"b"}').data).toEqual({ a: "b" });
});
