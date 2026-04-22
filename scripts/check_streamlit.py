import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

PORT = 8765

proc = subprocess.Popen(
    [
        "uv", "run", "streamlit", "run", "dashboard/app.py",
        "--server.headless=true",
        f"--server.port={PORT}",
        "--server.address=127.0.0.1",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)
try:
    for _ in range(30):
        time.sleep(1)
        try:
            r = urlopen(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=1)
            if r.status == 200:
                print("streamlit: ok")
                sys.exit(0)
        except URLError:
            continue
    err = (proc.stderr.read() or b"").decode(errors="replace")[-2000:]
    print(f"streamlit: fail\n---stderr tail---\n{err}")
    sys.exit(1)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
