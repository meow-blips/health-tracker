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
    if (name === 'period') { loadPeriodPhase(); loadPeriodCalendar(); loadPeriodInsights(); applyDiscreetMode(); }
    if (name === 'overview') refreshOverview();
    if (name === 'log') { loadAllergies(); }

    lucide.createIcons();
}

// ─── Dashboard Init ─────────────────────────────────────────────────────────

async function initDashboard() {
    await refreshOverview();
    loadHeatmap();
    loadAllergies();
    if (typeof USER_GENDER !== 'undefined' && USER_GENDER === 'female') {
        loadPeriodPhase();
        loadPeriodCalendar();
        loadPeriodInsights();
        applyDiscreetMode();
    }
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

// ─── Period Tracker (Smart Prediction, Calendar, Symptoms, Insights) ────────

const PHASE_COLORS = {
    menstrual: '#f43f5e', follicular: '#22c55e',
    ovulatory: '#f59e0b', luteal: '#8b5cf6'
};

const SYMPTOM_LIST = [
    'cramps', 'headache', 'bloating', 'fatigue', 'mood swings',
    'back pain', 'nausea', 'breast tenderness', 'acne', 'insomnia',
    'cravings', 'dizziness', 'irritability', 'anxiety'
];

let calMonth = new Date().getMonth() + 1;
let calYear = new Date().getFullYear();
let symptomModalDate = null;

async function logPeriod(e) {
    e.preventDefault();
    const form = document.getElementById('periodForm');
    const fd = new FormData(form);
    const data = await apiPost('/api/period', fd);
    if (data) {
        showToast(`Logged: ${data.phase} (Day ${data.cycle_day})`);
        loadPeriodPhase();
        loadPeriodCalendar();
    }
    return false;
}

async function loadPeriodPhase() {
    const data = await apiGet('/api/period/phase');
    if (!data || !data.phase) return;

    const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '--';
    setText('phaseName', cap(data.phase));
    setText('phaseDay', `Day ${data.cycle_day}`);

    const circle = document.getElementById('phaseCircle');
    if (circle) {
        circle.style.borderColor = PHASE_COLORS[data.phase] || '#6366f1';
        circle.style.boxShadow = `0 0 25px ${PHASE_COLORS[data.phase] || '#6366f1'}30`;
    }
    const phaseName = document.getElementById('phaseName');
    if (phaseName) phaseName.style.color = PHASE_COLORS[data.phase] || '#6366f1';

    document.documentElement.setAttribute('data-phase', data.phase);

    const cycleLen = data.cycle_length || 28;
    const pct = Math.min(((data.cycle_day || 1) - 1) / (cycleLen - 1) * 100, 100);
    const marker = document.getElementById('phaseMarker');
    if (marker) marker.style.left = pct + '%';

    // Countdown ring
    const daysUntil = data.days_until_period;
    setText('countdownDays', daysUntil != null ? daysUntil : '--');
    if (data.next_period_date) {
        const nd = new Date(data.next_period_date + 'T00:00:00');
        setText('countdownDate', nd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }));
    }

    const arc = document.getElementById('countdownArc');
    if (arc && daysUntil != null) {
        const circumference = 2 * Math.PI * 52;
        const progress = Math.max(0, 1 - (daysUntil / cycleLen));
        arc.style.strokeDashoffset = circumference * (1 - progress);
    }

    // Exercise tip
    const tipEl = document.getElementById('phaseTip');
    const tipText = document.getElementById('phaseTipText');
    if (tipEl && tipText && data.exercise_tip) {
        tipText.textContent = data.exercise_tip;
        tipEl.style.display = 'flex';
    }

    // Irregularity alert
    const alertEl = document.getElementById('irregularityAlert');
    const alertText = document.getElementById('irregularityText');
    if (alertEl && alertText) {
        if (data.irregularity && data.irregularity.alert) {
            alertText.textContent = data.irregularity.message;
            alertEl.style.display = 'flex';
        } else {
            alertEl.style.display = 'none';
        }
    }
}

// ─── Interactive Calendar ──────────────────────────────────

async function loadPeriodCalendar() {
    const data = await apiGet(`/api/period/calendar?month=${calMonth}&year=${calYear}`);
    if (!data) return;

    const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    setText('calMonthTitle', `${monthNames[calMonth - 1]} ${calYear}`);

    const grid = document.getElementById('calGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const dayHeaders = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    dayHeaders.forEach(d => {
        const el = document.createElement('div');
        el.className = 'cal-day-header';
        el.textContent = d;
        grid.appendChild(el);
    });

    const firstDay = new Date(calYear, calMonth - 1, 1).getDay();
    const daysInMonth = new Date(calYear, calMonth, 0).getDate();
    const todayStr = new Date().toISOString().slice(0, 10);

    const fertileStart = data.fertile_window ? data.fertile_window.start : null;
    const fertileEnd = data.fertile_window ? data.fertile_window.end : null;
    const predictedSet = new Set(data.predicted_period || []);

    for (let i = 0; i < firstDay; i++) {
        const el = document.createElement('div');
        el.className = 'cal-day empty';
        grid.appendChild(el);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${calYear}-${String(calMonth).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
        const el = document.createElement('div');
        el.className = 'cal-day';
        el.textContent = day;

        if (dateStr === todayStr) el.classList.add('today');

        const flow = data.period_dates[dateStr];
        if (flow) {
            el.classList.add('period-day');
            if (flow === 'heavy') el.classList.add('heavy');
        }

        if (fertileStart && fertileEnd && dateStr >= fertileStart && dateStr <= fertileEnd && !flow) {
            el.classList.add('fertile-day');
        }

        if (predictedSet.has(dateStr) && !flow) {
            el.classList.add('predicted-day');
        }

        if (data.symptom_dates[dateStr]) {
            el.classList.add('has-symptoms');
        }

        el.addEventListener('click', () => openSymptomModal(dateStr));
        grid.appendChild(el);
    }
}

function changeCalMonth(delta) {
    calMonth += delta;
    if (calMonth > 12) { calMonth = 1; calYear++; }
    if (calMonth < 1) { calMonth = 12; calYear--; }
    loadPeriodCalendar();
    lucide.createIcons();
}

// ─── Symptom Quick-Log Modal ───────────────────────────────

async function openSymptomModal(dateStr) {
    symptomModalDate = dateStr;
    const d = new Date(dateStr + 'T00:00:00');
    setText('symptomModalDate', d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));

    const chips = document.getElementById('symptomChips');
    chips.innerHTML = '';
    SYMPTOM_LIST.forEach(s => {
        const chip = document.createElement('span');
        chip.className = 'symptom-chip';
        chip.textContent = s;
        chip.addEventListener('click', () => logSymptomChip(s, chip));
        chips.appendChild(chip);
    });

    document.getElementById('symptomModal').style.display = 'flex';
    await loadSymptomsForDate(dateStr);
}

function closeSymptomModal() {
    document.getElementById('symptomModal').style.display = 'none';
    symptomModalDate = null;
}

async function logSymptomChip(symptom, chipEl) {
    const fd = new FormData();
    fd.append('symptom', symptom);
    fd.append('severity', 2);
    fd.append('log_date', symptomModalDate);
    const res = await apiPost('/api/period/symptom', fd);
    if (res) {
        chipEl.classList.add('active');
        showToast(`Logged: ${symptom}`);
        await loadSymptomsForDate(symptomModalDate);
        loadPeriodCalendar();
    }
}

async function loadSymptomsForDate(dateStr) {
    const data = await apiGet(`/api/period/symptoms?log_date=${dateStr}`);
    const logged = document.getElementById('symptomLogged');
    if (!logged || !data) return;
    logged.innerHTML = '';
    if (data.length === 0) {
        logged.innerHTML = '<p style="font-size:13px;color:var(--text-muted);text-align:center">No symptoms logged for this date</p>';
        return;
    }
    data.forEach(s => {
        const row = document.createElement('div');
        row.className = 'symptom-logged-item';
        const severityLabels = { 1: 'Mild', 2: 'Moderate', 3: 'Severe' };
        row.innerHTML = `<span>${s.symptom} <small style="color:var(--text-light)">(${severityLabels[s.severity] || 'Moderate'})</small></span>
            <button onclick="deleteSymptom(${s.id})">&times;</button>`;
        logged.appendChild(row);
    });

    document.querySelectorAll('.symptom-chip').forEach(chip => {
        const isLogged = data.some(s => s.symptom === chip.textContent);
        chip.classList.toggle('active', isLogged);
    });
}

async function deleteSymptom(id) {
    const res = await apiDelete(`/api/period/symptom/${id}`);
    if (res) {
        await loadSymptomsForDate(symptomModalDate);
        loadPeriodCalendar();
    }
}

// ─── Cycle Insights ────────────────────────────────────────

async function loadPeriodInsights() {
    const data = await apiGet('/api/period/insights');
    const el = document.getElementById('insightsContent');
    if (!el || !data) return;

    let html = '';
    html += `<div class="insight-row"><strong>Avg cycle length:</strong>&nbsp;${data.cycle_length} days</div>`;

    if (data.irregularity && data.irregularity.alert) {
        html += `<div class="insight-row" style="color:var(--accent-red)">
            <i data-lucide="alert-triangle" style="width:14px;height:14px;flex-shrink:0"></i>&nbsp;${data.irregularity.message}</div>`;
    }

    const phases = ['menstrual', 'follicular', 'ovulatory', 'luteal'];
    const phaseLabels = { menstrual: 'Menstrual', follicular: 'Follicular', ovulatory: 'Ovulatory', luteal: 'Luteal' };
    phases.forEach(p => {
        const ps = data.phase_stats[p];
        if (!ps) return;
        let detail = `Avg exercise: ${ps.avg_exercise_min} min`;
        if (ps.avg_energy != null) detail += ` | Energy: ${ps.avg_energy}/5`;
        html += `<div class="insight-row">
            <span class="insight-phase-dot ${p}"></span>
            <span><strong>${phaseLabels[p]}:</strong> ${detail}</span></div>`;
        if (ps.exercise_tip) {
            html += `<div class="insight-row" style="padding-left:22px;font-size:12px;color:var(--accent-green)">
                <i data-lucide="lightbulb" style="width:12px;height:12px;flex-shrink:0"></i>&nbsp;${ps.exercise_tip}</div>`;
        }
    });

    if (data.top_symptoms && data.top_symptoms.length > 0) {
        html += '<div class="insight-row" style="border-bottom:none"><strong>Top symptoms (90 days):</strong></div>';
        const maxCount = data.top_symptoms[0].count;
        data.top_symptoms.forEach(s => {
            const pct = Math.max(10, (s.count / maxCount) * 100);
            html += `<div class="insight-row" style="flex-direction:column;align-items:flex-start;padding:4px 0;border-bottom:none">
                <span>${s.symptom} (${s.count}x)</span>
                <div class="top-symptom-bar" style="width:${pct}%"></div></div>`;
        });
    }

    el.innerHTML = html;
    lucide.createIcons();
}

// ─── Discreet Mode ─────────────────────────────────────────

async function toggleDiscreetMode() {
    const res = await apiPost('/api/period/discreet', new FormData());
    if (res) {
        DISCREET_MODE = res.discreet_mode;
        applyDiscreetMode();
        showToast(DISCREET_MODE ? 'Discreet mode on' : 'Discreet mode off');
    }
}

function applyDiscreetMode() {
    const periodTab = document.getElementById('tab-period');
    if (!periodTab) return;
    periodTab.classList.toggle('discreet', !!DISCREET_MODE);
    const icon = document.getElementById('discreetIcon');
    if (icon) icon.setAttribute('data-lucide', DISCREET_MODE ? 'eye' : 'eye-off');
    lucide.createIcons();
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
