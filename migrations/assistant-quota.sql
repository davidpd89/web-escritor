-- Asistente web: cuota diaria exacta para impedir consumo de IA por encima del presupuesto gratuito previsto.
-- Aplicar a la D1 enlazada como ASSISTANT_QUOTA_DB antes de activar ASSISTANT_ENABLED.
CREATE TABLE IF NOT EXISTS assistant_daily_quota (
  bucket TEXT NOT NULL,
  day_utc TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0 CHECK (count >= 0),
  PRIMARY KEY (bucket, day_utc)
);

CREATE INDEX IF NOT EXISTS idx_assistant_daily_quota_day
  ON assistant_daily_quota(day_utc);
