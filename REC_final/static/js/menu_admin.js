document.addEventListener('DOMContentLoaded', () => {
    console.log('Admin Dashboard loaded');

    const menuItems = document.querySelectorAll('.menu_item');
    const sections = document.querySelectorAll('.content_section');

    async function requestJson(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'Erro ao processar solicitação');
        }
        return data;
    }

    async function loadUsuarios() {
        const listEl = document.getElementById('usuarios_list');
        listEl.innerHTML = '<p class="loading">Carregando usuários...</p>';

        try {
            const response = await requestJson('/api/admin/usuarios');

            if (response.success && response.usuarios.length > 0) {
                let html = '';
                response.usuarios.forEach(user => {
                    const statusBadge = user.active ? 
                        '<span class="badge" style="background-color: #E8F5E9; color: #2E7D32;">Ativo</span>' :
                        '<span class="badge" style="background-color: #FFEBEE; color: #C62828;">Inativo</span>';
                    
                    html += `
                        <div class="list_item">
                            <div class="item_info">
                                <div class="item_title">${user.name}</div>
                                <div class="item_subtitle">${user.email} • ${user.role}</div>
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                ${statusBadge}
                                <div class="item_actions">
                                    <button class="btn_delete" data-user-id="${user.id}">Remover</button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                listEl.innerHTML = html;
            } else {
                listEl.innerHTML = '<p class="loading">Nenhum usuário encontrado</p>';
            }
        } catch (error) {
            console.error('Erro ao carregar usuários:', error);
            listEl.innerHTML = '<p class="loading">Erro ao carregar usuários</p>';
        }
    }

    async function loadCardapio() {
        const gridEl = document.getElementById('cardapio_list');
        gridEl.innerHTML = '<p class="loading">Carregando cardápio...</p>';

        try {
            const response = await requestJson('/api/admin/cardapio');

            if (response.success && response.items.length > 0) {
                let html = '';
                response.items.forEach(item => {
                    const statusBadge = item.disponivel ? 
                        '<span class="badge" style="background-color: #E8F5E9; color: #2E7D32; font-size: 0.8em;">Disponível</span>' :
                        '<span class="badge" style="background-color: #FFEBEE; color: #C62828; font-size: 0.8em;">Indisponível</span>';
                    
                    html += `
                        <div class="cardapio_item">
                            <div class="cardapio_item_info">
                                <h4>${item.nome}</h4>
                                <p>${item.descricao || 'Sem descrição'}</p>
                                <div class="cardapio_preco">R$ ${item.preco.toFixed(2)}</div>
                                <div style="margin-bottom: 10px;">
                                    ${statusBadge}
                                </div>
                                <div class="cardapio_actions">
                                    <button class="btn_delete" data-item-id="${item.id}" style="background-color: #F44336; color: white;">Remover</button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                gridEl.innerHTML = html;
            } else {
                gridEl.innerHTML = '<p class="loading">Nenhum item no cardápio</p>';
            }
        } catch (error) {
            console.error('Erro ao carregar cardápio:', error);
            gridEl.innerHTML = '<p class="loading">Erro ao carregar cardápio</p>';
        }
    }

    async function handleAddUsuario() {
        const nome = window.prompt('Nome do funcionário:');
        if (!nome) return;

        const email = window.prompt('E-mail do funcionário:');
        if (!email) return;

        const senha = window.prompt('Senha do funcionário:');
        if (!senha) return;

        const role = window.prompt('Função (ATENDENTE, ADMIN ou CLIENTE):', 'ATENDENTE') || 'ATENDENTE';
        const body = new FormData();
        body.append('name', nome);
        body.append('email', email);
        body.append('password', senha);
        body.append('role', role.toUpperCase());

        try {
            const response = await requestJson('/api/admin/usuarios', { method: 'POST', body });
            if (response.success) {
                window.alert(response.message || 'Usuário criado com sucesso.');
                loadUsuarios();
            }
        } catch (error) {
            window.alert(error.message || 'Não foi possível criar o usuário.');
        }
    }

    async function handleAddItem() {
        const nome = window.prompt('Nome do item:');
        if (!nome) return;

        const descricao = window.prompt('Descrição do item:', '') || '';
        const preco = window.prompt('Preço do item:', '0.00');
        if (preco === null) return;

        const disponivel = window.confirm('Deseja deixar o item disponível imediatamente?');
        const body = new FormData();
        body.append('name', nome);
        body.append('description', descricao);
        body.append('price', preco);
        body.append('disponivel', disponivel ? 'true' : 'false');

        try {
            const response = await requestJson('/api/admin/cardapio', { method: 'POST', body });
            if (response.success) {
                window.alert(response.message || 'Item adicionado com sucesso.');
                loadCardapio();
            }
        } catch (error) {
            window.alert(error.message || 'Não foi possível adicionar o item.');
        }
    }

    document.getElementById('btn_novo_usuario').addEventListener('click', handleAddUsuario);
    document.getElementById('btn_novo_item').addEventListener('click', handleAddItem);

    document.addEventListener('click', async (event) => {
        const userButton = event.target.closest('[data-user-id]');
        if (userButton) {
            const userId = userButton.getAttribute('data-user-id');
            const confirmed = window.confirm('Deseja remover este usuário?');
            if (!confirmed) return;
            try {
                const response = await requestJson(`/api/admin/usuarios/${userId}`, { method: 'DELETE' });
                if (response.success) {
                    window.alert(response.message || 'Usuário removido.');
                    loadUsuarios();
                }
            } catch (error) {
                window.alert(error.message || 'Não foi possível remover o usuário.');
            }
            return;
        }

        const itemButton = event.target.closest('[data-item-id]');
        if (itemButton) {
            const itemId = itemButton.getAttribute('data-item-id');
            const confirmed = window.confirm('Deseja remover este item do cardápio?');
            if (!confirmed) return;
            try {
                const response = await requestJson(`/api/admin/cardapio/${itemId}`, { method: 'DELETE' });
                if (response.success) {
                    window.alert(response.message || 'Item removido.');
                    loadCardapio();
                }
            } catch (error) {
                window.alert(error.message || 'Não foi possível remover o item.');
            }
        }
    });

    // Função para mudar de seção
    function switchSection(sectionId) {
        // Remove classe active de todas as seções
        sections.forEach(section => section.classList.remove('active'));
        
        // Remove classe active de todos os menu items
        menuItems.forEach(item => item.classList.remove('active'));
        
        // Adiciona classe active à seção selecionada
        const selectedSection = document.getElementById(sectionId);
        if (selectedSection) {
            selectedSection.classList.add('active');
        }
        
        // Adiciona classe active ao menu item
        const selectedMenuItem = document.querySelector(`[data-section="${sectionId}"]`);
        if (selectedMenuItem) {
            selectedMenuItem.classList.add('active');
        }

        // Carrega dados específicos da seção
        if (sectionId === 'dashboard') {
            loadDashboard();
        } else if (sectionId === 'usuarios') {
            loadUsuarios();
        } else if (sectionId === 'pedidos') {
            loadPedidos();
        } else if (sectionId === 'cardapio') {
            loadCardapio();
        }
    }

    // Event listeners para menu items
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = item.dataset.section;
            switchSection(sectionId);
        });
    });

    // ====== DASHBOARD ======
    async function loadDashboard() {
        const loadingEl = document.getElementById('loading_dashboard');
        const contentEl = document.getElementById('dashboard_content');
        
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';

        try {
            const response = await fetch('/api/admin/dashboard');
            const data = await response.json();

            if (data.success) {
                updateDashboardUI(data.dashboard);
                loadingEl.style.display = 'none';
                contentEl.style.display = 'block';
            } else {
                loadingEl.textContent = 'Erro ao carregar dados';
            }
        } catch (error) {
            console.error('Erro ao carregar dashboard:', error);
            loadingEl.textContent = 'Erro ao carregar dados';
        }
    }

    function updateDashboardUI(dashboard) {
        // Mesas
        document.getElementById('stat_mesas').textContent = dashboard.mesas.ativas;
        document.getElementById('stat_mesas_desc').textContent = `de ${dashboard.mesas.total} total`;

        // Usuários
        document.getElementById('stat_usuarios').textContent = dashboard.usuarios.total;
        document.getElementById('stat_usuarios_desc').textContent = 'registrados';

        // Vendas
        document.getElementById('stat_vendas').textContent = 'R$ ' + dashboard.vendas.total.toFixed(2);
        document.getElementById('stat_vendas_desc').textContent = 'todas as transações';

        // Pedidos
        document.getElementById('stat_pedidos').textContent = dashboard.pedidos.total;
        document.getElementById('stat_pedidos_desc').textContent = 'processados';

        // Resumo usuários
        document.getElementById('resumo_clientes').textContent = dashboard.usuarios.clientes;
        document.getElementById('resumo_atendentes').textContent = dashboard.usuarios.atendentes;
        document.getElementById('resumo_admins').textContent = dashboard.usuarios.admins;

        // Resumo pedidos
        document.getElementById('resumo_pedidos_abertos').textContent = dashboard.pedidos.abertos;
        document.getElementById('resumo_pedidos_pagos').textContent = dashboard.pedidos.pagos;
        document.getElementById('resumo_pedidos_total').textContent = dashboard.pedidos.total;
    }

    // ====== PEDIDOS ======
    async function loadPedidos() {
        const listEl = document.getElementById('pedidos_list');
        listEl.innerHTML = '<p class="loading">Carregando pedidos...</p>';

        try {
            const response = await fetch('/api/admin/pedidos');
            const data = await response.json();

            if (data.success && data.pedidos.length > 0) {
                let html = '';
                data.pedidos.forEach(order => {
                    const statusColor = order.status === 'PAID' ? '#2E7D32' : 
                                      order.status === 'CLOSED' ? '#1976D2' : '#E65100';
                    const statusBg = order.status === 'PAID' ? '#E8F5E9' : 
                                    order.status === 'CLOSED' ? '#E3F2FD' : '#FFF3E0';
                    
                    const createdDate = new Date(order.created_at).toLocaleDateString('pt-BR');
                    
                    html += `
                        <div class="list_item">
                            <div class="item_info">
                                <div class="item_title">Pedido #${order.id}</div>
                                <div class="item_subtitle">Total: R$ ${order.total.toFixed(2)} • ${createdDate}</div>
                            </div>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span class="badge" style="background-color: ${statusBg}; color: ${statusColor};">${order.status}</span>
                                <div class="item_actions">
                                </div>
                            </div>
                        </div>
                    `;
                });
                listEl.innerHTML = html;
            } else {
                listEl.innerHTML = '<p class="loading">Nenhum pedido encontrado</p>';
            }
        } catch (error) {
            console.error('Erro ao carregar pedidos:', error);
            listEl.innerHTML = '<p class="loading">Erro ao carregar pedidos</p>';
        }
    }

    // Carrega o dashboard inicialmente
    loadDashboard();
});
