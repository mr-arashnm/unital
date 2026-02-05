async function loadTeams() {
    const data = await apiFetch('/teams');
    const tbody = document.querySelector('#teams-table tbody');
    tbody.innerHTML = '';

    if (!data || !Array.isArray(data)) return;

    data.forEach(team => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${team.id}</td>
            <td>${team.name}</td>
            <td>${team.members ? team.members.join(', ') : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

loadTeams();
