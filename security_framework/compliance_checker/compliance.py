from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json
from sqlalchemy.orm import Session

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ComplianceCheck(BaseModel):
    standard: str  # e.g., HIPAA, GDPR

class ComplianceChecker:
    async def check_compliance(self, user_id: str, request: ComplianceCheck) -> Dict:
        compliance_id = f"compliance_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        result = {"standard": request.standard, "compliant": True}
        output_path = Path("E:/Neurogenesis/compliance") / user_id / f"{compliance_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f)

        return {
            "compliance_id": compliance_id,
            "standard": request.standard,
            "compliant": result["compliant"],
            "checked_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/compliance")
async def check_compliance(request: ComplianceCheck, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    checker = ComplianceChecker()
    return await checker.check_compliance(user.id, request)
