from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from database import SessionLocal

load_dotenv()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class MoleculeGenerate(BaseModel):
    target_properties: Dict[str, float]
    max_length: int = 100

class MolecularGenerator:
    def __init__(self):
        model_name = "seyonec/ChemBERTa-77M-MLM"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    async def generate_molecule(self, properties: Dict[str, float], max_length: int) -> Dict:
        input_text = f"Generate molecule with properties: {properties}"
        inputs = self.tokenizer(input_text, return_tensors="pt", padding=True, truncation=True)
        outputs = self.model.generate(**inputs, max_length=max_length, num_return_sequences=1)
        generated_smiles = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return {
            "smiles": generated_smiles,
            "properties": properties,
            "generated_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/molecules/generate")
async def generate_molecule(
    request: MoleculeGenerate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    generator = MolecularGenerator()
    return await generator.generate_molecule(request.target_properties, request.max_length)
