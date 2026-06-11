import { useState } from "react";
import { articleLabel, couleurLabel, usageLabel } from "../labels.js";

const PLACEHOLDERS = ["#c7b9a6", "#8a8f84", "#3e3a45", "#a6553f", "#b5a8b8"];

export default function Card({ item, index, decision, onDecide }) {
  const [imgErreur, setImgErreur] = useState(false);
  const ecartee = decision === "rejected";
  const gardee = decision === "approved";

  return (
    <article
      className={"card" + (ecartee ? " card-ecartee" : "")}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="card-visuel">
        {imgErreur ? (
          <div
            className="card-photo card-placeholder"
            style={{ background: PLACEHOLDERS[index % PLACEHOLDERS.length] }}
          >
            {articleLabel(item.article_type)}
          </div>
        ) : (
          <img
            className="card-photo"
            src={`/api/images/${item.item_id}`}
            alt={`${articleLabel(item.article_type)} ${couleurLabel(item.base_colour)}`}
            loading="lazy"
            onError={() => setImgErreur(true)}
          />
        )}
        {gardee && <span className="badge badge-gardee">Gardée</span>}
        {ecartee && <span className="badge badge-ecartee">Écartée</span>}
      </div>
      <h3 className="card-titre serif">{articleLabel(item.article_type)}</h3>
      <p className="card-sous">
        {couleurLabel(item.base_colour)} · {usageLabel(item.usage)}
      </p>
      <div className="card-pied">
        <span
          className="card-rang"
          title={`score du modèle : ${Number(item.score).toFixed(4)}`}
        >
          № {index + 1}
        </span>
        <span className="card-actions">
          <button
            type="button"
            className={"rond" + (gardee ? " rond-plein" : "")}
            aria-label="Garder cette pièce"
            disabled={!!decision}
            onClick={() => onDecide(item, "approved")}
          >
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12.5l4.5 4.5L19 7.5" />
            </svg>
          </button>
          <button
            type="button"
            className={"rond rond-muted" + (ecartee ? " rond-sombre" : "")}
            aria-label="Écarter cette pièce"
            disabled={!!decision}
            onClick={() => onDecide(item, "rejected")}
          >
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </span>
      </div>
    </article>
  );
}
