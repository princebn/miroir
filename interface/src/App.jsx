import { useEffect, useRef, useState } from "react";
import Card from "./components/Card.jsx";
import Planche from "./components/Planche.jsx";
import {
  OCCASIONS,
  NOMS,
  articleLabel,
  couleurHex,
  couleurLabel,
  clientChips,
  initiales,
  prenom,
} from "./labels.js";
import "./seance.css";

const CATALOGUE = "44 419";

const FAMILLES = {
  tout: null,
  hauts: ["Topwear"],
  bas: ["Bottomwear"],
  robes: ["Dress"],
  chaussures: ["Shoes", "Sandal", "Flip Flops"],
  sacs: ["Bags"],
  bijoux: ["Jewellery", "Watches"],
};

const FAMILLE_LABELS = [
  ["tout", "Tout"],
  ["hauts", "Hauts"],
  ["bas", "Bas"],
  ["robes", "Robes"],
  ["chaussures", "Chaussures"],
  ["sacs", "Sacs"],
  ["bijoux", "Bijoux"],
];

export default function App() {
  const [clients, setClients] = useState([]);
  const [clientIdx, setClientIdx] = useState(0);
  const [occasion, setOccasion] = useState("cocktail");
  const [famille, setFamille] = useState("tout");
  const [taille, setTaille] = useState(5);
  const [items, setItems] = useState(null);
  const [selection, setSelection] = useState([]);
  const [vue, setVue] = useState("seance");
  const [envoyee, setEnvoyee] = useState(false);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [version, setVersion] = useState("–");
  const [latence, setLatence] = useState(null);
  const [similaires, setSimilaires] = useState(null);
  const reserveRef = useRef([]);
  const excludeRef = useRef([]);
  const seenRef = useRef(new Set());
  const refillingRef = useRef(false);
  const ajoutsRef = useRef(0);
  const rangRef = useRef(0);

  useEffect(() => {
    fetch("/api/clients")
      .then((r) => r.json())
      .then((data) => setClients(Array.isArray(data) ? data : []))
      .catch(() => setErreur("API injoignable — lance l'API sur le port 8000."));
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => setVersion(String(h.model_version)))
      .catch(() => {});
  }, []);

  const client = clients[clientIdx];
  const nom = NOMS[clientIdx % NOMS.length] || "Cliente";
  const occasionLabel =
    OCCASIONS.find((o) => o.id === occasion)?.label || occasion;

  function resetSeance() {
    setItems(null);
    setSimilaires(null);
    setSelection([]);
    setEnvoyee(false);
    setVue("seance");
    reserveRef.current = [];
    excludeRef.current = [];
    seenRef.current = new Set();
    rangRef.current = 0;
  }

  async function appelRecommend(excludeList, fam = famille) {
    const r = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: client.client_id,
        occasion,
        k: 20,
        exclude_ids: excludeList,
        categories: FAMILLES[fam] || [],
      }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return (await r.json()).items;
  }

  async function composer(fam = famille) {
    if (!client || chargement) return;
    setChargement(true);
    setErreur(null);
    const t0 = performance.now();
    try {
      const recus = await appelRecommend(excludeRef.current, fam);
      setLatence(Math.round(performance.now() - t0));
      rangRef.current = 0;
      const numerotes = recus.map((it) => ({ ...it, rang: ++rangRef.current }));
      numerotes.forEach((it) => seenRef.current.add(it.item_id));
      reserveRef.current = numerotes.slice(taille);
      setItems(numerotes.slice(0, taille));
      setSimilaires(null);
    } catch (e) {
      setErreur("La composition a échoué — vérifie que l'API répond.");
    } finally {
      setChargement(false);
    }
  }

  async function recharger() {
    if (refillingRef.current || !client) return;
    if (reserveRef.current.length >= 3) return;
    refillingRef.current = true;
    try {
      const recus = await appelRecommend([...seenRef.current]);
      const nouveaux = recus
        .filter((it) => !seenRef.current.has(it.item_id))
        .map((it) => ({ ...it, rang: ++rangRef.current }));
      nouveaux.forEach((it) => seenRef.current.add(it.item_id));
      reserveRef.current = [...reserveRef.current, ...nouveaux];
    } catch (e) {
      /* recharge silencieuse */
    } finally {
      refillingRef.current = false;
    }
  }

  function decider(item, action) {
    fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: client.client_id,
        item_id: item.item_id,
        occasion,
        action,
        score: item.score,
        model_version: version,
      }),
    }).catch(() => {});

    excludeRef.current = [...excludeRef.current, item.item_id];
    if (action === "approved") {
      setSelection((prev) => [...prev, item]);
    }
    setItems((prev) => {
      const idx = prev.findIndex((x) => x.item_id === item.item_id);
      if (idx === -1) return prev;
      const next = [...prev];
      next.splice(idx, 1);
      if (reserveRef.current.length > 0) {
        next.push(reserveRef.current[0]);
        reserveRef.current = reserveRef.current.slice(1);
      }
      return next;
    });
    recharger();
  }

  async function voirSimilaires(item) {
    try {
      const r = await fetch(`/api/similar/${item.item_id}?limit=6`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const dejaLa = new Set([
        ...(items || []).map((x) => x.item_id),
        ...selection.map((x) => x.item_id),
      ]);
      const filtres = data.filter((d) => !dejaLa.has(d.item_id)).slice(0, 4);
      ajoutsRef.current = 0;
      setSimilaires({ source: item, total: filtres.length, items: filtres });
    } catch (e) {
      /* silencieux */
    }
  }

  function garderSimilaire(item) {
    if (selection.some((x) => x.item_id === item.item_id)) return;
    fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: client.client_id,
        item_id: item.item_id,
        occasion,
        action: "approved",
        score: null,
        model_version: version,
      }),
    }).catch(() => {});
    excludeRef.current = [...excludeRef.current, item.item_id];
    seenRef.current.add(item.item_id);
    setSelection((prev) => [...prev, item]);
    ajoutsRef.current += 1;
    setSimilaires((prev) => {
      if (!prev) return prev;
      const restants = prev.items.filter((x) => x.item_id !== item.item_id);
      if (restants.length === 0) return null;
      return { ...prev, items: restants };
    });
  }

  function changerFamille(id) {
    if (id === famille) return;
    setFamille(id);
    if (items !== null) {
      composer(id);
    }
  }

  function changerTaille(n) {
    if (n === taille) return;
    setTaille(n);
    setItems((prev) => {
      if (!prev) return prev;
      if (n > prev.length) {
        const ajout = reserveRef.current.slice(0, n - prev.length);
        reserveRef.current = reserveRef.current.slice(ajout.length);
        return [...prev, ...ajout];
      }
      if (n < prev.length) {
        reserveRef.current = [...prev.slice(n), ...reserveRef.current];
        return prev.slice(0, n);
      }
      return prev;
    });
    recharger();
  }

  const [confirmVider, setConfirmVider] = useState(false);

  function viderTout() {
    selection.forEach((item) => {
      fetch(
        `/api/feedback?client_id=${encodeURIComponent(client.client_id)}&item_id=${encodeURIComponent(item.item_id)}`,
        { method: "DELETE" }
      ).catch(() => {});
    });
    excludeRef.current = excludeRef.current.filter(
      (id) => !selection.some((x) => x.item_id === id)
    );
    setSelection([]);
    setConfirmVider(false);
  }

  function retirer(item) {
    fetch(
      `/api/feedback?client_id=${encodeURIComponent(client.client_id)}&item_id=${encodeURIComponent(item.item_id)}`,
      { method: "DELETE" }
    ).catch(() => {});
    setSelection((prev) => prev.filter((x) => x.item_id !== item.item_id));
    excludeRef.current = excludeRef.current.filter((id) => id !== item.item_id);
  }

  function changerCliente(idx) {
    setClientIdx(idx);
    resetSeance();
  }

  function changerOccasion(id) {
    if (id === occasion) return;
    setOccasion(id);
    if (items !== null || selection.length > 0) {
      resetSeance();
    }
  }

  const dateSeance = new Date().toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
  });

  return (
    <div className="page">
      <header className="topbar">
        <div className="marque serif">
          Miroir<span className="point">.</span>
        </div>
        <div className="topbar-droite">
          <span className="seance-date">Séance du {dateSeance}</span>
          <div className="avatar-consultante" title="Aïcha — conseillère en image">
            A
          </div>
        </div>
      </header>

      <h1 className="sr-only">Miroir — séance de recommandation</h1>

      {vue === "planche" ? (
        <main className="contenu">
          <Planche
            prenomCliente={prenom(nom)}
            occasionLabel={occasionLabel}
            dateStr={dateSeance}
            pieces={selection}
            envoyee={envoyee}
            onEnvoyer={() => setEnvoyee(true)}
            onNouvelleSeance={resetSeance}
            onRetour={() => setVue("seance")}
            articleLabel={articleLabel}
            couleurLabel={couleurLabel}
          />
        </main>
      ) : (
        <>
          <section className="barre-seance">
            <div className="cliente">
              <div className="avatar-cliente serif">{initiales(nom)}</div>
              <div className="cliente-infos">
                <label className="sr-only" htmlFor="select-cliente">
                  Choisir une cliente
                </label>
                <select
                  id="select-cliente"
                  className="cliente-select serif"
                  value={clientIdx}
                  onChange={(e) => changerCliente(Number(e.target.value))}
                >
                  {clients.map((c, i) => (
                    <option key={c.client_id} value={i}>
                      {NOMS[i % NOMS.length]}
                    </option>
                  ))}
                </select>
                <p className="cliente-chips">{clientChips(client)}</p>
              </div>
            </div>
            <button
              type="button"
              className="cta"
              onClick={() => composer()}
              disabled={!client || chargement}
            >
              {chargement ? "Composition…" : "Composer la sélection"}
            </button>
          </section>

          <nav className="occasions" aria-label="Occasion">
            {OCCASIONS.map((o) => (
              <button
                key={o.id}
                type="button"
                className={"pill" + (occasion === o.id ? " pill-active" : "")}
                onClick={() => changerOccasion(o.id)}
              >
                {o.label}
              </button>
            ))}
          </nav>

          <nav className="filtres" aria-label="Type de pièce">
            <span className="filtres-label">Type</span>
            {FAMILLE_LABELS.map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={"pill" + (famille === id ? " pill-active" : "")}
                onClick={() => changerFamille(id)}
              >
                {label}
              </button>
            ))}
          </nav>

          <main className="contenu">
            {erreur && <p className="message-erreur">{erreur}</p>}

            {!items && !erreur && (
              <div className="accueil">
                <p className="accueil-titre serif">
                  Choisissez une cliente et une occasion —<br />
                  Miroir compose une sélection parmi {CATALOGUE} pièces,
                  ordonnée pour elle.
                </p>
                <p className="accueil-sous">
                  Gardez les pièces justes, écartez les autres : la proposition
                  se construit, puis part à la cliente.
                </p>
              </div>
            )}

            {items && (
              <div className="layout-seance">
                <div className={"colonne" + (similaires ? " colonne-estompee" : "")}>
                  <div className="ligne-propositions">
                    <p className="selection-titre serif">
                      Propositions pour {prenom(nom)} —{" "}
                      {occasionLabel.toLowerCase()}
                    </p>
                    <span className="taille-controle">
                      Afficher
                      {[5, 10, 15].map((n) => (
                        <button
                          key={n}
                          type="button"
                          className={
                            "taille-btn" + (taille === n ? " taille-active" : "")
                          }
                          onClick={() => changerTaille(n)}
                        >
                          {n}
                        </button>
                      ))}
                    </span>
                  </div>
                  {items.length === 0 ? (
                    <p className="note-vide">
                      Plus de pièces à proposer dans ce contexte.
                    </p>
                  ) : (
                    <div className="grille">
                      {items.map((item, i) => (
                        <Card
                          key={item.item_id}
                          item={item}
                          index={i}
                          decision={undefined}
                          onDecide={decider}
                          onVoir={voirSimilaires}
                        />
                      ))}
                    </div>
                  )}

                  {similaires && (
                    <section className="similaires similaires-scene">
                      <div className="similaires-tete">
                        <div>
                          <p className="similaires-surtitre">
                            VOISINAGE VISUEL — EMBEDDINGS CLIP
                          </p>
                          <p className="similaires-titre serif">
                            Les {similaires.total} pièces les plus proches de
                            cette {articleLabel(similaires.source.article_type).toLowerCase()}
                          </p>
                        </div>
                        <div className="similaires-actions">
                          {ajoutsRef.current > 0 && (
                            <span className="similaires-compteur">
                              {ajoutsRef.current}/{similaires.total} ajoutée
                              {ajoutsRef.current > 1 ? "s" : ""}
                            </span>
                          )}
                          <button
                            type="button"
                            className="btn-texte"
                            onClick={() => setSimilaires(null)}
                          >
                            Fermer
                          </button>
                        </div>
                      </div>
                      <div className="similaires-liste">
                        {similaires.items.map((item) => (
                          <div className="simil-item" key={item.item_id}>
                            <div className="simil-visuel">
                              <img
                                className="simil-photo"
                                src={`/api/images/${item.item_id}`}
                                alt={articleLabel(item.article_type)}
                                title={item.product_display_name || undefined}
                              />
                            </div>
                            <div className="simil-nom serif">
                              {articleLabel(item.article_type)}
                            </div>
                            <div className="simil-sous">
                              <span
                                className="pastille"
                                style={{
                                  background: couleurHex(item.base_colour),
                                }}
                                aria-hidden="true"
                              ></span>
                              {couleurLabel(item.base_colour)}
                            </div>
                            <button
                              type="button"
                              className="simil-garder"
                              onClick={() => garderSimilaire(item)}
                            >
                              Garder
                            </button>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </div>
                <aside className="rail">
                  <div className="rail-tete">
                    <p className="rail-titre serif">
                      La sélection — {selection.length}{" "}
                      {selection.length > 1 ? "pièces" : "pièce"}
                    </p>
                    {selection.length > 0 &&
                      (confirmVider ? (
                        <span className="rail-confirm">
                          Vider ?{" "}
                          <button
                            type="button"
                            className="btn-texte"
                            onClick={viderTout}
                          >
                            Oui
                          </button>
                          <span aria-hidden="true"> · </span>
                          <button
                            type="button"
                            className="btn-texte"
                            onClick={() => setConfirmVider(false)}
                          >
                            Annuler
                          </button>
                        </span>
                      ) : (
                        <button
                          type="button"
                          className="btn-texte rail-vider"
                          onClick={() => setConfirmVider(true)}
                        >
                          tout vider
                        </button>
                      ))}
                  </div>
                  {selection.length === 0 ? (
                    <p className="rail-vide">
                      Gardez des pièces pour composer la proposition de{" "}
                      {prenom(nom)}.
                    </p>
                  ) : (
                    <div className="rail-liste">
                      {selection.map((item) => (
                        <div className="rail-item" key={item.item_id}>
                          <img
                            className="rail-thumb"
                            src={`/api/images/${item.item_id}`}
                            alt=""
                          />
                          <div>
                            <div className="rail-nom">
                              {articleLabel(item.article_type)}
                            </div>
                            <div className="rail-couleur">
                              {couleurLabel(item.base_colour)}
                            </div>
                          </div>
                          <button
                            type="button"
                            className="rail-retirer"
                            aria-label="Retirer de la sélection"
                            onClick={() => retirer(item)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <button
                    type="button"
                    className="cta cta-bloc"
                    disabled={selection.length === 0}
                    onClick={() => setVue("planche")}
                  >
                    Terminer la séance
                  </button>
                </aside>
              </div>
            )}
          </main>
        </>
      )}

      <footer className="trace">
        <span>miroir_reranker @production · v{version}</span>
        <span>
          {latence !== null ? `${latence} ms · ` : ""}top {taille} sur{" "}
          {CATALOGUE}{" "}
          articles
        </span>
      </footer>
    </div>
  );
}
