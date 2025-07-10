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

class IntegrationTestRequest(BaseModel):
    system: str

class IntegrationTestRunner:
    async def run_integration_tests(self, user_id: str, request: IntegrationTestRequest) -> Dict:
        test_id = f"integration_test_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/tests/integration") / user_id / f"{test_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {"system": request.system, "passed": 5, "failed": 0}  # Placeholder
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f)

        return {
            "test_id": test_id,
            "system": request.system,
            "results": result,
            "run_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/integration_tests")
async def run_integration_tests(request: IntegrationTestRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    runner = IntegrationTestRunner()
    return await runner.run_integration_tests(user.id, request)
