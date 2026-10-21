from typing import List, Union
from chromadb.utils import embedding_functions

# Instantiate the local ONNX embedding model (all-MiniLM-L6-v2)
_embedding_fn = None

def get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    return _embedding_fn

def get_embedding(text: str) -> List[float]:
    """Generates real 384-dimensional dense semantic embedding using all-MiniLM-L6-v2."""
    if not text or not text.strip():
        text = "empty"
    fn = get_embedding_function()
    vectors = fn([text])
    return [float(x) for x in vectors[0]]

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch generate real dense embeddings for a list of strings."""
    if not texts:
        return []
    clean_texts = [t if t and t.strip() else "empty" for t in texts]
    fn = get_embedding_function()
    vectors = fn(clean_texts)
    return [[float(x) for x in v] for v in vectors]
