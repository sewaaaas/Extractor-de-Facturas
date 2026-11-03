# Extractor de facturas

Proyecto personal en Python para facilitar la rendición de viáticos: la idea es leer varias boletas y facturas, extraer sus datos y organizarlos en un único archivo Excel.
El proyecto surgió al ver cómo se gestionaban las rendiciones de viáticos de los vendedores. Los comprobantes llegaban en distintos formatos: algunos eran electrónicos y otros eran boletas físicas que se escaneaban. Revisarlos y registrar sus datos manualmente hacía que el proceso fuera más lento.

Mi objetivo es que se puedan cargar varios comprobantes, tanto electrónicos como escaneados, y que sus datos queden ordenados en una tabla de Excel sin tener que copiarlos uno por uno.

**Por ahora sigue en desarrollo:** estoy probando la lectura de imágenes y PDF mediante OCR. Todavía no procesa lotes de comprobantes ni genera automáticamente el Excel.

## Herramientas

- Python 3.12 y FastAPI.
- PaddleOCR para las pruebas de reconocimiento de texto.
- PyMuPDF para leer archivos PDF.
- Pytest para las pruebas.

## Cómo ejecutarlo

Necesitas Python 3.12 y [uv](https://docs.astral.sh/uv/).

```powershell
uv python install 3.12
uv sync --frozen
Copy-Item .env.example .env
uv run uvicorn invoice_extractor.main:app --host 127.0.0.1 --port 8000 --reload
```

Puedes comprobar el servicio en `http://127.0.0.1:8000/health`.

## Pruebas

```powershell
uv run pytest
uv run python scripts/smoke_pdf.py
uv run python scripts/smoke_ocr.py
```

La primera prueba de OCR puede descargar modelos. No guardes facturas privadas, credenciales ni archivos `.env` en el repositorio.

## Estado

En desarrollo. Las pruebas actuales sirven para validar OCR y lectura de PDF con datos de ejemplo; todavía no hay extracción de campos como RUC, fecha o importe total.

Las decisiones y notas técnicas están en la carpeta [docs](docs/).
