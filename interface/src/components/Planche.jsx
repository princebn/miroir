import { couleurHex } from "../labels.js";

export default function Planche({
  prenomCliente,
  occasionLabel,
  dateStr,
  pieces,
  envoyee,
  onEnvoyer,
  onNouvelleSeance,
  onRetour,
  articleLabel,
  couleurLabel,
}) {
  return (
    <div className="planche">
      <button type="button" className="lien-retour" onClick={onRetour}>
        ← Reprendre la séance
      </button>
      <p className="planche-surtitre">Miroir — proposition de séance</p>
      <h1 className="planche-titre">Pour {prenomCliente}</h1>
      <p className="planche-sous">
        {occasionLabel} · {dateStr}
      </p>
      <div className="planche-grille">
        {pieces.map((item) => (
          <figure className="plaque" key={item.item_id}>
            <div className="plaque-visuel">
              <img
                className="card-photo"
                title={item.product_display_name || undefined}
                src={`/api/images/${item.item_id}`}
                alt={`${articleLabel(item.article_type)} ${couleurLabel(item.base_colour)}`}
              />
            </div>
            <figcaption>
              <div className="plaque-nom">{articleLabel(item.article_type)}</div>
              <div className="plaque-couleur">
                <span
                  className="pastille"
                  style={{ background: couleurHex(item.base_colour) }}
                  aria-hidden="true"
                ></span>
                {couleurLabel(item.base_colour)}
              </div>
            </figcaption>
          </figure>
        ))}
      </div>
      <p className="planche-signature">
        Préparée par Aïcha · <span className="serif">Miroir.</span>
      </p>
      <div className="planche-actions">
        {envoyee ? (
          <span className="badge-envoyee">Envoyée à {prenomCliente} ✓</span>
        ) : (
          <button type="button" className="cta" onClick={onEnvoyer}>
            Marquer comme envoyée
          </button>
        )}
        <button type="button" className="btn-texte" onClick={onNouvelleSeance}>
          Nouvelle séance
        </button>
      </div>
    </div>
  );
}
