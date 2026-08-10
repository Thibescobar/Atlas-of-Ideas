from .models import Passage, SourceDocument


def chunk_document(document: SourceDocument, chunk_size: int = 900, overlap: int = 120) -> list[Passage]:
    text = document.text.strip()
    passages: list[Passage] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            passages.append(
                Passage(
                    id=f"{document.id}:p{index}",
                    workspace_id=document.workspace_id,
                    document_id=document.id,
                    text=chunk,
                    start_char=start,
                    end_char=end,
                )
            )

        if end == len(text):
            break

        start = max(end - overlap, start + 1)
        index += 1

    return passages
