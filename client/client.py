import requests
import pandas as pd

import time
import os
from enum import Enum

BASE_URL = "http://localhost:8000"
FILE = "alexnet.pdf"
STOPWATCH = "stopwatch.csv"

class DataSource(Enum):
    CACHE = "cache"
    FS = "fs"
    DB = "db"
def log_time(src, time):
    data = [{ "src": src, "time": time, "filename": FILE }]
    df = pd.DataFrame(data, columns=['src', 'time', 'filename'])
    if os.path.exists(STOPWATCH): df.to_csv(STOPWATCH, mode='a', header=False, index=False)
    else: df.to_csv(STOPWATCH, mode='w', header=True, index=False)

for i in range(0, 20):
    files = { "file": (FILE, open(FILE, "rb")) }
    # upload file for the first time. sent file name as separate formdata param
    resp = requests.post(f"{BASE_URL}/upload", files=files, data={ "filename": FILE })
    assert resp.status_code == 200, "file upload failed"

    # TIME GET FROM CACHE
    t0 = time.time()
    resp = requests.get(f"{BASE_URL}/file/{FILE}")
    content = resp.content
    t1 = time.time()
    assert resp.status_code == 200, "could not download file"
    log_time(DataSource.CACHE.value, f"{(t1 - t0):.3f}")
    print(f"from cache took {(t1 - t0):.3f}")

    # TIME GET FROM SERVER FILE SYSTEM
    time.sleep(2) # sleep so that ttl for cache entry runs out
    t0 = time.time()
    resp = requests.get(f"{BASE_URL}/file/{FILE}")
    content = resp.content
    t1 = time.time()
    log_time(DataSource.FS.value, f"{(t1 - t0):.3f}")
    print(f"from fs took {(t1 - t0):.3f}")

    # TIME GET FROM SERVER SQLITE DB

    # upload to db first
    resp = requests.post(f"{BASE_URL}/upload/db", files=files, data={ "filename": FILE })
    assert resp.status_code == 200, "upload to db on server failed"

    t0 = time.time()
    resp = requests.get(f"{BASE_URL}/file/db/{FILE}")
    content = resp.content
    t1 = time.time()
    log_time(DataSource.DB.value, f"{(t1 - t0):.3f}")
    print(f"from db took {(t1 - t0):.3f}")

