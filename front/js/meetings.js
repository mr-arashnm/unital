async function loadMeetings() {
    const data = await apiFetch('/meetings');
    const tbody = document.querySelector('#meetings-table tbody');
    tbody.innerHTML = '';

    if (!data || !Array.isArray(data)) return;

    data.forEach(meeting => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${meeting.id}</td>
            <td>${meeting.title}</td>
            <td>${meeting.scheduled_date?.split('T')[0] || '-'}</td>
            <td>${meeting.scheduled_date?.split('T')[1]?.split('.')[0] || '-'}</td>
            <td>${meeting.status}</td>
        `;
        tbody.appendChild(tr);
    });
}

loadMeetings();
