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
    email: str = None
    mobile: str = None
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
        
        # Generate Unique Patient ID
        import random
        import string
        from datetime import datetime
        year = datetime.now().year
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        patient_id = f"PID-{year}-{random_str}"
        
        # Populate values in result returned to client
        result["patient_id"] = patient_id
        result["mobile"] = request.mobile or "N/A"
        result["email"] = request.email or "N/A"
        
        # Save to patients.csv if a doctor was successfully assigned
        if result.get("assigned_doctor") and "No doctor currently free" not in result["assigned_doctor"]:
            patients_file = os.path.join(os.path.dirname(CSV_PATH), 'patients.csv')
            new_patient = {
                "patient_id": patient_id,
                "name": result["name"],
                "age": result.get("age", "N/A"),
                "email": request.email or "N/A",
                "mobile": request.mobile or "N/A",
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

            # Forward to Google Sheets if configured in .env
            sheet_webhook = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
            if sheet_webhook and sheet_webhook.strip():
                import urllib.request
                import urllib.error
                import json
                try:
                    payload = json.dumps(new_patient).encode('utf-8')
                    req = urllib.request.Request(
                        sheet_webhook.strip(),
                        data=payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        res_body = response.read().decode('utf-8')
                        print(f"Google Sheets webhook response: {res_body}")
                        result["sheet_status"] = "success"
                except urllib.error.HTTPError as e:
                    response_body = e.read().decode('utf-8', errors='ignore')
                    print(f"Google Sheets logging HTTP error: {e.code} {e.reason} {response_body}")
                    result["sheet_status"] = "failed"
                    result["sheet_error"] = f"Google Sheets webhook HTTP {e.code}: {e.reason}"
                except Exception as e:
                    print(f"Google Sheets logging error: {e}")
                    result["sheet_status"] = "failed"
                    result["sheet_error"] = f"Google Sheets webhook failed: {str(e)}"

            # Send SMS via Twilio if configured in .env
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_from = os.getenv("TWILIO_FROM_NUMBER")
            if twilio_sid and twilio_token and twilio_from and request.mobile and request.mobile.strip() != "N/A":
                import urllib.parse
                import base64
                try:
                    sms_body = (
                        f"MedFlow AI Triage Ticket\n"
                        f"Patient ID: {patient_id}\n"
                        f"Patient: {result['name']}\n"
                        f"Ward: {result['ward'].upper()}\n"
                        f"Doctor: {result['assigned_doctor']}\n"
                        f"Slot Time: {result['assigned_slot']}\n"
                        f"Please scan the QR code in your ticket at check-in."
                    )
                    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                    post_params = urllib.parse.urlencode({
                        'From': twilio_from.strip(),
                        'To': request.mobile.strip(),
                        'Body': sms_body
                    }).encode('utf-8')
                    
                    req_sms = urllib.request.Request(twilio_url, data=post_params)
                    auth_bytes = f"{twilio_sid.strip()}:{twilio_token.strip()}".encode('utf-8')
                    req_sms.add_header("Authorization", f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}")
                    
                    with urllib.request.urlopen(req_sms, timeout=5) as resp_sms:
                        pass
                except Exception as ex_sms:
                    print(f"Twilio SMS sending failed: {ex_sms}")

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


