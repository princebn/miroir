export const OCCASIONS = [
  { id: "bureau", label: "Bureau" },
  { id: "cocktail", label: "Cocktail" },
  { id: "vacances", label: "Vacances" },
  { id: "sport", label: "Sport" },
  { id: "soiree", label: "Soirée" },
  { id: "casual", label: "Casual" },
];

export const NOMS = [
  "Camille Diallo",
  "Inès Moreau",
  "Awa Ndiaye",
  "Léa Kowalski",
  "Soraya Benali",
  "Margaux Fontaine",
  "Nadia Okonkwo",
  "Élise Laurent",
];

const ARTICLE_FR = {
  Skirts: "Jupe",
  Trousers: "Pantalon",
  Dresses: "Robe",
  Tops: "Top",
  Shirts: "Chemise",
  Tshirts: "T-shirt",
  Jeans: "Jean",
  Jackets: "Veste",
  Sweaters: "Pull",
  Sweatshirts: "Sweat",
  Blazers: "Blazer",
  Shrug: "Boléro",
  Tunics: "Tunique",
  Shorts: "Short",
  Leggings: "Legging",
  Jeggings: "Jegging",
  Capris: "Pantacourt",
  "Track Pants": "Pantalon de sport",
  Heels: "Escarpins",
  Flats: "Ballerines",
  "Casual Shoes": "Souliers casual",
  "Sports Shoes": "Baskets",
  "Formal Shoes": "Souliers habillés",
  Sandals: "Sandales",
  "Flip Flops": "Tongs",
  Handbags: "Sac à main",
  Clutches: "Pochette",
  Backpacks: "Sac à dos",
  Wallets: "Portefeuille",
  Earrings: "Boucles d'oreilles",
  "Necklace and Chains": "Collier",
  Bracelet: "Bracelet",
  Ring: "Bague",
  Watches: "Montre",
  Sunglasses: "Lunettes de soleil",
  Scarves: "Écharpe",
  Stoles: "Étole",
  Belts: "Ceinture",
  Caps: "Casquette",
  Kurtas: "Kurta",
  Sarees: "Sari",
  Nightdress: "Nuisette",
  Camisoles: "Caraco",
};

const COULEUR_FR = {
  Black: "noir",
  White: "blanc",
  "Off White": "blanc cassé",
  Grey: "gris",
  Charcoal: "anthracite",
  Silver: "argenté",
  Blue: "bleu",
  "Navy Blue": "bleu marine",
  "Turquoise Blue": "turquoise",
  Teal: "bleu canard",
  Green: "vert",
  Olive: "olive",
  Khaki: "kaki",
  Red: "rouge",
  Maroon: "grenat",
  Burgundy: "bourgogne",
  Pink: "rose",
  Magenta: "magenta",
  Peach: "pêche",
  Purple: "violet",
  Lavender: "lavande",
  Yellow: "jaune",
  Mustard: "moutarde",
  Orange: "orange",
  Rust: "rouille",
  Brown: "marron",
  Coffee: "café",
  Beige: "beige",
  Cream: "crème",
  Tan: "fauve",
  Gold: "doré",
  Bronze: "bronze",
  Copper: "cuivré",
  Multi: "multicolore",
};

const USAGE_FR = {
  Formal: "formel",
  Casual: "casual",
  Sports: "sport",
  Party: "soirée",
  Ethnic: "ethnique",
  Travel: "voyage",
  "Smart Casual": "smart casual",
  Home: "maison",
};

const ARCHETYPE_FR = {
  naturel: "naturelle",
  creatif: "créative",
  classique: "classique",
  romantique: "romantique",
  dramatique: "dramatique",
  elegant: "élégante",
  minimaliste: "minimaliste",
  boheme: "bohème",
  sportif: "sportive",
};

function propre(s) {
  if (!s) return "";
  return String(s).replaceAll("_", " ");
}

function majuscule(s) {
  const t = propre(s);
  return t.charAt(0).toUpperCase() + t.slice(1);
}

export function articleLabel(type) {
  return ARTICLE_FR[type] || majuscule(type);
}

export function couleurLabel(c) {
  return COULEUR_FR[c] || propre(c).toLowerCase();
}

export function usageLabel(u) {
  return USAGE_FR[u] || propre(u).toLowerCase();
}

export function clientChips(c) {
  if (!c) return "";
  const saison = majuscule(c.saison_colorimetrique);
  const morpho = propre(c.morphologie);
  const arch = (c.archetypes || [])
    .map((a) => ARCHETYPE_FR[a] || propre(a))
    .join(", ");
  return [saison, morpho, arch, `taille ${c.taille}`]
    .filter(Boolean)
    .join(" · ");
}

export function initiales(nom) {
  return nom
    .split(" ")
    .map((p) => p.charAt(0))
    .slice(0, 2)
    .join("");
}

export function prenom(nom) {
  return nom.split(" ")[0];
}
