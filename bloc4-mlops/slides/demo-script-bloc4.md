# Miroir — Bloc 4 · Script de démonstration Loom (5 min)

**Objectif** : montrer une solution d'IA industrialisée de bout en bout — le produit (séance de recommandation) ET l'usine (CI/CD, réentraînement, monitoring). Durée cible : 5 minutes.

**Avant de filmer** — tout doit tourner :
- API : `cd bloc4-mlops && export MLFLOW_TRACKING_URI="sqlite:///$PWD/mlflow.db" && nohup python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 < /dev/null > /tmp/miroir-api.log 2>&1 &`
- Interface : `cd interface && npm run dev` → http://127.0.0.1:5173
- Grafana (Docker) : http://localhost:3000 (admin/admin), dashboard Miroir ouvert
- MLflow : `mlflow ui --backend-store-uri sqlite:///mlflow.db` → http://localhost:5000
- Swagger : http://localhost:8000/docs
- Trafic de démo prêt : `python scripts/demo_traffic.py` (à lancer pour animer Grafana)

---

## Acte 1 — Le produit : une séance de conseil (0:00 → 1:00)

**Écran : interface, http://127.0.0.1:5173**

> « Voici Miroir, côté conseillère. Aïcha prépare une séance pour sa cliente Camille. »

- Sélectionner **Camille** + occasion **Cocktail**.
- Cliquer **Composer la sélection**.

> « En 250 millisecondes, le moteur a parcouru 44 419 articles et en a classé cinq, pour Camille — hiver lumineux, silhouette sablier. La conseillère ne cherche plus, elle arbitre. »

- **Garder** 3 pièces (le rail se remplit à droite), **Écarter** une (remplacée par la suivante).
- Cliquer une photo → le tiroir **VOISINAGE VISUEL — EMBEDDINGS CLIP** prend la scène.

> « Ici, le ML devient visible : ces pièces sont les plus proches dans l'espace d'embeddings CLIP. La similarité visuelle, en direct. »

- Garder une voisine, fermer le tiroir.
- **Terminer la séance** → la planche « Pour Camille ».

> « La séance produit un livrable : une proposition signée, prête à être envoyée. »

---

## Acte 2 — La personnalisation, prouvée (1:00 → 1:45)

**Écran : interface**

> « Est-ce vraiment personnalisé ? Changeons de cliente, même occasion. »

- Repasser en séance, sélectionner **Inès** (automne chaud, romantique), occasion **Cocktail** identique.
- **Composer**.

> « Même occasion, cliente différente — et la sélection change : autres couleurs, autres coupes. Le profil pilote réellement le classement. Ce n'est pas une galerie, c'est une décision. »

---

## Acte 3 — L'usine : du code à la production (1:45 → 3:15)

**Écran : Swagger, http://localhost:8000/docs**

> « Derrière l'écran, une API de production. »

- Montrer `/recommend`, `/feedback`, `/similar`, `/health`.
- Déplier `/health` → exécuter → montrer la version du modèle servi.

**Écran : GitHub Actions (onglet Actions du repo)**

> « Chaque push passe par l'intégration continue : lint, format, 72 tests, build de l'image. La qualité bloque le déploiement. »

- Montrer un run vert, dérouler les étapes.

**Écran : MLflow, http://localhost:5000**

> « Les modèles sont versionnés. L'API ne pointe pas sur un fichier mais sur un alias : @production. »

- Montrer le registry `miroir_reranker`, les versions v1 / v2, l'alias **@production**.

> « Promouvoir un modèle, c'est déplacer cet alias. Rollback instantané, sans redéploiement. »

**Écran : DAG Airflow (capture ou UI)**

> « Et ce modèle se réentraîne tout seul, chaque semaine. »

- Montrer le DAG : régénération → garde-fou qualité → entraînement → évaluation → promotion conditionnelle.

> « Règle d'or : le challenger n'est promu que s'il ne dégrade pas la production. Sinon, rollback automatique. »

---

## Acte 4 — Le monitoring vivant (3:15 → 4:30)

**Écran : Grafana, http://localhost:3000**

> « En production, on pilote par la mesure. »

- Lancer dans un terminal : `python scripts/demo_traffic.py`
- Revenir sur Grafana, montrer les panneaux qui s'animent : latence p50/p95, débit, requêtes cumulées, feedback par action.

> « Latence p95 sous la barre des 300 millisecondes. Le débit monte, les décisions des conseillères remontent en base — ce sont elles qui nourriront le prochain réentraînement. »

**Écran : rapport Evidently (HTML drift)**

> « Et on surveille la dérive : si les données d'entrée changent, un double critère le détecte — dérive globale ou feature sentinelle. »

---

## Clôture (4:30 → 5:00)

**Écran : interface, sur la planche de Camille**

> « De la donnée brute au livrable signé : un modèle entraîné, servi, intégré en continu, réentraîné automatiquement, surveillé. Une solution d'IA industrialisée — où la machine fait la recherche, et l'humaine garde la décision. »

> « Tout est sur github.com/princebn/miroir. Merci. »

---

### Aide-mémoire ordre des écrans
Interface (séance Camille) → Interface (bascule Inès) → Swagger → GitHub Actions → MLflow → Airflow → Grafana (+ demo_traffic) → Evidently → Interface (planche).
