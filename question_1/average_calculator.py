from fastapi import FastAPI, HTTPException
from collections import deque
import aiohttp
import asyncio
from typing import List
import time

app = FastAPI()

WINDOW_SIZE = 10
VALID_NUMBER_IDS = {"p", "f", "e", "r"}
TEST_SERVER_URLS = {
    "p": "http://20.244.56.144/evaluation-service/primes",
    "f": "http://20.244.56.144/evaluation-service/fibo",
    "e": "http://20.244.56.144/evaluation-service/even",
    "r": "http://20.244.56.144/evaluation-service/rand"
}
TIMEOUT_MS = 500

number_window = deque(maxlen=WINDOW_SIZE)

async def fetch_numbers(number_id: str, token: str) -> List[int]:
    url = TEST_SERVER_URLS.get(number_id)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=TIMEOUT_MS / 1000) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                return data.get("numbers", [])
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

@app.get("/numbers/{number_id}")
async def get_average(number_id: str):
    start_time = time.time()
    if number_id not in VALID_NUMBER_IDS:
        raise HTTPException(status_code=400, detail="Invalid number_id")
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQ5MDE3NjQyLCJpYXQiOjE3NDkwMTczNDIsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6IjhkNmVlN2ZiLTBmZDgtNDBlMi1hNThiLTVmYTAxOGY5MjczOSIsInN1YiI6ImFiaGlzaGVrd2FsZTg1ODJAZ21haWwuY29tIn0sImVtYWlsIjoiYWJoaXNoZWt3YWxlODU4MkBnbWFpbC5jb20iLCJuYW1lIjoiYWJoaXNoZWsgd2FsZSIsInJvbGxObyI6IjcyMzA5NjgyYiIsImFjY2Vzc0NvZGUiOiJLUmpVVVUiLCJjbGllbnRJRCI6IjhkNmVlN2ZiLTBmZDgtNDBlMi1hNThiLTVmYTAxOGY5MjczOSIsImNsaWVudFNlY3JldCI6ImFUQllKemNqcXZRYkhaRWYifQ.3b4nMC2TUbxv1OgH4BeCaS2cGwuqSK5RjRRfZw1OeiQ"  
    window_prev_state = list(number_window)
    new_numbers = await fetch_numbers(number_id, token)
    if not new_numbers:
        avg = sum(number_window) / len(number_window) if number_window else 0.0
        return {
            "windowPrevState": window_prev_state,
            "windowCurrState": list(number_window),
            "numbers": [],
            "avg": round(avg, 2)
        }
    for num in new_numbers:
        if num not in number_window:
            number_window.append(num)
    avg = sum(number_window) / len(number_window) if number_window else 0.0
    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > TIMEOUT_MS:
        raise HTTPException(status_code=500, detail="Response too slow")
    return {
        "windowPrevState": window_prev_state,
        "windowCurrState": list(number_window),
        "numbers": new_numbers,
        "avg": round(avg, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9876)