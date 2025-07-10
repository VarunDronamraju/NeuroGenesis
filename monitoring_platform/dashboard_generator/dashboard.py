from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import plotly.express as px
import pandas as pd
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DashboardRequest(BaseModel):
    metrics: List[str]
    time_range: str

class DashboardGenerator:
    async def generate_dashboard(self, user_id: str, request: DashboardRequest) -> Dict:
        metrics_dir = Path("E:/Neurogenesis/metrics") / user_id
        metrics_files = list(metrics_dir.glob("metrics_*.json"))

        data = []
        for file in metrics_files:
            with open(file, "r", encoding="utf-8") as f:
                metric = json.load(f)
                if any(m in metric["metrics"] for m in request.metrics):
                    data.append(metric)

        df = pd.DataFrame([{
            "timestamp": metric["monitored_at"],
            **metric["metrics"]
        } for metric in data])

        dashboard_id = f"dashboard_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        dashboard_path = Path("E:/Neurogenesis/dashboards") / user_id / f"{dashboard_id}.json"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)

        fig = px.line(df, x="timestamp", y=request.metrics, title="System Metrics Dashboard")
        fig.write_json(dashboard_path)

        return {
            "dashboard_id": dashboard_id,
            "metrics": request.metrics,
            "time_range": request.time_range,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/dashboards")
async def generate_dashboard(
    request: DashboardRequest,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = DashboardGenerator()
    return await generator.generate_dashboard(user.id, request)
