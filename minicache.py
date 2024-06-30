import os
import io
import hashlib
from datetime import datetime
from functools import reduce

from typing import Annotated
from fastapi import FastAPI, Form, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

DB = "./disk.db"
FILES = "file-storage"

# super simple cache policy, just use filename and host
def hash_key(filename, host): return hashlib.md5(bytes(f"{filename},{host}", "utf-8")).hexdigest()

class Minicache:

    # simple in-memory key value store
    _store = {}
    def __init__(self, ttl=30*60, memory_max=5*2**20): # time to live in seconds, mem max in bytes, default to 5 MiB (Mebibyte)
        self.ttl = ttl
        self.memory_max = memory_max

    def get(self, key):
        # cache misses 
        if key in self._store and self.is_ttl_up(key):
            self.delete(key)
            return None
        if key not in self._store: return None

        # cache hit
        return self._store[key]

    def put(self, key, value):
        self._store[key] = { "data": value, "timestamp": datetime.now().isoformat() }
        # memory usage in MiB
        mem_usage = self.memory_usage()
        print(f"memory usage after PUT {mem_usage / 2**20:.2f} MiB")
        if mem_usage > self.memory_max:
            print("more than designated memory, evicting keys now")
            self.evict_keys(mem_usage)
            mem_usage = self.memory_usage()
            print(f"memory usage after evicting oldest keys {(mem_usage / 2**20):.2f} MiB")

    def delete(self, key):
        if key in self._store: del self._store[key]

    def values(self): return self._store.values()

    def keys(self): return self._store.keys()

    def evict_keys(self, mem_usage):
        # key-values from oldest to newest
        kvs = sorted(self._store.items(), key=lambda item: datetime.fromisoformat(item[1]["timestamp"]))
        for k, v in kvs:
            if mem_usage <= self.memory_max: return
            self.delete(k)
            mem_usage -= len(v["data"])

    def is_ttl_up(self, key):
        if key not in self._store: return False
        t0 = datetime.fromisoformat(self._store[key]["timestamp"]).timestamp()
        return (datetime.now().timestamp() - t0) > self.ttl

    def memory_usage(self): return reduce(lambda acc, value: acc + len(value["data"]), self.values(), 0)

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
    key = hash_key(filename, req.headers.get("host"))
    if (file_bytes:=mini.get(key)) is not None:
        print("CACHE HIT")
        return StreamingResponse(iterfile(file_bytes), media_type="application/pdf")

    # read from server file system, add to cache for next time 
    print("CACHE MISS, READ FROM FS INSTEAD")
    with open(FILES + "/" + filename, "r+b") as f:
        mini.put(key, f.read())
    return FileResponse(FILES + "/" + filename, filename=filename)

if __name__ == "__main__":
    print("nothing yet")
