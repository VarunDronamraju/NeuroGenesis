from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import logging
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ThreatScan(BaseModel):
    resource_id: str
    resource_type: str

class ThreatDetector:
    def __init__(self):
        self.logger = logging.getLogger("ThreatDetector")
        self.logger.setLevel(logging.WARNING)
        handler = logging.FileHandler("E:/Neurogenesis/logs/threats.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

    async def scan_threats(self, user_id: str, scan: ThreatScan):
        threat_detected = hash(user_id + scan.resource_id) % 3 == 0
        if threat_detected:
            self.logger.warning(f"Threat detected for {scan.resource_type} {scan.resource_id} by {user_id}")
        return {
            "scan_id": f"scan_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource_id": scan.resource_id,
            "resource_type": scan.resource_type,
            "threat_detected": threat_detected,
            "scanned_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/threats/scan")
async def scan_threats(scan: ThreatScan, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    detector = ThreatDetector()
    return await detector.scan_threats(user.id, scan)
