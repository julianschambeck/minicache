import os
import io
import hashlib
import time
from datetime import datetime
from functools import reduce

from typing import Annotated
from fastapi import FastAPI, Form, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

DB = "./disk.db"
FILES = "file-storage"
TTL = 60 * 5 # time to live in seconds
CACHE_MEMORY_MAX = 5 * 2**20 # 5 MiB
minicache = {}

app = FastAPI()
# host client site via webserver to avoid CORS
app.mount("/client", StaticFiles(directory="client"), name="client")

# super simple cache policy, just use filename and host
def hash_key(filename, host):
    return hashlib.md5(bytes(f"{filename},{host}", "utf-8")).hexdigest()
def ttl_up(key):
    if key not in minicache: return None
    t0 = int(datetime.fromisoformat(minicache[key]["timestamp"]).timestamp())
    return int(time.time()) - t0 > TTL
def cache_bytes_size():
    val_sizes = map(lambda x: len(x["data"]), list(minicache.values()))
    total_size = reduce(lambda size, cur: size+cur, val_sizes)
    return total_size 
def evict_keys():
    pass

@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()], req: Request):
    # write to file system
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)

    # cache for next time
    minicache[hash_key(filename, req.headers.get("host"))] = {"data": bytes(file), "timestamp": datetime.now().isoformat()}
    print(f"{filename} size is {(len(bytes(file)) / (1 << 20)):.2f} MiB")
    return {"msg": "file uploaded"}

def iterfile(key):
    with io.BytesIO(minicache[key]["data"]) as fp:
        yield from fp

@app.get("/file/{filename}")
def download_file(filename: str, req: Request):
    if not ttl_up(key:=hash_key(filename, req.headers.get("host"))) and ttl_up(key) is not None: # cache hit 
        print("CACHE HIT")
        return StreamingResponse(iterfile(key), media_type="application/pdf")
    elif ttl_up(key): del minicache[key]

    # read from source, add to cache again 
    print("READ FROM FS")
    with open(FILES + "/" + filename, "r+b") as f:
        f_bytes = f.read()
    minicache[key] = {"data": f_bytes, "timestamp": datetime.now().isoformat()}
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")