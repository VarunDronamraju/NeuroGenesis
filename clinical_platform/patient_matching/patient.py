from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class PatientMatching(BaseModel):
    trial_id: str
    patient_features: List[Dict[str, float]]

class PatientMatcher:
    async def match_patients(self, trial_id: str, patient_features: List[Dict[str, float]]) -> Dict:
        df = pd.DataFrame(patient_features)
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(df.values)

        return {
            "trial_id": trial_id,
            "matches": [
                {"patient_id": f"patient_{i}", "cluster": int(cluster), "features": patient}
                for i, (cluster, patient) in enumerate(zip(clusters, patient_features))
            ],
            "matched_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/patients/match")
async def match_patients(
    request: PatientMatching,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    matcher = PatientMatcher()
    return await matcher.match_patients(request.trial_id, request.patient_features)
