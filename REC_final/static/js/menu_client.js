document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard loaded');

    // Intercepta o formulário de pagamento
    const formPagamento = document.getElementById('form_pagamento');
    if (formPagamento) {
        formPagamento.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            try {
                const response = await fetch('/api/solicitar-pagamento', {method: 'POST'});
                if (!response.ok) {
                    console.error('Erro HTTP:', response.status);
                    alert('Erro ao solicitar a conta. Status: ' + response.status);
                    return;
                }
                const text = await response.text();
                console.log('Resposta bruta:', text);
                let data;
                try {
                    data = JSON.parse(text);
                } catch (parseError) {
                    console.error('Erro ao fazer parse de JSON:', parseError);
                    console.error('Resposta recebida:', text);
                    alert('Erro ao processar resposta do servidor.');
                    return;
                }
                if (data.success) {
                    alert('✓ Conta solicitada! Um atendente virá fechar sua mesa em breve.');
                    // Desabilita o botão após solicitar
                    const btnPagamento = document.getElementById('btn_pagamento');
                    if (btnPagamento) {
                        btnPagamento.disabled = true;
                        btnPagamento.style.opacity = '0.5';
                        btnPagamento.style.cursor = 'not-allowed';
                        btnPagamento.textContent = '✓ Conta Solicitada';
                    }
                } else {
                    alert('Erro: ' + (data.message || 'Não foi possível solicitar a conta.'));
                }
            } catch (error) {
                console.error('Erro ao solicitar pagamento:', error);
                alert('Erro ao processar solicitação. Tente novamente.');
            }
        });
    }
});
