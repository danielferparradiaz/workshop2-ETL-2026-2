-- AR1–AR3: KPIs. No direct CSV connections.
SELECT * FROM dw.v_kpis;
-- AR1: coverage over source year and category, including unmatched/ambiguous.
SELECT * FROM dw.v_coverage ORDER BY year, category;
-- AR2/AR3: group averages with sample size, not averages of averages.
SELECT * FROM dw.v_category_metrics ORDER BY category;
-- AR3: scatter of matched observations.
SELECT year,category,artist,nominee,energy,danceability
FROM dw.v_entries WHERE matched=1;
