from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from typing import Dict
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
import pandas as pd
from pathlib import Path

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DataImporter:
    async def import_data(self, user_id: str, file: UploadFile) -> Dict:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")

        dataset_id = f"dataset_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        dataset_path = Path(f"E:/Neurogenesis/datasets/{user_id}/{dataset_id}.csv")
        dataset_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(file.file)
        df.to_csv(dataset_path, index=False)

        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "created_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/data/import")
async def import_data(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    importer = DataImporter()
    return await importer.import_data(user.id, file)
