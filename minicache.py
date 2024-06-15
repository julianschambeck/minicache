import time
import sqlite3
from typing import Union
from fastapi import FastAPI

DB = "disk.db"

class Minicache:
    _storage = {"name": "Jake"}

    def set(self, k, v):
        self._storage[k] = v
    def get(self, k): return self._storage[k]

minicache = Minicache()

app = FastAPI()
@app.get("/get/{key}")
def get_val(key: str):
    t0 = time.time()
    val = minicache.get(key)
    t1 = time.time()
    print(f"Time taken: {t1 - t0}") # 0.0000003099 3 zehn millionstel
    return {"val": val}

@app.get("/get_from_disk/{key}")
def get_val_from_disk(key: str):
    t0 = time.time()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    res = cur.execute("SELECT * FROM disk WHERE key ='name'")
    print(res.fetchone())
    t1 = time.time()
    print(f"Time taken: {t1 - t0}") # 0.00040 4 zehn tausendstel
    return {"val_from_disk": "tmp"}

if __name__ == "__main__":
    print("something")