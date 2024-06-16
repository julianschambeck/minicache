import os
from typing import Annotated
from fastapi import FastAPI, Form, File

DB = "./disk.db"
FILES = "file-storage"

class Minicache:
    _storage = {}

    def set(self, k, v):
        self._storage[k] = v
    def get(self, k): return self._storage[k]

minicache = Minicache()

app = FastAPI()

@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()]):
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)
    return { "msg": "success"}

if __name__ == "__main__":
    print("nothing yet")