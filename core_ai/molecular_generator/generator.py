from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json
import numpy as np

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MoleculeRequest(BaseModel):
    target: str
    parameters: Dict

class MolecularGenerator:
    async def generate_molecule(self, user_id: str, request: MoleculeRequest) -> Dict:
        molecule_id = f"molecule_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        output_path = Path("E:/Neurogenesis/molecules") / user_id / f"{molecule_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        molecule_data = {
            "molecule_id": molecule_id,
            "target": request.target,
            "structure": {"smiles": "C1=CC=CC=C1"},
            "parameters": request.parameters
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(molecule_data, f)
        return {
            "molecule_id": molecule_id,
            "target": request.target,
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/molecules")
async def generate_molecule(request: MoleculeRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = MolecularGenerator()
    return await generator.generate_molecule(user.id, request)
