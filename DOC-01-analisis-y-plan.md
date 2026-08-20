# DOC-01 — Análisis y plan

**Proyecto:** extracción inteligente de comprobantes de pago  
**Fecha del análisis:** 19 de agosto de 2026  
**Estado:** propuesta para aprobación; no se implementan DOC-02 ni fases posteriores  

## 1. Resumen ejecutivo

El repositorio fue inspeccionado al inicio de DOC-01. Está vacío salvo por el directorio `.git`; no existen archivos de aplicación ni trabajo previo que deba modificarse o preservarse.

Se recomienda una aplicación modular en Python con FastAPI, separada en dominio, casos de uso e infraestructura. El núcleo no debe depender directamente de PaddleOCR, PyMuPDF, el sistema de archivos, SharePoint ni SUNAT: accederá a ellos mediante interfaces. De ese modo será posible sustituir el OCR, agregar persistencia, incorporar un extractor de Document Understanding o integrar servicios externos sin reescribir el flujo completo.

La estrategia de procesamiento será por página, no solamente por archivo:

1. Validar y almacenar el original bajo un identificador único.
2. Detectar el tipo real del contenido.
3. En PDF, intentar extracción nativa y medir la utilidad del texto de cada página.
4. Aplicar OCR únicamente a imágenes y páginas sin texto nativo suficiente.
5. Conservar texto, posiciones y puntuaciones del motor OCR.
6. Generar candidatos mediante contexto, patrones, layout y reglas del dominio peruano.
7. Resolver candidatos con validaciones y consistencia entre campos.
8. Mostrar valor, evidencia y confianza para revisión humana.

Para el primer benchmark se propone **PaddleOCR 3.7.0 en inferencia local, con PP-OCRv6 small como candidato base para CPU**, comparado contra **PP-OCRv5 Latin** sobre comprobantes peruanos anonimizados. La elección definitiva debe basarse en precisión por campo, tiempo, memoria e instalación reproducible en el Windows objetivo. PP-StructureV3 y PaddleOCR-VL no se incluirán inicialmente: aportan capacidades valiosas para documentos complejos, pero aumentan instalación, consumo y superficie de mantenimiento antes de demostrar una mejora en este caso de uso.

El extractor será híbrido y explicable. Regex será una herramienta de generación de candidatos, no el extractor completo. Cada valor incluirá procedencia, evidencias y confianza por campo. La confianza global no se presentará como probabilidad real hasta calibrarla con datos etiquetados.

## 2. Arquitectura propuesta

### 2.1 Estilo arquitectónico

Se propone una arquitectura modular inspirada en puertos y adaptadores, sin convertir el MVP en una colección innecesaria de microservicios. Será un solo proceso desplegable y un solo repositorio, con límites internos claros.

```text
Navegador / cliente API
          |
          v
FastAPI: rutas, formularios, respuestas y manejo de errores
          |
          v
Casos de uso: recibir -> procesar -> revisar -> confirmar
          |
          v
Dominio: documentos, campos, evidencias, reglas y confidence
          |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
Puerto FileStore       Puerto TextSource    Puerto FieldExtractor
          |                   |                   |
          v                   +---------+---------+
Sistema de archivos              PDF nativo | OCR Paddle

Adaptadores futuros: base de datos, SharePoint, SUNAT, autenticación,
cola de trabajos, auditoría y extractor basado en modelo/LLM.
```

Las dependencias de código apuntarán hacia el dominio y los puertos. La capa web orquesta; no contendrá heurísticas de facturas. El adaptador Paddle traducirá la salida concreta de PaddleOCR a modelos internos estables, evitando que cambios de API del proveedor se propaguen por el proyecto.

### 2.2 Componentes y responsabilidades

| Componente | Responsabilidad | No debe hacer |
|---|---|---|
| `Web/API` | Formulario, endpoints, estado de procesamiento, edición y confirmación | OCR, parsing o reglas tributarias |
| `UploadService` | Validación, lectura acotada, UUID, hash, almacenamiento seguro y metadatos | Interpretar el contenido de la factura |
| `DocumentProcessor` | Orquestar páginas, seleccionar texto nativo u OCR y consolidar resultados | Conocer detalles de FastAPI |
| `PdfTextExtractor` | Extraer texto y posiciones de PDF con PyMuPDF; renderizar páginas cuando corresponda | Decidir campos comerciales |
| `OCRService` | Convertir imagen/página en líneas o tokens con polígonos y puntuaciones | Inferir RUC, total o fecha |
| `ImagePreprocessor` | Aplicar transformaciones selectivas y trazables | Encadenar filtros indiscriminadamente |
| `TextNormalizer` | Crear una vista normalizada conservando el vínculo con el texto original | Borrar o reemplazar la evidencia original |
| `InvoiceExtractor` | Proponer, validar, puntuar y resolver candidatos por campo | Depender de PaddleOCR o del framework web |
| `ConfidenceScorer` | Combinar evidencia OCR, contexto, layout y coherencia; exponer desglose | Declarar una probabilidad calibrada sin medición |
| `ReviewService` | Aplicar correcciones, distinguir valor detectado de confirmado | Sobrescribir silenciosamente la detección |
| `FileStore` | Movimientos de estado y escritura atómica local | Usar nombres entregados por el usuario como rutas |

### 2.3 Interfaces principales

Conceptualmente, el núcleo necesita contratos pequeños:

```python
class OCRService(Protocol):
    def recognize(self, image: ImageInput) -> OCRResult: ...

class PDFTextExtractor(Protocol):
    def extract_pages(self, document: StoredDocument) -> list[PageText]: ...

class DocumentExtractor(Protocol):
    def extract(self, document: ParsedDocument) -> ExtractionResult: ...

class FileStore(Protocol):
    def save_upload(self, stream: BinaryIO, metadata: UploadMetadata) -> StoredDocument: ...
```

`InvoiceExtractor` implementará `DocumentExtractor`. Un futuro `ModelBasedInvoiceExtractor` podrá implementar el mismo contrato, o combinarse mediante un `CompositeDocumentExtractor`, sin modificar carga, almacenamiento, revisión ni API.

### 2.4 Extensibilidad prevista

- **SharePoint:** nuevo adaptador de almacenamiento/documentos detrás de un puerto; el sistema de archivos seguirá disponible para desarrollo.
- **SUNAT:** servicio de validación separado de la extracción. El extractor informa lo leído; SUNAT verifica después y nunca reemplaza evidencia sin registrarlo.
- **Base de datos:** repositorios para procesos, resultados, revisiones y auditoría.
- **Autenticación/roles:** dependencia en la capa web y políticas de aplicación, no dentro del OCR.
- **Procesamiento por lotes/cola:** el caso de uso `ProcessDocument` podrá ejecutarse en un worker conservando el mismo identificador idempotente.
- **IA/LLM opcional:** adaptador adicional con contrato, versionado de prompts/modelos y política explícita de privacidad.

## 3. Stack recomendado

### 3.1 Dependencias de ejecución

| Tecnología | Recomendación | Motivo |
|---|---|---|
| Python | **3.12.x de 64 bits** | Base conservadora para Windows y para las rutas de inferencia de Paddle; usar el último parche 3.12 disponible en el momento de instalar |
| FastAPI | **0.140.8** como versión de evaluación | API, validación de entradas e integración sencilla con plantillas; requiere Python 3.10+ |
| Pydantic | **2.13.4** | Modelos internos, API y validación; no usar compatibilidad `pydantic.v1` en código nuevo |
| pydantic-settings | Rama estable compatible con Pydantic 2, fijada en el lock | Configuración desde entorno y `.env` sin código artesanal |
| Uvicorn | Versión estable compatible, fijada en el lock | Servidor ASGI local; instalar solo extras realmente usados |
| Jinja2 | **3.1.6** | Formulario y pantalla de revisión simples |
| python-multipart | Versión estable compatible, fijada en el lock | Recepción de formularios multipart; dependencia directa necesaria para upload |
| PyMuPDF | **1.28.0** | Texto nativo, bloques/coordenadas y renderizado de páginas; dispone de wheels para Windows |
| PaddleOCR | **3.7.0** | API y modelos actuales de la rama 3.x; no copiar ejemplos de 2.x |
| PaddlePaddle CPU | **3.3.1** como baseline de compatibilidad | Runtime local; existen wheels de Windows x86-64, incluido CPython 3.12/3.13 |
| Pillow | Añadir únicamente la versión estable compatible que resuelva el lock | Decodificación segura, EXIF orientation y conversiones simples |

No se recomienda incorporar OpenCV al inicio de DOC-02. Se añadirá solo si el benchmark demuestra que corrección de perspectiva, deskew o realce selectivo mejora resultados netos. Si Pillow y las capacidades de preprocesamiento de PaddleOCR son suficientes, OpenCV sería dependencia innecesaria.

### 3.2 Dependencias de desarrollo

| Tecnología | Recomendación | Uso |
|---|---|---|
| pytest | **9.1.1** | Pruebas unitarias, integración y evaluación |
| httpx | Versión compatible fijada en el lock | Pruebas del cliente ASGI de FastAPI |
| Ruff | Versión estable fijada en el lock | Formato y lint en una sola herramienta |
| mypy o Pyright | Opcional tras el esqueleto | Comprobación estática de límites e interfaces |

### 3.3 Política de versiones

Las cifras anteriores son una línea base comprobable al 19/08/2026, no una invitación a actualizar automáticamente en producción. En DOC-01 de implementación se debe:

1. declarar rangos directos en `pyproject.toml`;
2. generar un lock reproducible con versiones exactas y hashes;
3. ejecutar una matriz mínima en el Windows y CPU reales;
4. registrar versión del paquete, runtime y modelo en cada resultado OCR;
5. actualizar dependencias en cambios separados y repetir el corpus de regresión.

El punto de mayor riesgo no es FastAPI sino la combinación Python + PaddlePaddle + PaddleOCR + hardware de Windows. Debe validarse primero mediante un spike de instalación y una inferencia pequeña antes de completar el resto del esqueleto.

## 4. Árbol de carpetas propuesto

Este es el árbol objetivo incremental. En esta ejecución solo se crean los dos documentos solicitados; el árbol de aplicación se crearía al aprobar DOC-01.

```text
.
├── README.md
├── pyproject.toml
├── lockfile                         # uv.lock o equivalente aprobado
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture/
│   └── decisions/                   # ADR breves para decisiones relevantes
├── src/
│   └── invoice_extractor/
│       ├── main.py
│       ├── api/
│       │   ├── routes_upload.py
│       │   ├── routes_review.py
│       │   ├── schemas.py
│       │   └── error_handlers.py
│       ├── application/
│       │   ├── upload_document.py
│       │   ├── process_document.py
│       │   └── review_document.py
│       ├── domain/
│       │   ├── models.py
│       │   ├── ports.py
│       │   ├── errors.py
│       │   └── confidence.py
│       ├── extraction/
│       │   ├── invoice_extractor.py
│       │   ├── candidate_generators.py
│       │   ├── candidate_resolver.py
│       │   ├── normalizer.py
│       │   └── peru_validators.py
│       ├── infrastructure/
│       │   ├── filesystem_store.py
│       │   ├── pymupdf_adapter.py
│       │   ├── paddleocr_adapter.py
│       │   └── image_preprocessor.py
│       ├── core/
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── ids.py
│       └── web/
│           ├── templates/
│           │   ├── upload.html
│           │   └── review.html
│           └── static/
│               └── styles.css
├── data/
│   ├── uploads/                     # originales inmutables, ignorados por Git
│   ├── processed/                   # derivados/resultados, ignorados por Git
│   └── failed/                      # cuarentena controlada, ignorada por Git
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── evaluation/
│   │   ├── manifests/
│   │   └── expected/
│   └── fixtures/                    # solo muestras sintéticas/anonimizadas autorizadas
└── scripts/
    └── evaluate_extraction.py
```

Se evitarán módulos genéricos como `utils.py`. Cada función tendrá una responsabilidad y un nombre de dominio. `data/` contendrá solo `.gitkeep` cuando corresponda; documentos reales, resultados y temporales no entrarán en Git.

## 5. Flujo completo del procesamiento

### 5.1 Recepción y validación

1. FastAPI recibe un único archivo multipart.
2. Se valida que haya nombre y extensión permitida: `.pdf`, `.jpg`, `.jpeg` o `.png`.
3. Se sanitiza el nombre solo como metadato de presentación; nunca se usa para construir la ruta física.
4. Se lee el stream en bloques y se corta al superar el límite. No se confía en `Content-Length`.
5. Se detecta el tipo por firma binaria y se compara con extensión y MIME declarado.
6. Se intenta decodificar la imagen o abrir el PDF de forma segura. Un archivo inválido se rechaza.
7. Se genera un UUID/ULID de procesamiento y un nombre interno independiente.
8. Se calcula SHA-256 durante la escritura. La escritura es temporal y luego atómica; no se sobrescribe un documento existente.
9. Se registra estado `received` y metadatos técnicos.

Límites iniciales propuestos para aprobación: 15 MiB por archivo, 10 páginas por PDF y límites de dimensiones/píxeles renderizados. Deben configurarse por entorno, no quedar dispersos en el código.

### 5.2 Clasificación y obtención del texto

1. Para una imagen se aplica EXIF orientation y se crea una representación decodificada.
2. Para un PDF se inspecciona cada página:
   - extraer texto nativo con palabras/bloques y coordenadas;
   - calcular señales de utilidad: cantidad de caracteres imprimibles, proporción de caracteres extraños, palabras plausibles, cobertura de página y consistencia del orden;
   - si el texto es suficiente, conservarlo sin OCR;
   - si es insuficiente, renderizar esa página con resolución limitada y enviarla a OCR.
3. Un PDF mixto puede usar texto nativo en algunas páginas y OCR en otras.
4. Se crea `ParsedDocument` con páginas, texto, tokens, cajas, método y puntuaciones.

No se debe decidir “PDF digital o escaneado” solo por la presencia de cualquier capa de texto: una imagen escaneada puede contener una capa OCR defectuosa, y un PDF digital puede incluir páginas rasterizadas.

### 5.3 Normalización y extracción

1. Conservar el texto de fuente original sin cambios.
2. Crear una vista normalizada: Unicode, espacios, saltos, mayúsculas auxiliares y variantes de separadores.
3. Mantener un mapa entre offsets/tokens normalizados y la evidencia original.
4. Generar varios candidatos por campo.
5. Puntuar candidatos por OCR, etiqueta cercana, relación espacial, formato, validador y coherencia entre campos.
6. Resolver conflictos sin inventar valores. Si no hay evidencia suficiente, devolver `null`.
7. Producir resultado estructurado y desglose de confianza.

### 5.4 Revisión

La pantalla mostrará valor detectado, confianza y alertas. La confirmación conservará por separado:

- valor detectado;
- valor corregido/confirmado;
- usuario o actor cuando exista autenticación;
- fecha de revisión;
- motivo o tipo de cambio, si se habilita;
- versión del extractor y OCR.

Aunque la persistencia definitiva está fuera del MVP inicial, el modelo debe distinguir estas entidades desde el comienzo para no perder trazabilidad.

### 5.5 Estados y errores

Estados mínimos sugeridos:

```text
received -> validated -> text_extracted -> fields_extracted -> needs_review
                                                           -> confirmed
         -> rejected
         -> failed
```

Los errores esperados tendrán códigos estables (`unsupported_type`, `size_limit`, `invalid_pdf`, `decode_failed`, `ocr_failed`, `page_limit`, etc.) y mensajes seguros para el usuario. Los detalles técnicos irán al log con el `processing_id`, nunca con el contenido completo del comprobante.

## 6. Diseño del OCR

### 6.1 Resultado interno estable

El adaptador de OCR devolverá un formato propio, independiente de Paddle:

```text
OCRResult
├── pages[]
│   ├── width, height, rotation
│   ├── lines[]
│   │   ├── text
│   │   ├── polygon
│   │   └── score
│   └── warnings[]
├── raw_text
├── engine
├── engine_version
├── model_name/model_version
├── preprocessing_profile
└── elapsed_ms
```

Esto permite usar layout aunque el extractor empiece simple y facilita pruebas con un OCR falso, resultados grabados y futuros adaptadores.

### 6.2 Modelo recomendado para evaluación

- **Baseline principal:** PaddleOCR 3.7.0 + PaddlePaddle CPU 3.3.1 + PP-OCRv6 small.
- **Competidor obligatorio:** PP-OCRv5 Latin/multilingual en la misma muestra.
- **Criterio de elección:** macro-F1 por campo crítico, exactitud de RUC/serie/número/total, CER/WER, latencia p50/p95, memoria máxima e instalación repetible.
- **Idioma:** priorizar modelos con buen desempeño en español/alfabeto latino, números y símbolos monetarios. No asumir que un modelo general más nuevo gana en tickets térmicos peruanos.

El tier `small` es el punto de partida: el tier `tiny` puede servir si el hardware es limitado y el `medium` solo si una prueba demuestra mejora material que compense costo. El modelo elegido y sus artefactos deben quedar fijados por nombre y checksum; la descarga implícita en la primera solicitud es inaceptable para una instalación controlada.

### 6.3 PP-StructureV3 y PaddleOCR-VL

| Componente | Posible valor | Decisión para MVP |
|---|---|---|
| PP-OCR | Detección y reconocimiento de texto con cajas y scores; suficiente para la mayoría de comprobantes | **Sí, baseline** |
| PP-StructureV3 | Layout, tablas, orientación, unwarping y análisis documental más amplio | Spike posterior si el layout simple falla; activar solo submódulos necesarios |
| PaddleOCR-VL | Parsing de documentos complejos con un VLM local y comprensión más amplia | No en MVP CPU; evaluar más adelante con hardware, licencia, privacidad y benchmark definidos |

PP-StructureV3 puede ser útil para tablas de detalle, comprobantes multipágina o fotos deformadas, pero su configuración completa incluye tareas irrelevantes como fórmulas, gráficos o sellos. La propia documentación advierte que funciones innecesarias pueden elevar memoria y latencia. PaddleOCR-VL es prometedor para documentos complejos y manuscritos, pero un modelo más pesado no sustituye una evaluación con facturas reales ni elimina la revisión humana.

### 6.4 Preprocesamiento adaptativo

Se conservará siempre el original. El primer intento usará la imagen con corrección de orientación y conversiones mínimas. Solo señales objetivas habilitarán perfiles adicionales:

- **Orientación:** EXIF para fotos; clasificador de orientación cuando la señal lo justifique.
- **Deskew:** para inclinación global medible, con ángulo y transformación registrados.
- **Recorte/perspectiva:** solo si se detecta un contorno de documento con alta confianza; nunca recortar información silenciosamente.
- **Escala:** elevar resolución de texto pequeño hasta un máximo de píxeles/memoria.
- **Contraste/iluminación:** corrección suave o CLAHE ante contraste bajo/sombras; comparar con el original.
- **Denoise/binarización:** último recurso para ruido o ticket térmico; pueden borrar puntos decimales y trazos finos.
- **Nitidez:** moderada y únicamente si una métrica de desenfoque lo indica.

Si se prueban varias variantes, se seleccionará por calidad OCR más reglas de plausibilidad, no solo por score medio del motor. El resultado registrará qué variante ganó. La comparación A/B debe medir campos finales, porque mejorar CER no garantiza mejorar `total` o `ruc_emisor`.

## 7. Diseño del extractor inteligente

### 7.1 Pipeline híbrido

```text
tokens/texto/layout
        |
        v
normalización no destructiva
        |
        v
generadores de candidatos por campo
  patrones + etiquetas + vecinos + zonas
        |
        v
validadores de dominio y tipo
        |
        v
coherencia entre campos/documento
        |
        v
ranking + abstención + evidencia
```

No habrá un regex único por documento. Los generadores podrán buscar, entre otros:

- valores a la derecha/debajo de etiquetas como `RUC`, `TOTAL`, `IGV`, `FECHA DE EMISIÓN`;
- patrones plausibles en zonas frecuentes del documento;
- pares serie/número cerca del tipo de comprobante;
- importes alineados en la sección de totales;
- razón social próxima al RUC emisor y encabezado;
- moneda explícita (`PEN`, `S/`, `USD`, `$`) y señales del documento.

### 7.2 Reglas y validaciones

- **RUC:** exactamente 11 dígitos después de una normalización contextual; validación del dígito verificador cuando corresponda. No corregir `O` a `0` fuera de un candidato claramente numérico.
- **Tipo:** vocabulario controlado inicialmente (`factura`, `boleta`, `nota de crédito`, `nota de débito`, `recibo`, `otro`) con posibilidad de `null`.
- **Serie/número:** preservar por separado `serie` y `numero_comprobante`; aceptar separadores visuales variados y validar el contexto.
- **Fecha:** parsear formatos plausibles con orden peruano como hipótesis, rechazar fechas imposibles y conservar la cadena fuente.
- **Moneda:** normalizar a código ISO (`PEN`, `USD`) cuando exista evidencia; un símbolo ambiguo no basta por sí solo.
- **Importes:** usar `Decimal`, nunca `float`; resolver coma/punto considerando contexto, cantidad de decimales, moneda y relaciones aritméticas.
- **Consistencia:** verificar aproximadamente `subtotal + igv = total`, admitiendo redondeos y otros conceptos. Una inconsistencia reduce confianza, pero no autoriza a recalcular y reemplazar el valor leído.

Las confusiones `0/O` y `1/I/l` se corregirán únicamente dentro de un tipo esperado y conservando la evidencia. Por ejemplo, una secuencia candidata a RUC puede permitir sustituciones limitadas y penalizadas; la razón social no debe alterarse con esa regla.

### 7.3 Candidatos y evidencia

Cada candidato incluirá como mínimo:

```text
field_name
raw_value
normalized_value
page
bounding_box / source_span
source_method               # pdf_text | ocr
ocr_score                   # null para texto PDF nativo
matched_label
validator_results[]
consistency_results[]
score_components{}
extractor_version
```

El resolver podrá abstenerse. Es preferible `null` con alerta a un valor convincente pero sin evidencia. Los candidatos no ganadores pueden persistirse en modo diagnóstico para explicar errores y mejorar el extractor, evitando mostrarlos innecesariamente al usuario final.

### 7.4 Evolución sin reconstrucción

Las reglas iniciales se organizarán por campo y por señal, no por emisor dentro de un `if/elif` gigante. Si aparecen emisores de alto volumen, se podrán añadir perfiles versionados que extiendan las reglas comunes. Más adelante, un modelo de clasificación/token labeling o un VLM podrá proponer candidatos que atraviesen los mismos validadores, scorer y revisión.

## 8. Modelo de datos inicial

Todos los campos solicitados admiten `null`. Se recomienda no usar una única clase plana para todo el ciclo; separar metadatos, detección y revisión.

```json
{
  "processing_id": "01K...",
  "status": "needs_review",
  "document": {
    "nombre_archivo": "factura-agosto.pdf",
    "tipo_archivo": "application/pdf",
    "sha256": "...",
    "size_bytes": 123456,
    "page_count": 1
  },
  "detected": {
    "tipo_comprobante": "FACTURA",
    "ruc_emisor": "20123456789",
    "razon_social_emisor": "EMPRESA SAC",
    "serie": "F001",
    "numero_comprobante": "12345",
    "fecha_emision": "2026-08-19",
    "moneda": "PEN",
    "subtotal": "100.00",
    "igv": "18.00",
    "total": "118.00",
    "texto_ocr_original": "...",
    "confidence": 0.94
  },
  "field_confidence": {
    "ruc_emisor": 0.98,
    "total": 0.96
  },
  "evidence": {},
  "warnings": [],
  "versions": {
    "pipeline": "...",
    "ocr_engine": "...",
    "ocr_model": "...",
    "extractor": "..."
  }
}
```

Notas de modelado:

- Importes se serializan como strings decimales para evitar pérdida binaria; internamente serán `Decimal`.
- `fecha_emision` se normaliza como ISO `YYYY-MM-DD`, conservando el texto fuente en evidencia.
- `tipo_archivo` debe representar el MIME detectado; se puede conservar por separado el MIME declarado.
- `texto_ocr_original` conservará, por compatibilidad con el requisito, el texto fuente sin normalizar. En PDF digital contendrá texto nativo, aunque el nombre histórico diga OCR. Conviene aprobar antes de implementar si se renombra a `texto_fuente_original` dejando un alias de salida.
- `confidence` y cada entrada de `field_confidence` también pueden ser `null` si no hay score defendible.
- Un resultado confirmado debe agregar una sección `confirmed` en vez de alterar `detected`.

## 9. Manejo de confidence

### 9.1 Principios

La puntuación debe comunicar fuerza de evidencia, no una certeza inventada. Se calculará por campo mediante componentes trazables:

- calidad OCR o calidad del texto nativo;
- proximidad y fuerza de una etiqueta semántica;
- compatibilidad del layout;
- validez de formato/dominio;
- coherencia con otros campos;
- ambigüedad frente al segundo candidato;
- transformaciones/correcciones requeridas;
- acuerdo entre variantes de preprocesamiento o motores, si se comparan.

Los pesos serán específicos por campo: el dígito verificador aporta mucho al RUC, pero no existe equivalente para razón social. El score global no será un promedio ingenuo. Puede ser una combinación ponderada de campos críticos presentes, acompañada siempre por alertas y scores individuales.

### 9.2 Calibración

Al inicio, la puntuación se llamará `evidence_score` internamente aunque la API exponga `confidence` por requisito. Con un conjunto de validación suficiente se calibrará para responder preguntas como: “de los totales con score ≥ 0.90, ¿qué proporción era correcta?”. Se usarán curvas de calibración y métricas por intervalos.

Umbrales provisionales, sujetos a datos:

| Score | Tratamiento inicial |
|---|---|
| `>= 0.90` | Mostrar como alta confianza; aún revisable |
| `0.70–0.89` | Resaltar para revisión |
| `< 0.70` | No prellenar o marcar baja confianza, según campo |
| Sin candidato defendible | `null` |

No se habilitará confirmación automática en el MVP. La tasa de cobertura y la precisión deben medirse juntas: subir precisión devolviendo todo `null` no es éxito, y subir cobertura con falsos positivos tampoco.

## 10. PDF digital vs PDF escaneado e imagen

### 10.1 PDF con texto utilizable

- Extraer palabras/bloques y coordenadas con PyMuPDF.
- Conservar orden de lectura y página.
- No aplicar OCR por defecto: evita errores nuevos, reduce CPU y mejora latencia.
- Si fuentes embebidas producen texto ilegible o faltante, marcar la página para OCR.
- No interpretar JavaScript, adjuntos ni contenido activo del PDF.

### 10.2 PDF escaneado

- Renderizar por página a una resolución objetivo configurable, con tope de dimensiones y memoria.
- Aplicar el mismo pipeline controlado que a una imagen.
- Registrar resolución, tiempo y perfil de preprocesamiento.
- Limitar páginas y abortar limpiamente ante PDF cifrado, corrupto o que exceda recursos.

### 10.3 PDF mixto

- Decidir por página.
- Para una página con texto parcial, evaluar cobertura y calidad; puede combinarse texto nativo y OCR por regiones solo en una fase posterior.
- En el MVP, elegir una fuente principal por página evita duplicados y un orden de lectura incoherente.

### 10.4 JPG/PNG/foto móvil

- Verificar firma y decodificación completa.
- Aplicar EXIF transpose.
- Controlar píxeles totales para prevenir decompression bombs.
- Detectar orientación/perspectiva solo cuando aporte evidencia.
- Mantener fondo si no existe un contorno de documento fiable.

## 11. Estrategia de pruebas

### 11.1 Pirámide de pruebas

1. **Unitarias:** normalización, parsing decimal/fecha, validación RUC, candidatos, scorer, sanitización y estados.
2. **Contrato:** el adaptador Paddle y el adaptador PDF producen el modelo interno esperado ante respuestas grabadas; esto detecta cambios de API.
3. **Integración:** upload real pequeño, validación, almacenamiento temporal, PDF nativo y OCR con fixtures autorizadas.
4. **End-to-end:** subir, procesar, revisar y confirmar usando componentes reales en un entorno controlado.
5. **Evaluación/regresión:** corpus etiquetado, separado de las pruebas funcionales rápidas.
6. **No funcionales:** límites de tamaño/páginas/píxeles, archivos truncados, concurrencia moderada, latencia y memoria.

Las pruebas normales no descargarán modelos ni requerirán red. El OCR real se marcará como suite separada; las unitarias usarán `OCRService` falso o resultados versionados.

### 11.2 Corpus y ground truth

Cada documento autorizado tendrá un ID opaco y un manifiesto independiente del nombre original:

```json
{
  "document_id": "sample-0042",
  "file": "samples/sample-0042.pdf",
  "expected": {
    "tipo_comprobante": "FACTURA",
    "ruc_emisor": "20123456789",
    "razon_social_emisor": "EMPRESA SAC",
    "serie": "F001",
    "numero_comprobante": "12345",
    "fecha_emision": "2026-08-19",
    "moneda": "PEN",
    "subtotal": "100.00",
    "igv": "18.00",
    "total": "118.00"
  },
  "tags": ["pdf_scan", "low_contrast", "one_page"]
}
```

Se almacenará además quién y cuándo etiquetó, versión del esquema y estado de doble revisión. La anonimización debe conservar la dificultad visual y relaciones válidas; tapar datos y luego evaluar OCR sobre el área tapada invalida la muestra. Los documentos reales no se incluirán en Git sin autorización y controles de acceso.

El corpus debe estratificarse por:

- tipo de archivo y origen;
- emisor/diseño;
- tipo de comprobante;
- calidad, rotación, sombra, perspectiva y resolución;
- moneda y formatos numéricos;
- PDF nativo, escaneado y mixto;
- casos con campos realmente ausentes.

La partición entrenamiento/desarrollo/prueba se hará, cuando sea posible, por emisor o plantilla y no al azar por documento, para medir generalización y evitar que documentos casi idénticos aparezcan en ambos lados. El conjunto de prueba quedará congelado.

### 11.3 Comparación esperado vs detectado

El evaluador producirá una fila por documento y campo:

```text
document_id | field | expected | detected | normalized_match |
confidence | source | error_type | latency_ms | pipeline_version
```

Se aplicarán dos comparaciones explícitas:

- **exacta normalizada:** fechas ISO, códigos de moneda, decimales canónicos, espacios controlados y mayúsculas solo donde sea semánticamente válido;
- **exacta cruda/estricta:** útil para detectar cambios de presentación y OCR.

No se usará similitud difusa para declarar correcto un RUC, serie, número, fecha o importe. Para razón social se reportará exactitud normalizada y una métrica secundaria de similitud, sin ocultar el resultado exacto.

### 11.4 Métricas

- exactitud, precisión, recall y F1 por campo;
- macro-promedio para evitar que campos fáciles oculten campos débiles;
- exactitud de documento completo;
- tasa de `null` correcta, falsos positivos y cobertura;
- CER/WER del OCR como diagnóstico, no como única métrica de negocio;
- precisión por banda de confidence y error de calibración;
- tasa de corrección humana por campo;
- latencia p50/p95 y memoria máxima por tipo de entrada;
- fallos técnicos y rechazos correctos.

Además se reportarán matrices por `tags`, por ejemplo `low_contrast`, `photo_perspective` o `pdf_native`. Cada cambio de modelo, preprocesamiento o regla deberá comparar contra el baseline y no aceptarse solo por ejemplos favorables.

### 11.5 Casos mínimos de regresión

- RUC con `0/O`, `1/I/l`, espacios y guiones espurios.
- Serie/número juntos, separados, con guion largo o salto de línea.
- `1,234.56`, `1.234,56`, `1234.56` y `1234,56`.
- `S/`, `PEN`, `US$`, `USD` y símbolo ambiguo.
- Fechas válidas, ambiguas, imposibles y futuras.
- Subtotal + IGV igual o no igual a total por redondeo/otros cargos.
- RUC del emisor y del cliente en el mismo documento.
- Varios importes que contienen la palabra `total`.
- PDF con capa de texto buena, defectuosa, vacía y mixta.
- PNG/JPEG truncado, extensión falsa, archivo sobredimensionado y demasiados píxeles.
- Páginas rotadas, perspectiva, sombra, fondo y baja resolución.
- Campos ausentes: el valor esperado y detectado debe ser `null`.

## 12. Seguridad

### 12.1 Controles desde el primer incremento funcional

- Lista positiva de extensiones y firmas admitidas.
- Comparar extensión, MIME declarado, firma y decodificación; el MIME del cliente no es confiable.
- Lectura streaming con límite efectivo, límites de páginas y de píxeles.
- Nombre físico generado por el servidor; nombre original sanitizado solo para mostrar.
- Resolver y comprobar rutas dentro de la raíz configurada; no aceptar segmentos del usuario.
- Directorio privado fuera de `static`; ningún upload debe servirse como contenido activo.
- Escritura temporal seguida de rename atómico y modo de no sobrescritura.
- Hash del original e inmutabilidad; derivados en ubicaciones separadas.
- Procesar parsers/OCR con tiempos y memoria acotados cuando la plataforma lo permita.
- Nunca ejecutar macros, JavaScript, adjuntos, comandos ni metadatos del documento.
- Escape automático de Jinja2; no renderizar texto OCR como HTML seguro.
- Formularios preparados para CSRF cuando exista sesión/autenticación; no posponer el diseño del límite.
- `.env`, documentos, logs sensibles, modelos descargados y temporales fuera de Git.
- `.env.example` sin secretos ni credenciales plausibles.
- Logs estructurados con ID, estado, duración y código de error; evitar texto OCR, RUC y montos salvo necesidad aprobada.
- Mensajes externos genéricos y excepciones técnicas solo en logs protegidos.
- Dependencias bloqueadas, revisión de vulnerabilidades y checksums de modelos.
- Política de retención y eliminación aprobada antes de usar documentos reales.

### 12.2 Aislamiento futuro

Aunque Docker está fuera del alcance, el OCR y los parsers se encapsulan detrás de puertos para poder moverlos después a un worker con aislamiento, límites de recursos y cola. Este diseño también evita bloquear el event loop: el trabajo CPU-bound debe salir del handler asíncrono, inicialmente mediante ejecución controlada y más adelante mediante worker si el volumen lo exige.

## 13. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación propuesta |
|---|---|---|
| Manuscrito | Reconocimiento muy inferior e impredecible | Fuera del baseline; etiquetar, medir por separado y exigir revisión; evaluar modelo especializado/VL solo después |
| Fotos borrosas, sombras o poca luz | Dígitos/decimales perdidos | Guía de captura, quality gate, perfiles selectivos y solicitud de nueva foto |
| Perspectiva/fondo | Orden/layout incorrecto o recorte | Corrección solo con contorno fiable; conservar original y comparar variantes |
| Muchos diseños | Reglas frágiles o sobreajuste | Candidatos genéricos, corpus diverso, split por emisor y perfiles versionados solo donde aporten |
| `0/O`, `1/I/l` | RUC, serie e importes incorrectos | Corrección contextual penalizada, validadores, evidencia y abstención |
| Separadores decimales | Montos multiplicados/divididos por 100/1000 | `Decimal`, contexto monetario, reglas de agrupación y coherencia aritmética |
| Fechas ambiguas | Día/mes invertidos | Formatos permitidos, contexto peruano explícito, fecha imposible/futura como alerta |
| Moneda ambigua | Importe correcto con moneda errónea | Buscar código/etiqueta y contexto; devolver `null` si solo hay símbolo ambiguo |
| RUC del cliente vs emisor | Selección del RUC incorrecto | Posición de encabezado, etiquetas, razón social asociada y múltiples candidatos |
| PDF con capa OCR mala | Se acepta basura como texto nativo | Score de utilidad por página y fallback a OCR |
| PDF mixto | Omisión de páginas o duplicación | Clasificación y procedencia por página |
| PDF corrupto/cifrado/malicioso | Fallo o consumo excesivo | Rechazo controlado, límites, timeouts, parsers actualizados y aislamiento futuro |
| CPU/memoria | Mala UX y baja concurrencia | Modelo small, límites, carga única del modelo, medición p95 y worker futuro |
| Instalación de PaddleOCR en Windows | Wheels incompatibles, DLL/runtime o modelos no descargados | Python 3.12 x64 limpio, spike inicial, lock, script de diagnóstico y artefactos predescargados |
| Cambios de API PaddleOCR 3.x | Rotura al actualizar | Adaptador propio, pruebas de contrato y versiones fijadas |
| Descarga inicial de modelos | Fallo offline o latencia inesperada | Aprovisionar/cachar modelos antes de servir y verificar checksum |
| Confidence no calibrada | Usuario confía demasiado | Llamarla score de evidencia internamente, revisión obligatoria y calibración con corpus |
| Datos personales/tributarios | Exposición en Git, logs o copias | Retención, control de acceso, minimización, anonimización y auditoría futura |
| Dataset pequeño/sesgado | Métrica optimista | Estratificación, conjunto congelado, nuevos emisores y revisión doble |
| Error silencioso en normalización | Evidencia alterada | Vista normalizada separada, offsets al original y tests de propiedad/regresión |

### 13.1 Riesgo específico de Windows

La ruta Python pura de PaddleOCR es viable, pero la compatibilidad debe demostrarse en el equipo objetivo. Las optimizaciones de inferencia de alto rendimiento documentadas por PaddleOCR tienen restricciones mayores y su documentación recomienda WSL/Docker para Windows; por eso no forman parte del baseline. Se comenzará con wheels CPU estándar de 64 bits y se medirán tiempos reales. WSL o Linux se considerarán únicamente si la instalación nativa no resulta reproducible o el rendimiento requerido no se alcanza.

## 14. Roadmap

| Fase | Resultado verificable | Dependencias |
|---|---|---|
| **DOC-01 — Inicialización y arquitectura** | Decisiones aprobadas, esqueleto, configuración, CI/local checks y spike OCR/PDF | Este análisis |
| **DOC-02 — Carga y validación** | Upload seguro, límites, firma/MIME, IDs y almacenamiento local inmutable | DOC-01 |
| **DOC-03 — Texto PDF** | Extracción nativa por página, métricas de utilidad y render controlado | DOC-02 |
| **DOC-04 — OCR** | Adaptador PaddleOCR 3.x, imagen/PDF escaneado, resultados con layout y benchmark | DOC-03 |
| **DOC-05 — Normalización y calidad** | Texto normalizado trazable, quality gate y preprocesamiento selectivo medido | DOC-04 |
| **DOC-06 — Extracción estructurada** | Candidatos, validadores peruanos, resolución y JSON nullable | DOC-05 |
| **DOC-07 — Confidence y revisión humana** | Score por campo, evidencias, UI de corrección y confirmación | DOC-06 |
| **DOC-08 — Persistencia y auditoría** | Base de datos, estados, correcciones, retención e historial | DOC-07 |
| **DOC-09 — SharePoint** | Adaptador, carga/consulta, reintentos e idempotencia | DOC-08 |
| **DOC-10 — Validación SUNAT** | Contrato, estados de verificación, rate limits y conciliación | DOC-08 |
| **DOC-11 — Identidad y seguridad** | Autenticación corporativa, roles, autorización y auditoría completa | Requisitos corporativos |
| **DOC-12 — Producción y escala** | Worker/cola si aplica, observabilidad, backups, despliegue y runbooks | Métricas de uso |

La evaluación no es una fase aislada al final: desde DOC-01 se define el formato de fixtures y desde DOC-03 cada incremento agrega casos al corpus. SharePoint y SUNAT se mantienen fuera hasta contar con resultados revisables y persistencia trazable.

## 15. Qué se implementaría exactamente en DOC-01

Una vez aprobadas las decisiones de la sección 16, DOC-01 de implementación incluiría únicamente:

1. Inicializar estructura `src/` y `tests/` sin lógica de fases futuras.
2. Crear `pyproject.toml`, entorno Python 3.12 y lock reproducible.
3. Crear `.gitignore`, `.env.example`, configuración tipada y README de instalación.
4. Definir modelos de dominio y protocolos mínimos, todos sin dependencias concretas innecesarias.
5. Crear una aplicación FastAPI con health check, sin upload funcional.
6. Configurar pytest y pruebas de arranque/configuración.
7. Ejecutar un spike técnico aislado:
   - instalar PaddlePaddle/PaddleOCR en Windows CPU;
   - cargar explícitamente el modelo candidato;
   - ejecutar una imagen sintética no sensible;
   - abrir un PDF sintético con PyMuPDF;
   - registrar versiones, memoria y tiempo aproximado.
8. Documentar comandos reproducibles y una ADR para la selección provisional de OCR.
9. Preparar el esquema de manifiesto de evaluación, sin incorporar comprobantes reales.

No incluiría carga de documentos, almacenamiento real, OCR integrado en endpoint, extracción de campos, UI de revisión, SharePoint, SUNAT, base de datos, Docker ni autenticación. Esos resultados pertenecen a DOC-02 y posteriores.

## 16. Decisiones que deben aprobarse antes de comenzar la implementación

### Bloqueantes para DOC-01

1. **Plataforma objetivo:** versión de Windows, CPU, RAM y si el proceso puede descargar modelos durante la instalación (nunca durante la primera petición).
2. **Baseline de runtime:** aprobar Python 3.12 x64, PaddleOCR 3.7.0 y PaddlePaddle CPU 3.3.1 para el spike.
3. **Modelo a comparar:** aprobar PP-OCRv6 small como baseline y PP-OCRv5 Latin como competidor.
4. **Gestor/lock:** aprobar `uv` con `pyproject.toml` y `uv.lock`, o indicar estándar corporativo distinto.
5. **Licencias:** confirmar revisión corporativa de Apache-2.0 (Paddle/PaddleOCR), AGPL/comercial aplicable a PyMuPDF y demás dependencias antes de distribución. En particular, la licencia de PyMuPDF requiere decisión consciente; si no es aceptable, evaluar `pypdf` + renderizador permitido.
6. **Acceso a red/modelos:** definir repositorio interno, caché y checksum para pesos.

### Bloqueantes antes de DOC-02/DOC-04

7. **Límites:** aprobar o ajustar 15 MiB, 10 páginas y máximo de píxeles/render.
8. **Retención local:** tiempo de conservación de originales, procesados y fallidos; responsable de eliminación.
9. **Dataset:** fuente, autorización, anonimización, ubicación protegida y responsables de ground truth.
10. **Campos:** confirmar catálogo de `tipo_comprobante`, códigos de moneda, separación serie/número y alias `texto_ocr_original` versus `texto_fuente_original`.
11. **Política de revisión:** campos obligatorios para confirmar y comportamiento de baja confianza/null.
12. **Rendimiento esperado:** latencia aceptable por página, volumen diario y concurrencia aproximada.
13. **PDF:** comportamiento frente a cifrado, demasiadas páginas y documentos mixtos.
14. **Privacidad/logs:** datos permitidos en logs y quién puede acceder a archivos locales.

## 17. Recomendación final

Aprobar primero el spike de compatibilidad Windows y el protocolo de evaluación. Si la instalación estándar de PP-OCRv6 small es reproducible y supera al candidato PP-OCRv5 en campos críticos con costo aceptable, se fija como baseline. Después se inicia DOC-02 con validación y almacenamiento seguro. No conviene construir el extractor hasta que texto nativo, OCR y dataset entreguen evidencia estable y medible.

## 18. Fuentes técnicas consultadas

Consultadas el 19/08/2026. Se priorizaron documentación oficial, repositorios de los proyectos y registros oficiales de paquetes.

- PaddleOCR, guía rápida 3.x y requisito de PaddlePaddle 3.0+: <https://paddlepaddle.github.io/PaddleOCR/main/en/quick_start.html>
- PaddleOCR, repositorio y release 3.7.0/PP-OCRv6: <https://github.com/PaddlePaddle/PaddleOCR>
- PaddleOCR en PyPI, versión 3.7.0: <https://pypi.org/project/paddleocr/>
- PaddlePaddle en PyPI, wheels 3.3.1 para Windows: <https://pypi.org/project/paddlepaddle/>
- PP-StructureV3, configuración, submódulos y consideraciones de recursos: <https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/pipeline_usage/PP-StructureV3.html>
- PaddleOCR, inferencia de alto rendimiento y restricciones en Windows: <https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/deployment/high_performance_inference.html>
- FastAPI en PyPI, versión y requisito de Python: <https://pypi.org/project/fastapi/>
- Pydantic en PyPI, versión 2.13.4: <https://pypi.org/project/pydantic/>
- Jinja2 en PyPI, versión 3.1.6: <https://pypi.org/project/Jinja2/>
- PyMuPDF, instalación y plataformas soportadas: <https://pymupdf.readthedocs.io/en/latest/installation.html>
- PyMuPDF, changelog 1.28.0: <https://pymupdf.readthedocs.io/en/latest/changes.html>
- pytest en PyPI, versión 9.1.1: <https://pypi.org/project/pytest/>

---

**Fin de DOC-01 — Análisis y plan.**
