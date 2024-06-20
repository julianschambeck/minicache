import os
import io
import hashlib
from typing import Annotated
from fastapi import FastAPI, Form, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

DB = "./disk.db"
FILES = "file-storage"
minicache = {}
app = FastAPI()

# super simple cache policy, just use filename and host
def hash_req(filename, host):
    return hashlib.md5(bytes(f"{filename},{host}", "utf-8")).hexdigest()

# host client site via webserver to avoid CORS
app.mount("/client", StaticFiles(directory="client"), name="client")
@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()], req: Request):
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)
    if not filename in minicache:
        host = req.headers.get("host")
        minicache[hash_req(filename, host)] = bytes(file)
    return { "msg": "file uploaded"}

def iterfile(file_key):
    with io.BytesIO(minicache[file_key]) as fp:
        yield from fp

@app.get("/file/{filename}")
def download_file(filename: str, req: Request):
    key = hash_req(filename, req.headers.get("host"))
    if key in minicache:
        print("CACHE HIT")
        return StreamingResponse(iterfile(key), media_type="application/pdf")
    print("READ FROM FS")
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")