from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ToxicityPrediction(BaseModel):
    molecule_smiles: str
    features: Dict[str, float]

class ToxicityPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    async def predict_toxicity(self, molecule_smiles: str, features: Dict[str, float]) -> Dict:
        feature_values = np.array(list(features.values())).reshape(1, -1)
        # Placeholder: In real implementation, load trained model
        prediction = self.model.predict_proba(feature_values)[0][1]
        return {
            "molecule_smiles": molecule_smiles,
            "toxicity_probability": float(prediction),
            "features": features,
            "predicted_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/toxicity/predict")
async def predict_toxicity(
    request: ToxicityPrediction,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    predictor = ToxicityPredictor()
    return await predictor.predict_toxicity(request.molecule_smiles, request.features)
