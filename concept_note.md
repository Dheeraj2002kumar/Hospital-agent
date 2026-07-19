# Project Concept Note: MedFlow AI

**System Name:** MedFlow AI – Intelligent Hospital Triage & Scheduling Portal  
**Document Version:** 1.0  
**Author:** [Your Name / Team Name]  
**Target Audience:** Stakeholders, Medical Administrators, and Technical Teams  

---

## 1. Executive Summary
In busy healthcare environments, immediate and accurate patient triage is a major challenge. MedFlow AI addresses this by decoupling patient routing and appointment scheduling from manual operations. 

Using an **Agentic AI workflow (built with LangGraph)** and a **fast API gateway (FastAPI)**, MedFlow AI processes patient symptoms, classifies them into correct care departments (Emergency, Mental Health, General Ward), dynamically books the next available time slot for matching on-call specialists, and presents it in a premium, glassmorphic client interface.

---

## 2. Problem Statement
Hospital emergency rooms and outpatient clinics suffer from significant inefficiencies during the patient intake phase:
1. **Bottlenecks in Manual Triage**: Understaffed intake desks cause delays in evaluating patients, which can worsen critical health conditions.
2. **Human Routing Errors**: Directing psychological crises or acute cardiac conditions to general clinics can lead to poor patient outcomes.
3. **Disjointed Doctor Scheduling**: Medical staff coordinates schedules manually or via separate databases, making it difficult to allocate appointments dynamically.
4. **Outdated User Interfaces**: Healthcare systems often rely on legacy software, which slows down intake coordinators and increases cognitive load.

---

## 3. Proposed Solution: MedFlow AI
MedFlow AI is a modern clinical assistant platform split into two decoupled layers:
* **The Brain (AI Backend)**: A LangGraph state machine that evaluates patient intake details. It uses safety keyword lists (crisis and emergency bypass rules) and LLMs (Llama 3.3 via Groq) to route patients and calculate appointments.
* **The Portal (Responsive Frontend)**: A modern, glassmorphic dashboard built using Vanilla CSS and JavaScript, allowing coordinators to quickly run evaluations, check doctors' schedules, and reset staff logs.

### Agentic Workflow Diagram
Here is the LangGraph agent state machine diagram showing the flow of patient routing and resource checks:

![LangGraph Architecture Flow](/Users/dheeraj_kumar/Downloads/Hospital-agent/image-3.png)

---

## 4. Core System Workflow
1. **Patient Intake**: The coordinator inputs the patient's name, age, and symptoms in the web app.
2. **Safety Routing Guardrails**: 
   - If emergency indicators (e.g. *chest pain*) are present, the patient is routed directly to the Emergency ward.
   - If crisis indicators (e.g. *self-harm*) are present, the patient is routed to the Mental Health ward.
   - Standard queries are processed by Llama 3.3 to classify the department.
3. **Smart Scheduling**: The system queries the `doctors.csv` database, identifies the specialist in the assigned ward with the earliest slot, calculates their next appointment slot, and saves the appointment details to `patients.csv`.
4. **Visual Portal Update**: The result card displays the routed ward, the doctor's name, the assigned time slot, and the reasoning behind the classification.

---

## 5. Technology Stack
* **Core Agent Engine**: `langgraph` (v1.2+), `langchain-core`, and `langchain-groq` (Llama 3.3 70B model).
* **API Gateway & Middleware**: `fastapi` and `uvicorn` (cross-origin CORS enabled).
* **Data Management**: Python `pandas` operating on local CSV structures (`doctors.csv`, `patients.csv`).
* **Web UI Layout**: Vanilla HTML5, CSS3, JavaScript (responsive UI, CSS transitions, custom SVG loader, modal schedule viewer).

---

## 6. Key Value Proposition & Impact
1. **Improved Patient Safety**: Automatic keyword triggers ensure that emergency and mental health patients bypass LLM reasoning queues for immediate care.
2. **Reduced Wait Times**: Automated time slot calculations assign patients to available specialists without scheduling conflicts.
3. **Streamlined Coordination**: Doctors' schedules are logged centrally. Staff can review any doctor's daily patient list with a single click in the Doctor Directory.
4. **Modern Design System**: The premium dark slate dashboard with glowing status badges reduces visual fatigue for administrative staff.

---

## 7. Future Expansion Roadmap
* **EHR Integration**: Connect patient records directly to standard HL7/FHIR hospital databases.
* **Notification System**: Send SMS and email reminders with confirmed slot times.
* **Telehealth Integration**: Include links to video consultation interfaces directly on the assigned result cards.
