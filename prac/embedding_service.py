from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI()

# load once (cached after first run)
model = SentenceTransformer("all-MiniLM-L6-v2")

class Input(BaseModel):
    texts: list[str]

@app.post("/embed")
def embed(input: Input):
    embeddings = model.encode(input.texts).tolist()
    return {"embeddings": embeddings}
