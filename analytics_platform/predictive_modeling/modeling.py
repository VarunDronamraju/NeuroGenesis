from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import joblib
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PredictiveModelRequest(BaseModel):
    dataset_id: str
    target_column: str
    features: List[str]

class PredictiveModeler:
    async def train_model(self, user_id: str, request: PredictiveModelRequest) -> Dict:
        dataset_path = Path(f"E:/Neurogenesis/datasets/{user_id}/{request.dataset_id}.csv")
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = pd.read_csv(dataset_path)
        X = df[request.features]
        y = df[request.target_column]

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        model_id = f"model_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        model_path = Path(f"E:/Neurogenesis/models/{user_id}/{model_id}.joblib")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)

        return {
            "model_id": model_id,
            "target_column": request.target_column,
            "features": request.features,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/models/train")
async def train_model(
    request: PredictiveModelRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    modeler = PredictiveModeler()
    return await modeler.train_model(user.id, request)
