import hashlib
import re


def chunk_document(document: dict, chunk_words: int = 180, overlap_words: int = 30) -> list[dict]:
    """Split markdown into stable overlapping word windows with inherited ACL metadata."""
    words = re.findall(r"\S+", document["text"])
    if not words:
        return []
    step = max(1, chunk_words - overlap_words)
    output = []
    for start in range(0, len(words), step):
        text = " ".join(words[start:start + chunk_words])
        if not text:
            break
        digest = hashlib.sha256(f"{document['document_id']}:{start}:{text}".encode()).hexdigest()[:16]
        output.append({"chunk_id": f"{document['document_id']}:{digest}",
                       "document_id": document["document_id"], "title": document["title"],
                       "access_level": document["access_level"], "text": text})
        if start + chunk_words >= len(words):
            break
    return output
