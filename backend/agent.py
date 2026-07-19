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
    assigned_slot: str

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
        "assigned_slot": "",
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

def parse_time(time_str):
    try:
        parts = str(time_str).split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 9 * 60  # fallback to 09:00

def format_time(minutes):
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def doctor_availability_node(state: PatientState) -> PatientState:
    ward = state["ward"]
    
    # Reload from CSV for latest availability
    if os.path.exists(CSV_PATH):
        doctors_df = pd.read_csv(CSV_PATH)
    else:
        # Fallback dictionary/data if file is missing
        doctors_df = pd.DataFrame(columns=["doctor_name", "ward", "status", "next_slot", "slot_minutes"])

    # Find active doctors in the specified ward
    active_docs = doctors_df[
        (doctors_df["ward"] == ward) & (doctors_df["status"] == "active")
    ]

    if not active_docs.empty:
        # Find the doctor with the earliest next_slot time
        minutes_list = active_docs["next_slot"].apply(parse_time)
        earliest_index = minutes_list.idxmin()
        
        doctor_row = active_docs.loc[earliest_index]
        doctor_name = doctor_row["doctor_name"]
        booked_slot = doctor_row["next_slot"]
        slot_duration = int(doctor_row["slot_minutes"])
        
        # Calculate next slot
        current_minutes = parse_time(booked_slot)
        new_minutes = current_minutes + slot_duration
        next_slot_time = format_time(new_minutes)
        
        # Update the next_slot for this doctor in the DataFrame
        doctors_df.loc[doctors_df["doctor_name"] == doctor_name, "next_slot"] = next_slot_time
        doctors_df.to_csv(CSV_PATH, index=False)
        
        assigned_doctor = doctor_name
        assigned_slot = booked_slot
    else:
        assigned_doctor = "No doctor currently free — patient will be queued"
        assigned_slot = "N/A"

    print(f"Doctor assigned: {assigned_doctor} (Slot: {assigned_slot})")
    return {**state, "assigned_doctor": assigned_doctor, "assigned_slot": assigned_slot}


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
