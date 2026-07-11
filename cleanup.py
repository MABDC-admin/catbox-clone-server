import os
import time

UPLOAD_DIR = "/home/admin/catbox-clone-server/uploads"
SIX_DAYS = 6 * 24 * 60 * 60

now = time.time()
for f in os.listdir(UPLOAD_DIR):
    path = os.path.join(UPLOAD_DIR, f)
    if os.path.isfile(path):
        if os.stat(path).st_mtime < now - SIX_DAYS:
            try:
                os.remove(path)
            except:
                pass
