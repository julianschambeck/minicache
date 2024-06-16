import os
from typing import Annotated
from fastapi import FastAPI, Form, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB = "./disk.db"
FILES = "file-storage"

minicache = {}

app = FastAPI()
# simulate client
app.mount("/client", StaticFiles(directory="client"), name="client")
@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()]):
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)
    print(type(file))
    return { "msg": "file uploaded"}

@app.get("/file/{filename}")
def download_file(filename: str):
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")