from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from sklearn.ensemble import GradientBoostingRegressor
import numpy as np

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class EfficacyPrediction(BaseModel):
    trial_id: str
    treatment_features: Dict[str, float]

class EfficacyPredictor:
    def __init__(self):
        self.model = GradientBoostingRegressor(random_state=42)

    async def predict_efficacy(self, trial_id: str, treatment_features: Dict[str, float]) -> Dict:
        feature_values = np.array(list(treatment_features.values())).reshape(1, -1)
        # Placeholder: In real implementation, use trained model
        prediction = self.model.predict(feature_values)[0]
        return {
            "trial_id": trial_id,
            "efficacy_score": float(prediction),
            "features": treatment_features,
            "predicted_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/efficacy/predict")
async def predict_efficacy(
    request: EfficacyPrediction,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    predictor = EfficacyPredictor()
    return await predictor.predict_efficacy(request.trial_id, request.treatment_features)
