# Contrato de transformación e integración

| Decisión | Antes → después | Excepciones / motivo | Impacto |
|---|---|---|---|
| Eliminar índice exportado del grano analítico | Fila por exportación/género → pista única elegible | Índice no identifica grabación | AR1–3, evitar duplicación |
| Colapsar track_id repetido compatible | Múltiples filas de una pista → una pista | Solo si track_name, artists, popularity, energy, danceability son consistentes; álbum/género no entran al modelo | AR1–3 |
| Cuarentena de IDs conflictivos | 720 IDs con variantes → excluidos del índice de enlace | No existe fecha para decidir cuál valor es vigente; todas sus filas se retienen en cuarentena | AR2–3, no elegir primera/max popularidad |
| Cuarentena de claves faltantes Spotify | Nombre/artista/ID vacío → registro auditado, no enlazable | No hay base para imputar una identidad | AR1 |
| Selección Grammy | 4.810 entradas → 82 en dos categorías | 4.728 fuera de alcance, contabilizadas; los originales y SQL fuente permanecen completos | AR1–3 |
| Normalización de clave de matching | NFKC, casefold, colapsar espacios | Mantiene acentos, puntuación y sufijos de versión. `Song - Live` no se convierte en `Song` | AR1; minimiza falsos positivos |
| Colaboradores Spotify | `A;B` → índices `(título,A)` y `(título,B)` al mismo ID | No separar Grammy por conjunciones: pueden ser nombres reales de grupos | AR1 |
| Conversión año Grammy | String de cuatro cifras validado → entero | No confundir fechas web/ceremonia con año fuente | dim_year / AR1 |
| Clave de hecho | Tupla literal year/category/nominee/artist → SHA-256(JSON) | Duplicados exactos colapsados y contados; strings originales conservados | Idempotencia / AR1–3 |
| Medidas ausentes | No match/ambiguo → NULL, nunca cero | Cero es valor real de una característica, no ausencia | AR2–3 |

## Claves, cardinalidad y límites

Clave de búsqueda: `(normalize(Grammy.nominee), normalize(Grammy.artist))` contra `(normalize(Spotify.track_name), normalize(un colaborador Spotify))`. El índice devuelve un **set de track_id**, de modo que géneros o créditos repetidos no multiplican candidatos.

- 0 candidatos: `unmatched`, sin pista ni medidas.
- 1 candidato: `matched`, se asigna su pista y medidas.
- Más de 1: `ambiguous`, se preserva lista de candidatos y no se elige pista.

Relación final **muchas entradas Grammy → a lo sumo una pista Spotify**. Un mismo track_id puede participar en varias entradas Grammy, coherente con el grano del hecho. La clave de negocio única y P03 protegen el grano; P07 protege cardinalidad/estado y P08 las medidas. El loader realiza merges `validate='many_to_one'` con dimensiones.

Evidencias: `reconciliation.json`, `match_candidates.json`, `spotify_quarantine.parquet` y `prepared.parquet`, organizados por run. Identidades no equivalentes textualmente generan falsos negativos posibles; versiones distintas con títulos iguales generan ambigüedades. Matching exacto no demuestra identidad universal de una grabación. Cualquier mejora fuzzy requiere revisión de pares y nuevas reglas, no una subida artificial de cobertura.

La validación raw ocurre **antes** de todas estas decisiones. La transformación tiene justificación por grano, identidad y medidas, independientemente de si el lote pasa GX.
