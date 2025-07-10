from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal
from datetime import datetime
import networkx as nx
from pathlib import Path
import json

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class DependencyGraph(BaseModel):
    workflow_id: str
    dependencies: List[Dict[str, str]]

class DependencyManager:
    async def create_dependency_graph(self, user_id: str, graph: DependencyGraph) -> Dict:
        workflow_path = Path(r"E:\Neurogenesis\workflows") / user_id / f"{graph.workflow_id}.json"
        if not workflow_path.exists():
            raise HTTPException(status_code=404, detail="Workflow not found")

        G = nx.DiGraph()
        for dep in graph.dependencies:
            G.add_edge(dep["depends_on"], dep["task_id"])

        if nx.is_directed_acyclic_graph(G):
            dep_path = Path(r"E:\Neurogenesis\dependencies") / user_id / f"{graph.workflow_id}_deps.json"
            dep_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dep_path, "w", encoding="utf-8") as f:
                json.dump(graph.dependencies, f)
            return {
                "workflow_id": graph.workflow_id,
                "dependency_count": len(graph.dependencies),
                "created_at": datetime.utcnow()
            }
        else:
            raise HTTPException(status_code=400, detail="Cyclic dependencies detected")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/dependencies")
async def create_dependency_graph(graph: DependencyGraph, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from user_management.authentication.auth import get_current_user
    user = await get_current_user(token, db)
    manager = DependencyManager()
    return await manager.create_dependency_graph(user.id, graph)
