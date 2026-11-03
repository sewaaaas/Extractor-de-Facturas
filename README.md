# Extractor de facturas

Proyecto personal en Python para explorar la lectura de comprobantes mediante OCR y archivos PDF.

La idea es facilitar la extracción de información de facturas. Por ahora es una base técnica: todavía no realiza una extracción completa de datos reales ni tiene una interfaz para cargar documentos.

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
