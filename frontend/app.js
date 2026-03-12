// Base API URL configuration
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
// In production, we'll assume the backend is on the same domain or proxied at /api
const API_URL = isLocal ? 'http://127.0.0.1:8000' : 'http://dgwv6mw80k9e4uoew72v20os.72.60.248.159.sslip.io';
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showLogin();
    } else {
        checkUserRole().then(() => showDashboard());
    }

    document.getElementById('logoutBtn').addEventListener('click', logout);
}

// Global User State
let currentUser = null;
let currentPage = 'dashboard'; // Track current view

// Navigation
function goBack() {
    if (currentPage !== 'dashboard') {
        showDashboard();
    }
}

// Modal instances
let txModal;
let partnerModal;
let pwdModal;

function showTransactionModal() {
    txModal = new bootstrap.Modal(document.getElementById('transactionModal'));
    txModal.show();
}

function showChangePasswordModal() {
    pwdModal = new bootstrap.Modal(document.getElementById('pwdModal'));
    pwdModal.show();
}

async function changePassword() {
    const current = document.getElementById('currentPwd').value;
    const newPwd = document.getElementById('newPwd').value;
    if (!current || !newPwd) return alert("Complete los campos");

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/users/me/password`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: current, new_password: newPwd })
        });
        if (!res.ok) throw new Error("Error al cambiar contraseña");

        alert("Contraseña actualizada");
        pwdModal.hide();
        document.getElementById('pwdForm').reset();
    } catch (e) {
        alert(e.message);
    }
}

async function checkUserRole() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/users/me`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!res.ok) throw new Error("Sesión inválida");

        currentUser = await res.json();
    } catch (e) {
        console.error(e);
        logout();
    }
}

async function submitTransaction() {
    const type = document.getElementById('txType').value;
    let amount = document.getElementById('txAmount').value;
    const desc = document.getElementById('txDesc').value;

    // Advanced fields
    const origin = document.getElementById('txOrigin') ? document.getElementById('txOrigin').value : 'external';
    const partnerId = document.getElementById('txPartner') ? document.getElementById('txPartner').value : null;
    const reason = document.getElementById('txReason') ? document.getElementById('txReason').value : null;

    const debtIds = [];
    if (type === 'income' && origin === 'partner' && reason === 'quota') {
        document.querySelectorAll('.debt-check:checked').forEach(cb => debtIds.push(parseInt(cb.value)));
    }

    if (!amount || !desc) return alert('Complete todos los campos obligatorios');

    const payload = {
        amount: parseFloat(amount),
        type: type,
        description: desc,
        debt_ids: debtIds.length > 0 ? debtIds : null
    };

    if (type === 'income' && origin === 'partner') {
        if (!partnerId) return alert('Seleccione un socio');
        payload.user_id = parseInt(partnerId);
        payload.category = reason;
    }

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/transactions/`, { // Note trailing slash if API strict
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Error al guardar');
        }

        txModal.hide();
        document.getElementById('transactionForm').reset();
        // Reset dynamic fields visibility
        if (typeof updateTxModalFields === 'function') updateTxModalFields();

        // Refresh
        const content = document.getElementById('content');
        if (content.innerHTML.includes('Gestión de Socios')) {
            // showPartners(); 
        } else if (content.innerHTML.includes('Historial de Movimientos')) {
            loadTransactions();
        } else {
            showDashboard();
        }

    } catch (err) {
        console.error(err);
        alert(err.message);
    }
}

// Transaction Modal Logic (RF-05)
function updateTxModalFields() {
    const type = document.getElementById('txType').value;
    const originDiv = document.getElementById('originDiv');
    const partnerDiv = document.getElementById('partnerDiv');
    const reasonDiv = document.getElementById('reasonDiv');
    const debtDiv = document.getElementById('debtDiv');

    // Reset availability
    originDiv.classList.add('d-none');
    partnerDiv.classList.add('d-none');
    reasonDiv.classList.add('d-none');
    debtDiv.classList.add('d-none');

    if (type === 'income') {
        originDiv.classList.remove('d-none');
        // Trigger origin change logic
        updateOriginFields();
    }
}

function updateOriginFields() {
    const origin = document.getElementById('txOrigin').value;
    const partnerDiv = document.getElementById('partnerDiv');
    const reasonDiv = document.getElementById('reasonDiv');
    const debtDiv = document.getElementById('debtDiv');

    if (origin === 'partner') {
        partnerDiv.classList.remove('d-none');
        reasonDiv.classList.remove('d-none');
        loadPartnersSelect(); // ensure select is populated
        updateReasonFields();
    } else {
        partnerDiv.classList.add('d-none');
        reasonDiv.classList.add('d-none');
        debtDiv.classList.add('d-none');
    }
}

function updateReasonFields() {
    const reason = document.getElementById('txReason').value;
    const debtDiv = document.getElementById('debtDiv');
    const partnerId = document.getElementById('txPartner').value;

    if (reason === 'quota' && partnerId) {
        debtDiv.classList.remove('d-none');
        loadPendingDebts(partnerId);
    } else {
        debtDiv.classList.add('d-none');
    }
}

async function loadPartnersSelect() {
    const select = document.getElementById('txPartner');

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/users/?role=partner`, { headers: { 'Authorization': `Bearer ${token}` } });

        if (!res.ok) throw new Error("Error al cargar socios");

        const users = await res.json();

        if (!Array.isArray(users)) {
            console.error("Expected array, got:", users);
            return;
        }

        select.innerHTML = '<option value="">Seleccione Socio</option>' +
            users.map(u => `<option value="${u.id}">${u.name || u.email} (${u.email})</option>`).join('');

    } catch (e) {
        console.error("Failed to load partners:", e);
        select.innerHTML = '<option value="">Error al cargar</option>';
    }
}

async function loadPendingDebts(userId) {
    const container = document.getElementById('debtList');
    container.innerHTML = 'Cargando deudas...';

    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_URL}/users/${userId}/debts`, { headers: { 'Authorization': `Bearer ${token}` } });
    const debts = await res.json();

    if (debts.length === 0) {
        container.innerHTML = '<p class="text-success small">No tiene deudas pendientes.</p>';
        return;
    }

    container.innerHTML = debts.map(d => `
        <div class="form-check">
            <input class="form-check-input debt-check" type="checkbox" value="${d.id}" data-amount="${d.amount}" id="debt_${d.id}" onchange="calculateTotalAmount()">
            <label class="form-check-label" for="debt_${d.id}">
                ${d.month}/${d.year} - $${d.amount}
            </label>
        </div>
    `).join('');
}

function calculateTotalAmount() {
    let total = 0;
    document.querySelectorAll('.debt-check:checked').forEach(cb => {
        total += parseFloat(cb.getAttribute('data-amount'));
    });
    if (total > 0) {
        document.getElementById('txAmount').value = total;
    }
}

function showLogin() {
    document.getElementById('loading').classList.add('d-none');
    document.getElementById('app-nav').classList.add('d-none');
    const content = document.getElementById('content');
    content.classList.remove('d-none');
    content.innerHTML = `
        <div class="row justify-content-center mt-5">
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card p-4 shadow-lg login-card">
                    <div class="text-center mb-4">
                        <img src="logo.jpeg" alt="Logo" width="80" height="80" class="rounded-circle mb-3 border border-secondary">
                        <h3 class="fw-bold">DARK RIDERS</h3>
                        <p class="text-muted">Tesorería</p>
                    </div>
                    <form id="loginForm">
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control bg-dark text-light" id="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Contraseña</label>
                            <input type="password" class="form-control bg-dark text-light" id="password" required>
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary fw-bold">INGRESAR</button>
                        </div>
                        <div id="loginError" class="text-danger mt-3 text-center d-none"></div>
                    </form>
                </div>
            </div>
        </div>
    `;

    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let detail = '';
            try {
                const errData = await response.json();
                detail = errData.detail || '';
            } catch(e) {}
            throw new Error(`Error ${response.status}: ${detail || 'Credenciales inválidas'}`);
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);

        await checkUserRole(); // Update currentUser state
        showDashboard();
    } catch (err) {
        errorDiv.textContent = err.message;
        errorDiv.classList.remove('d-none');
        console.error("Login Error:", err);
    }
}

function logout() {
    localStorage.removeItem('access_token');
    showLogin();
}

async function showDashboard() {
    currentPage = 'dashboard';
    document.getElementById('app-nav').classList.remove('d-none');
    document.getElementById('loading').classList.add('d-none'); // Hide Spinner
    const content = document.getElementById('content');
    content.classList.remove('d-none');

    // Initial content with loading skeleton or just structure
    content.innerHTML = `
        <div id="dashboardData" class="text-center"><div class="spinner-border text-light"></div></div>
    `;

    await loadDashboardData();
}

async function loadDashboardData() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/dashboard/summary`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const data = await response.json();
        renderDashboardParams(data);
    } catch (err) {
        console.error("Failed to load dashboard", err);
    }
}

function renderDashboardParams(data) {
    const container = document.getElementById('dashboardData');
    const fmt = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' });
    const isAdmin = currentUser && currentUser.role === 'admin';

    container.innerHTML = `
        <div class="dashboard-title">
            <h2>💀 Dark Riders</h2>
            <div class="user-role-badge">Sesión de: <span class="text-white fw-bold">${currentUser ? (currentUser.nickname || currentUser.name) : 'Usuario'}</span></div>
        </div>

        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-title">Ingresos</div>
                <div class="stat-value text-green">${fmt.format(data.total_income)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Egresos</div>
                <div class="stat-value text-red">${fmt.format(data.total_expense)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Saldo</div>
                <div class="stat-value text-white">${fmt.format(data.balance)}</div>
            </div>
        </div>
        
        <!-- Actions Grid (Visible only for Admin?) User said "visible depending on Type" -->
        ${isAdmin ? `
        <div class="actions-container">
            <button class="action-btn btn-new" onclick="showTransactionModal()">+ NUEVO</button>
            <button class="action-btn btn-socios" onclick="showPartners()">👥 SOCIOS</button>
            <button class="action-btn btn-morosidad" onclick="showMorosity()">📉 MOROSIDAD</button>
        </div>
        <div class="actions-row-2">
            <button class="action-btn btn-reports" onclick="showReports()">📊 VER REPORTES Y GRÁFICOS</button>
        </div>
        ` : ''}

        <div class="row mt-4">
             <div class="col-12">
                 <h4 class="mb-3 text-white">Movimientos del Club</h4>
                 <!-- Transactions Table Container -->
                 <div id="transactionsContainer">
                     <div class="table-header">
                         <div style="width: 200px;">
                             <select class="form-select bg-dark text-light border-secondary" id="txFilterType">
                                <option value="all">Todos</option>
                                <option value="income">Ingresos</option>
                                <option value="expense">Egresos</option>
                             </select>
                         </div>
                         <input type="text" class="search-bar" id="txSearch" placeholder="Buscar en todo...">
                     </div>
                     <div class="table-responsive">
                         <table class="custom-table" id="txTable">
                            <thead>
                                <tr>
                                    <th>FECHA</th>
                                    <th>TIPO</th>
                                    <th>DETALLE</th>
                                    <th>SOCIO</th>
                                    <th>MONTO</th>
                                    <th>REGISTRÓ</th>
                                </tr>
                            </thead>
                            <tbody id="txTableBody">
                                <tr><td colspan="6" class="text-center">Cargando...</td></tr>
                            </tbody>
                         </table>
                     </div>
                 </div>
             </div>
        </div>
    `;

    // Auto load transactions
    loadTransactions();

    // Bind Events (Safe binding)
    const filterSelect = document.getElementById('txFilterType');
    const searchInput = document.getElementById('txSearch');

    if (filterSelect) {
        filterSelect.addEventListener('change', filterTransactions);
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterTransactions);
        searchInput.addEventListener('keyup', filterTransactions); // Fallback
    }
}

let allTransactions = []; // Store for filtering

// Expose globally
window.filterTransactions = filterTransactions;

async function loadTransactions() {
    const tbody = document.getElementById('txTableBody');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Cargando...</td></tr>';

    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/transactions/`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!res.ok) throw new Error("Error al cargar movimientos");

        allTransactions = await res.json();
        renderTransactions(allTransactions);

    } catch (e) {
        console.error(e);
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error: ${e.message}</td></tr>`;
    }
}

function filterTransactions() {
    const typeFilter = document.getElementById('txFilterType').value;
    const searchText = document.getElementById('txSearch').value.toLowerCase();

    const filtered = allTransactions.filter(tx => {
        // 1. Type Filter
        if (typeFilter !== 'all' && tx.type !== typeFilter) return false;

        // 2. Search Filter (Search in description, category, user name, amount)
        if (searchText) {
            const dateStr = new Date(tx.date).toLocaleDateString().toLowerCase();
            const desc = (tx.description || '').toLowerCase();
            const cat = (tx.category || '').toLowerCase();

            // Check Name, Nickname AND Email
            let userStr = 'admin';
            if (tx.user) {
                userStr = [tx.user.name, tx.user.nickname, tx.user.email].filter(Boolean).join(' ').toLowerCase();
            }

            const amount = tx.amount.toString();

            return desc.includes(searchText) ||
                cat.includes(searchText) ||
                userStr.includes(searchText) ||
                amount.includes(searchText) ||
                dateStr.includes(searchText);
        }

        return true;
    });

    renderTransactions(filtered);
}

function renderTransactions(transactions) {
    const tbody = document.getElementById('txTableBody');
    const fmt = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' });

    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-white">No se encontraron movimientos.</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const isExpense = tx.type === 'expense';
        const dateObj = new Date(tx.date);
        const dateStr = dateObj.toLocaleDateString();
        const colorClass = isExpense ? 'text-danger' : 'text-success';
        const partnerName = tx.user ? (tx.user.nickname || tx.user.name) : '-';

        return `
            <tr>
                <td>${dateStr}</td>
                <td><span class="${colorClass} fw-bold">${isExpense ? 'Egreso' : 'Ingreso'}</span></td>
                <td>
                    <span class="d-block text-white">${tx.description || '-'}</span>
                </td>
                <td>
                    ${!isExpense && tx.user_id ? `<span class="badge-socio">${partnerName}</span>` : '-'}
                </td>
                <td class="fw-bold ${colorClass}">
                    ${isExpense ? '-' : '+'}${fmt.format(tx.amount)}
                </td>
                <td class="small text-muted">${tx.created_by ? (tx.created_by.nickname || tx.created_by.name) : '-'}</td> 
            </tr>
        `;
    }).join('');
}

// function showPartners(e) DEPRECATED - Embedded in Dashboard? 
// No, user can still manage partners via action button.

async function showPartners(e) {
    if (e) e.preventDefault();
    currentPage = 'partners';
    document.getElementById('content').innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>Gestión de Socios</h2>
             <button class="btn btn-success" onclick="showCreatePartnerModal()">+ Nuevo Socio</button>
        </div>
        <div id="partnersList" class="row g-3">Loading...</div>
    `;
    await loadPartners();
}

async function showMorosity() {
    // Phase 6 View
    currentPage = 'morosity';
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="card bg-dark-custom border-secondary mb-4">
            <div class="card-header text-center border-secondary">
                <h3 class="text-danger">Visión General de Deudas</h3>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-dark table-hover mb-0" id="morosityTable">
                        <thead>
                            <tr class="text-muted text-uppercase small">
                                <th>Socio</th>
                                <th>Meses Adeudados</th>
                                <th>Deuda Total</th>
                                <th style="width: 30%;">% Morosidad</th>
                            </tr>
                        </thead>
                        <tbody id="morosityBody">
                            <tr><td colspan="4" class="text-center">Cargando...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="card bg-dark-custom border-secondary">
            <div class="card-header text-center border-secondary">
                <h5 class="text-muted">Herramientas de Tesorería</h5>
            </div>
            <div class="card-body d-flex justify-content-center gap-3 align-items-center flex-wrap">
                <select id="genMonth" class="form-select bg-dark text-light border-secondary" style="width: 150px;">
                    <option value="1">Enero</option>
                    <option value="2">Febrero</option>
                    <option value="3">Marzo</option>
                    <option value="4">Abril</option>
                    <option value="5">Mayo</option>
                    <option value="6">Junio</option>
                    <option value="7">Julio</option>
                    <option value="8">Agosto</option>
                    <option value="9">Septiembre</option>
                    <option value="10">Octubre</option>
                    <option value="11">Noviembre</option>
                    <option value="12">Diciembre</option>
                </select>
                <select id="genYear" class="form-select bg-dark text-light border-secondary" style="width: auto; min-width: 100px;">
                    <option value="2025">2025</option>
                    <option value="2026" selected>2026</option>
                </select>
                <button class="btn btn-danger fw-bold" onclick="generateDebtsFromUI()">⚡ GENERAR CUOTAS</button>
            </div>
        </div>
    `;

    // Set default month
    document.getElementById('genMonth').value = new Date().getMonth() + 1;

    await loadMorosityStats();
}

async function loadMorosityStats() {
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_URL}/dashboard/morosidad`, { headers: { 'Authorization': `Bearer ${token}` } });

        if (!res.ok) {
            const errDetail = await res.json();
            throw new Error(errDetail.detail || "Error del servidor");
        }

        const data = await res.json();
        const tbody = document.getElementById('morosityBody');
        const fmt = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' });

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-success">¡Sin Morosidad!</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(item => `
            <tr>
                <td class="fw-bold">${item.user_name}</td>
                <td class="text-danger small">${item.months_str}</td>
                <td class="fw-bold text-danger">${fmt.format(item.total_debt)}</td>
                <td>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        console.error(e);
        document.getElementById('morosityBody').innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error: ${e.message}</td></tr>`;
    }
}

async function generateDebtsFromUI() {
    const month = parseInt(document.getElementById('genMonth').value);
    const year = parseInt(document.getElementById('genYear').value);
    const amount = prompt("Ingrese Monto de la Cuota:", "5000"); // Still prompt for amount for safety? Or hardcode? User said "Generar Cuotas", implied defaults or easy. Let's keep prompt for amount flex.

    if (!amount) return;

    if (!confirm(`¿Generar cuota de $${amount} para ${month} / ${year} ? `)) return;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/debts/generate`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, year, amount: parseFloat(amount) })
        });

        if (response.status === 401) {
            alert("Sesión expirada.");
            logout();
            return;
        }

        const data = await response.json();
        alert(data.message);
        loadMorosityStats(); // Refresh
    } catch (e) {
        alert(e.message);
    }
}


// Partner Management
function showCreatePartnerModal() {
    // Reset Form
    document.getElementById('partnerForm').reset();
    document.getElementById('partnerId').value = ''; // clear ID
    document.querySelector('#partnerModal .modal-title').innerText = 'Registrar Socio';
    document.getElementById('partnerEmail').disabled = false; // Enable email for new

    partnerModal = new bootstrap.Modal(document.getElementById('partnerModal'));
    partnerModal.show();
}

async function showEditPartnerModal(id, name, email, nick, phone, birth, role) {
    document.getElementById('partnerId').value = id;
    document.getElementById('partnerName').value = name;
    document.getElementById('partnerEmail').value = email;
    // document.getElementById('partnerEmail').disabled = true; // Maybe allow editing email?
    document.getElementById('partnerNick').value = nick || '';
    document.getElementById('partnerPhone').value = phone || '';

    // Date format fix if needed (yyyy-MM-dd)
    if (birth) {
        document.getElementById('partnerBirth').value = birth.split('T')[0];
    }

    document.getElementById('partnerRole').value = role;

    document.querySelector('#partnerModal .modal-title').innerText = 'Editar Socio';

    partnerModal = new bootstrap.Modal(document.getElementById('partnerModal'));
    partnerModal.show();
}

async function submitPartner() {
    const id = document.getElementById('partnerId').value;
    const name = document.getElementById('partnerName').value;
    const email = document.getElementById('partnerEmail').value;
    const nickname = document.getElementById('partnerNick').value;
    const phone_number = document.getElementById('partnerPhone').value;
    const birth_date = document.getElementById('partnerBirth').value;
    const role = document.getElementById('partnerRole').value;

    const payload = {
        name,
        email,
        nickname,
        phone_number,
        role,
        ...(birth_date && { birth_date })
    };

    const token = localStorage.getItem('access_token');
    let url = `${API_URL}/users/`;
    let method = 'POST';

    if (id) {
        // Update Mode
        url = `${API_URL}/users/${id}`;
        method = 'PUT';
    } else {
        // Create Mode
        payload.password = "123456"; // Frontend default fallback? Backend handles "DarkRiders123" if missing.
        // But backend create_partner expects password in schema.
        payload.password = "temp";
    }

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Error al guardar");
        }

        alert(id ? "Socio actualizado" : "Socio creado (Clave: DarkRiders123)");
        partnerModal.hide();
        loadPartners(); // Refresh list

    } catch (e) {
        alert(e.message);
    }
}


async function promptGenerateDebts() {
    const amount = prompt("Ingrese monto de la cuota:", "5000");
    if (!amount) return;

    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentYear = now.getFullYear();

    const monthStr = prompt("Ingrese Mes (1-12):", currentMonth);
    if (!monthStr) return;
    const yearStr = prompt("Ingrese Año:", currentYear);
    if (!yearStr) return;

    const month = parseInt(monthStr);
    const year = parseInt(yearStr);

    if (isNaN(month) || month < 1 || month > 12 || isNaN(year)) {
        return alert("Fecha inválida");
    }

    if (!confirm(`¿Generar deuda de $${amount} para ${month} / ${year} a todos los socios activos ? `)) return;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL} / debts / generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                month: month,
                year: year,
                amount: parseFloat(amount)
            })
        });

        if (!response.ok) throw new Error("Error en servidor");

        const data = await response.json();
        alert(data.message);

    } catch (e) {
        alert("Error al generar cuotas: " + e.message);
    }
}

async function loadPartners() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/users/?role=partner`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const users = await response.json();

        const container = document.getElementById('partnersList');
        if (!response.ok || users.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay socios registrados.</p>';
            return;
        }

        container.innerHTML = users.map(u => `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card-body text-center">
                    <div class="mb-3">
                        <span class="fs-1">👤</span>
                    </div>
                    <h5 class="fw-bold">${u.name || 'Sin Nombre'}</h5>
                    <p class="text-muted mb-1">${u.email}</p>
                    <span class="badge ${u.is_active ? 'bg-success' : 'bg-danger'}">${u.is_active ? 'Activo' : 'Inactivo'}</span>
                    <div class="mt-2">
                         <button class="btn btn-sm btn-outline-warning me-1" onclick="showEditPartnerModal('${u.id}', '${u.name || ''}', '${u.email}', '${u.nickname || ''}', '${u.phone_number || ''}', '${u.birth_date || ''}', '${u.role}')">✏ Editar</button>
                         <button class="btn btn-outline-info btn-sm" onclick="showMorosity()">Ver en Morosidad</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}


async function showReports() {
    currentPage = 'reports';
    const content = document.getElementById('content');
    content.innerHTML = `
        <h2 class="mb-4 text-center">📊 Reportes Financieros</h2>
        
        <div class="row g-4">
            <!-- Monthly Chart -->
            <div class="col-12 col-lg-8">
                <div class="card bg-dark-custom border-secondary h-100">
                    <div class="card-header border-secondary">
                        <h5 class="mb-0">Evolución Mensual (Ingresos vs Egresos)</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="monthlyChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Category Chart -->
            <div class="col-12 col-lg-4">
                <div class="card bg-dark-custom border-secondary h-100">
                    <div class="card-header border-secondary">
                        <h5 class="mb-0">Distribución de Gastos</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="categoryChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;

    await loadCharts();
}

async function loadCharts() {
    try {
        const token = localStorage.getItem('access_token');

        // Fetch Monthly Data
        const resMonthly = await fetch(`${API_URL}/dashboard/reports/monthly`, { headers: { 'Authorization': `Bearer ${token}` } });
        const dataMonthly = await resMonthly.json();

        // Fetch Category Data
        const resCat = await fetch(`${API_URL}/dashboard/reports/categories`, { headers: { 'Authorization': `Bearer ${token}` } });
        const dataCat = await resCat.json();

        initMonthlyChart(dataMonthly);
        initCategoryChart(dataCat);

    } catch (e) {
        console.error("Error loading charts:", e);
    }
}

function initMonthlyChart(data) {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Ingresos',
                    data: data.income,
                    backgroundColor: '#2ecc71',
                    borderRadius: 4
                },
                {
                    label: 'Egresos',
                    data: data.expense,
                    backgroundColor: '#e74c3c',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#fff' } }
            },
            scales: {
                y: {
                    ticks: { color: '#aaa' },
                    grid: { color: '#333' }
                },
                x: {
                    ticks: { color: '#aaa' },
                    grid: { display: false }
                }
            }
        }
    });
}

function initCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    '#e74c3c', '#8e44ad', '#3498db', '#f39c12', '#1abc9c', '#95a5a6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#fff' } }
            }
        }
    });
}
