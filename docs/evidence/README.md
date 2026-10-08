# Registro de evidencias

Ejecuciones reales del **2026-10-08**, UTC en JSON; la UI muestra hora local UTC−5. Datos originales identificados por SHA-256 en `input_manifest.json`. Las capturas son de la UI en funcionamiento, no diagramas simulados.

| ID | Run / tarea | Artefacto | Afirmación demostrada | Política / regla |
|---|---|---|---|---|
| E01 | Preparación | `input_manifest.json`, `source_import.json` | Originales preservados y 4.810 filas con todas sus celdas reconciliadas en SQL | Fuente Grammy relacional |
| E02 | Perfilamiento | `profile.json`, `../../notebooks/data_profiling.ipynb` | Estructura, ausencias, duplicación, dominios, tiempo y compatibilidad | Diseño de calidad |
| E03 | baseline_20261008T144933Z | `20261008T144933Z/baseline_20261008T144933Z/airflow_states.json`, `screenshots/baseline.png` | Siete tareas success | Test A |
| E04 | Gates baseline | Mismo directorio: `gx_spotify_raw.json`, `gx_grammy_raw.json`, `gx_prepared.json` | Suites, IDs, métricas y política Critical/Warning ejecutadas | S*, G*, P* |
| E05 | Integración baseline | `reconciliation.json`, `match_candidates.json` en directorio baseline | 82 entradas; 12 matched, 9 ambiguous, 61 unmatched; conteos balanceados | Contrato de enlace |
| E06 | failure_20261008T144933Z / validate_spotify_raw | `20261008T144933Z/failure_20261008T144933Z/gx_spotify_raw.json` | 101 viola popularidad [0,100]; evidencia persistida antes de excepción | S05-popularity Critical |
| E07 | Fallo y propagación | Directorio failure: `airflow_states.json`, `task_logs/task_id=validate_spotify_raw/attempt=1.log`; `screenshots/failure.png`, `screenshots/failure_task.png` | Raw falla una vez; transform/prepared/load quedan upstream_failed con 0 intentos | Test B / sin retries deterministas |
| E08 | rerun_20261008T144933Z | `20261008T144933Z/rerun_20261008T144933Z/airflow_states.json`, `screenshots/rerun.png` | Recuperación sin alterar el DAG o el original | Safe rerun |
| E09 | DW antes/fallo/rerun | `latest_reliability.json` y `20261008T144933Z/reliability_summary.json` | Igualdad de conteos, sumas de control y SHA-256 de todas las filas de la vista dimensional | Idempotencia / aislamiento del fallo |
| E10 | Dashboard | `screenshots/dashboard.png` | Tres KPIs y tres gráficos alimentados desde el DW | AR1–3; Streamlit con aval docente confirmado por el estudiante |
| E11 | Runtime / esquema | `runtime_checks.json` | Airflow 3.1.8, dependencias del DAG, retries selectivos, restricciones SQL y conteos | Reproducibilidad |
| E12 | Bootstrap portable | `20261008T155343Z/reliability_summary.json` y estados/logs de sus tres runs | Segundo experimento lanzado por bootstrap: éxito, fallo controlado y rerun con el mismo hash del DW | Arranque reproducible para el clon |

## Interpretación de Test B

La extracción Spotify termina correctamente: el parámetro de prueba altera solo su copia de la primera popularidad a 101. GX detecta exactamente la violación **S05-popularity** y lanza `QualityError`. `validate_spotify_raw` tiene un intento; la rama Grammy completa su validación. Como transformación depende de ambas ramas mediante `all_success`, sus tres tareas downstream muestran `upstream_failed` y **cero intentos**, no una transformación parcial ni una carga parcial.

El fallo no cambia el DW: antes y después hay 82 hechos, 12 matches, suma de control popularidad 838, suma energía 5,748 y el mismo hash de contenido. El tercer run normal reproduce esas mismas cifras y hash. Las sumas son controles técnicos, no KPIs analíticos aditivos.

## Resultados de verificación adicional

- Seis pruebas unitarias pasan: duplicación por género, versiones ambiguas, cuarentena de conflictos, fallo GX con evidencia, warning que continúa, esquema faltante y rechazo de medidas en no-match (algunos casos comparten prueba).
- Notebook ejecutado contra CSV Spotify y `source.grammy` PostgreSQL; outputs incluidos.
- Streamlit AppTest: sin excepciones, tres tarjetas y tres gráficos. Captura tomada también con navegador Edge real en modo headless.
- No se provocó una caída SQL transitoria: se documenta la configuración selectiva y la justificación; no se presenta una prueba inexistente de retries de red.

## Reproducir

`docker compose exec -T airflow-scheduler python -m scripts.reliability` crea tres runs nuevos y otro directorio fechado, conservando esta evidencia. `latest_reliability.json` apunta al experimento más reciente. Para capturas automáticas: instalar Playwright 1.51.0 en el venv y disponer de Edge; ejecutar `python -m scripts.capture_evidence` desde el host. Alternativamente capturar Grid y logs manualmente en la UI.
