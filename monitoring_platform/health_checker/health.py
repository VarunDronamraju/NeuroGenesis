from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import requests
from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class HealthCheck(BaseModel):
    service: str

class HealthChecker:
    def __init__(self):
        self.services = {
            "core_ai": "http://localhost:8001/health",
            "analytics_platform": "http://localhost:8003/health",
            "integration_platform": "http://localhost:8004/health"
        }

    async def check_health(self, user_id: str, check: HealthCheck) -> Dict:
        if check.service not in self.services:
            raise HTTPException(status_code=400, detail="Invalid service")
        try:
            response = requests.get(self.services[check.service], timeout=5)
            response.raise_for_status()
            status = "healthy" if response.status_code == 200 else "unhealthy"
        except requests.RequestException:
            status = "unhealthy"

        health_path = Path("E:/Neurogenesis/health") / user_id / f"health_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        health_path.parent.mkdir(parents=True, exist_ok=True)
        with open(health_path, "w", encoding="utf-8") as f:
            json.dump({
                "service": check.service,
                "status": status,
                "checked_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "check_id": f"check_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "service": check.service,
            "status": status,
            "checked_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/health")
async def check_health(
    check: HealthCheck,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    checker = HealthChecker()
    return await checker.check_health(user.id, check)
