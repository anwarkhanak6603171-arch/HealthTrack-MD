const API_BASE = '';

// State Management
let patients = [];
let filteredPatients = [];
const token = localStorage.getItem('doctor_token');
const doctorUsername = localStorage.getItem('doctor_username');

// DOM Elements
const patientGrid = document.getElementById('patient-grid');
const patientForm = document.getElementById('patient-form');
const patientModal = document.getElementById('patient-modal');
const addPatientBtn = document.getElementById('add-patient-btn');
const logoutBtn = document.getElementById('logout-btn');
const closeModalBtn = document.querySelector('.close-modal');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const totalCountEl = document.getElementById('total-count');
const avgBmiEl = document.getElementById('avg-bmi');
const doctorNameEl = document.getElementById('doctor-name');
const modalTitle = document.getElementById('modal-title');
const formMode = document.getElementById('form-mode');
const pIdInput = document.getElementById('p-id');

// Initialization
async function init() {
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    doctorNameEl.textContent = `Dr. ${doctorUsername || 'Physician'}`;
    await fetchPatients();
    setupEventListeners();
}

// Event Listeners
function setupEventListeners() {
    addPatientBtn.onclick = () => openModal('create');
    logoutBtn.onclick = handleLogout;
    closeModalBtn.onclick = () => closeModal();
    window.onclick = (e) => { if (e.target == patientModal) closeModal(); };

    patientForm.onsubmit = handleFormSubmit;
    searchInput.oninput = handleSearch;
    sortSelect.onchange = handleSort;
}

function handleLogout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// Helper for authenticated requests
async function authFetch(url, options = {}) {
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    const response = await fetch(url, options);
    if (response.status === 401) {
        handleLogout();
        throw new Error('Unauthorized');
    }
    return response;
}

// API Calls
async function fetchPatients() {
    try {
        const response = await authFetch(`${API_BASE}/patients`);
        patients = await response.json();
        filteredPatients = [...patients];
        renderDashboard();
    } catch (error) {
        console.error('Failed to fetch patients:', error);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(patientForm);
    const data = Object.fromEntries(formData.entries());
    
    // Type conversion
    data.age = parseInt(data.age);
    data.height = parseFloat(data.height);
    data.weight = parseFloat(data.weight);

    const mode = formMode.value;
    const url = mode === 'create' ? `${API_BASE}/patients` : `${API_BASE}/patients/${data.id}`;
    const method = mode === 'create' ? 'POST' : 'PATCH';

    try {
        const response = await authFetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeModal();
            patientForm.reset();
            await fetchPatients();
        } else {
            const err = await response.json();
            alert(`Error: ${err.detail || 'Action failed'}`);
        }
    } catch (error) {
        console.error('Submit error:', error);
    }
}

async function deletePatient(id) {
    if (!confirm(`Permanently delete medical record for Patient ${id}?`)) return;

    try {
        const response = await authFetch(`${API_BASE}/patients/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await fetchPatients();
        }
    } catch (error) {
        console.error('Delete error:', error);
    }
}

async function editPatient(id) {
    const patient = patients.find(p => p.id === id);
    if (!patient) return;

    openModal('edit');
    modalTitle.textContent = `Update Record: ${patient.id}`;
    
    // Fill form
    pIdInput.value = patient.id;
    pIdInput.readOnly = true;
    document.getElementById('p-name').value = patient.name;
    document.getElementById('p-city').value = patient.city;
    document.getElementById('p-age').value = patient.age;
    document.getElementById('p-gender').value = patient.gender;
    document.getElementById('p-height').value = patient.height;
    document.getElementById('p-weight').value = patient.weight;
    document.getElementById('p-notes').value = patient.medical_notes || '';
}

// UI Rendering
function renderDashboard() {
    renderStats();
    renderGrid(filteredPatients);
}

function renderStats() {
    totalCountEl.textContent = patients.length;
    if (patients.length > 0) {
        const totalBmi = patients.reduce((acc, p) => acc + p.bmi, 0);
        avgBmiEl.textContent = (totalBmi / patients.length).toFixed(1);
    } else {
        avgBmiEl.textContent = '0.0';
    }
}

function renderGrid(data) {
    if (data.length === 0) {
        patientGrid.innerHTML = `<div class="loader">No medical records found.</div>`;
        return;
    }

    patientGrid.innerHTML = data.map(p => {
        const lastUpdated = new Date(p.updated_at).toLocaleDateString();
        return `
            <div class="patient-card">
                <div class="patient-header">
                    <span class="p-id-badge">${p.id}</span>
                    <div class="p-actions">
                        <button class="btn-edit" onclick="editPatient('${p.id}')" title="Edit Record">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-delete" onclick="deletePatient('${p.id}')" title="Delete Record">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                <div class="p-name">${p.name}</div>
                <div class="p-city"><i class="fas fa-map-marker-alt"></i> ${p.city}</div>
                
                <div class="medical-notes-preview">
                    <span class="metric-label">Medical Notes</span>
                    <p>${p.medical_notes || 'No clinical notes.'}</p>
                </div>

                <div class="p-metrics">
                    <div class="metric-item">
                        <span class="metric-label">Age</span>
                        <span class="metric-value">${p.age}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Gender</span>
                        <span class="metric-value" style="text-transform: capitalize;">${p.gender}</span>
                    </div>
                </div>

                <div class="p-footer">
                    <div class="bmi-badge">
                        <span class="metric-label">BMI Score</span>
                        <span class="bmi-val">${p.bmi}</span>
                    </div>
                    <span class="status-indicator status-${p.verdict.toLowerCase()}">${p.verdict}</span>
                </div>
                <div class="last-exam-text">
                    Last Exam: ${lastUpdated}
                </div>
            </div>
        `;
    }).join('');
}

// Logic Handlers
function handleSearch() {
    const term = searchInput.value.toLowerCase();
    filteredPatients = patients.filter(p => 
        p.name.toLowerCase().includes(term) || 
        p.id.toLowerCase().includes(term) ||
        p.city.toLowerCase().includes(term)
    );
    renderGrid(filteredPatients);
}

function handleSort() {
    const field = sortSelect.value;
    if (!field) return;

    filteredPatients.sort((a, b) => {
        if (typeof a[field] === 'string') {
            return a[field].localeCompare(b[field]);
        }
        return a[field] - b[field];
    });
    renderGrid(filteredPatients);
}

function openModal(mode = 'create') {
    formMode.value = mode;
    modalTitle.textContent = mode === 'create' ? 'Register New Patient' : 'Update Clinical Record';
    pIdInput.readOnly = mode === 'edit';
    if (mode === 'create') {
        patientForm.reset();
    }
    patientModal.style.display = 'flex';
}

function closeModal() {
    patientModal.style.display = 'none';
}

// Start app
init();
