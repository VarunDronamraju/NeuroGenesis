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

class UnitTestRequest(BaseModel):
    module: str

class UnitTestRunner:
    async def run_unit_tests(self, user_id: str, request: UnitTestRequest) -> Dict:
        test_id = f"unit_test_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/tests/unit") / user_id / f"{test_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = {"module": request.module, "passed": 10, "failed": 0}  # Placeholder
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f)

        return {
            "test_id": test_id,
            "module": request.module,
            "results": result,
            "run_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/unit_tests")
async def run_unit_tests(request: UnitTestRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    runner = UnitTestRunner()
    return await runner.run_unit_tests(user.id, request)
