# utils/gpt_unlock.py

import time
from fastapi import Request

TEMP_UNLOCKS = {}

# ✅ Hard-disable GPT-4 for now (no matter what IP unlocks say)
FORCE_DISABLE_GPT4 = True

def is_gpt4_unlocked(request: Request) -> bool:
    if FORCE_DISABLE_GPT4:
        return False
    ip = request.client.host
    if ip in TEMP_UNLOCKS:
        now = time.time()
        if now - TEMP_UNLOCKS[ip] < 600:  # 10 min
            return True
        else:
            del TEMP_UNLOCKS[ip]
    return False
