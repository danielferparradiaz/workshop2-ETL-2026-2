# Requerimientos analíticos y alcance

Se estudia la presencia de entradas Grammy de **Record Of The Year** y **Best Pop Solo Performance** en el catálogo Spotify proporcionado. Estas categorías se refieren a grabaciones/interpretaciones; se excluyen álbumes, artistas y composición. Cada observación es una entrada del archivo Grammy, no un premio ganado verificado. No se afirma que el archivo contenga todas las nominaciones.

| ID | Pregunta / decisión | Datos requeridos de ambas fuentes | KPI | Detalle / visualización |
|---|---|---|---|---|
| AR1 | ¿Qué cobertura tiene el catálogo suministrado de las entradas Grammy seleccionadas? | Grammy: year, category, nominee, artist; Spotify: track_id, track_name, artists | Entradas con coincidencia inequívoca / total de entradas en alcance × 100 | Año y categoría; línea de cobertura |
| AR2 | ¿Qué categorías y cohortes Grammy tienen mayor popularidad en el snapshot Spotify? | Atributos AR1 y Spotify popularity | Popularidad media de entradas emparejadas | Categoría; barras y tamaño de muestra |
| AR3 | ¿Cómo varía la energía musical de las grabaciones Grammy por categoría? | Atributos AR1 y Spotify energy, danceability | Energía media de entradas emparejadas | Categoría; dispersión energía/bailabilidad |

Todos requieren ambas fuentes: Grammy define población y contexto; Spotify aporta identidad de catálogo y medidas. Popularidad no es histórica: el CSV no incluye fecha de captura. El año se conserva tal como viene en Grammy y no se interpreta como fecha de lanzamiento. Los promedios son por entrada: una pista en dos años/categorías participa en dos observaciones. No se suman popularidad o energía como KPIs aditivos.

La selección inicial de categorías precedió al perfilamiento. El perfil reveló que `winner` es True en las 4.810 filas, incluso múltiples entradas de una categoría/año. Por ello se afinó el vocabulario del alcance a **entradas registradas**. Sin corroboración externa, no se construye una comparación ganador/no ganador. La cobertura real y las ambigüedades se miden: una entrada sin coincidencia sigue en el denominador de AR1 y no aporta un cero artificial a AR2/AR3.
