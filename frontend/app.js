// Replace with your actual Render URL after deploying the backend
const RENDER_BACKEND_URL = "https://your-hospital-backend.onrender.com";

const API_BASE_URL = 
    window.location.hostname === "localhost" || 
    window.location.hostname === "127.0.0.1" || 
    window.location.protocol === "file:" || 
    !window.location.hostname
        ? "http://127.0.0.1:8000"
        : RENDER_BACKEND_URL;



// Set current date
document.addEventListener("DOMContentLoaded", () => {
    const dateElement = document.getElementById("current-date");
    if (dateElement) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = new Date().toLocaleDateString('en-US', options);
    }
    // Load initial doctor list in background
    fetchDoctors();
    checkApiStatus();

    // Close modal event listeners
    const modal = document.getElementById("patient-modal");
    const closeBtn = document.getElementById("close-modal-btn");
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }
    if (modal) {
        modal.onclick = (e) => {
            if (e.target === modal) {
                closeModal();
            }
        };
    }
});

// Check if Backend API is running
async function checkApiStatus() {
    const indicator = document.querySelector(".status-indicator");
    const statusText = document.querySelector(".status-text");
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (response.ok) {
            indicator.className = "status-indicator online";
            statusText.textContent = "Server Online";
        } else {
            throw new Error();
        }
    } catch (e) {
        indicator.className = "status-indicator offline";
        statusText.textContent = "Server Offline";
    }
}

// Tab Switching Mechanism
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll(".dashboard-tab").forEach(tab => {
        tab.classList.remove("active");
    });
    
    // Deactivate all nav menu items
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });

    // Activate selected tab & nav item
    document.getElementById(tabId).classList.add("active");
    if (tabId === "triage-tab") {
        document.getElementById("nav-triage").classList.add("active");
    } else if (tabId === "doctors-tab") {
        document.getElementById("nav-doctors").classList.add("active");
        fetchDoctors(); // Refresh doctors list
    }
}

// Submit Patient Triage Form
async function submitTriage(event) {
    event.preventDefault();
    
    const name = document.getElementById("patient-name").value;
    const age = document.getElementById("patient-age").value;
    const query = document.getElementById("patient-query").value;

    const placeholder = document.getElementById("output-placeholder");
    const loader = document.getElementById("ecg-loader");
    const resultCard = document.getElementById("triage-result");

    // Show loading ECG animation
    placeholder.style.display = "none";
    resultCard.style.display = "none";
    loader.style.display = "flex";

    try {
        const response = await fetch(`${API_BASE_URL}/api/triage`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, age, query })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to classify triage state.");
        }

        const data = await response.json();
        
        // Update results values
        document.getElementById("result-name").textContent = data.name;
        document.getElementById("result-age").textContent = data.age || "N/A";
        document.getElementById("result-doctor").textContent = data.assigned_doctor;
        document.getElementById("result-slot").textContent = data.assigned_slot || "No slot assigned";
        document.getElementById("result-reasoning").textContent = data.reasoning;

        // Configure Ward Badge Style
        const wardBadge = document.getElementById("result-ward");
        wardBadge.textContent = data.ward.replace('_', ' ');
        wardBadge.className = "ward-badge"; // clear previous classes
        
        if (data.ward === "emergency") {
            wardBadge.classList.add("ward-emergency");
        } else if (data.ward === "mental_health") {
            wardBadge.classList.add("ward-mental_health");
        } else {
            wardBadge.classList.add("ward-general");
        }

        // Hide loader, show result
        loader.style.display = "none";
        resultCard.style.display = "flex";

        // Update connection status since API request was successful
        checkApiStatus();

    } catch (error) {
        loader.style.display = "none";
        placeholder.style.display = "flex";
        alert(`Triage Error: ${error.message}`);
    }
}

// Fetch all doctors from database
async function fetchDoctors() {
    const container = document.getElementById("doctors-container");
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/doctors`);
        if (!response.ok) throw new Error("Could not retrieve doctors directory.");
        
        const doctors = await response.json();
        container.innerHTML = ""; // Clear existing grid

        doctors.forEach(doc => {
            const card = document.createElement("div");
            card.className = "doctor-card";
            
            const isActive = doc.status === "active";
            const statusClass = isActive ? "status-free" : "status-busy";
            const statusText = isActive ? "Active" : "Inactive";
            
            card.innerHTML = `
                <div class="doctor-profile">
                    <div class="doctor-avatar">
                        <i class="fa-solid fa-user-md"></i>
                    </div>
                    <div class="doctor-meta">
                        <h3>${doc.doctor_name}</h3>
                        <span class="specialty">${doc.ward.replace('_', ' ')} specialist</span>
                    </div>
                </div>
                <div class="doctor-status" style="display: flex; flex-direction: column; gap: 0.8rem; align-items: stretch; border-top: 1px solid var(--card-border); padding-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="status-label">Status</span>
                        <span class="status-badge ${statusClass}">
                            <span class="status-dot"></span>
                            ${statusText}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="status-label">Next Slot</span>
                        <span class="status-badge slot-badge" style="background: rgba(0, 242, 254, 0.1); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.2);">
                            <i class="fa-regular fa-clock" style="margin-right: 4px;"></i> ${doc.next_slot} (${doc.slot_minutes}m)
                        </span>
                    </div>
                </div>
            `;
            
            // Make card clickable
            card.style.cursor = "pointer";
            card.title = `Click to view ${doc.doctor_name}'s scheduled patients`;
            card.onclick = () => showDoctorPatients(doc.doctor_name, doc.ward);

            container.appendChild(card);
        });

    } catch (err) {
        container.innerHTML = `<div class="error-msg"><p>Failed to load doctors: ${err.message}</p></div>`;
    }
}

// Reset Doctor Database
async function resetDoctors() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/doctors/reset`, {
            method: "POST"
        });
        if (!response.ok) throw new Error("Failed to reset database.");
        
        const data = await response.json();
        alert(data.message);
        
        // Refresh grid
        fetchDoctors();
    } catch (err) {
        alert(`Reset Error: ${err.message}`);
    }
}

// View Patient list assigned to a doctor
async function showDoctorPatients(doctorName, ward) {
    const modal = document.getElementById("patient-modal");
    const docNameElem = document.getElementById("modal-doctor-name");
    const docWardElem = document.getElementById("modal-doctor-ward");
    const patientsList = document.getElementById("modal-patients-list");
    
    if (!modal || !docNameElem || !docWardElem || !patientsList) return;
    
    // Set headers
    docNameElem.textContent = doctorName;
    
    // Set ward badge style
    docWardElem.textContent = ward.replace('_', ' ') + " Ward";
    docWardElem.className = "ward-badge";
    if (ward === "emergency") {
        docWardElem.classList.add("ward-emergency");
    } else if (ward === "mental_health") {
        docWardElem.classList.add("ward-mental_health");
    } else {
        docWardElem.classList.add("ward-general");
    }
    
    // Show spinner while loading
    patientsList.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 2.2rem; color: var(--primary); margin-bottom: 0.8rem;"></i>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Retrieving doctor's schedule...</p>
        </div>
    `;
    
    // Show modal overlay
    modal.style.display = "flex";
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/patients?doctor=${encodeURIComponent(doctorName)}`);
        if (!response.ok) throw new Error("Failed to load patient records.");
        
        const patients = await response.json();
        patientsList.innerHTML = "";
        
        if (patients.length === 0) {
            patientsList.innerHTML = `
                <div class="no-patients-msg">
                    <i class="fa-solid fa-calendar-xmark"></i>
                    <p style="font-size: 1.05rem; font-weight: 500; margin-bottom: 0.2rem;">Schedule is Empty</p>
                    <p style="font-size: 0.85rem; color: var(--text-muted);">No patients have been assigned to ${doctorName} today.</p>
                </div>
            `;
            return;
        }
        
        // Sort patients chronologically by their slot times
        patients.sort((a, b) => a.assigned_slot.localeCompare(b.assigned_slot));
        
        patients.forEach(pat => {
            const item = document.createElement("div");
            item.className = "patient-schedule-item";
            item.innerHTML = `
                <div class="patient-schedule-header">
                    <span class="patient-schedule-name">${pat.name}</span>
                    <span class="patient-schedule-slot">${pat.assigned_slot}</span>
                </div>
                <p class="patient-schedule-query">"${pat.query}"</p>
                <div class="patient-schedule-meta">
                    <span><i class="fa-solid fa-hourglass-half"></i> Age: ${pat.age || "N/A"}</span>
                    <span><i class="fa-solid fa-notes-medical"></i> Routing: ${pat.reasoning.split('based on')[0] || "AI Routed"}</span>
                </div>
            `;
            patientsList.appendChild(item);
        });
        
    } catch (err) {
        patientsList.innerHTML = `
            <div class="no-patients-msg" style="color: var(--emergency);">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p style="font-weight: 600;">Failed to Load Schedule</p>
                <p style="font-size: 0.85rem; color: var(--text-muted);">${err.message}</p>
            </div>
        `;
    }
}

// Close Modal helper
function closeModal() {
    const modal = document.getElementById("patient-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

