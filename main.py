from fastapi import FastAPI

app = FastAPI(title="NeuroGenesis API")

@app.get("/")
async def root():
    return {"message": "Welcome to NeuroGenesis"}
