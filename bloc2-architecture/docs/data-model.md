# Modèle de données Miroir — Bloc 2

5 schemas logiques : `core` (metier), `catalog` (produits + vecteurs),
`signals` (H&M brut), `reco` (recommandations), `events` (interactions).

```mermaid
erDiagram
  advisors ||--o{ clients : gere
  clients ||--|| client_profiles : possede
  clients ||--o{ client_budgets : a
  clients ||--o{ client_occasions : a
  advisors ||--o{ recommendations : cree
  clients ||--o{ recommendations : recoit
  recommendations ||--o{ recommendation_items : contient
  products ||--o{ recommendation_items : reference
  products ||--|| product_embeddings : a
  products ||--o{ product_colors : a
  hm_customers ||--o{ hm_transactions : effectue
  hm_articles ||--o{ hm_transactions : concerne

  advisors {
    uuid advisor_id PK
    text full_name
    text country
    smallint seniority_years
  }
  clients {
    uuid client_id PK
    uuid advisor_id FK
    enum region
    text segment
  }
  client_profiles {
    uuid profile_id PK
    uuid client_id FK
    enum morphotype
    enum color_season
    enum skin_undertone
    array style_archetypes
  }
  client_budgets {
    uuid client_id FK
    text category
    numeric budget_min
    numeric budget_max
  }
  client_occasions {
    uuid client_id FK
    text occasion
    numeric probability
  }
  products {
    int product_id PK
    text article_type
    text base_colour
    text usage
    text image_path
  }
  product_embeddings {
    int product_id PK
    vector embedding
    text model
  }
  product_colors {
    int product_id FK
    smallint rank
    char hex
    numeric ratio
  }
  recommendations {
    uuid reco_id PK
    uuid client_id FK
    uuid advisor_id FK
    enum status
  }
  recommendation_items {
    uuid reco_id FK
    int product_id FK
    smallint rank
    numeric score
    enum source
    enum advisor_action
  }
  hm_customers {
    text customer_id PK
    smallint age
    text club_member_status
  }
  hm_articles {
    text article_id PK
    text prod_name
    text product_type_name
  }
  hm_transactions {
    date t_dat
    text customer_id FK
    text article_id FK
    numeric price
  }
```

## Choix de modélisation

- **UUID** pour les entites metier (`core`, `reco`) : pattern SaaS, pas de fuite de cardinalite.
- **Types ENUM** (morphotype, saison colorimetrique, sous-ton, statut reco) : integrite forte.
- **pgvector `vector(512)`** : embeddings CLIP ViT-B/32 stockes au cote du catalogue.
- **`signals`** = landing zone brute H&M (fidele aux CSV), transformee au Bloc 3 (dbt).
- **Human-in-the-loop** trace via `recommendation_items.advisor_action` (kept/removed/added).
