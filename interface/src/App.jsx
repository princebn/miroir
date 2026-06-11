import { useEffect, useRef, useState } from "react";
import Card from "./components/Card.jsx";
import Planche from "./components/Planche.jsx";
import {
  OCCASIONS,
  NOMS,
  articleLabel,
  couleurLabel,
  clientChips,
  initiales,
  prenom,
} from "./labels.js";
import "./seance.css";

const CATALOGUE = "44 419";

export default function App() {
  const [clients, setClients] = useState([]);
  const [clientIdx, setClientIdx] = useState(0);
  const [occasion, setOccasion] = useState("cocktail");
  const [items, setItems] = useState(null);
  const [selection, setSelection] = useState([]);
  const [vue, setVue] = useState("seance");
  const [envoyee, setEnvoyee] = useState(false);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [version, setVersion] = useState("–");
  const [latence, setLatence] = useState(null);
  const reserveRef = useRef([]);
  const excludeRef = useRef([]);
  const seenRef = useRef(new Set());
  const refillingRef = useRef(false);

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
    setSelection([]);
    setEnvoyee(false);
    setVue("seance");
    reserveRef.current = [];
    excludeRef.current = [];
    seenRef.current = new Set();
  }

  async function appelRecommend(excludeList) {
    const r = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: client.client_id,
        occasion,
        k: 20,
        exclude_ids: excludeList,
      }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return (await r.json()).items;
  }

  async function composer() {
    if (!client || chargement) return;
    setChargement(true);
    setErreur(null);
    const t0 = performance.now();
    try {
      const recus = await appelRecommend(excludeRef.current);
      setLatence(Math.round(performance.now() - t0));
      recus.forEach((it) => seenRef.current.add(it.item_id));
      reserveRef.current = recus.slice(5);
      setItems(recus.slice(0, 5));
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
      const nouveaux = recus.filter((it) => !seenRef.current.has(it.item_id));
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
      if (reserveRef.current.length > 0) {
        next[idx] = reserveRef.current[0];
        reserveRef.current = reserveRef.current.slice(1);
      } else {
        next.splice(idx, 1);
      }
      return next;
    });
    recharger();
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
              onClick={composer}
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
                <div className="colonne">
                  <p className="selection-titre serif">
                    Propositions pour {prenom(nom)} — {occasionLabel.toLowerCase()}
                  </p>
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
                        />
                      ))}
                    </div>
                  )}
                </div>
                <aside className="rail">
                  <p className="rail-titre serif">
                    La sélection — {selection.length}{" "}
                    {selection.length > 1 ? "pièces" : "pièce"}
                  </p>
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
          {latence !== null ? `${latence} ms · ` : ""}top 5 sur {CATALOGUE}{" "}
          articles
        </span>
      </footer>
    </div>
  );
}
