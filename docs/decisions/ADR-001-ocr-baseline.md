# ADR-001 — Baseline OCR local

- **Estado:** aceptada provisionalmente para spike
- **Fecha:** 2026-08-19
- **Decisores:** equipo del proyecto, sujeto al benchmark posterior

## Contexto

El proyecto necesita demostrar OCR local en Windows x64 y CPU, sin APIs cloud ni costo por documento. Los comprobantes futuros tendrán texto latino, números, símbolos y calidad variable. La arquitectura debe permitir cambiar el motor.

PaddleOCR 3.7.0 publica PP-OCRv6 en tiers tiny, small y medium. `small` apunta a escritorio/móvil y equilibra precisión y costo. El análisis aprobado exige compararlo posteriormente con PP-OCRv5 Latin sobre comprobantes peruanos anonimizados.

## Decisión

Usar para DOC-01:

- PaddleOCR `3.7.0`;
- PaddlePaddle CPU `3.3.1`;
- Python `3.12.x` x64;
- dispositivo explícito `cpu`;
- baseline lógico `PP-OCRv6_small`;
- detector explícito `PP-OCRv6_small_det`;
- reconocedor explícito `PP-OCRv6_small_rec`;
- orientación de documento, unwarping y orientación de línea desactivados en el smoke.
- MKL-DNN/oneDNN desactivado en Windows para evitar un fallo del ejecutor PIR observado con PaddlePaddle 3.3.1 y PP-OCRv6 small.

La aplicación accede al motor mediante `OCRService`. `PaddleOCRAdapter` traduce texto, score y polígonos a `OCRResult`/`OCRLine`, de modo que no expone objetos del SDK.

PP-OCRv5 Latin queda como candidato obligatorio del benchmark de DOC-04. La decisión de DOC-01 no lo declara peor ni fija definitivamente PP-OCRv6.

## Alternativas no adoptadas ahora

### PP-StructureV3

Ofrece layout, tablas, orientación y unwarping, pero carga submódulos y complejidad que DOC-01 no necesita. Se evaluará si los comprobantes reales demuestran que layout OCR básico y preprocesamiento selectivo son insuficientes.

### PaddleOCR-VL

Puede aportar comprensión de documentos complejos, pero aumenta requisitos y superficie de despliegue. No se justificó para el baseline CPU ni existe aún un corpus que pruebe su mejora en campos de negocio.

### Servicios cloud

Azure AI, AI Builder, Google Vision, AWS Textract, OpenAI y otros servicios externos quedan fuera del MVP por alcance, costo y privacidad.

## Consecuencias

- El primer smoke requiere red para descargar dos modelos; deben precargarse durante aprovisionamiento.
- Los modelos no se agregan a Git y deben verificarse/cacharse en cada entorno.
- La inferencia CPU puede ser lenta al cargar el proceso; se medirá por separado carga e inferencias calientes en DOC-04.
- Desactivar oneDNN reduce opciones de aceleración, pero mantiene el mismo modelo y evita sustituir silenciosamente el motor; debe reevaluarse cuando PaddlePaddle corrija la compatibilidad.
- PaddleOCR trae dependencias transitivas relevantes, incluido OpenCV mediante PaddleX; no se usa OpenCV directamente en código DOC-01.
- Las actualizaciones requieren pruebas de contrato y smoke test porque la API 3.x puede evolucionar.
- Un motor futuro podrá reemplazar PaddleOCR implementando `OCRService`.

## Validación

`scripts/smoke_ocr.py` genera una imagen no sensible, carga los modelos por nombre, ejecuta inferencia local CPU, imprime versiones/modelo/tiempo/scores y falla si no obtiene texto.

## Referencias

- <https://github.com/PaddlePaddle/PaddleOCR>
- <https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv6/PP-OCRv6.en.md>
- <https://paddlepaddle.github.io/PaddleOCR/main/en/quick_start.html>
