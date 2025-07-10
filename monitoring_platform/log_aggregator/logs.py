from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import glob
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LogQuery(BaseModel):
    resource_id: str
    resource_type: str

class LogAggregator:
    async def aggregate_logs(self, user_id: str, query: LogQuery) -> Dict:
        log_dir = Path("E:/Neurogenesis/logs") / user_id
        log_files = glob.glob(str(log_dir / f"{query.resource_type}_{query.resource_id}*.log"))

        logs = []
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                logs.extend([line.strip() for line in f if line.strip()])

        aggregate_path = Path("E:/Neurogenesis/logs/aggregated") / user_id / f"agg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        aggregate_path.parent.mkdir(parents=True, exist_ok=True)
        with open(aggregate_path, "w", encoding="utf-8") as f:
            json.dump({"logs": logs}, f)

        return {
            "aggregate_id": f"agg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource_id": query.resource_id,
            "resource_type": query.resource_type,
            "log_count": len(logs),
            "aggregated_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/logs/aggregate")
async def aggregate_logs(
    query: LogQuery,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    aggregator = LogAggregator()
    return await aggregator.aggregate_logs(user.id, query)
