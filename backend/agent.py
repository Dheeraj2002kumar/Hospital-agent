import os
import pandas as pd
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Define CSV Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(CURRENT_DIR, 'doctors.csv')

# Define PatientState
class PatientState(TypedDict):
    name: str
    age: str
    query: str
    ward: str
    reasoning: str
    assigned_doctor: str

# Define nodes
def intake_node(state: PatientState):
    # Simply read the inputs passed into the graph initial state
    return {
        "name": state.get("name", ""),
        "age": state.get("age", ""),
        "query": state.get("query", ""),
        "ward": "",
        "reasoning": "",
        "assigned_doctor": "",
    }

# Router configuration
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _llm

ROUTER_SYSTEM_PROMPT = """You are a hospital triage router. Based on the patient's
description, classify them into EXACTLY ONE of these wards:

- emergency: life-threatening or urgent physical conditions (severe pain, bleeding,
  breathing difficulty, chest pain, accidents, high fever, unconsciousness, etc.)
- mental_health: psychological/emotional distress (anxiety, depression, panic attacks,
  suicidal thoughts, self-harm, trauma, etc.)
- general: everything else (routine checkups, mild/chronic non-urgent symptoms, colds,
  minor aches, follow-ups, etc.)

Respond with ONLY one word: emergency, mental_health, or general.
"""

EMERGENCY_KEYWORDS = ["chest pain", "can't breathe", "unconscious", "severe bleeding", "heart attack"]
CRISIS_KEYWORDS = ["suicide", "kill myself", "self-harm", "want to die"]

def router_node(state: PatientState) -> PatientState:
    query_lower = state["query"].lower()

    if any(kw in query_lower for kw in CRISIS_KEYWORDS):
        ward, reasoning = "mental_health", "Crisis keyword detected — routed immediately for safety."
    elif any(kw in query_lower for kw in EMERGENCY_KEYWORDS):
        ward, reasoning = "emergency", "Emergency keyword detected — routed immediately for safety."
    else:
        try:
            response = get_llm().invoke([
                SystemMessage(content=ROUTER_SYSTEM_PROMPT),
                HumanMessage(content=f"Age: {state['age']}\nSymptoms: {state['query']}")
            ])
            raw = response.content.strip().lower()

            # Defensive parsing
            if "emergency" in raw:
                ward = "emergency"
            elif "mental_health" in raw or "mental health" in raw:
                ward = "mental_health"
            elif "general" in raw:
                ward = "general"
            else:
                ward = "general"  # safe default
            
            reasoning = f"LLM classified based on: '{state['query']}'"
        except Exception as e:
            # Fallback if API fails or GROQ_API_KEY is not configured
            ward = "general"
            reasoning = f"Fallback to general due to API error: {str(e)}"

    return {**state, "ward": ward, "reasoning": reasoning}

def general_ward_node(state: PatientState) -> PatientState:
    print(f"\n{state['name']} -> GENERAL WARD")
    print(f"Reason: {state['reasoning']}")
    return state

def emergency_ward_node(state: PatientState) -> PatientState:
    print(f"\n{state['name']} -> EMERGENCY WARD (priority)")
    print(f"Reason: {state['reasoning']}")
    return state

def mental_health_ward_node(state: PatientState) -> PatientState:
    print(f"\n{state['name']} -> MENTAL HEALTH WARD")
    print(f"Reason: {state['reasoning']}")
    return state

def doctor_availability_node(state: PatientState) -> PatientState:
    ward = state["ward"]
    
    # Reload from CSV for latest availability
    if os.path.exists(CSV_PATH):
        doctors_df = pd.read_csv(CSV_PATH)
    else:
        # Fallback dictionary/data if file is missing
        doctors_df = pd.DataFrame(columns=["doctor_name", "ward", "status"])

    available = doctors_df[
        (doctors_df["ward"] == ward) & (doctors_df["status"] == "free")
    ]

    if not available.empty:
        doctor = available.iloc[0]["doctor_name"]
        assigned_doctor = doctor
        # Mark doctor busy and write to CSV
        doctors_df.loc[doctors_df["doctor_name"] == doctor, "status"] = "busy"
        doctors_df.to_csv(CSV_PATH, index=False)
    else:
        assigned_doctor = "No doctor currently free — patient will be queued"

    print(f"Doctor assigned: {assigned_doctor}")
    return {**state, "assigned_doctor": assigned_doctor}

# Build LangGraph workflow
def route_decision(state: PatientState) -> Literal["general", "emergency", "mental_health"]:
    return state["ward"]

builder = StateGraph(PatientState)

builder.add_node("intake", intake_node)
builder.add_node("router", router_node)
builder.add_node("general", general_ward_node)
builder.add_node("emergency", emergency_ward_node)
builder.add_node("mental_health", mental_health_ward_node)
builder.add_node("doctor_check", doctor_availability_node)

builder.set_entry_point("intake")
builder.add_edge("intake", "router")

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "general": "general",
        "emergency": "emergency",
        "mental_health": "mental_health",
    },
)

builder.add_edge("general", "doctor_check")
builder.add_edge("emergency", "doctor_check")
builder.add_edge("mental_health", "doctor_check")

builder.add_edge("doctor_check", END)

graph = builder.compile()
