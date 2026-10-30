"""Retrieval with LlamaIndex + a local Chroma vector store + local FastEmbed embeddings.

Retrieval needs no API key. Answering uses llm.ask() with the model you pick.

    .venv/bin/python rag.py index docs/                              # (re)build the index from a folder
    .venv/bin/python rag.py ask "When does demurrage start?"         # top passages + answer (if a key is set)
    .venv/bin/python rag.py ask "..." --model haiku-5.5
"""
import sys

import chromadb
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from llm import ask, has_key

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=".models")
Settings.node_parser = SentenceSplitter(chunk_size=256, chunk_overlap=32)

_collection = chromadb.PersistentClient(path=".chroma").get_or_create_collection("docs")
_store = ChromaVectorStore(chroma_collection=_collection)


def build(folder: str) -> int:
    """Index every file in a folder (md, txt, pdf, csv, docx...). Replaces the previous index."""
    for doc_id in set(m["ref_doc_id"] for m in _collection.get()["metadatas"] or []):
        _store.delete(doc_id)
    docs = SimpleDirectoryReader(folder, recursive=True).load_data()
    VectorStoreIndex.from_documents(docs, storage_context=StorageContext.from_defaults(vector_store=_store))
    return _collection.count()


def retrieve(question: str, k: int = 4):
    index = VectorStoreIndex.from_vector_store(_store)
    return index.as_retriever(similarity_top_k=k).retrieve(question)


def answer(question: str, model_key: str = "sonnet-5.5", k: int = 4) -> tuple[str, list]:
    hits = retrieve(question, k)
    context = "\n\n".join(f"[{i + 1}] ({h.metadata.get('file_name')}) {h.get_content()}" for i, h in enumerate(hits))
    if not has_key(model_key):
        return "(no API key for the answer model; showing retrieval only)", hits
    system = ("Answer only from the numbered sources. Cite them like [1]. "
              "If the sources do not contain the answer, say so instead of guessing.")
    return ask(model_key, f"Sources:\n{context}\n\nQuestion: {question}", system=system, effort="low"), hits


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "index":
        print(f"Indexed {build(sys.argv[2] if len(sys.argv) > 2 else 'docs')} chunks into .chroma")
    elif cmd == "ask":
        model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "sonnet-5.5"
        text, hits = answer(sys.argv[2], model)
        for i, h in enumerate(hits):
            print(f"[{i + 1}] {h.score:.2f} {h.metadata.get('file_name')}: {h.get_content()[:110]}...")
        print(f"\n{text}")
    else:
        print(__doc__)
