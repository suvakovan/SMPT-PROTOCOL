document.getElementById('emailForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const btn = document.getElementById('sendBtn');
    const msgDiv = document.getElementById('message');

    // Reset UI
    btn.classList.add('loading');
    btn.disabled = true;
    msgDiv.classList.add('hidden');
    msgDiv.className = 'hidden';

    // Collect Data
    const formData = {
        sender_email: document.getElementById('sender_email').value,
        password: document.getElementById('password').value,
        receiver_email: document.getElementById('receiver_email').value,
        subject: document.getElementById('subject').value,
        body: document.getElementById('body').value
    };

    try {
        const response = await fetch('/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(result.message, 'success');
            // Optional: Clear form on success
            // document.getElementById('emailForm').reset();
        } else {
            showMessage(result.message || 'Failed to send email.', 'error');
        }

    } catch (error) {
        showMessage('Network error. Check your connection.', 'error');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

function showMessage(text, type) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = text;
    msgDiv.className = type; // 'success' or 'error'
    msgDiv.classList.remove('hidden');
}
