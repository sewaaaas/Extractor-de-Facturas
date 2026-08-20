# Límites arquitectónicos de DOC-01

## Objetivo

Mantener un monolito modular pequeño cuyos proveedores puedan sustituirse sin cambiar el dominio ni la API.

## Regla de dependencias

```text
api ---------> core
 |              |
 v              v
domain <--- infrastructure
  ^
  |
application (vacío hasta que exista un caso de uso real)
```

- `domain` solo depende de la biblioteca estándar.
- `core.config` puede depender de Pydantic Settings.
- `api` puede depender de FastAPI/Pydantic y del dominio.
- `infrastructure` implementa puertos y contiene imports de PaddleOCR/PyMuPDF.
- `application` contendrá orquestación desde DOC-02; no se anticipa lógica inexistente.

## Contratos presentes

- `OCRService.recognize(ImageInput) -> OCRResult`
- `PDFTextExtractor.extract_pages(StoredDocument) -> list[PageText]`
- `DocumentExtractor.extract(ParsedDocument) -> ExtractionResult`

`DocumentExtractor` es solo un límite arquitectónico. DOC-01 no implementa `InvoiceExtractor`, reglas, regex ni confidence.

## Decisiones de alcance

- `GET /health` no consulta OCR, filesystem ni PDF. Es un indicador de disponibilidad del proceso.
- Los scripts smoke son herramientas manuales y pueden imprimir; el código de aplicación usa logging.
- El modelo OCR se carga de forma diferida para que importar/iniciar FastAPI sea rápido y offline.
- Los directorios `data/` solo tienen marcadores. No existe upload ni persistencia.
- El PDF sintético se crea en un temporal y se elimina al terminar el spike.
- La imagen OCR sintética se crea en un temporal y se elimina al terminar el spike.

## Extensiones posteriores

DOC-02 añadirá carga/validación/almacenamiento. DOC-03 definirá calidad de texto PDF. DOC-04 integrará OCR en un caso de uso. Esos cambios consumirán los puertos presentes y no estructuras internas de los SDK.

