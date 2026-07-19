import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import graph, CSV_PATH

app = FastAPI(title="Hospital Triage Agent API")

# Enable CORS for local development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TriageRequest(BaseModel):
    name: str
    age: str
    query: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hospital Triage Agent API"}

@app.post("/api/triage")
def triage_patient(request: TriageRequest):
    if not request.name.strip() or not request.query.strip():
        raise HTTPException(status_code=400, detail="Patient Name and symptoms/query are required.")
    
    try:
        # Invoke the compiled LangGraph workflow
        result = graph.invoke({
            "name": request.name,
            "age": request.age,
            "query": request.query
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage process failed: {str(e)}")

@app.get("/api/doctors")
def get_doctors():
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail="Doctors data store not found.")
    
    try:
        df = pd.read_csv(CSV_PATH)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve doctors: {str(e)}")

@app.post("/api/doctors/reset")
def reset_doctors():
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail="Doctors data store not found.")
    
    try:
        df = pd.read_csv(CSV_PATH)
        df["status"] = "free"
        df.to_csv(CSV_PATH, index=False)
        return {"status": "success", "message": "All doctors set back to free availability."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not reset doctors database: {str(e)}")
