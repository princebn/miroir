# Script video demo — Bloc 2 (Loom, 3-5 min)

Objectif : prouver que l'infrastructure tourne reellement. Enregistrer en une prise,
ecran partage + voix. Avoir ouverts a l'avance : Terminal, navigateur (Grafana + MinIO).

## 0:00 - 0:30 — Intro
- "Miroir, plateforme B2B de conseil en image. Voici l'infrastructure de donnees du Bloc 2."
- Montrer l'arborescence du repo (VS Code ou `tree`), pointer : db, docker, scripts, terraform, k8s, monitoring, docs.

## 0:30 - 1:15 — Stack data qui tourne
- Terminal : `cd ~/Documents/miroir/bloc2-architecture/docker && docker compose ps`
- "PostgreSQL avec pgvector, MinIO et Redis, tous healthy."
- `PGPASSWORD=miroir_local_pwd psql -h localhost -U miroir -d miroir -P pager=off -c "SELECT table_schema, count(*) FROM information_schema.tables WHERE table_schema IN ('core','catalog','signals','reco','events') GROUP BY 1 ORDER BY 1;"`
- "14 tables sur 5 schemas metier."

## 1:15 - 2:00 — Donnees a l'echelle
- `psql ... -c "SELECT count(*) FROM signals.hm_transactions;"`
- "31,8 millions de transactions chargees par COPY en streaming."
- `psql ... -c "SELECT count(*) FROM catalog.products;"` -> 44 424 produits
- Navigateur : MinIO console (localhost:9001), montrer le bucket miroir-products avec les 44k images.

## 2:00 - 2:45 — Deploiement Kubernetes
- `kubectl -n miroir get pods` -> 3 pods Running
- `kubectl -n miroir get pvc` -> volumes Bound
- "Le meme stack, deploye via un Helm chart sur Kubernetes. C'est notre cible orchestree."

## 2:45 - 3:30 — Observabilite
- Navigateur : Grafana (localhost:3000), datasource Prometheus.
- Prometheus (localhost:9090) -> Status > Targets : postgres, redis, prometheus = UP.
- "Metriques scrappees en continu, base de l'observabilite."

## 3:30 - 4:15 — IaC
- Terminal : `cd ../terraform/gcp && terraform validate` -> Success
- "Les memes ressources en version cloud GCP : VPC, GKE, Cloud SQL, GCS. Validees, pretes a deployer."
- `cd ../local && terraform output` -> les 4 buckets geres en IaC.

## 4:15 - 4:45 — Cloture
- "Infrastructure complete, reproductible, documentee, versionnee sur GitHub."
- Montrer rapidement le repo GitHub (README + diagrammes Mermaid rendus).

## Checklist avant enregistrement
- [ ] docker compose up -d (stack data)
- [ ] helm install miroir-stack (si pods eteints)
- [ ] docker compose -f monitoring/... up -d (Prometheus/Grafana)
- [ ] Grafana et MinIO ouverts dans le navigateur
- [ ] Fenetres rangees, police terminal lisible
