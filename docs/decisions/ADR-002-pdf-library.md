# ADR-002 — Uso provisional de PyMuPDF

- **Estado:** aceptada provisionalmente para spike; revisión legal pendiente
- **Fecha:** 2026-08-19

## Contexto

DOC-01 debe validar que Python puede crear, abrir y extraer texto de un PDF sintético. PyMuPDF ofrece wheels para Windows, lectura de texto y coordenadas, y renderizado que será útil para evaluar PDFs escaneados. Su modelo de licencia requiere revisión antes de distribución corporativa.

## Decisión

Usar PyMuPDF `1.28.0` únicamente detrás del puerto `PDFTextExtractor`, implementado por `PyMuPDFTextExtractor`. Los tipos de PyMuPDF no cruzan hacia el dominio.

El smoke abre un PDF sintético temporal. DOC-01 no clasifica PDF digital versus escaneado, no renderiza para OCR, no procesa adjuntos y no ejecuta contenido del PDF.

## Consecuencias

- La viabilidad técnica puede comprobarse sin comprometer el diseño con la biblioteca.
- Antes de distribución o uso corporativo debe decidirse si AGPL/comercial es aceptable.
- Si no se aprueba, se evaluará una combinación alternativa permitida para extracción y renderizado; el puerto evita cambiar API, dominio y futuros casos de uso.
- La seguridad de parsers y los límites de páginas/recursos pertenecen a DOC-02/DOC-03.

## Validación

`scripts/smoke_pdf.py` crea una página sintética, la lee mediante el adaptador y exige recuperar texto y cantidad de páginas. Existe además una prueba de integración rápida y offline.

## Referencias

- <https://pymupdf.readthedocs.io/en/latest/installation.html>
- <https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright>

