from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class APICall(BaseModel):
    service: str  # e.g., "core_ai", "clinical_platform"
    endpoint: str
    payload: Dict

class APIGateway:
    def __init__(self):
        self.services = {
            "core_ai": "http://localhost:8001",
            "clinical_platform": "http://localhost:8002",
            "analytics_platform": "http://localhost:8003"
        }

    async def forward_request(self, user_id: str, call: APICall) -> Dict:
        if call.service not in self.services:
            raise HTTPException(status_code=400, detail="Invalid service")

        url = f"{self.services[call.service]}{call.endpoint}"
        try:
            response = requests.post(url, json=call.payload, headers={"X-User-ID": user_id})
            response.raise_for_status()
            return {
                "service": call.service,
                "endpoint": call.endpoint,
                "response": response.json(),
                "called_at": datetime.utcnow()
            }
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/call")
async def forward_api_call(
    call: APICall,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    gateway = APIGateway()
    return await gateway.forward_request(user.id, call)
