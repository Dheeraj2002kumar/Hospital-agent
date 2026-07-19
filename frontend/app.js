const API_BASE_URL = "http://127.0.0.1:8000";

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
            
            const isFree = doc.status === "free";
            const statusClass = isFree ? "status-free" : "status-busy";
            const statusText = isFree ? "Available" : "Busy";
            
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
                <div class="doctor-status">
                    <span class="status-label">Status</span>
                    <span class="status-badge ${statusClass}">
                        <span class="status-dot"></span>
                        ${statusText}
                    </span>
                </div>
            `;
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
