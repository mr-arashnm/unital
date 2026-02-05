async function loadTasks() {
    const data = await apiFetch('/tasks'); 
    const tbody = document.querySelector('#tasks-table tbody');
    tbody.innerHTML = '';

    if (!data || !Array.isArray(data)) return;

    data.forEach(task => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${task.id}</td>
            <td>${task.title}</td>
            <td>${task.team_name || '-'}</td>
            <td>${task.status}</td>
            <td>${task.due_date || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

loadTasks();
