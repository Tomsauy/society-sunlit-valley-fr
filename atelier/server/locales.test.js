import { test, expect } from "vitest";
import { isLocale, localeLabel } from "./locales.js";

test("reconnaît les locales Minecraft", () => {
  expect(isLocale("fr_fr")).toBe(true);
  expect(isLocale("zh_cn")).toBe(true);
  expect(isLocale("es_mx")).toBe(true);
});

test("rejette ce qui n'est pas une locale", () => {
  expect(isLocale("en_us_template")).toBe(false);
  expect(isLocale("building_shop_generated")).toBe(false);
  expect(isLocale("FR_FR")).toBe(false);
});

test("libellé connu et libellé inconnu", () => {
  expect(localeLabel("fr_fr")).toBe("Français");
  expect(localeLabel("zh_hk")).toBe("Chinois (Hong Kong)");
  expect(localeLabel("xx_yy")).toBe("xx_yy");
});
