# Bloc 3 — Script de démo (Loom, ~4 min)

## Objectif
Démontrer un pipeline temps réel opérationnel sur 31,8 M de transactions H&M réelles : ingestion Kafka → consumer Postgres → transformations dbt → qualité GE → orchestration Airflow → console Streamlit interactive avec heatmap d'affinité.

---

## Pré-flight (avant Rec)

**Fermer** Slack, Mail, notifs, badges.

**3 terminaux** (split iTerm/Terminal) :

```bash
# Onglet 1 — pipeline & dbt
cd ~/Documents/miroir && source .venv/bin/activate
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "kafka|postgres|redis"

# Onglet 2 — airflow (déjà actif normalement)
# Sinon :
# cd ~/Documents/miroir && source .venv-airflow/bin/activate
# airflow webserver -p 8080 &  ; airflow scheduler &

# Onglet 3 — streamlit
cd ~/Documents/miroir/bloc3-pipelines/streamlit
~/Documents/miroir/.venv/bin/python -m streamlit run app.py
```

**Onglets navigateur**, dans cet ordre :

1. `https://github.com/princebn/miroir/tree/main/bloc3-pipelines` (vue repo)
2. `http://localhost:8080` (Airflow UI, DAG `miroir_pipeline`, vue Graph)
3. `http://localhost:8501` (Streamlit, segment = "Tous les segments")

**Vérifier** que `signals.stream_transactions` a ≥ 4 500 lignes — sinon faire tourner le producer avant.

---

## Séquence (≈ 4 min)

### 1. Ouverture — 15 s
**Écran** : slide 1 du deck.
**Voix** :
> Bloc 3 — pipelines de données temps réel. Je vais démontrer un pipeline complet qui rejoue 31,8 millions de transactions H&M réelles, les transforme, les valide, et expose des signaux exploitables pour la recommandation.

### 2. Vue repo — 30 s
**Action** : onglet GitHub, arbo `bloc3-pipelines/` (docker, dags, dbt, python, streamlit, tests).
**Voix** :
> Le code est versionné sur GitHub. Six dossiers : docker pour Kafka, dags pour Airflow, dbt pour les transformations, python pour le producer et le consumer, streamlit pour la console, tests pour Great Expectations.

### 3. Kafka & ingestion — 30 s
**Action** : terminal onglet 1 :
```bash
docker ps --format "{{.Names}}" | grep kafka
docker exec miroir-kafka kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --topic miroir.transactions
```
**Voix** :
> Kafka 3.8 en mode KRaft — sans Zookeeper. Topic `miroir.transactions`, trois partitions, clé customer_id pour la cohérence par client. Le producer Python lit `transactions_train.csv` ligne par ligne, avec un stride pour étaler l'échantillon sur deux ans.

### 4. Airflow DAG — 60 s
**Action** : Airflow UI, vue Graph de `miroir_pipeline`. Cliquer sur la dernière run. Les 4 tâches vertes : `produce → consume → dbt_build → quality`. Cliquer `quality` → Logs.
**Voix** :
> Le pipeline est orchestré par Airflow. Quatre tâches en série dans des venvs isolés. La tâche `dbt_build` tourne avec `--exclude tag:reference` pour rester rapide — les marts lourds sont construits une fois, séparément. La tâche `quality` lance Great Expectations sur le batch et propage le code de sortie. Si la qualité échoue, le DAG échoue. Pas de chargement silencieux de données invalides.

### 5. dbt — 30 s
**Action** : terminal onglet 1 :
```bash
cd bloc3-pipelines/dbt/miroir
dbt ls --models tag:stream
dbt ls --models tag:reference
```
**Voix** :
> Deux familles de modèles. Tag `stream` : staging et mart canal-jour, build à chaque run. Tag `reference` : six marts au grain segment construits une fois sur 31,8 M — c'est ce qui alimente la console.

### 6. Console Streamlit — 90 s ★
**Action** : Streamlit, segment = "Tous les segments". Pointer le bandeau chips en haut.
**Voix** :
> La console fait le pont entre la plomberie et le business. En haut : les KPI du flux temps réel — 4 500 transactions streamées, dernière validation Airflow. La caption rappelle que dbt et GE valident le batch avant insertion.

**Action** : scroller à Section 2, montrer les 4 panneaux en mode "Tous". Changer le filtre en **Ladies Accessories**.
**Voix** :
> Section 2 — l'intelligence de la demande, sur deux ans complets. Je filtre sur Ladies Accessories. Les quatre panneaux se recalculent : on voit la concentration catégorielle, la signature d'âge, et la palette dominante du segment.

**Action** : scroller à la heatmap. Pointer la cellule Ladies Accessories × Accessories (14,6×).
**Voix** :
> Et le panneau-clé : la heatmap d'affinité. Chaque cellule = part de la catégorie dans le segment, divisée par sa part globale. Indice supérieur à 1 = sur-consommation. Ladies Accessories sur-indexe à 14,6× sur les accessoires et 13× sur la lingerie. Menswear pointe à 2,7× sur la lingerie homme. Sport à 2,0× sur le swimwear. Chaque cellule chargée est une piste de reco prioritaire, par segment. C'est exactement ce que consommera le moteur du Bloc 4.

### 7. Clôture — 15 s
**Action** : terminal onglet 1 :
```bash
echo "github.com/princebn/miroir"
```
**Voix** :
> Code, modèles dbt, slides et console : tout est sur github.com/princebn/miroir, dossier bloc3-pipelines. Pipeline temps réel industrialisé, signaux exploitables. Merci.

---

## Total
≈ 4 min 10 s. Si trop long → couper l'étape 5 (dbt) à 15 s.

## Règles de tournage
- **Curseur** : ralentir, ne pas balayer.
- **Zoom navigateur** : 110–125 %.
- **Bascules** nettes, pas de Cmd-Tab erratique.
- **Audio** : casque ou micro USB, pièce calme.
- **Refaire** si une étape rate — un seul take propre > 5 collés.
