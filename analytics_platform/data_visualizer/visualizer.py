from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import pandas as pd
import plotly.express as px
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class VisualizationRequest(BaseModel):
    dataset_id: str
    chart_type: str
    x_axis: str
    y_axis: str
    filters: Dict = {}

class DataVisualizer:
    async def create_visualization(self, user_id: str, request: VisualizationRequest) -> Dict:
        dataset_path = Path(f"E:/Neurogenesis/datasets/{user_id}/{request.dataset_id}.csv")
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = pd.read_csv(dataset_path)
        for key, value in request.filters.items():
            df = df[df[key] == value]

        fig = getattr(px, request.chart_type)(
            df, x=request.x_axis, y=request.y_axis, title=f"{request.chart_type.capitalize()} Chart"
        )
        output_path = Path(f"E:/Neurogenesis/visualizations/{user_id}/vis_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_json(output_path)

        return {
            "visualization_id": output_path.name,
            "chart_type": request.chart_type,
            "x_axis": request.x_axis,
            "y_axis": request.y_axis,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/visualizations")
async def create_visualization(
    request: VisualizationRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    visualizer = DataVisualizer()
    return await visualizer.create_visualization(user.id, request)
