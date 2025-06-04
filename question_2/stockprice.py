from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
from typing import List, Dict
import time
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()


TEST_SERVER_BASE_URL = "http://20.244.56.144/evaluation-service/stocks"
TIMEOUT_MS = 500  

class PriceEntry(BaseModel):
    price: float
    lastUpdatedAt: str

class StockResponse(BaseModel):
    averageStockPrice: float
    priceHistory: List[PriceEntry]

async def fetch_stock_data(ticker: str, minutes: int, token: str) -> List[Dict]:
    """
    Fetch stock price history from test server for the given ticker and time window.
    """
    url = f"{TEST_SERVER_BASE_URL}/{ticker}?minutes={minutes}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=TIMEOUT_MS / 1000) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to fetch data for ticker {ticker}")
                data = await response.json()
                return data if isinstance(data, list) else [data.get("stock", {})]
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise HTTPException(status_code=500, detail="Test server request failed or timed out")

@app.get("/stocks/{ticker}", response_model=StockResponse)
async def get_stock_average(ticker: str, minutes: int, aggregation: str = "average"):
    """
    GET /stocks/{ticker}?minutes=m&aggregation=average
    Returns the average stock price and price history for the last m minutes.
    """
    start_time = time.time()
    
    if aggregation != "average":
        raise HTTPException(status_code=400, detail="Aggregation must be 'average'")
    if minutes <= 0:
        raise HTTPException(status_code=400, detail="Minutes must be positive")

    token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQ5MDIxNjUxLCJpYXQiOjE3NDkwMjEzNTEsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6IjhkNmVlN2ZiLTBmZDgtNDBlMi1hNThiLTVmYTAxOGY5MjczOSIsInN1YiI6ImFiaGlzaGVrd2FsZTg1ODJAZ21haWwuY29tIn0sImVtYWlsIjoiYWJoaXNoZWt3YWxlODU4MkBnbWFpbC5jb20iLCJuYW1lIjoiYWJoaXNoZWsgd2FsZSIsInJvbGxObyI6IjcyMzA5NjgyYiIsImFjY2Vzc0NvZGUiOiJLUmpVVVUiLCJjbGllbnRJRCI6IjhkNmVlN2ZiLTBmZDgtNDBlMi1hNThiLTVmYTAxOGY5MjczOSIsImNsaWVudFNlY3JldCI6ImFUQllKemNqcXZRYkhaRWYifQ.UNJlo28vaVdn58CPEm-tq9AbpzI0oxs7gBV1Vtz-XjY"

    price_history = await fetch_stock_data(ticker, minutes, token)
    
    valid_entries = [
        entry for entry in price_history 
        if "price" in entry and "lastUpdatedAt" in entry
    ]
    
    if not valid_entries:
        raise HTTPException(status_code=400, detail="No valid price data found")

    total_price = sum(entry["price"] for entry in valid_entries)
    avg_price = total_price / len(valid_entries)

    elapsed_ms = (time.time() - start_time) * 1000
    if elapsed_ms > TIMEOUT_MS:
        raise HTTPException(status_code=500, detail="Response time exceeded 500 ms")

    return {
        "averageStockPrice": round(avg_price, 2),
        "priceHistory": [
            {"price": entry["price"], "lastUpdatedAt": entry["lastUpdatedAt"]}
            for entry in valid_entries
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9876)