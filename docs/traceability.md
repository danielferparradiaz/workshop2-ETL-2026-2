# Trazabilidad end-to-end

| Requerimiento | Datos | Evidencia / riesgo | Regla y GX | Transformación | DW | Salida |
|---|---|---|---|---|---|---|
| AR1 cobertura | Grammy year/category/nominee/artist; Spotify track_id/track_name/artists | 24.259 repeticiones de ID, variantes de versión y crédito | S03 Unique (warning); G05 InSet; P03 Unique; P07 InSet | Colapso compatible, cuarentena, clave normalizada y set de candidatos | fact_grammy_catalog matched/status; dim_year/category/track | v_coverage; línea por año y KPI 14,63 % |
| AR2 popularidad | Atributos AR1 + popularity | 720 IDs con conflictos; riesgo de escoger un valor arbitrario o inválido | S05 Between/NotNull; P08 InSet | Excluir ID conflictivo, copiar una medida solo con match único | fact.popularity, dim_category | v_category_metrics; barras y promedio 69,83 |
| AR3 audio | Atributos AR1 + energy/danceability | Rango [0,1]; falta de coincidencia no es cero | S05 Between/NotNull; P08 InSet; P09 Sum | NULL para no match, características para match único | fact.energy/danceability, dim_category | Dispersión y energía media 0,479 |
| AR1–3 interpretación | Grammy winner, fechas y año; fecha Spotify ausente | 4.810 True; datos web no son fecha musical | G06 UniqueValueCount (warning), G03 MatchRegex | Año literal; no clasificar por winner | dim_year, documentación de snapshot | Etiquetas explícitas y limitaciones del dashboard |

Los valores indicados pertenecen al lote de evidencia del 8 de octubre de 2026 y no son constantes codificadas en las consultas o el dashboard.
