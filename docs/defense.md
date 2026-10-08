# Guion de sustentación (8–10 minutos)

1. **Problema y alcance (1 min).** Presentar AR1–AR3 y por qué cada uno necesita las dos fuentes. Explicar las dos categorías de grabaciones y `winner` constante.
2. **Datos y evidencia (1 min).** Abrir notebook: 114.000/4.810 filas, 720 IDs conflictivos y claves sin correspondencia. Mostrar cómo esos hallazgos justifican reglas, no limpieza para aprobar tests.
3. **Arquitectura (1 min).** Mostrar CSV Spotify y tabla Grammy; diferenciar importación de fuente de load_dw. Abrir DAG con ambas ramas y gates raw/prepared.
4. **GX y fallos (2 min).** Abrir baseline y fallo. Señalar S05-popularity, valor 101, log, JSON GX y downstream upstream_failed con 0 intentos. Explicar Warning vs Critical y retries selectivos.
5. **Integración y modelo (1 min).** Mostrar un caso matched, unmatched y ambiguous en candidatos. Explicar grano por entrada, dimensiones y medidas NULL. No multiplicar por géneros ni elegir una versión arbitraria.
6. **Rerun (1 min).** Comparar hashes/conteos/medidas antes-después. Explicar transacción y rollback; un retry después de commit reconstruye el mismo snapshot.
7. **Dashboard (1–2 min).** Mostrar conexión PostgreSQL, 3 KPIs, 3 gráficos y n=12. Interpretar cobertura 14,63 % como limitación observable. Presentar Streamlit como herramienta avalada por el docente, según confirmación del estudiante.

## Preguntas para practicar

- ¿Por qué el hecho no tiene una fila por Spotify track_id? Porque el proceso es una entrada Grammy y una pista puede estar en varias categorías/años.
- ¿Qué significa un porcentaje de cobertura bajo? Que este catálogo y este contrato encuentran pocos enlaces inequívocos; no que las canciones no existan en Spotify.
- ¿Por qué no usar fuzzy matching directamente? Riesgo de falsos positivos entre grabaciones, versiones y personas; requiere evaluación de pares y política de ambigüedad.
- ¿Por qué una suite puede tener success=false y una tarea success? Fallaron reglas Warning; las Critical pasaron y la política permite continuar dejando evidencia.
- ¿Por qué no reintentar calidad tres veces? El mismo dato 101 vuelve a violar [0,100]. SQL transitorio sí puede recuperarse.
- ¿Qué ocurre al fallar a mitad de carga? PostgreSQL revierte toda la transacción; los lectores conservan un snapshot válido.
- ¿Puede atribuirse una subida de popularidad al Grammy? No: faltan fecha de captura y mediciones longitudinales, además de un diseño causal.
- ¿Qué queda fuera? Otras categorías, verificación de ganadores e historia de snapshots.
