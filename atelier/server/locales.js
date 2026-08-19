const RE = /^[a-z]{2}_[a-z]{2}$/;

const LIBELLES = {
  fr_fr: "Français", en_us: "Anglais", es_es: "Espagnol", es_mx: "Espagnol (Mexique)",
  pt_br: "Portugais (Brésil)", de_de: "Allemand", it_it: "Italien", nl_nl: "Néerlandais",
  ru_ru: "Russe", uk_ua: "Ukrainien", pl_pl: "Polonais", cs_cz: "Tchèque",
  ja_jp: "Japonais", ko_kr: "Coréen", th_th: "Thaï", tr_tr: "Turc",
  zh_cn: "Chinois simplifié", zh_tw: "Chinois (Taïwan)", zh_hk: "Chinois (Hong Kong)",
};

export function isLocale(nom) {
  return RE.test(nom);
}

// Une locale absente de la table s'affiche par son code plutôt que de casser l'interface.
export function localeLabel(code) {
  return LIBELLES[code] ?? code;
}
