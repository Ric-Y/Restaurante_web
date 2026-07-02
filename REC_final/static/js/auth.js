document.addEventListener("DOMContentLoaded", () => {
    const loginButton = document.getElementById("div_login");
    const registerButton = document.getElementById("div_sing_up");

    if (loginButton) {
        loginButton.addEventListener("click", function () {
            window.location.href = "/login";
        });
    }

    if (registerButton) {
        registerButton.addEventListener("click", function () {
            window.location.href = "/signup";
        });
    }

    const backButton = document.getElementById("BACK");
    if (backButton) {
        backButton.addEventListener("click", function () {
            window.location.href = "/";
        });
    }

    const form = document.getElementById("form");
    if (form) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const isLoginPage = window.location.pathname.includes("/login");
            const username = document.getElementById("username")?.value.trim() || "";
            const password = document.getElementById("password")?.value.trim() || "";
            const email = document.getElementById("email")?.value.trim() || "";

            if (!username || !password) {
                alert("Nome/Email e senha são obrigatórios.");
                return;
            }

            if (!isLoginPage && !email) {
                alert("O e-mail é obrigatório no cadastro.");
                return;
            }

            const endpoint = isLoginPage ? "/api/auth/login" : "/api/auth/signup";
            const payload = isLoginPage ? { email: username, password } : { username, email, password };

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const result = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(result.message || "Usuário ou senha inválidos.");
                }

                alert(result.message || "Sucesso");
                // Usa o redirect_url retornado pelo backend, ou fallback baseado no role
                const redirectUrl = result.redirect_url || 
                    (result.user?.role === "ADMIN" ? "/admin" : 
                     result.user?.role === "ATENDENTE" ? "/atendente" : 
                     "/cliente");
                window.location.href = redirectUrl;
            } catch (error) {
                alert(error.message);
            }
        });
    }
});
