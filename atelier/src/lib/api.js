const j = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} sur ${url}`);
  return r.json();
};

export const sante = () => j("/api/sante");
export const locales = () => j("/api/locales");
export const quetes = () => j("/api/quetes");
export const livres = () => j("/api/livres");
export const entree = (id) => j(`/api/entree/${encodeURIComponent(id)}`);
export const detail = (id) => j(`/api/detail/${encodeURIComponent(id)}`);
export const revoir = () => j("/api/revoir");
export const recherche = (params) =>
  j(`/api/recherche?${new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== null))}`);
