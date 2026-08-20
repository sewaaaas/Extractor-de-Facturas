# Invoice Extractor

Base técnica de DOC-01 para una futura aplicación de extracción inteligente de comprobantes de pago. Este incremento valida el stack local, los límites arquitectónicos y dos rutas técnicas aisladas: OCR e inspección de PDF.

## Estado y alcance

DOC-01 incluye una aplicación FastAPI mínima, configuración tipada, modelos y puertos neutrales, logging estructurado, adaptadores provisionales de PaddleOCR/PyMuPDF, pruebas rápidas y scripts de smoke test.

Todavía **no** procesa comprobantes reales, recibe uploads, extrae RUC, fecha, subtotal, IGV o total, calcula confidence, presenta formularios/revisión, usa base de datos ni integra SharePoint o SUNAT.

## Requisitos

- Windows 11 x64 (baseline validado en DOC-01; Windows 10 x64 deberá comprobarse si es requisito).
- CPython 3.12 x64. La ejecución de DOC-01 usó Python 3.12.13.
- `uv` 0.12.5 o compatible.
- CPU x86-64. No se requiere GPU ni CUDA.
- Acceso a PyPI durante `uv sync` y acceso al origen de modelos durante la precarga inicial.
- Espacio suficiente para `.venv`, dependencias de Paddle y dos modelos OCR. Los pesos no se guardan en Git.

PaddleOCR 3.7.0 necesita PaddlePaddle 3.x. El proyecto fija PaddlePaddle CPU 3.3.1 y el baseline `PP-OCRv6_small` mediante los modelos explícitos `PP-OCRv6_small_det` y `PP-OCRv6_small_rec`.

## Instalación reproducible

Instale `uv` siguiendo la [documentación oficial](https://docs.astral.sh/uv/getting-started/installation/) y, desde PowerShell en la raíz del repositorio, ejecute:

```powershell
uv python install 3.12
uv sync --frozen
```

`uv.lock` fija el grafo completo. No instale las dependencias globalmente ni ejecute `pip install` dentro del Python del sistema como flujo normal.

Para crear configuración local:

```powershell
Copy-Item .env.example .env
```

`.env` está ignorado por Git. Ningún secreto debe agregarse a `.env.example`.

## Ejecutar FastAPI

```powershell
uv run uvicorn invoice_extractor.main:app --host 127.0.0.1 --port 8000 --reload
```

Comprobar el servicio:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{"status":"ok","service":"invoice-extractor"}
```

El endpoint no carga PaddleOCR ni abre PDFs.

## Verificaciones

### Pruebas rápidas y offline

```powershell
uv run pytest
```

La suite normal no descarga modelos ni ejecuta inferencia real.

### Lint y formato

```powershell
uv run ruff check .
uv run ruff format --check .
```

Para aplicar formato localmente:

```powershell
uv run ruff format .
```

### Spike PDF

```powershell
uv run python scripts/smoke_pdf.py
```

El script crea un PDF temporal sintético, lo abre mediante `PyMuPDFTextExtractor`, imprime número de páginas y texto, y devuelve un código distinto de cero ante fallo.

### Spike OCR y precarga

```powershell
uv run python scripts/smoke_ocr.py
```

El primer uso descarga `PP-OCRv6_small_det` y `PP-OCRv6_small_rec`; por eso debe ejecutarse durante aprovisionamiento, nunca como primera petición de un servicio. El script genera una imagen temporal no sensible, fuerza dispositivo `cpu`, imprime versiones/modelo/tiempo/scores y falla si no reconoce texto. En Windows, PaddleOCR 3.7.0 los almacenó en:

```text
C:\Users\<usuario>\.paddlex\official_models\PP-OCRv6_small_det
C:\Users\<usuario>\.paddlex\official_models\PP-OCRv6_small_rec
```

PaddleOCR/PaddleX descarga modelos oficiales desde Hugging Face de forma predeterminada. Si ese origen no está disponible, la documentación permite seleccionar BOS antes de la precarga:

```powershell
$env:PADDLE_PDX_MODEL_SOURCE = "BOS"
uv run python scripts/smoke_ocr.py
```

Después de una precarga correcta, se puede omitir el chequeo de conectividad y exigir los modelos cacheados:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = "True"
uv run python scripts/smoke_ocr.py
```

Para verificar la precarga:

```powershell
Get-ChildItem "$HOME\.paddlex\official_models\PP-OCRv6_small_det"
Get-ChildItem "$HOME\.paddlex\official_models\PP-OCRv6_small_rec"
```

Finalmente repita el smoke test con la red realmente deshabilitada en el equipo que se aprovisionará. DOC-01 verificó el uso del caché y la omisión del chequeo de origen, pero no modificó la conectividad del host.

El adaptador desactiva MKL-DNN/oneDNN: en este Windows, el ejecutor optimizado de PaddlePaddle 3.3.1 falló al convertir atributos PIR de PP-OCRv6 small. La ruta CPU regular reconoció correctamente la muestra. Véanse el ADR y el informe de implementación para el diagnóstico exacto.

## Configuración

| Variable | Default | Estado en DOC-01 |
|---|---:|---|
| `APP_ENV` | `local` | Identifica el entorno |
| `APP_HOST` | `127.0.0.1` | Usada por el comando Uvicorn/documentación |
| `APP_PORT` | `8000` | Usada por el comando Uvicorn/documentación |
| `DATA_DIR` | `data` | Reservada; no hay almacenamiento funcional |
| `MAX_UPLOAD_SIZE_MB` | `15` | Reservada para DOC-02 |
| `MAX_PDF_PAGES` | `10` | Reservada para DOC-02/DOC-03 |
| `OCR_MODEL` | `PP-OCRv6_small` | Usada por el smoke OCR |
| `LOG_LEVEL` | `INFO` | Usada al crear la aplicación |

## Arquitectura breve

```text
FastAPI/API -> casos de uso futuros -> dominio (modelos + puertos)
                                      ^
                                      |
                     infraestructura/adaptadores
                         PaddleOCR | PyMuPDF
```

El dominio usa `dataclasses` y `Protocol` de Python; no importa FastAPI, PaddleOCR ni PyMuPDF. La salida de cada proveedor se traduce a modelos internos. Véanse:

- [`docs/architecture/DOC-01-boundaries.md`](docs/architecture/DOC-01-boundaries.md)
- [`docs/decisions/ADR-001-ocr-baseline.md`](docs/decisions/ADR-001-ocr-baseline.md)
- [`docs/decisions/ADR-002-pdf-library.md`](docs/decisions/ADR-002-pdf-library.md)

## Datos, modelos y seguridad

- `data/uploads`, `data/processed` y `data/failed` no deben contener archivos versionados.
- Los uploads futuros nunca se servirán desde un directorio `static`.
- Los logs estructurados no deben incluir texto OCR ni datos del comprobante.
- Los PDFs se abren para lectura/extracción; la aplicación no ejecuta JavaScript, adjuntos ni contenido embebido.
- `.env`, `.venv`, herramientas locales, caches y modelos están ignorados.
- PyMuPDF es provisional: su licencia debe aprobarse antes de distribución corporativa.

## Base de evaluación futura

`tests/fixtures/evaluation-manifest.example.json` define una muestra sintética del esquema esperado. No contiene comprobantes reales y DOC-01 no implementa todavía el evaluador ni extracción de campos.

## Comandos de mantenimiento

```powershell
uv lock --check
uv sync --frozen
uv run python -c "import invoice_extractor; print(invoice_extractor.__version__)"
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python scripts/smoke_pdf.py
uv run python scripts/smoke_ocr.py
```
