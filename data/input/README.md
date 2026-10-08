# Fuentes originales

Los originales `spotify_dataset.csv` y `the_grammy_awards.csv` están incluidos en Git para reproducir el taller desde un clon nuevo, también en macOS. No requieren Git LFS ni una descarga adicional.

`.gitattributes` preserva sus bytes, incluidos finales de línea, entre Windows y macOS. `python3 -m scripts.verify_inputs` comprueba tamaños y SHA-256 contra `docs/evidence/input_manifest.json`.

`python -m scripts.stage_inputs --source-dir <directorio>` permite volver a copiar los originales sin sobrescribir archivos distintos y registra SHA-256. No hace falta ejecutarlo después de clonar. No se descargan versiones sustitutas de los datasets.
