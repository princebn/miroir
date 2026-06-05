-- ============================================================
-- MIROIR — Schema OLTP PostgreSQL (Bloc 2 Architecture)
-- Domaine : conseil en image B2B
-- Idempotent : re-jouable sans destruction
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS signals;
CREATE SCHEMA IF NOT EXISTS reco;
CREATE SCHEMA IF NOT EXISTS events;

-- ---------- Types ENUM (idempotents) ----------
DO $$ BEGIN CREATE TYPE core.morphotype AS ENUM ('A','V','H','O','X','8');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE core.skin_undertone AS ENUM ('cold','warm','neutral');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE core.color_season AS ENUM
  ('bright_spring','light_spring','true_spring','light_summer','true_summer',
   'soft_summer','soft_autumn','true_autumn','deep_autumn','deep_winter',
   'true_winter','bright_winter');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE core.style_archetype AS ENUM
  ('classic','romantic','dramatic','natural','creative','elegant');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE core.client_region AS ENUM ('europe','africa');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE reco.reco_status AS ENUM ('draft','validated','adjusted','shared');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE reco.reco_source AS ENUM ('collaborative','content','visual','color_match');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE reco.advisor_action AS ENUM ('kept','removed','added');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE events.event_type AS ENUM
  ('product_view','product_click','reco_validation','purchase');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- CORE ----------
CREATE TABLE IF NOT EXISTS core.advisors (
  advisor_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name       TEXT NOT NULL,
  email           TEXT UNIQUE NOT NULL,
  country         TEXT NOT NULL,
  city            TEXT,
  seniority_years SMALLINT CHECK (seniority_years >= 0),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.clients (
  client_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advisor_id  UUID NOT NULL REFERENCES core.advisors(advisor_id) ON DELETE CASCADE,
  full_name   TEXT NOT NULL,
  region      core.client_region NOT NULL,
  country     TEXT,
  segment     TEXT,
  birth_year  SMALLINT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_clients_advisor ON core.clients(advisor_id);

CREATE TABLE IF NOT EXISTS core.client_profiles (
  profile_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id        UUID NOT NULL UNIQUE REFERENCES core.clients(client_id) ON DELETE CASCADE,
  morphotype       core.morphotype NOT NULL,
  color_season     core.color_season NOT NULL,
  skin_undertone   core.skin_undertone NOT NULL,
  style_archetypes core.style_archetype[] NOT NULL,
  height_cm        SMALLINT,
  bust_cm          SMALLINT,
  waist_cm         SMALLINT,
  hips_cm          SMALLINT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.client_budgets (
  client_id  UUID NOT NULL REFERENCES core.clients(client_id) ON DELETE CASCADE,
  category   TEXT NOT NULL,
  budget_min NUMERIC(10,2),
  budget_max NUMERIC(10,2),
  PRIMARY KEY (client_id, category)
);

CREATE TABLE IF NOT EXISTS core.client_occasions (
  client_id   UUID NOT NULL REFERENCES core.clients(client_id) ON DELETE CASCADE,
  occasion    TEXT NOT NULL,
  probability NUMERIC(4,3) CHECK (probability BETWEEN 0 AND 1),
  PRIMARY KEY (client_id, occasion)
);

-- ---------- CATALOG ----------
CREATE TABLE IF NOT EXISTS catalog.products (
  product_id      INTEGER PRIMARY KEY,
  gender          TEXT,
  master_category TEXT,
  sub_category    TEXT,
  article_type    TEXT,
  base_colour     TEXT,
  season          TEXT,
  year            SMALLINT,
  usage           TEXT,
  display_name    TEXT,
  image_path      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_products_article_type ON catalog.products(article_type);
CREATE INDEX IF NOT EXISTS idx_products_base_colour  ON catalog.products(base_colour);
CREATE INDEX IF NOT EXISTS idx_products_usage         ON catalog.products(usage);

CREATE TABLE IF NOT EXISTS catalog.product_embeddings (
  product_id INTEGER PRIMARY KEY REFERENCES catalog.products(product_id) ON DELETE CASCADE,
  embedding  vector(512) NOT NULL,
  model      TEXT NOT NULL DEFAULT 'clip-vit-base-patch32',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS catalog.product_colors (
  product_id INTEGER NOT NULL REFERENCES catalog.products(product_id) ON DELETE CASCADE,
  rank       SMALLINT NOT NULL,
  hex        CHAR(7) NOT NULL,
  ratio      NUMERIC(5,4) NOT NULL,
  PRIMARY KEY (product_id, rank)
);

-- ---------- SIGNALS (H&M) ----------
CREATE TABLE IF NOT EXISTS signals.hm_articles (
  article_id         TEXT PRIMARY KEY,
  product_code       TEXT,
  prod_name          TEXT,
  product_type_name  TEXT,
  product_group_name TEXT,
  colour_group_name  TEXT,
  department_name    TEXT,
  index_name         TEXT,
  garment_group_name TEXT,
  detail_desc        TEXT
);

CREATE TABLE IF NOT EXISTS signals.hm_customers (
  customer_id            TEXT PRIMARY KEY,
  active                 SMALLINT,
  club_member_status     TEXT,
  fashion_news_frequency TEXT,
  age                    SMALLINT,
  postal_code            TEXT
);

CREATE TABLE IF NOT EXISTS signals.hm_transactions (
  t_dat            DATE NOT NULL,
  customer_id      TEXT NOT NULL,
  article_id       TEXT NOT NULL,
  price            NUMERIC(12,8) NOT NULL,
  sales_channel_id SMALLINT
);

-- ---------- RECO ----------
CREATE TABLE IF NOT EXISTS reco.recommendations (
  reco_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id    UUID NOT NULL REFERENCES core.clients(client_id) ON DELETE CASCADE,
  advisor_id   UUID NOT NULL REFERENCES core.advisors(advisor_id),
  status       reco.reco_status NOT NULL DEFAULT 'draft',
  occasion     TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  validated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_reco_client ON reco.recommendations(client_id);

CREATE TABLE IF NOT EXISTS reco.recommendation_items (
  reco_id        UUID NOT NULL REFERENCES reco.recommendations(reco_id) ON DELETE CASCADE,
  product_id     INTEGER NOT NULL REFERENCES catalog.products(product_id),
  rank           SMALLINT NOT NULL,
  score          NUMERIC(6,5),
  source         reco.reco_source NOT NULL,
  advisor_action reco.advisor_action,
  PRIMARY KEY (reco_id, product_id)
);

-- ---------- EVENTS ----------
CREATE TABLE IF NOT EXISTS events.interaction_events (
  event_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type  events.event_type NOT NULL,
  advisor_id  UUID REFERENCES core.advisors(advisor_id),
  client_id   UUID REFERENCES core.clients(client_id),
  product_id  INTEGER,
  payload     JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_type     ON events.interaction_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred ON events.interaction_events(occurred_at);
