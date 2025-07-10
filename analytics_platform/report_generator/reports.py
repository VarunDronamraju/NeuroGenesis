from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ReportRequest(BaseModel):
    dataset_id: str
    report_type: str

class ReportGenerator:
    async def generate_report(self, user_id: str, request: ReportRequest) -> Dict:
        dataset_path = Path(f"E:/Neurogenesis/datasets/{user_id}/{request.dataset_id}.csv")
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = pd.read_csv(dataset_path)
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        report_path = Path(f"E:/Neurogenesis/reports/{user_id}/{report_id}.pdf")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        plt.figure()
        df.hist()
        plt.savefig(report_path)
        plt.close()

        summary = df.describe().to_dict() if request.report_type == "summary" else {
            "stats": df.describe().to_dict(),
            "rows": df.head().to_dict()
        }

        return {
            "report_id": report_id,
            "report_type": request.report_type,
            "summary": summary,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/reports")
async def generate_report(
    request: ReportRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = ReportGenerator()
    return await generator.generate_report(user.id, request)
