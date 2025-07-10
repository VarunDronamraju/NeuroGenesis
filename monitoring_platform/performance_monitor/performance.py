from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import psutil
import json
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PerformanceQuery(BaseModel):
    resource_id: str
    resource_type: str

class PerformanceMonitor:
    async def monitor_performance(self, user_id: str, query: PerformanceQuery) -> Dict:
        metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("E:/Neurogenesis").percent
        }
        metrics_path = Path("E:/Neurogenesis/metrics") / user_id / f"metrics_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump({
                "resource_id": query.resource_id,
                "resource_type": query.resource_type,
                "metrics": metrics,
                "monitored_at": datetime.utcnow().isoformat()
            }, f)
        return {
            "monitor_id": f"monitor_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource_id": query.resource_id,
            "resource_type": query.resource_type,
            "metrics": metrics,
            "monitored_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/performance")
async def monitor_performance(
    query: PerformanceQuery,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    monitor = PerformanceMonitor()
    return await monitor.monitor_performance(user.id, query)
