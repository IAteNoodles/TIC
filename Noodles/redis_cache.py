"""Basic connection example.
"""

import redis
from fastapi import FastAPI, HTTPException
import uvicorn

r = redis.Redis(
    host='redis-18811.crce206.ap-south-1-1.ec2.redns.redis-cloud.com',
    port=18811,
    decode_responses=True,
    username="default",
    password="vXmEaxjcUEjWzlHprbAVasVRAldDG8ME",
)

app = FastAPI(title="Redis cache service")

@app.get("/health")
async def health():
    try:
        if r.ping():
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"redis error: {e}")
    raise HTTPException(status_code=503, detail="redis ping failed")

@app.post("/cache/{key}")
async def set_key(key: str, value: str):
    r.set(key, value)
    return {"key": key, "value": value}

@app.get("/cache/{id}")
async def get_patients_detail(id: str):
    val = r.get(f"patient_id={id}")
    if val is None:
        raise HTTPException(status_code=404, detail="patient not found")
    return {"patient_id": id, "value": val}

if __name__ == "__main__":
    uvicorn.run("redis_cache:app", host="0.0.0.0", port=8010)

