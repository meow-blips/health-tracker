/* ═══════════════════════════════════════════════════════════════════════════
   HealthTrack — Main JavaScript
   Handles dashboard interactivity, API calls, charts, and animations
   ═══════════════════════════════════════════════════════════════════════════ */

// ─── Utility ────────────────────────────────────────────────────────────────

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}

async function apiPost(url, formData) {
    const res = await fetch(url, { method: 'POST', body: formData });
    if (res.status === 401) { window.location.href = '/login'; return null; }
    return res.json();
}

async function apiGet(url) {
    const res = await fetch(url);
    if (res.status === 401) { window.location.href = '/login'; return null; }
    return res.json();
}

async function apiDelete(url) {
    const res = await fetch(url, { method: 'DELETE' });
    return res.json();
}

// ─── Password Toggle ────────────────────────────────────────────────────────

function togglePassword(id) {
    const input = document.getElementById(id);
    input.type = input.type === 'password' ? 'text' : 'password';
}

// ─── Password Strength Indicator ────────────────────────────────────────────

const pwInput = document.getElementById('reg_password');
if (pwInput) {
    pwInput.addEventListener('input', () => {
        const val = pwInput.value;
        const bar = document.querySelector('.strength-bar');
        if (!bar) return;
        let strength = 0;
        if (val.length >= 8) strength++;
        if (/[A-Z]/.test(val)) strength++;
        if (/[0-9]/.test(val)) strength++;
        if (/[^A-Za-z0-9]/.test(val)) strength++;
        const pct = strength * 25;
        const colors = ['#ef4444', '#f59e0b', '#f59e0b', '#22c55e'];
        bar.style.width = pct + '%';
        bar.style.background = colors[strength - 1] || '#e2e8f0';
    });
}

// ─── Multi-Step Registration ────────────────────────────────────────────────

let currentStep = 1;

function nextStep(step) {
    if (step === 2) {
        const username = document.getElementById('username');
        const email = document.getElementById('reg_email');
        const password = document.getElementById('reg_password');
        if (!username.value || !email.value || !password.value) {
            showToast('Please fill in all required fields.', 'error');
            return;
        }
        if (password.value.length < 8) {
            showToast('Password must be at least 8 characters.', 'error');
            return;
        }
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email.value)) {
            showToast('Please enter a valid email address.', 'error');
            return;
        }
    }

    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById(`step${step}`).classList.add('active');

    document.querySelectorAll('.step').forEach(s => {
        const n = parseInt(s.dataset.step);
        s.classList.toggle('active', n === step);
        s.classList.toggle('completed', n < step);
    });

    currentStep = step;
    lucide.createIcons();
}

function prevStep(step) {
    nextStep(step);
}

// ─── BMI Preview on Registration ────────────────────────────────────────────

const heightInput = document.getElementById('height_cm');
const weightInput = document.getElementById('weight_kg');
if (heightInput && weightInput) {
    const calcBmiPreview = () => {
        const h = parseFloat(heightInput.value);
        const w = parseFloat(weightInput.value);
        const preview = document.getElementById('bmiPreview');
        if (h > 0 && w > 0) {
            const bmi = w / ((h / 100) ** 2);
            const pct = Math.min(Math.max((bmi - 15) / 25 * 100, 0), 100);
            document.getElementById('bmiPointer').style.left = pct + '%';
            document.getElementById('bmiValue').textContent = `BMI: ${bmi.toFixed(1)}`;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    };
    heightInput.addEventListener('input', calcBmiPreview);
    weightInput.addEventListener('input', calcBmiPreview);
}

// ─── Feature Card Animation (Landing Page) ──────────────────────────────────

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('[data-aos]').forEach(el => observer.observe(el));

// ─── Dashboard Logic ────────────────────────────────────────────────────────

const isDashboard = document.querySelector('.dashboard');

if (isDashboard) {
    const dateEl = document.getElementById('dashDate');
    if (dateEl) {
        dateEl.textContent = new Date().toLocaleDateString('en-US', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
    }

    initDashboard();
}

// ─── Tab Switching ──────────────────────────────────────────────────────────

function switchTab(name) {
    document.querySelectorAll('.dash-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.toggle('active', t.id === `tab-${name}`));

    if (name === 'trends') loadTrends();
    if (name === 'meds') loadMedications();
    if (name === 'period') loadPeriodPhase();
    if (name === 'overview') refreshOverview();
    if (name === 'log') { loadAllergies(); }

    lucide.createIcons();
}

// ─── Dashboard Init ─────────────────────────────────────────────────────────

async function initDashboard() {
    await refreshOverview();
    loadHeatmap();
    loadAllergies();
    if (typeof USER_GENDER !== 'undefined' && USER_GENDER === 'female') loadPeriodPhase();
    updateBmiGauge();

    const params = new URLSearchParams(window.location.search);
    if (params.get('tab')) switchTab(params.get('tab'));
}

async function refreshOverview() {
    const data = await apiGet('/api/dashboard/summary');
    if (!data) return;

    waterGoalMl = data.water_goal_ml || 3000;
    const waterPct = Math.min(data.water_ml / waterGoalMl, 1);
    const exPct = Math.min(data.exercise_min / data.exercise_goal, 1);
    const overall = Math.round((waterPct + exPct) / 2 * 100);

    animateRing('ringWater', waterPct, 88);
    animateRing('ringExercise', exPct, 56);

    const pctEl = document.getElementById('ringPct');
    if (pctEl) pctEl.textContent = overall + '%';

    const wLiters = (data.water_ml / 1000).toFixed(1);
    setText('legendWater', `${wLiters}L`);
    setText('legendEx', `${Math.round(data.exercise_min)} min`);
    setText('statEx', Math.round(data.exercise_min));
    setText('statSleep', data.sleep_hours);
    updateWaterUI(data.water_ml);

    if (data.mood > 0) {
        document.querySelectorAll('.mood-btn').forEach(b => {
            b.classList.toggle('active', parseInt(b.dataset.mood) === data.mood);
        });
    }
}

function animateRing(id, pct, radius) {
    const el = document.getElementById(id);
    if (!el) return;
    const circumference = 2 * Math.PI * radius;
    const dashArray = pct * circumference;
    el.style.transition = 'stroke-dasharray 1s ease';
    el.setAttribute('stroke-dasharray', `${dashArray} ${circumference}`);
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function updateBmiGauge() {
    if (typeof USER_BMI === 'undefined' || USER_BMI === null) return;
    const pct = Math.min(Math.max((USER_BMI - 15) / 25 * 100, 0), 100);
    const pointer = document.getElementById('dashBmiPointer');
    if (pointer) pointer.style.left = pct + '%';
}

// ─── Heatmap ────────────────────────────────────────────────────────────────

async function loadHeatmap() {
    const data = await apiGet('/api/dashboard/heatmap');
    if (!data) return;
    const grid = document.getElementById('heatmapGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const today = new Date();
    for (let i = 90; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const key = d.toISOString().split('T')[0];
        const level = data[key] || 0;
        const cell = document.createElement('div');
        cell.className = `heatmap-cell level-${Math.min(level, 5)}`;
        cell.title = `${key}: ${level} tracker${level !== 1 ? 's' : ''} logged`;
        grid.appendChild(cell);
    }
}

// ─── Water (liter-based) ────────────────────────────────────────────────────

let waterGoalMl = 3000;

function updateWaterUI(ml) {
    const liters = (ml / 1000).toFixed(1);
    const goalLiters = (waterGoalMl / 1000).toFixed(1);
    setText('waterLiters', liters);
    setText('waterMl', ml);
    setText('waterGoalLiters', goalLiters);
    setText('waterRingCount', liters);
    setText('statWater', liters + 'L');

    const pct = Math.min(ml / waterGoalMl, 1);
    const ring = document.getElementById('waterRingMini');
    if (ring) {
        const circ = 2 * Math.PI * 34;
        ring.style.transition = 'stroke-dasharray .6s ease';
        ring.setAttribute('stroke-dasharray', `${pct * circ} ${circ}`);
    }

    const limitMsg = document.getElementById('waterLimitMsg');
    if (limitMsg) limitMsg.style.display = ml >= 6000 ? 'block' : 'none';

    document.querySelectorAll('.water-btn').forEach(btn => {
        btn.disabled = ml >= 6000;
        btn.style.opacity = ml >= 6000 ? '0.4' : '1';
    });
}

async function addWaterMl(amount) {
    const fd = new FormData();
    fd.append('ml', amount);
    const data = await apiPost('/api/water', fd);
    if (data) {
        updateWaterUI(data.ml);
        if (data.at_limit) {
            showToast('Daily water limit reached (6L)', 'error');
        } else {
            const added = amount >= 1000 ? `${amount/1000}L` : `${amount}ml`;
            showToast(`+${added} water logged!`);
        }
        refreshOverview();
    }
}

async function quickLogWater() {
    await addWaterMl(250);
}

function logWater(e) {
    e.preventDefault();
    addWaterMl(250);
    return false;
}

// ─── Exercise ───────────────────────────────────────────────────────────────

async function logExercise(e) {
    e.preventDefault();
    const form = document.getElementById('exerciseForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/exercise', fd);
    if (data) {
        form.reset();
        showToast(`Exercise logged: ${data.duration} min`);
        refreshOverview();
    }
    return false;
}

// ─── Sleep ──────────────────────────────────────────────────────────────────

function setSleepQuality(val) {
    document.getElementById('sleepQualityInput').value = val;
    document.querySelectorAll('#sleepStars .star').forEach(s => {
        s.classList.toggle('active', parseInt(s.dataset.val) <= val);
    });
}

async function logSleep(e) {
    e.preventDefault();
    const form = document.getElementById('sleepForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/sleep', fd);
    if (data) {
        form.reset();
        showToast(`Sleep logged: ${data.hours} hours`);
        refreshOverview();
    }
    return false;
}

// ─── Mood ───────────────────────────────────────────────────────────────────

async function logMoodQuick(val) {
    const fd = new FormData();
    fd.append('mood', val);
    fd.append('energy', 3);
    fd.append('stress', 3);
    const data = await apiPost('/api/mood', fd);
    if (data) {
        document.querySelectorAll('.mood-btn').forEach(b => {
            b.classList.toggle('active', parseInt(b.dataset.mood) === val);
        });
        showToast('Mood logged!');
    }
}

async function logMood(e) {
    e.preventDefault();
    const form = document.getElementById('moodForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/mood', fd);
    if (data) {
        showToast('Mood & energy logged!');
        refreshOverview();
    }
    return false;
}

// ─── Allergies ──────────────────────────────────────────────────────────────

async function addAllergy(e) {
    e.preventDefault();
    const form = document.getElementById('allergyForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/allergies', fd);
    if (data) {
        form.reset();
        showToast('Allergy added!');
        loadAllergies();
    }
    return false;
}

async function loadAllergies() {
    const data = await apiGet('/api/allergies');
    if (!data) return;
    const list = document.getElementById('allergyList');
    if (list) {
        if (data.length === 0) {
            list.innerHTML = '<p class="empty-state">No allergies recorded</p>';
        } else {
            list.innerHTML = data.map(a => `
                <div class="allergy-item">
                    <div>
                        <strong>${a.allergen}</strong>
                        <span class="allergy-tag ${a.severity}">${a.severity}</span>
                        ${a.reaction ? `<br><small>${a.reaction}</small>` : ''}
                    </div>
                    <button class="delete-btn" onclick="deleteAllergy(${a.id})">&times;</button>
                </div>
            `).join('');
        }
    }

    const emergencyList = document.getElementById('emergencyAllergies');
    if (emergencyList) {
        if (data.length === 0) {
            emergencyList.innerHTML = '<p>No allergies on file.</p>';
        } else {
            emergencyList.innerHTML = data.map(a => `
                <div class="emergency-allergy-item">
                    <strong>${a.allergen}</strong> — <span style="text-transform:uppercase">${a.severity}</span>
                    ${a.reaction ? `<p>Reaction: ${a.reaction}</p>` : ''}
                    ${a.contact ? `<p>Contact: ${a.contact} — ${a.phone}</p>` : ''}
                </div>
            `).join('');
        }
    }
}

async function deleteAllergy(id) {
    await apiDelete(`/api/allergies/${id}`);
    loadAllergies();
}

// ─── Emergency Card Modal ───────────────────────────────────────────────────

function showEmergencyCard() {
    loadAllergies();
    document.getElementById('emergencyModal').classList.add('open');
}

function closeEmergencyCard() {
    document.getElementById('emergencyModal').classList.remove('open');
}

// ─── Medications ────────────────────────────────────────────────────────────

async function addMedication(e) {
    e.preventDefault();
    const form = document.getElementById('medForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/medications', fd);
    if (data) {
        form.reset();
        showToast('Medication added!');
        loadMedications();
    }
    return false;
}

async function loadMedications() {
    const data = await apiGet('/api/medications');
    if (!data) return;
    const list = document.getElementById('medList');
    if (!list) return;
    if (data.length === 0) {
        list.innerHTML = '<p class="empty-state">No active medications</p>';
        return;
    }
    list.innerHTML = data.map(m => `
        <div class="med-item">
            <div class="med-info">
                <div class="med-name">${m.name}</div>
                <div class="med-dosage">${m.dosage} · ${m.frequency} · ${m.time}</div>
                <div class="med-pills ${m.needs_refill ? 'low' : ''}">${m.pills_remaining} pills left${m.needs_refill ? ' — REFILL NEEDED' : ''}</div>
            </div>
            <div class="med-actions">
                <button class="med-take-btn" onclick="takeMed(${m.id})">Take</button>
                <button class="delete-btn" onclick="deleteMed(${m.id})">&times;</button>
            </div>
        </div>
    `).join('');
}

async function takeMed(id) {
    const data = await apiPost(`/api/medications/${id}/take`, new FormData());
    if (data) {
        showToast(data.needs_refill ? 'Taken! Refill needed soon.' : 'Medication taken!',
                  data.needs_refill ? 'error' : 'success');
        loadMedications();
    }
}

async function deleteMed(id) {
    await apiDelete(`/api/medications/${id}`);
    showToast('Medication removed.');
    loadMedications();
}

// ─── Period Tracker ─────────────────────────────────────────────────────────

async function logPeriod(e) {
    e.preventDefault();
    const form = document.getElementById('periodForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/period', fd);
    if (data) {
        showToast(`Logged: ${data.phase} (Day ${data.cycle_day})`);
        loadPeriodPhase();
    }
    return false;
}

async function loadPeriodPhase() {
    const data = await apiGet('/api/period/phase');
    if (!data || !data.phase) return;

    setText('phaseName', data.phase.charAt(0).toUpperCase() + data.phase.slice(1));
    setText('phaseDay', `Day ${data.cycle_day}`);

    const phaseColors = {
        menstrual: '#f43f5e', follicular: '#22c55e',
        ovulatory: '#f59e0b', luteal: '#8b5cf6'
    };
    const circle = document.getElementById('phaseCircle');
    if (circle) circle.style.borderColor = phaseColors[data.phase] || '#6366f1';

    const phaseName = document.getElementById('phaseName');
    if (phaseName) phaseName.style.color = phaseColors[data.phase] || '#6366f1';

    document.documentElement.setAttribute('data-phase', data.phase);

    const pct = Math.min(((data.cycle_day || 1) - 1) / 27 * 100, 100);
    const marker = document.getElementById('phaseMarker');
    if (marker) marker.style.left = pct + '%';
}

// ─── Trends / Charts ────────────────────────────────────────────────────────

let trendChart, waterChartInst, sleepChartInst;

async function loadTrends() {
    const data = await apiGet('/api/dashboard/trends');
    if (!data) return;

    const labels = data.map(d => d.label);
    const calories = data.map(d => d.calories);
    const exercise = data.map(d => d.exercise_burned);
    const water = data.map(d => d.water_ml ? (d.water_ml / 1000).toFixed(1) : 0);
    const sleep = data.map(d => d.sleep);

    const chartFont = { family: "'Outfit', sans-serif", weight: '600' };
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const gridColor = isLight ? 'rgba(0,0,0,.06)' : 'rgba(255,255,255,.05)';
    const tickColor = isLight ? 'rgba(90,80,120,.7)' : 'rgba(165,160,208,.7)';
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { font: chartFont, color: tickColor } } },
        scales: {
            x: { grid: { color: gridColor }, ticks: { font: chartFont, color: tickColor } },
            y: { beginAtZero: true, grid: { color: gridColor }, ticks: { font: chartFont, color: tickColor } }
        }
    };

    if (trendChart) trendChart.destroy();
    const tCtx = document.getElementById('trendChart');
    if (tCtx) {
        trendChart = new Chart(tCtx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Calories Consumed',
                        data: calories,
                        borderColor: '#fbbf24',
                        backgroundColor: 'rgba(251,191,36,.1)',
                        tension: 0.4, fill: true, borderWidth: 3,
                    },
                    {
                        label: 'Calories Burned',
                        data: exercise,
                        borderColor: '#34d399',
                        backgroundColor: 'rgba(52,211,153,.1)',
                        tension: 0.4, fill: true, borderWidth: 3,
                    }
                ]
            },
            options: commonOptions,
        });
    }

    if (waterChartInst) waterChartInst.destroy();
    const wCtx = document.getElementById('waterChart');
    if (wCtx) {
        waterChartInst = new Chart(wCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Liters',
                    data: water,
                    backgroundColor: 'rgba(56,189,248,.5)',
                    hoverBackgroundColor: 'rgba(56,189,248,.8)',
                    borderRadius: 8,
                }]
            },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false } } },
        });
    }

    if (sleepChartInst) sleepChartInst.destroy();
    const sCtx = document.getElementById('sleepChart');
    if (sCtx) {
        sleepChartInst = new Chart(sCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Hours',
                    data: sleep,
                    backgroundColor: 'rgba(167,139,250,.5)',
                    hoverBackgroundColor: 'rgba(167,139,250,.8)',
                    borderRadius: 8,
                }]
            },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false } } },
        });
    }
}
