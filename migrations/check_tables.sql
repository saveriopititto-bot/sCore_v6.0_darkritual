-- 📊 QUERY DI VERIFICA TABELLE
-- Elenca tutte le tabelle, numero di righe e dimensione su disco.

SELECT
    schemaname as schema,
    relname as tabella,
    n_live_tup as righe_stimate,
    pg_size_pretty(pg_total_relation_size(relid)) as dimensione_totale
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- Se vuoi vedere solo i nomi delle colonne per una specifica tabella (es. 'runs'):
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'runs';
