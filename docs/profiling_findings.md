# Perfilamiento y riesgos observados

Evidencia reproducible: [notebook ejecutado](../notebooks/data_profiling.ipynb), [perfil completo JSON](evidence/profile.json), [manifiesto original](evidence/input_manifest.json). El notebook consulta Grammy desde PostgreSQL; el JSON inicial describe los archivos suministrados. Los vacíos Grammy se interpretan como ausencia solo en la vista de análisis, sin actualizar la fuente.

| Fuente/atributo | Evidencia | Riesgo | Requerimiento / control |
|---|---|---|---|
| Spotify estructura | 114.000 filas, 21 columnas incluyendo índice exportado | Confundir índice con identidad de pista | AR1: S02, se usa track_id |
| Spotify track_id | 24.259 filas repetidas respecto de la primera aparición; 720 IDs con conflictos en nombre, artista o medidas | Multiplicar observaciones y asignar valores arbitrarios | AR1–3: S03, cuarentena de IDs conflictivos |
| Spotify duplicados | 450 filas duplicadas si se excluye índice exportado | Inflar catálogo y hechos | AR1–3: colapso de IDs compatibles |
| Spotify nombre/artista/álbum | Una ausencia en cada campo (0,000877 % de filas) | Enlaces por claves vacías | AR1: S04, cuarentena de claves faltantes |
| Spotify popularity, energy, danceability | Rangos de perfil dentro de 0–100, 0–1, 0–1; 0 nulos | Futuros lotes pueden corromper promedios | AR2–3: S05 Critical, unidades justifican límites |
| Grammy artist | 1.840 ausencias, 38,2536 % global | Excluir indiscriminadamente categorías cuyo crédito está en otros campos | AR1: G05 solo exige identidad en alcance |
| Grammy nominee | 6 ausencias globales | Uniones incompletas | AR1: alcance y G05 |
| Grammy winner | 4.810 True, sin False; dos grupos en alcance tienen múltiples True | Suposición injustificada de clasificación ganador/no ganador | AR1–3: G06 Warning y excluir esa comparación |
| Grammy tiempo | Años 1958–2019 sin huecos globales; fechas web parseables | Confundir año fuente, ceremonia, lanzamiento o publicación web | AR1–3: año literal; sin inferencia causal/histórica |
| Spotify tiempo | Sin timestamp de snapshot | Popularidad no puede alinearse al año Grammy | AR2: popularidad del archivo, no popularidad al recibir premio |
| Entre fuentes | Créditos conjuntos, versiones y nombres no uniformes; sin ID común | Falsos positivos y many-to-many | AR1–3: NFKC+casefold+espacios, enlace exacto conservador |

En alcance: **82 entradas**, 69 Record Of The Year y 13 Best Pop Solo Performance; sin duplicados de clave literal ni artistas ausentes. Es un estudio acotado de grabaciones, no una evaluación de todas las categorías. El histórico observado no demuestra exhaustividad de nominaciones.

## Resultado de aplicar el contrato de integración

- Spotify: 1.933 filas en cuarentena, 23.047 repeticiones compatibles colapsadas, 89.020 pistas elegibles únicas. Suma = 114.000.
- Grammy: 4.728 filas fuera del alcance analítico y 82 conservadas. No se eliminan originales.
- Enlaces: **12 matched, 61 unmatched, 9 ambiguous**. Suma = 82.
- La baja cobertura restringe la representatividad de AR2/AR3. Los promedios describen 12 entradas inequívocas, no 82 pistas ni la totalidad de los premios. Ver candidatos preservados antes de proponer nuevas reglas de matching.
