# DOC-01 — Implementation review

**Fecha:** 19 de agosto de 2026  
**Estado:** READY  
**Alcance:** inicialización y arquitectura; DOC-02 y fases posteriores no implementadas

## 1. Resumen de implementación

DOC-01 deja una base Python reproducible en Windows x64 con:

- proyecto `src` instalable y bloqueado mediante `uv.lock`;
- FastAPI mínimo y `GET /health`;
- configuración tipada desde entorno/`.env`;
- dominio neutral basado en `dataclasses` y `Protocol`;
- logging JSON y UUID de procesamiento;
- adaptadores sustituibles para PaddleOCR y PyMuPDF;
- 9 pruebas rápidas sin red ni descarga de modelos;
- Ruff configurado y limpio;
- spike PDF sintético exitoso;
- spike OCR local CPU exitoso con PP-OCRv6 small;
- documentación de instalación, límites y dos ADR;
- manifiesto sintético como base de evaluación futura.

No se creó upload, formulario, extracción de campos, regex de factura, confidence, revisión, persistencia, SharePoint, SUNAT, autenticación, colas, Docker, PP-StructureV3 ni PaddleOCR-VL.

## 2. Entorno verificado

| Elemento | Valor observado |
|---|---|
| Sistema | Windows 11, build `10.0.26200` |
| Arquitectura SO/proceso | AMD64 / 64 bits |
| CPU | Intel Core i7-10700 @ 2.90 GHz |
| Python | CPython 3.12.13 x64 |
| Python usado inicialmente | Runtime local de Codex; no había `python` ni `py` en `PATH` |
| uv | 0.12.5 (`x86_64-pc-windows-msvc`) |
| Entorno | `.venv`, gestionado por uv |
| Lock | `uv.lock`, 83 paquetes resueltos |

`uv` tampoco estaba en `PATH`. Para esta ejecución se instaló 0.12.5 en `.tools/uv`, ignorado por Git, usando el Python 3.12.13 ya disponible. El README documenta el flujo normal para otros desarrolladores: instalar uv, `uv python install 3.12` y `uv sync --frozen`.

## 3. Árbol final

Se omiten `.git`, `.venv` y `.tools` porque no se versionan.

```text
.
├── .env.example
├── .gitignore
├── .python-version
├── DOC-01-analisis-y-plan.md
├── DOC-01-analisis-y-plan.txt
├── README.md
├── pyproject.toml
├── uv.lock
├── data/
│   ├── failed/.gitkeep
│   ├── processed/.gitkeep
│   └── uploads/.gitkeep
├── docs/
│   ├── DOC-01-implementation-review.md
│   ├── DOC-01-implementation-review.txt
│   ├── architecture/DOC-01-boundaries.md
│   └── decisions/
│       ├── ADR-001-ocr-baseline.md
│       └── ADR-002-pdf-library.md
├── scripts/
│   ├── smoke_ocr.py
│   └── smoke_pdf.py
├── src/invoice_extractor/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── application/__init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── ids.py
│   │   └── logging.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── models.py
│   │   └── ports.py
│   └── infrastructure/
│       ├── __init__.py
│       ├── paddleocr_adapter.py
│       └── pymupdf_adapter.py
└── tests/
    ├── fixtures/evaluation-manifest.example.json
    ├── integration/
    │   ├── test_health.py
    │   └── test_pymupdf_adapter.py
    └── unit/
        ├── test_config.py
        ├── test_domain.py
        ├── test_ids.py
        └── test_paddleocr_adapter.py
```

## 4. Archivos creados y modificados

### Existentes preservados

- `DOC-01-analisis-y-plan.md`
- `DOC-01-analisis-y-plan.txt`

No se alteró su contenido. Ruff excluye Markdown para no reformatear el análisis aprobado.

### Creados

- raíz/configuración: `.env.example`, `.gitignore`, `.python-version`, `README.md`, `pyproject.toml`, `uv.lock`;
- documentación: límites arquitectónicos, ADR-001, ADR-002 y este informe/copia;
- dominio y aplicación: todos los módulos bajo `src/invoice_extractor`;
- smoke tests: `scripts/smoke_ocr.py`, `scripts/smoke_pdf.py`;
- pruebas: 6 archivos Python y un manifiesto JSON sintético;
- datos: tres `.gitkeep` en directorios ignorados.

No había código anterior que modificar.

## 5. Versiones exactas instaladas

### Dependencias directas

| Paquete/herramienta | Versión |
|---|---:|
| Python | 3.12.13 |
| uv | 0.12.5 |
| FastAPI | 0.140.8 |
| Pydantic | 2.13.4 |
| pydantic-settings | 2.14.2 |
| Uvicorn | 0.52.4 |
| PaddleOCR | 3.7.0 |
| PaddlePaddle CPU | 3.3.1 |
| Pillow | 12.3.0 |
| PyMuPDF | 1.28.0 |
| pytest | 9.1.1 |
| Ruff | 0.16.0 |
| HTTPX2 | 2.12.0 |

### Transitivas relevantes

| Paquete | Versión | Motivo para registrarlo |
|---|---:|---|
| PaddleX | 3.7.2 | Pipeline/model cache usado por PaddleOCR 3.7 |
| OpenCV contrib | 4.10.0.84 | Dependencia transitiva de PaddleOCR/PaddleX; no se usa directamente |
| NumPy | 2.3.5 | Runtime OCR |
| Starlette | 1.6.0 | Runtime FastAPI |
| HTTPX | 0.28.1 | Sigue en el grafo transitivo; los tests FastAPI usan HTTPX2 |

La lista completa de 83 paquetes, versiones y artefactos reproducibles está en `uv.lock`.

## 6. Configuración del entorno

`Settings` usa `pydantic-settings`, carga `.env` UTF-8, ignora variables extra y valida límites/tipos. Defaults:

```text
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8000
DATA_DIR=data
MAX_UPLOAD_SIZE_MB=15
MAX_PDF_PAGES=10
OCR_MODEL=PP-OCRv6_small
LOG_LEVEL=INFO
```

`.env.example` no contiene secretos. `.env`, `.venv`, `.tools`, caches, modelos y contenido de `data/*` están ignorados. `MAX_UPLOAD_SIZE_MB` y `MAX_PDF_PAGES` son configuración preparada, no controles funcionales: pertenecen a DOC-02/DOC-03.

## 7. Resultado de instalación y lock

Comandos de esta ejecución:

```powershell
& '<python-3.12.13>\python.exe' -m pip install uv==0.12.5 --target '.tools\uv'
& '.\.tools\uv\bin\uv.exe' lock --python '<python-3.12.13>\python.exe'
& '.\.tools\uv\bin\uv.exe' sync --frozen
& '.\.tools\uv\bin\uv.exe' lock --check
```

Resultado final:

```text
Resolved 83 packages
uv.lock válido
.venv creado con CPython 3.12.13
proyecto invoice-extractor 0.1.0 instalado en editable
```

La primera sincronización falló porque `pyproject.toml` declaraba `README.md` antes de que el archivo existiera. Se creó el README y se repitió la operación correctamente; no se relajó ninguna validación del backend de build.

## 8. Resultado FastAPI e import

Comando:

```powershell
uv run --frozen python -c "import invoice_extractor; from invoice_extractor.main import app; print(invoice_extractor.__version__); print(app.title)"
```

Resultado:

```text
0.1.0
Invoice Extractor
```

La importación no carga PaddleOCR, no descarga pesos y no abre PDFs. El modelo se inicializa de forma diferida solo en el adaptador/spike.

## 9. Resultado health check

Se verificó primero con `TestClient` y después iniciando Uvicorn real, oculto, en `127.0.0.1:8765`. Se consultó por HTTP y se detuvo exactamente el PID creado.

```text
HTTP 200
{"status":"ok","service":"invoice-extractor"}
```

El health check no depende de OCR, PDF ni filesystem.

## 10. Resultado pytest

Comando:

```powershell
uv run --frozen pytest
```

Resultado final:

```text
platform win32 -- Python 3.12.13, pytest-9.1.1
collected 9 items
9 passed in 0.58s
```

Cobertura funcional del suite:

- defaults y overrides por entorno;
- contrato exacto de `/health`;
- construcción de modelos neutrales;
- sustitución estructural de puertos con fakes;
- UUID v4 y unicidad;
- conversión de payload PaddleOCR grabado a modelos internos;
- extracción PDF sintética mediante adaptador.

No se ejecuta OCR real dentro de pytest.

## 11. Resultado Ruff

Comandos:

```powershell
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

Resultado final:

```text
All checks passed!
24 files already formatted
```

Reglas activas: `E`, `F`, `I`, `UP`, `B`, target Python 3.12 y línea de 100 caracteres. Markdown está excluido para no modificar documentos aprobados ni reformatear fences de ejemplo.

## 12. Resultado del spike PDF

Comando:

```powershell
uv run --frozen python scripts/smoke_pdf.py
```

Resultado:

```text
PDF smoke test: OK
PyMuPDF: 1.28.0
Pages: 1
Page 1 text: 'PDF SINTETICO DOC-01\nSin datos reales'
```

El PDF se creó en un directorio temporal, se leyó a través de `PyMuPDFTextExtractor` y se eliminó al terminar. No se implementó clasificación digital/escaneado.

## 13. Resultado del spike OCR

Comando:

```powershell
uv run --frozen python scripts/smoke_ocr.py
```

Resultado exitoso final:

```text
OCR smoke test: OK
Python: 3.12.13 (AMD64)
PaddleOCR: 3.7.0
PaddlePaddle: 3.3.1
OCR model: PP-OCRv6_small
Device: cpu
Model cache: C:\Users\Sewas\.paddlex
Elapsed ms (load + inference): 5956.44
Recognized lines:
  - 'FACTURA DEMO' (score=0.9995)
  - 'DOCUMENTO 12345' (score=0.9991)
```

Una segunda ejecución con pesos cacheados y:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
uv run --frozen python scripts/smoke_ocr.py
```

también fue exitosa en `4951.75 ms`, usando los modelos existentes y omitiendo el chequeo de conectividad del origen. La batería final repitió esa ruta en `4312.03 ms`. DOC-01 no desconectó físicamente el host; esa prueba debe repetirse durante el aprovisionamiento corporativo.

## 14. Modelo PaddleOCR realmente usado

El adaptador pidió explícitamente:

```text
pipeline: PP-OCRv6_small
detection: PP-OCRv6_small_det
recognition: PP-OCRv6_small_rec
device: cpu
document orientation: disabled
document unwarping: disabled
text-line orientation: disabled
MKL-DNN/oneDNN: disabled por compatibilidad Windows observada
```

Ubicaciones observadas:

```text
C:\Users\Sewas\.paddlex\official_models\PP-OCRv6_small_det
C:\Users\Sewas\.paddlex\official_models\PP-OCRv6_small_rec
```

Hashes SHA-256 de los pesos:

```text
PP-OCRv6_small_det/inference.pdiparams
5043D4CCC8D63402CCEA8FEEFCEE4DB57077431A873E78D2191836A178A492DA

PP-OCRv6_small_rec/inference.pdiparams
406E1E689C9A7FBB04178007A3FE10CF852AFE7BF8BB3BC6DBB9D532B13BD907
```

PP-OCRv5 Latin no se descargó ni probó: queda deliberadamente para el benchmark futuro. PP-StructureV3 y PaddleOCR-VL no fueron incorporados.

## 15. Problemas encontrados en Windows

### 15.1 Herramientas no disponibles en PATH

`python`, `py` y `uv` no estaban disponibles. Se reutilizó CPython 3.12.13 x64 del runtime local y se instaló uv en `.tools`, no globalmente.

### 15.2 ACL del sandbox para herramientas descargadas

La carpeta creada por el proceso con acceso de red no era atravesable desde el sandbox normal. Las operaciones posteriores de uv se ejecutaron con el mismo nivel autorizado. Esto es propio de la sesión controlada; no corresponde a una configuración del repositorio.

### 15.3 Fallo oneDNN de PaddlePaddle

Primera inferencia, con `enable_mkldnn` predeterminado:

```text
PaddleOCR inference failed:
(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support
[pir::ArrayAttribute<pir::DoubleAttribute>]
(at ..\paddle\fluid\framework\new_executor\instruction\onednn\onednn_instruction.cc:118)
```

Contexto exacto:

```text
Windows 11 10.0.26200 AMD64
Intel Core i7-10700
Python 3.12.13
PaddleOCR 3.7.0
PaddlePaddle 3.3.1
PaddleX 3.7.2
PP-OCRv6_small_det + PP-OCRv6_small_rec
CPU / oneDNN 3.6.2
```

Hipótesis: incompatibilidad del nuevo ejecutor PIR/oneDNN de PaddlePaddle 3.3.1 con un atributo array de los modelos PP-OCRv6 en Windows nativo. Solución aplicada dentro de la API soportada: `enable_mkldnn=False`. La ruta CPU regular funcionó con los mismos modelos y scores altos.

También aparece un warning informativo por ausencia de `ccache`. No se compilan extensiones del proyecto y no impide la inferencia; no se añadió otra herramienta para silenciarlo.

## 16. Decisiones tomadas

1. Dominio con biblioteca estándar (`dataclasses`, `Protocol`) y sin imports de proveedores.
2. Pydantic solo para settings/API; no se convirtió el dominio en modelos HTTP.
3. Modelo OCR explícito mediante dos nombres, no defaults silenciosos.
4. Inicialización OCR diferida y función `preload()` para aprovisionamiento futuro.
5. oneDNN desactivado y documentado; no se sustituyó PaddleOCR.
6. PyMuPDF aislado detrás de `PDFTextExtractor` y marcado provisional.
7. No usar Jinja2: DOC-01 no tiene formulario ni templates.
8. No usar OpenCV directamente: aparece solo como transitiva de PaddleOCR.
9. HTTPX2 2.12.0 para `TestClient`, siguiendo la deprecación emitida por FastAPI actual.
10. Logging JSON sin contenido de comprobantes; extras permiten `processing_id`/`elapsed_ms` cuando existan.
11. UUID v4 sin dependencia de ULID.
12. Smoke tests manuales separados del pytest rápido/offline.

## 17. Desviaciones respecto al plan

| Plan | Implementación | Razón |
|---|---|---|
| uv disponible globalmente | uv local en `.tools` para esta sesión | No existía en PATH; README conserva el flujo normal |
| Jinja2 evaluado | No instalado | No existe UI en DOC-01 |
| OpenCV solo si aporta | No dependencia directa, pero sí transitiva | PaddleOCR/PaddleX 3.7.0 la resuelve automáticamente |
| PP-OCRv6 small CPU | Implementado con oneDNN desactivado | La ruta optimizada falló en Windows; la CPU regular funciona |
| `httpx` para tests | `httpx2` directo | FastAPI/Starlette actuales deprecaban TestClient con httpx |

No hay desviaciones funcionales hacia DOC-02.

## 18. Deuda técnica y riesgos pendientes

- Revisión legal de PyMuPDF antes de distribución corporativa.
- Repetir smoke en el Windows corporativo real, no solo este host.
- Probar caché con conectividad físicamente deshabilitada y definir repositorio interno/checksums.
- Investigar si una versión futura de PaddlePaddle corrige oneDNN; medir costo de mantenerlo desactivado.
- Medir carga fría versus inferencia caliente; el smoke actual informa carga + una inferencia.
- Benchmark PP-OCRv6 small contra PP-OCRv5 Latin con corpus peruano anonimizado.
- Evaluar tamaño/tiempo del grafo de 83 paquetes; PaddleOCR introduce dependencias pesadas.
- Definir política corporativa para modelos en perfil de usuario versus ruta aprovisionada.
- Agregar CI cuando exista plataforma corporativa aprobada.
- `application` está intencionalmente vacío; DOC-02 agregará el primer caso de uso.
- Los límites de archivo/páginas solo están tipados; su enforcement pertenece a DOC-02/DOC-03.
- El `DocumentExtractor` solo es contrato; no existe extractor ni confidence.

## 19. Estado de criterios de aceptación

### Proyecto

- [x] Estructura creada.
- [x] `pyproject.toml` válido.
- [x] `uv.lock` reproducible y `uv lock --check` exitoso.
- [x] `.gitignore` protege secretos, entornos, modelos y datos.
- [x] `.env.example` creado sin secretos.

### FastAPI

- [x] Aplicación importa e inicia con Uvicorn.
- [x] `/health` responde HTTP 200 con el contrato requerido.

### Calidad

- [x] pytest: 9/9 pasan.
- [x] Ruff lint pasa.
- [x] Ruff format check pasa.

### PDF

- [x] PDF sintético creado, abierto y leído por adaptador.
- [x] Una página y texto recuperados.

### OCR

- [x] PaddleOCR carga localmente en Windows CPU.
- [x] `PP-OCRv6_small_det` y `PP-OCRv6_small_rec` cargan explícitamente.
- [x] Imagen sintética procesada.
- [x] Texto y scores mostrados.
- [x] Versiones, modelo, caché, dispositivo y tiempo registrados.
- [x] Fallo inicial diagnosticado y mitigado sin cambiar de producto.

### Arquitectura

- [x] Dominio no depende de PaddleOCR, FastAPI ni PyMuPDF.
- [x] OCR y PDF están detrás de puertos/adaptadores.
- [x] No se implementaron fases futuras.

### Documentación

- [x] README con instalación, comandos, caché, offline y limitaciones.
- [x] ADR OCR creado.
- [x] ADR PyMuPDF/licencia creado.
- [x] Informe y copia `.txt` creados.

## 20. Recomendación para iniciar DOC-02

**DOC-01 está READY.** Puede iniciarse DOC-02 una vez que el equipo acepte explícitamente:

1. mantener `enable_mkldnn=False` como workaround Windows provisional;
2. límites iniciales de 15 MiB y política de lectura streaming;
3. raíz/retención de datos locales;
4. firmas MIME permitidas y comportamiento de rechazo;
5. política de aprovisionamiento del caché OCR;
6. continuidad provisional de PyMuPDF mientras se completa la revisión legal.

DOC-02 debe implementar exclusivamente carga, validación y almacenamiento local seguro. No debería integrar aún OCR al endpoint ni iniciar extracción de campos.

## 21. Comandos de verificación final

Flujo normal documentado:

```powershell
uv sync --frozen
uv lock --check
uv run python -c "import invoice_extractor; from invoice_extractor.main import app; print(app.title)"
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python scripts/smoke_pdf.py
uv run python scripts/smoke_ocr.py
```

Para verificar uso del modelo cacheado sin chequeo del hoster:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = "True"
uv run python scripts/smoke_ocr.py
```

---

**Conclusión:** stack local verificado, arquitectura desacoplada y criterios DOC-01 satisfechos. Estado: **READY**.
