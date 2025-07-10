from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import pandas as pd
from scipy import stats
import numpy as np
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class StatisticalAnalysisRequest(BaseModel):
    dataset_id: str
    analysis_type: str
    columns: List[str]

class StatisticalAnalyzer:
    async def perform_analysis(self, user_id: str, request: StatisticalAnalysisRequest) -> Dict:
        dataset_path = Path(f"E:/Neurogenesis/datasets/{user_id}/{request.dataset_id}.csv")
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = pd.read_csv(dataset_path)
        result = {}
        if request.analysis_type == "t_test" and len(request.columns) == 2:
            result["statistic"], result["p_value"] = stats.ttest_ind(df[request.columns[0]], df[request.columns[1]])
        elif request.analysis_type == "correlation" and len(request.columns) == 2:
            result["correlation"], result["p_value"] = stats.pearsonr(df[request.columns[0]], df[request.columns[1]])
        elif request.analysis_type == "anova" and len(request.columns) > 1:
            result["statistic"], result["p_value"] = stats.f_oneway(*[df[col] for col in request.columns])
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type or columns")

        return {
            "analysis_id": f"analysis_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "analysis_type": request.analysis_type,
            "columns": request.columns,
            "results": result,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/stats")
async def perform_analysis(
    request: StatisticalAnalysisRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    analyzer = StatisticalAnalyzer()
    return await analyzer.perform_analysis(user.id, request)
