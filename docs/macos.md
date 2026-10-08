# Ejecutar el workshop desde macOS

## Requisitos

- Git y Python 3 (Python 3.12 recomendado; bootstrap solo utiliza la biblioteca estándar).
- Docker Desktop para tu arquitectura, abierto y con el motor iniciado. Compose v2 incluido.
- Memoria asignada a Docker: mínimo 4 GB, recomendable 8 GB para Airflow y el resto de servicios.
- Acceso al repositorio y a Internet para descargar imágenes/dependencias durante el primer build.

Las imágenes base `apache/airflow:3.1.8-python3.12`, `postgres:16.6` y `python:3.12-slim` publican variantes **linux/amd64** y **linux/arm64**. Docker selecciona automáticamente la apropiada para Mac Intel o Apple Silicon (M1/M2/M3/M4…). No se fija `platform: linux/amd64` ni se requiere Rosetta. Se verificaron los manifiestos multi-arquitectura; las ejecuciones end-to-end preservadas se realizaron en Docker Desktop Windows/amd64, no en hardware Mac.

## Arranque completo

En Terminal, con Docker Desktop abierto:

```bash
git clone git@github.com:danielferparradiaz/workshop2-ETL-2026-2.git
cd workshop2-ETL-2026-2
python3 -m scripts.bootstrap
```

Si usas Python instalado con Homebrew como `python3.12`, puedes reemplazar `python3` por `python3.12`. Si falta Python y ya tienes Homebrew: `brew install python@3.12`. El clone SSH requiere tu clave GitHub configurada; también puedes clonar con la URL HTTPS del repositorio y autenticarte según corresponda.

El comando de bootstrap:

1. Comprueba que los dos datasets incluidos coinciden byte por byte con el manifiesto.
2. Comprueba Docker y genera `.env` con secretos nuevos para tu Mac si no existe.
3. Construye y arranca los contenedores usando rutas relativas del clon.
4. Espera al API, scheduler, procesador y descubrimiento del DAG (hasta 5 minutos).
5. Importa Grammy a PostgreSQL y reconcilia las 4.810 filas.
6. Ejecuta tres DAG Runs reales: baseline, fallo Critical y rerun, comparando contenido del DW.
7. Verifica versión, dependencias, retries y restricciones dimensionales.

La primera construcción puede tardar varios minutos. Un bootstrap repetido conserva `.env`, reemplaza transaccionalmente la fuente Grammy y el snapshot DW de este proyecto, y genera nuevas evidencias fechadas. Para simplemente reabrir el entorno ya preparado, usa `docker compose up -d`.

## Abrir y comprobar

- Airflow: **http://localhost:8082**. Modo local all-admin; no necesitas contraseña de UI.
- Dashboard: **http://localhost:8502**.
- PostgreSQL desde macOS: `localhost:5434`, base `music`, usuario `workshop`; contraseña en tu `.env`.

```bash
docker compose ps
docker compose exec -T airflow-scheduler airflow version
docker compose exec -T postgres psql -U workshop -d music -c "SELECT * FROM dw.v_kpis;"
```

Resultado esperado con los CSV versionados: 82 entradas, 12 matches, cobertura 14,6341 %, popularidad media 69,8333 y energía media 0,479. En Airflow verás un run fallido **intencional**: `validate_spotify_raw` rechaza popularidad 101 y las tres tareas posteriores quedan `upstream_failed`; el run de recuperación termina exitoso.

Las capturas y evidencias históricas viajan en el repo. La base Airflow de tu Mac parte vacía: bootstrap crea sus propios run IDs y no restaura metadata de Windows. `docs/evidence/latest_reliability.json` y `runtime_checks.json` se actualizan con tu ejecución; es normal que Git muestre cambios en evidencias después de probar.

## Alternativa por pasos

```bash
python3 -m scripts.verify_inputs
python3 -m scripts.configure  # solo si aún no existe .env
docker compose config --quiet
docker compose build
docker compose up -d
docker compose exec -T airflow-scheduler python -m scripts.wait_ready
docker compose exec -T airflow-scheduler python -m scripts.prepare_source
docker compose exec -T airflow-scheduler python -m scripts.reliability
docker compose exec -T airflow-scheduler python -m scripts.verify_runtime
```

## Notebook y pruebas unitarias (opcionales para arrancar el DAG)

Con Python **3.12** instalado, ejecutar desde la raíz del clon:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.execute_notebook
```

El notebook necesita PostgreSQL arrancado y Grammy importado. Las dependencias del pipeline se instalan dentro de las imágenes Docker; no necesitas un venv ni instalar Airflow en macOS para el bootstrap. La captura automática de pantallas es opcional y usa Playwright con Edge; las capturas existentes ya vienen incluidas y puedes tomar nuevas manualmente desde tu navegador.

## Diagnóstico

- **Cannot connect to Docker daemon:** abrir Docker Desktop y esperar a que el motor esté listo.
- **No aparece el DAG / timeout de readiness:** `docker compose logs airflow-dag-processor airflow-scheduler airflow-api-server` y `docker compose exec -T airflow-scheduler airflow dags list-import-errors`.
- **Puerto ocupado:** liberar 8082, 8502 o 5434, o cambiar el puerto del host en Compose y las URLs usadas. El notebook local usa 5434 por defecto.
- **Mounts denied:** autorizar la carpeta del clon en Docker Desktop → Settings → Resources → File Sharing, si tu configuración lo requiere.
- **Contenedor termina por falta de memoria:** revisar recursos de Docker Desktop y aumentar RAM disponible.
- **Contraseña PostgreSQL no coincide:** conservar el `.env` que creó ese volumen. Cambiar `.env` no cambia la contraseña de una base ya inicializada.

Detener conservando los datos: `docker compose stop`. Reanudar: `docker compose up -d`. Los originales están incluidos, con sus bytes preservados por `.gitattributes`; no hace falta copiarlos desde Windows ni instalar Git LFS.
