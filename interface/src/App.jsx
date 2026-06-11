import { useEffect, useState } from "react";
import Card from "./components/Card.jsx";
import {
  OCCASIONS,
  NOMS,
  clientChips,
  initiales,
  prenom,
} from "./labels.js";

const CATALOGUE = "44 419";

export default function App() {
  const [clients, setClients] = useState([]);
  const [clientIdx, setClientIdx] = useState(0);
  const [occasion, setOccasion] = useState("cocktail");
  const [items, setItems] = useState(null);
  const [decisions, setDecisions] = useState({});
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [version, setVersion] = useState("–");
  const [latence, setLatence] = useState(null);
  const [composeePour, setComposeePour] = useState(null);

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

  async function composer() {
    if (!client || chargement) return;
    setChargement(true);
    setErreur(null);
    const t0 = performance.now();
    try {
      const r = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: client.client_id,
          occasion,
          k: 5,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setLatence(Math.round(performance.now() - t0));
      setItems(data.items);
      setDecisions({});
      setComposeePour({
        prenom: prenom(nom),
        occasion: OCCASIONS.find((o) => o.id === occasion)?.label || occasion,
      });
    } catch (e) {
      setErreur("La composition a échoué — vérifie que l'API répond.");
    } finally {
      setChargement(false);
    }
  }

  function decider(item, action) {
    setDecisions((d) => ({ ...d, [item.item_id]: action }));
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
              onChange={(e) => setClientIdx(Number(e.target.value))}
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
            onClick={() => setOccasion(o.id)}
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
              Miroir compose une sélection parmi {CATALOGUE} pièces, ordonnée
              pour elle.
            </p>
            <p className="accueil-sous">
              Chaque pièce gardée ou écartée affine les prochaines sélections.
            </p>
          </div>
        )}

        {items && (
          <>
            <p className="selection-titre serif">
              La sélection — cinq pièces pour {composeePour?.prenom},{" "}
              occasion {composeePour?.occasion.toLowerCase()}
            </p>
            <div className="grille">
              {items.map((item, i) => (
                <Card
                  key={item.item_id}
                  item={item}
                  index={i}
                  decision={decisions[item.item_id]}
                  onDecide={decider}
                />
              ))}
            </div>
          </>
        )}
      </main>

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
