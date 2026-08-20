"""Generación de identificadores opacos de procesamiento."""

from uuid import uuid4


def new_processing_id() -> str:
    """Crea un UUID aleatorio sin introducir una dependencia adicional."""

    return str(uuid4())
