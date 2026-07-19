# MedFlow AI - Hospital Triage Dashboard

MedFlow AI is an intelligent hospital triage agent that automatically routes patients to appropriate wards (Emergency, Mental Health, General) based on their symptoms and assigns available specialists. 

The project has been refactored into a separate **FastAPI backend** (running a LangGraph agent workflow) and a **premium vanilla HTML/CSS/JS frontend** featuring glassmorphic designs, responsive interfaces, and custom SVG animations.

## UI Showcase

Here is a preview of the interactive dashboard demonstrating patient triage submission, real-time routing result display, staff allocation updates, and availability reset triggers:

![MedFlow AI Triage Portal Demo](/Users/dheeraj_kumar/Downloads/Hospital-agent/demo.webp)

---

## Directory Structure

```text
/Hospital-agent
├── backend/
│   ├── .env               # Configuration file (Groq API Key)
│   ├── agent.py           # Headless LangGraph triage agent
│   ├── doctors.csv        # Doctor staff occupancy database
│   ├── main.py            # FastAPI server routes & CORS configurations
│   ├── requirements.txt   # Python dependency list
│   └── venv/              # Local virtual environment
└── frontend/
    ├── index.html         # Premium dashboard layout
    ├── style.css          # Vanilla CSS layout, glassmorphic panels, and animations
    └── app.js             # API connection and DOM update handler
```

---

## Getting Started

### 1. Setup the Backend API

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and Activate a Virtual Environment** (if not already done):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API Key**:
   - Open the `backend/.env` file.
   - Set your Groq API Key:
     ```env
     GROQ_API_KEY=gsk_your_groq_api_key_goes_here
     ```

5. **Start the FastAPI Server**:
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will start running at `http://127.0.0.1:8000`.

---

### 2. Launch the Frontend Portal

1. Locate the `frontend/index.html` file in your file explorer.
2. Open `index.html` directly in any modern web browser, or serve it using a simple static server (e.g. `npx serve` or Live Server extension).
3. The interface will automatically establish a connection with the backend API.

---

## REST API Endpoints

### `POST /api/triage`
Executes patient symptom triage.
- **Request Body**:
  ```json
  {
    "name": "Jane Smith",
    "age": "28",
    "query": "Sudden severe chest pain and difficulty breathing."
  }
  ```
- **Response Body**:
  ```json
  {
    "name": "Jane Smith",
    "age": "28",
    "query": "Sudden severe chest pain and difficulty breathing.",
    "ward": "emergency",
    "reasoning": "Emergency keyword detected — routed immediately for safety.",
    "assigned_doctor": "Dr. Sarah Jenkins"
  }
  ```

### `GET /api/doctors`
Returns a list of all specialists, their department wards, and availability status (`free` or `busy`).

### `POST /api/doctors/reset`
Resets the occupancy status of all medical staff back to `free`.

---

## Core Routing Features

1. **Safety overrides**: Patient queries containing crisis indicators (e.g., suicide, self-harm) or life-threatening symptoms (e.g., chest pain, heart attack) bypass the LLM entirely and get routed instantly to Mental Health or Emergency wards respectively.
2. **Robust Fallbacks**: If the Groq API key is missing or the external API call fails, the routing defaults to the General Ward and provides a detailed exception explanation in the reasoning response rather than throwing a server error.
