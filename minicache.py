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
TTL = 5  # time to live in seconds
CACHE_MEMORY_MAX = 1.5 * 2**20 # 5 MiB (Mebibyte) in bytes

class Minicache:

    # simple in-memory key value store
    _store = {}
    def __init__(self):
        pass

    def get(self, key):
        # cache misses 
        if key in self._store and self.is_ttl_up(key):
            del self._store[key]
            return None
        if key not in self._store: return None

        # cache hit
        return self._store[key]

    def put(self, key, value):
        self._store[key] = { "data": value, "timestamp": datetime.now().isoformat() }
        # memory usage in MiB
        mem_usage = reduce(lambda acc, val: acc + len(val["data"]), self.values(), 0)
        print(f"memory usage after PUT {mem_usage / 2**20:.2f} MiB")
        print("elements now", len(self.values()))
        if mem_usage > CACHE_MEMORY_MAX:
            print("more than designated memory, evict keys now!")
            self.evict_keys(mem_usage)
            mem_usage = reduce(lambda acc, val: acc + len(val["data"]), self.values(), 0)
            print(f"memory usage after evicting oldest keys {(mem_usage / 2**20):.2f} MiB")
            print("elements now", len(self.values()))

    def delete(self, key):
        if key in self._store: del self._store[key]

    def values(self):
        return self._store.values()

    def keys(self):
        return self._store.keys()

    def evict_keys(self, mem_usage):
        # key-values from oldest to newest
        kvs = sorted(self._store.items(), key=lambda item: datetime.fromisoformat(item[1]["timestamp"]))
        for k, v in kvs:
            if mem_usage <= CACHE_MEMORY_MAX: return
            del self._store[k]
            mem_usage -= len(v["data"])

    def is_ttl_up(self, key):
        if key not in self._store: return False
        t0 = int(datetime.fromisoformat(self._store[key]["timestamp"]).timestamp())
        return int(time.time()) - t0 > TTL


# super simple cache policy, just use filename and host
def hash_key(filename, host):
    return hashlib.md5(bytes(f"{filename},{host}", "utf-8")).hexdigest()
def cache_bytes_size():
    val_sizes = map(lambda x: len(x["data"]), list(minicache.values()))
    total_size = reduce(lambda size, cur: size+cur, val_sizes)
    return total_size 

app = FastAPI()
# host client site via webserver to avoid CORS
app.mount("/client", StaticFiles(directory="client"), name="client")

mini = Minicache()

@app.post("/upload")
def upload_file(file: Annotated[bytes, File()], filename: Annotated[str, Form()], req: Request):
    # save file on server file system
    PATH = f"{FILES}/{filename}"
    dir = os.path.dirname(PATH)
    if not os.path.exists(dir): os.makedirs(dir)
    with open(PATH, "wb") as fp:
        fp.write(file)

    # cache for next GET. for now, store files (as bytes) only
    mini.put(hash_key(filename, req.headers.get("host")), bytes(file))
    print(f"{filename} file size is {(len(bytes(file)) / (1 << 20)):.2f} MiB")
    return {"message": "file uploaded"}

def iterfile(file_bytes):
    with io.BytesIO(file_bytes) as f:
        yield from f

@app.get("/file/{filename}")
def download_file(filename: str, req: Request):
    if (file_bytes:=mini.get(hash_key(filename, req.headers.get("host")))) is not None:
        print("CACHE HIT")
        return StreamingResponse(iterfile(file_bytes), media_type="application/pdf")

    # read from server file system, add to cache for next time 
    print("READ FROM FS")
    with open(FILES + "/" + filename, "r+b") as f:
        mini.put(key, f.read())
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")
