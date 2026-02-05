async function loadNotifications() {
    const data = await apiFetch('/notifications');
    const ul = document.getElementById('notifications-list');
    ul.innerHTML = '';

    if (!data || !Array.isArray(data)) return;

    data.forEach(note => {
        const li = document.createElement('li');
        li.innerText = `[${note.notification_type}] ${note.title} - ${note.message}`;
        ul.appendChild(li);
    });
}

loadNotifications();
