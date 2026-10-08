# Dashboard y conexión al DW

Implementado y probado: **Streamlit**, `http://localhost:8502`, consulta `dw.v_entries` en PostgreSQL. Tres tarjetas y tres visualizaciones; filtros de categoría/año aplicados a las filas consultadas del DW. No hay lectura de CSV desde la aplicación.

**Aval académico confirmado:** el estudiante confirmó el 8 de octubre de 2026 que Streamlit cuenta con aval docente. Se utiliza como herramienta BI de la entrega bajo la opción de herramienta alternativa aprobada del enunciado. La guía, conexión y medidas Power BI son material complementario; un archivo `.pbix` no forma parte de esta solución en Streamlit.

| AR | KPI | Visualización | Consulta |
|---|---|---|---|
| AR1 | SUM(matched)/COUNT(*) ×100 | Línea año / categoría con tamaño de muestra | dw.v_entries → agrupación; SQL equivalente dw.v_coverage |
| AR2 | AVG(popularity) no nula | Barras por categoría con n | dw.v_entries → matched; dw.v_category_metrics |
| AR3 | AVG(energy) no nula | Scatter danceability vs energy, color categoría | dw.v_entries WHERE matched=1 |

N=82 entradas, n=12 emparejadas, 9 ambiguas y 61 sin coincidencia. No promediar promedios de categorías para obtener el KPI global. Campos nulos quedan fuera de las medias y dentro del denominador de cobertura. No interpretar los resultados como influencia causal de ganar un premio.

## Power BI Desktop

1. Obtener datos → PostgreSQL: servidor `localhost:5434`, base `music`; usuario `workshop`, contraseña del `.env` local.
2. Seleccionar la vista `dw.v_entries`, nombrar consulta `Entries`. Alternativamente pegar `dashboard/powerbi.pq` en una consulta en blanco. Usar modo Import y refrescar después de cada carga.
3. Crear **una medida a la vez** con las definiciones de `dashboard/measures.dax`. Formatear Cobertura % como porcentaje.
4. Crear tres tarjetas: Cobertura %, Popularidad media y Energia media.
5. Línea: eje year, leyenda category, valor Cobertura %, tooltip Entradas y Coincidencias.
6. Barras: eje category, valor Popularidad media; tooltip Coincidencias.
7. Scatter: X danceability, Y energy, detalle entry_key, leyenda category; filtrar matched=1 y usar medidas sin suma.
8. Añadir segmentadores de year/category y las limitaciones anteriores. Guardar `.pbix` y capturar conexión/visuales si se usa esta vía para evaluación.

## Evidencia implementada

`docs/evidence/screenshots/dashboard.png` muestra el dashboard ejecutado sobre el DW. También se verificó con Streamlit AppTest que renderiza sin excepciones, con exactamente tres tarjetas y tres gráficos. Las consultas SQL reproducibles están en `sql/analytics.sql`.
