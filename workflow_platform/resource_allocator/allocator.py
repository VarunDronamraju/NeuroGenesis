from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ResourceAllocation(BaseModel):
    workflow_id: str
    resources: Dict[str, float]

class ResourceAllocator:
    async def allocate_resources(self, user_id: str, allocation: ResourceAllocation) -> Dict:
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{allocation.workflow_id}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        allocation_id = f"allocation_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        allocation_path = Path(r"E:\Neurogenesis\allocations") / user_id / f"{allocation_id}.json"
        allocation_path.parent.mkdir(parents=True, exist_ok=True)
        with open(allocation_path, "w", encoding="utf-8") as f:
            json.dump({
                "workflow_id": allocation.workflow_id,
                "resources": allocation.resources,
                "allocated_at": datetime.utcnow().isoformat()
            }, f)

        return {
            "allocation_id": allocation_id,
            "workflow_id": allocation.workflow_id,
            "resources": allocation.resources,
            "allocated_at": datetime.utcnow()
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/allocations")
async def allocate_resources(allocation: ResourceAllocation, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    allocator = ResourceAllocator()
    return await allocator.allocate_resources(user.id, allocation)
