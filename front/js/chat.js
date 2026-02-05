// chat.js
async function sendChat(text) {
    const res = await apiFetch('/chat', {
        method: 'POST',
        body: JSON.stringify({ text })
    });
    return res;
}

async function handleChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById('chat-box');

    // User message
    chatBox.innerHTML += `
        <div class="msg user">
            ${message}
        </div>
    `;

    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // Typing indicator
    const typing = document.createElement('div');
    typing.className = 'msg bot';
    typing.id = 'typing';
    typing.innerText = 'Bot is typing...';
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;

    const res = await sendChat(message);

    // Remove typing
    typing.remove();

    if (res) {
        chatBox.innerHTML += `
            <div class="msg bot">
                ${res.response_text || res.intent}
            </div>
        `;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById('chat-form').addEventListener('submit', e => {
    e.preventDefault();
    handleChat();
});

// Send with Enter
document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') {
        e.preventDefault();
        handleChat();
    }
});
