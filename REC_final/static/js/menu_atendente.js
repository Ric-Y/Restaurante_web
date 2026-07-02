document.addEventListener("DOMContentLoaded", () => {
    const comandaId = document.body.dataset.comandaId || null;
    const total = parseFloat(document.body.dataset.comandaTotal) || 0;

    // Modal confirm fechando a comanda
    const form = document.getElementById("form_fechar_comanda");
    if (form) {
        const modal = document.getElementById("modalFechar");
        const cancelar = document.getElementById("cancelarFechar");
        const confirmarFechar = document.getElementById("confirmarFechar");
        const paymentMethodSelect = document.querySelector("[name='payment_method']");
        const amountInput = document.getElementById("amount_received");
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            if (modal) modal.classList.remove("hidden");
        });
        if (cancelar) {
            cancelar.onclick = () => { 
                if (modal) modal.classList.add("hidden");
            };
        }
        if (confirmarFechar) {
            confirmarFechar.onclick = async () => {

                const paymentMethod = paymentMethodSelect ? paymentMethodSelect.value : null;
                const amountReceived = amountInput ? parseFloat(amountInput.value) : 0;
                if (!paymentMethod) {
                    alert("Selecione a forma de pagamento.");
                    return;
                }
                if (isNaN(amountReceived) || amountReceived <= 0) {
                    alert("Informe um valor recebido válido.");
                    return;
                }
                if (amountReceived < total) {
                    alert(`Valor recebido (R$ ${amountReceived.toFixed(2)}) é menor que o total (R$ ${total.toFixed(2)})`);
                    return;
                }

                try {
                    const response = await fetch(form.action, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            payment_method: paymentMethod,
                            amount_received: amountReceived
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        alert("Comanda fechada com sucesso!");
                        if (modal) modal.classList.add("hidden");
                        window.location.href = "/atendente";
                    } else {
                        alert("Erro: " + (data.message || "Não foi possível fechar a comanda."));
                    }
                } catch (error) {
                    console.error("Erro ao fechar comanda:", error);
                    alert("Erro ao processar pagamento. Tente novamente.");
                }
            };
        }
    }

    // Troco calculo
    const amountInput = document.getElementById("amount_received");
    const changeSpan = document.getElementById("change_amount");
    if (amountInput && changeSpan) {
        amountInput.addEventListener("input", function () {
            let recebido = parseFloat(this.value);
            if (isNaN(recebido)) recebido = 0;
            let troco = recebido - total;
            if (troco < 0) troco = 0;
            changeSpan.innerText = "R$ " + troco.toFixed(2).replace(".", ",");
        });
    }

    // confirmar pagamento
    const confirmarPagamento = document.querySelector("[data-confirmar-pagamento]");
    if (confirmarPagamento) {
        confirmarPagamento.addEventListener("click", () => {
            const metodoEl = document.querySelector("[name='payment_method']");
            const metodo = metodoEl ? metodoEl.value : null;
            if (!metodo) {
                alert("Escolha a forma de pagamento.");
                return;
            }
            const payForm = confirmarPagamento.closest("form");
            if (payForm) payForm.submit();
        });
    }

    // Expose the selected comanda id globally for other scripts if needed
    window.COMANDA_SELECIONADA = comandaId ? parseInt(comandaId, 10) : null;

    // Polling: Verificar a cada 3 segundos se há mesas aguardando pagamento
    function atualizarStatusMesas() {
        fetch('/api/mesas')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.mesas) {
                    // Percorre todas as mesas e atualiza o status visual
                    data.mesas.forEach(mesa => {
                        // Procura pelo link que contém /comanda/ID
                        const cardSelector = `a.card_mesa[href*="/comanda/${mesa.id}"]`;
                        const card = document.querySelector(cardSelector);
                        if (card) {
                            // Remove classes de status anteriores
                            card.classList.remove('aguardando_pagamento', 'paga');
                            
                            // Adiciona a classe apropriada baseado no status
                            if (mesa.status === 'aguardando_pagamento') {
                                card.classList.add('aguardando_pagamento');
                            } else if (mesa.status === 'paga') {
                                card.classList.add('paga');
                            }
                        }
                    });
                }
            })
            .catch(err => console.log('Erro ao atualizar status das mesas:', err));
    }

    // Inicia o polling a cada 3 segundos
    setInterval(atualizarStatusMesas, 3000);
    // E faz uma atualização imediata quando a página carrega
    atualizarStatusMesas();
});