# Reglas, métricas, GX y política

Implementación: `src/validation.py`. Cada Expectation incluye `meta.rule_id` y `meta.severity`. Las variantes con sufijo identifican columna/subregla; todos los IDs evaluados quedan en las suites y resultados JSON. **Critical** requiere 100 % de cumplimiento y detiene el gate; **Warning** registra la desviación y continúa bajo la política indicada. Ningún umbral se ajusta para forzar aprobación del lote.

| Rule ID | Capa / campos | Dimensión | Regla, métrica y umbral | Severidad | GX Expectation (prefijo Expect) | Justificación / AR |
|---|---|---|---|---|---|---|
| `*-SCHEMA` | Las 3 capas | Validez estructural | Todas las columnas requeridas; preparado sin columnas extra, salvo diagnósticos declarados | Critical | TableColumnsToMatchSet | Contrato de extracción y carga; AR1–3 |
| `*-NONEMPTY` | Las 3 capas | Completitud | Conteo >=1 | Critical | TableRowCountToBeBetween | Un lote vacío no sustenta análisis; AR1–3 |
| S02, S02-format | Spotify track_id | Completitud/validez | 0 nulos; 100 % alfanumérico de 22 caracteres | Critical | ColumnValuesToNotBeNull / MatchRegex | Identidad Spotify; AR1–3 |
| S03 | Spotify track_id | Unicidad | 0 IDs repetidos como señal de advertencia | Warning | ColumnValuesToBeUnique | Repeticiones observadas; colapso/quarantine según conflicto; AR1–3 |
| S04-* | Spotify track_name, artists | Completitud | 0 nulos como señal de advertencia | Warning | ColumnValuesToNotBeNull | Una ausencia observada; cuarentena de claves vacías; AR1 |
| S05-*-complete | Spotify medidas | Completitud | 0 nulos | Critical | ColumnValuesToNotBeNull | No imputar medidas usadas por KPIs; AR2–3 |
| S05-popularity | Spotify popularity | Validez | 100 % en [0,100] | Critical | ColumnValuesToBeBetween | Escala del indicador, no percentil observado; AR2 |
| S05-energy / S05-danceability | Spotify atributos de audio | Validez | 100 % en [0,1] | Critical | ColumnValuesToBeBetween | Escalas de características; AR3 |
| G02-id / G02-complete | Grammy source_row_id | Unicidad/completitud | 0 duplicados, 0 nulos | Critical | ColumnValuesToBeUnique / NotBeNull | Reconciliación de importación y linaje; AR1 |
| G03 / G03-complete | Grammy year | Validez/completitud | 100 % strings de cuatro cifras en 1950–2099, sin nulos | Critical | ColumnValuesToMatchRegex / NotBeNull | Envolvente explícita del contrato, histórico observado 1958–2019; AR1 |
| G04 / G04-complete | Grammy category | Completitud | 100 % no nulo y contiene carácter no blanco | Critical | ColumnValuesToMatchRegex / NotBeNull | Selección de alcance y dimensión; AR1–3 |
| G05 | Grammy nominee, artist | Completitud contextual | 100 % de filas en alcance con identidad no vacía; `_scope_identity_valid=True` | Critical | ColumnValuesToBeInSet | Las ausencias globales no justifican bloquear categorías fuera de alcance; AR1 |
| G06 | Grammy winner | Capacidad de discriminar | 2 valores distintos como señal para análisis de resultados | Warning | ColumnUniqueValueCountToBeBetween | Con una clase no comparar ganadores/no ganadores; solo observar entradas; AR1–3 |
| P02 | Preparado filas | Consistencia | Conteo igual al preparado registrado en reconciliación | Critical | TableRowCountToEqual | Detecta pérdida de filas del artefacto entre tareas; reconciliación previa prueba balance de fuentes; AR1 |
| P03 | Preparado entry_key | Unicidad | 0 claves repetidas | Critical | ColumnValuesToBeUnique | Una fila por clave literal Grammy; AR1–3 |
| P04 | Preparado category | Validez | 100 % en las dos categorías declaradas | Critical | ColumnValuesToBeInSet | Modelo acotado de grabaciones; AR1–3 |
| P05 | Preparado year | Validez | 100 % en [1950,2099] | Critical | ColumnValuesToBeBetween | Dominio de dim_year; AR1 |
| P06 | Preparado match_status | Validez | matched/unmatched/ambiguous | Critical | ColumnValuesToBeInSet | Estado explícito para cobertura; AR1 |
| P07 | Preparado enlace | Consistencia | 100 % `_link_valid=True`: matched=1 implica un candidato y pista; unmatched=0 candidatos; ambiguous>1; ambos sin pista | Critical | ColumnValuesToBeInSet | Impedir atribución arbitraria/multiplicación; AR1–3 |
| P08 | Preparado medidas | Validez contextual | 100 % `_measures_valid=True`: matched con medidas en rangos; restantes nulas | Critical | ColumnValuesToBeInSet | Ausencia no equivale a energía/popularidad cero; AR2–3 |
| P09 | Preparado matched | Disponibilidad analítica | Suma matched >=1 | Critical | ColumnSumToBeBetween | Cero coincidencias impediría AR2/AR3; no garantiza representatividad |
| P10 | Preparado match_status | Cobertura | 100 % matched como señal aspiracional; cualquier ausencia/ambigüedad se expone | Warning | ColumnValuesToBeInSet | No exige cobertura falsa para pasar; tasas y candidatos documentados; AR1 |
| P11-* | Preparado atributos de hecho | Completitud | 0 nulos en clave, ID, año, categoría, título, artista y estados | Critical | ColumnValuesToNotBeNull | Requisitos NOT NULL del hecho/dimensiones; AR1–3 |

## Ejecución GX

Cada llamada crea un contexto **ephemeral** aislado, una fuente pandas, un DataFrame Asset por capa y un Batch Definition whole-dataframe. Una suite por capa se conecta al Batch Definition mediante `gx.ValidationDefinition`. `ValidationDefinition.run` constituye la ejecución controlada equivalente al Checkpoint. Se guarda tanto la suite serializada como el resultado completo, incluidas métricas y muestras inesperadas, en `gx_<capa>.json`.

Los diagnósticos `_scope_identity_valid`, `_link_valid` y `_measures_valid` son vistas booleanas de reglas compuestas sobre datos existentes; no corrigen el valor original ni se cargan al DW. Si faltan columnas se ejecuta primero el contrato de esquema, preservando un rechazo interpretable en vez de un KeyError. Errores internos GX también fallan la tarea.

El control consulta cada resultado por severidad, registra warnings y lanza excepción por IDs Critical. Por ello el baseline tiene advertencias reales (duplicados, ausencias, winner constante, cobertura parcial) y aun así es válido bajo la política. El fallo controlado usa `S05-popularity`: cambia la primera popularidad a 101 en la copia raw de esa ejecución, sin editar CSV ni desactivar Expectations.
