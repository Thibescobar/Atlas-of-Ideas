from atlas_of_ideas.ingest import chunk_document
from atlas_of_ideas.models import SourceDocument


def test_chunk_document_produces_passages():
    doc = SourceDocument(
        id="demo",
        title="Demo",
        domain="science",
        text="a" * 1200,
    )

    passages = chunk_document(doc, chunk_size=500, overlap=50)

    assert len(passages) >= 2
    assert passages[0].document_id == "demo"
