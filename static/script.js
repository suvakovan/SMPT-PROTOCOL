// ================================================================
// SMTP PROTOCOL MAILER v2.0 — Frontend Logic
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initForm();
    initPriority();
    loadConfig();
    loadHistory();
    initInbox();
});

// ===================== NAVIGATION =====================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabName = item.dataset.tab;

            // Update active nav
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // Switch tab content
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            const target = document.getElementById('tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
            if (target) {
                target.classList.add('active');
            }

            // Load data based on tab
            if (tabName === 'history') {
                loadHistory();
            } else if (tabName === 'inbox') {
                loadInbox();
            }
        });
    });
}

// ===================== CONFIG (Fixed Sender Setup) =====================
async function loadConfig() {
    try {
        const response = await fetch('/config');
        const data = await response.json();

        // Update UI with sender info
        const senderDisplay = document.getElementById('senderDisplay');
        const senderEmail = document.getElementById('senderEmail');
        const senderName = document.getElementById('senderName');
        const senderAvatar = document.getElementById('senderAvatar');
        const connectionStatus = document.getElementById('connectionStatus');

        if (data.is_configured) {
            senderDisplay.textContent = data.sender_display;
            senderEmail.textContent = data.sender_display;
            senderName.textContent = data.sender_name;
            senderAvatar.textContent = data.sender_name.charAt(0).toUpperCase();

            // Set GitHub link
            const githubLink = document.getElementById('navGitHub');
            if (githubLink) {
                githubLink.href = data.repo_url;
            }

            connectionStatus.innerHTML = `
                <div class="status-dot connected"></div>
                <span>Connected</span>
            `;

            // Update settings page
            document.getElementById('settSenderName').textContent = data.sender_name;
            document.getElementById('settSenderEmail').textContent = data.sender_display;
            document.getElementById('settSenderStatus').innerHTML =
                '<span class="status-pill status-active">Configured</span>';
        } else {
            senderDisplay.textContent = 'Not Configured';
            senderEmail.textContent = 'Not configured — see Settings';
            senderName.textContent = 'SMTP Mailer';

            connectionStatus.innerHTML = `
                <div class="status-dot disconnected"></div>
                <span>Not Configured</span>
            `;

            document.getElementById('settSenderStatus').innerHTML =
                '<span class="status-pill status-error">Not Configured</span>';
        }

        // Always ensure GitHub link is updated if it exists in response
        if (data.repo_url) {
            const githubLink = document.getElementById('navGitHub');
            if (githubLink) {
                githubLink.href = data.repo_url;
            }
        }
    } catch (error) {
        console.error('Failed to load config:', error);
        document.getElementById('connectionStatus').innerHTML = `
            <div class="status-dot disconnected"></div>
            <span>Error</span>
        `;
    }
}

// ===================== PRIORITY SELECTOR =====================
let selectedPriority = 'normal';

function initPriority() {
    const priorityBtns = document.querySelectorAll('.priority-btn');
    priorityBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            priorityBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedPriority = btn.dataset.priority;
        });
    });
}

// ===================== EMAIL FORM =====================
function initForm() {
    const form = document.getElementById('emailForm');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearBtn');
    const bodyTextarea = document.getElementById('body');
    const charCount = document.getElementById('charCount');

    // Character counter
    bodyTextarea.addEventListener('input', () => {
        charCount.textContent = bodyTextarea.value.length;
    });

    // Clear button
    clearBtn.addEventListener('click', () => {
        form.reset();
        charCount.textContent = '0';
        selectedPriority = 'normal';
        document.querySelectorAll('.priority-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-priority="normal"]').classList.add('active');
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        sendBtn.classList.add('loading');
        sendBtn.disabled = true;
        hideToast();

        const formData = {
            receiver_email: document.getElementById('receiver_email').value.trim(),
            subject: document.getElementById('subject').value.trim(),
            body: document.getElementById('body').value.trim(),
            priority: selectedPriority
        };

        try {
            const response = await fetch('/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                showToast('success', 'Email Sent!', result.message);
                form.reset();
                charCount.textContent = '0';
                updateHistoryBadge();
            } else {
                showToast('error', 'Send Failed', result.message || 'An error occurred.');
            }
        } catch (error) {
            showToast('error', 'Network Error', 'Could not connect to the server. Check if the Flask server is running.');
        } finally {
            sendBtn.classList.remove('loading');
            sendBtn.disabled = false;
        }
    });
}

// ===================== TOAST NOTIFICATIONS =====================
function showToast(type, title, message) {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    const toastClose = document.getElementById('toastClose');

    toast.className = `toast ${type}`;
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    toastIcon.textContent = type === 'success' ? '✓' : '✕';

    toastClose.onclick = () => hideToast();

    // Auto-hide after 6 seconds
    clearTimeout(window._toastTimeout);
    window._toastTimeout = setTimeout(() => hideToast(), 6000);
}

function hideToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('hidden');
}

// ===================== EMAIL HISTORY =====================
async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        const historyList = document.getElementById('historyList');
        const emptyHistory = document.getElementById('emptyHistory');
        const badge = document.getElementById('historyBadge');

        badge.textContent = data.history.length;

        if (data.history.length === 0) {
            historyList.innerHTML = '';
            historyList.appendChild(emptyHistory);
            emptyHistory.style.display = 'flex';
            return;
        }

        historyList.innerHTML = data.history.map((item, index) => `
            <div class="history-item" style="animation-delay: ${index * 0.05}s">
                <div class="history-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                </div>
                <div class="history-details">
                    <div class="history-to">${escapeHtml(item.to)}</div>
                    <div class="history-subject">${escapeHtml(item.subject)}</div>
                </div>
                <div class="history-meta">
                    <span class="history-time">${item.timestamp}</span>
                    <span class="history-priority ${item.priority}">${item.priority}</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function updateHistoryBadge() {
    const badge = document.getElementById('historyBadge');
    const current = parseInt(badge.textContent) || 0;
    badge.textContent = current + 1;
}

// Refresh history button
document.getElementById('refreshHistory')?.addEventListener('click', loadHistory);

// ===================== EMAIL INBOX =====================
function initInbox() {
    document.getElementById('refreshInbox')?.addEventListener('click', loadInbox);
}

async function loadInbox() {
    const inboxList = document.getElementById('inboxList');
    const emptyInbox = document.getElementById('emptyInbox');
    const refreshBtn = document.getElementById('refreshInbox');

    try {
        refreshBtn.classList.add('loading-spin');
        const response = await fetch('/receive');
        const data = await response.json();

        if (data.status === 'success') {
            if (data.emails.length === 0) {
                inboxList.innerHTML = '';
                inboxList.appendChild(emptyInbox);
                emptyInbox.style.display = 'flex';
                return;
            }

            inboxList.innerHTML = data.emails.map((email, index) => `
                <div class="history-item inbox-item" style="animation-delay: ${index * 0.05}s">
                    <div class="history-icon inbox-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,13 2,6"/>
                        </svg>
                    </div>
                    <div class="history-details">
                        <div class="history-to">From: ${escapeHtml(email.from)}</div>
                        <div class="history-subject">${escapeHtml(email.subject)}</div>
                        <div class="history-snippet">${escapeHtml(email.snippet)}</div>
                    </div>
                    <div class="history-meta">
                        <span class="history-time">${email.date}</span>
                    </div>
                </div>
            `).join('');
        } else {
            showToast('error', 'Fetch Failed', data.message);
        }
    } catch (error) {
        console.error('Failed to load inbox:', error);
        showToast('error', 'Fetch Error', 'Failed to connect to email server.');
    } finally {
        refreshBtn.classList.remove('loading-spin');
    }
}

// ===================== UTILITIES =====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
