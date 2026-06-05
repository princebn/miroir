CREATE INDEX IF NOT EXISTS idx_hm_tx_customer ON signals.hm_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_hm_tx_article  ON signals.hm_transactions(article_id);
CREATE INDEX IF NOT EXISTS idx_hm_tx_date     ON signals.hm_transactions(t_dat);
ANALYZE signals.hm_transactions;
ANALYZE signals.hm_articles;
ANALYZE signals.hm_customers;
