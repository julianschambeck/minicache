import os
import io
import hashlib
import time
from datetime import datetime

from typing import Annotated
from fastapi import FastAPI, Form, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

DB = "./disk.db"
FILES = "file-storage"
TTL = 60*3 # time to live in seconds
minicache = {}
app = FastAPI()

# super simple cache policy, just use filename and host
def hash_req(filename, host):
    return hashlib.md5(bytes(f"{filename},{host}", "utf-8")).hexdigest()
def ttl_expired(key):
    t0 = int(datetime.fromisoformat(minicache[key]["timestamp"]).timestamp())
    return int(time.time()) - t0 > TTL

# host client site via webserver to avoid CORS
app.mount("/client", StaticFiles(directory="client"), name="client")
@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()], req: Request):
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)
    key = hash_req(filename, req.headers.get("host"))
    minicache[key] = {"data": bytes(file), "timestamp": datetime.now().isoformat()}
    return { "msg": "file uploaded"}

def iterfile(key):
    with io.BytesIO(minicache[key]["data"]) as fp:
        yield from fp

@app.get("/file/{filename}")
def download_file(filename: str, req: Request):
    key = hash_req(filename, req.headers.get("host"))
    if key in minicache and not ttl_expired(key): # cache hit
        print("CACHE HIT")
        minicache[key]["timestamp"] = datetime.now().isoformat()
        return StreamingResponse(iterfile(key), media_type="application/pdf")
    print("READ FROM FS")
    with open(FILES + "/" + filename, "r+b") as fp:
        file_bytes = fp.read()
    minicache[key] = {"data": file_bytes, "timestamp": datetime.now().isoformat()}  # cache for next time
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")