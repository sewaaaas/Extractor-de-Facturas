from uuid import UUID

from invoice_extractor.core.ids import new_processing_id


def test_processing_id_is_a_unique_uuid() -> None:
    first = new_processing_id()
    second = new_processing_id()

    assert UUID(first).version == 4
    assert first != second
