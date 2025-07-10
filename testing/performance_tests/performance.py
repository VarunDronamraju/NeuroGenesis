from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PerformanceTestRequest(BaseModel):
    endpoint: str
    load: int

class PerformanceTestRunner:
    async def run_performance_tests(self, user_id: str, request: PerformanceTestRequest) -> Dict:
        test_id = f"perf_test_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/tests/performance") / user_id / f"{test_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "endpoint": request.endpoint,
            "load": request.load,
            "response_time_ms": 100  # Placeholder
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f)

        return {
            "test_id": test_id,
            "endpoint": request.endpoint,
            "results": result,
            "run_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/performance_tests")
async def run_performance_tests(request: PerformanceTestRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    runner = PerformanceTestRunner()
    return await runner.run_performance_tests(user.id, request)
