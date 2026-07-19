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
        
        # Save to patients.csv if a doctor was successfully assigned
        if result.get("assigned_doctor") and "No doctor currently free" not in result["assigned_doctor"]:
            patients_file = os.path.join(os.path.dirname(CSV_PATH), 'patients.csv')
            new_patient = {
                "name": result["name"],
                "age": result.get("age", "N/A"),
                "query": result["query"],
                "ward": result["ward"],
                "reasoning": result["reasoning"],
                "assigned_doctor": result["assigned_doctor"],
                "assigned_slot": result["assigned_slot"]
            }
            df_new = pd.DataFrame([new_patient])
            if os.path.exists(patients_file):
                try:
                    df_existing = pd.read_csv(patients_file)
                    df_updated = pd.concat([df_existing, df_new], ignore_index=True)
                except Exception:
                    df_updated = df_new
            else:
                df_updated = df_new
            df_updated.to_csv(patients_file, index=False)

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
    try:
        # Reset back to the initial database state with default slot times (using updated values)
        default_data = (
            "doctor_name,ward,status,next_slot,slot_minutes\n"
            "Dr. Sharma,general,active,09:00,20\n"
            "Dr. Iyer,general,active,09:15,20\n"
            "Dr. Khan,emergency,active,09:00,10\n"
            "Dr. Rao,emergency,active,08:50,10\n"
            "Dr. Mehta,mental_health,active,10:00,30\n"
            "Dr. Gupta,mental_health,active,10:00,30\n"
        )
        with open(CSV_PATH, "w") as f:
            f.write(default_data)
            
        # Clear patients.csv schedule log
        patients_file = os.path.join(os.path.dirname(CSV_PATH), 'patients.csv')
        if os.path.exists(patients_file):
            try:
                os.remove(patients_file)
            except Exception:
                pass
                
        return {"status": "success", "message": "All doctors reset back to active status, initial slot times, and schedules cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not reset doctors database: {str(e)}")

@app.get("/api/patients")
def get_patients(doctor: str = None):
    patients_file = os.path.join(os.path.dirname(CSV_PATH), 'patients.csv')
    if not os.path.exists(patients_file):
        return []
    
    try:
        df = pd.read_csv(patients_file)
        df = df.fillna("")
        records = df.to_dict(orient="records")
        if doctor:
            records = [r for r in records if r["assigned_doctor"] == doctor]
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve patients list: {str(e)}")


