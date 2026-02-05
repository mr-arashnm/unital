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
    const message = input.value;
    if (!message.trim()) return;

    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="user-msg">You: ${message}</div>`;

    const res = await sendChat(message);
    if (res) {
        chatBox.innerHTML += `<div class="bot-msg">Bot: ${res.response_text || res.intent}</div>`;
    }

    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById('chat-form').addEventListener('submit', e => {
    e.preventDefault();
    handleChat();
});
