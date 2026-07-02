import hashlib
import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from flask_sqlalchemy import SQLAlchemy

MESAS = {}
PROXIMO_NUMERO_AVULSO = 1000  # legado; o fallback atual agora é derivado da sessão

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, "templates"), static_folder=os.path.join(PROJECT_ROOT, "static"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", "mobonga-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "mysql+pymysql://flask:FragilX@localhost:3306/restauranteMobonga"
)
db = SQLAlchemy(app)


class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def to_dict(self):
        return {"id": self.id, "nome": self.name, "descricao": self.description or "", "preco": float(self.price), "disponivel": bool(self.available)}


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("CLIENTE", "ATENDENTE", "ADMIN"), nullable=False, default="CLIENTE")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    closed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.Enum("OPEN", "CLOSED", "PAID"), default="OPEN")
    total = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    closed_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    payment_method = db.Column(db.Enum("Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    amount_received = db.Column(db.Numeric(10, 2), nullable=False)
    change_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())


# identifica o usuário atual com base na sessão e sua mesa (o ID da sessão é usado para gerar o ID da mesa)

def usuario_atual():
    u = session.get("user") or {}
    return {"id": u.get("id"), "name": u.get("name") or "Cliente", "role": u.get("role") or "CLIENTE"}


def get_or_criar_mesa(numero_mesa, ativa=False):
    mesa = MESAS.setdefault(numero_mesa, {
        "id": numero_mesa,
        "numero_mesa": numero_mesa,
        "itens": [],
        "total": 0.0,
        "ativa": False,
        "status": "aberta",
    })
    if ativa:
        mesa["ativa"] = True
    return mesa


def _fallback_mesa_id():
    seed = session.get("_mesa_seed")
    if not seed:
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        seed = request.cookies.get(cookie_name)
        if not seed:
            seed = f"anon-{os.urandom(8).hex()}"
        session["_mesa_seed"] = seed

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return 100_000 + int.from_bytes(digest[:3], "big") % 900_000


def mesa_atual_id(numero_mesa=None):
    if numero_mesa is not None:
        session["mesa_id"] = numero_mesa
        get_or_criar_mesa(numero_mesa)
        return numero_mesa

    numero_mesa = session.get("mesa_id")
    if not numero_mesa:
        numero_mesa = _fallback_mesa_id()
        session["mesa_id"] = numero_mesa
        get_or_criar_mesa(numero_mesa)
    return numero_mesa


def cardapio():
    try:
        return [i.to_dict() for i in MenuItem.query.filter_by(available=True).all()]
    except Exception:
        return []


def cardapio_por_id():
    return {i["id"]: i for i in cardapio()}


def pedido_da_mesa(numero_mesa):
    return get_or_criar_mesa(numero_mesa)["itens"]


def comanda_da_mesa(numero_mesa):
    mesa = get_or_criar_mesa(numero_mesa)
    mesa["total"] = round(sum(i["preco"] * i["quantidade"] for i in mesa["itens"]), 2)
    return mesa


def volta_para_mesa(numero_mesa):
    usuario = usuario_atual()
    if usuario["role"] == "ATENDENTE":
        return redirect(url_for("menu_atendente_page"))
    if numero_mesa and numero_mesa != session.get("mesa_id"):
        return redirect(url_for("mesa_page", mesa_id=numero_mesa))
    return redirect(url_for("cliente_page"))


# Rotas de logine e cadastro --------------------------------------------------------------------------------------------
def pagina_cliente(mesa_id=None):
    user = usuario_atual()
    if user["role"] == "ATENDENTE":
        return redirect(url_for("menu_atendente_page"))
    mesa_id = mesa_atual_id(mesa_id)
    return render_template("menu_cliente.html", cliente={"nome": user["name"]}, cardapio=cardapio(), comanda=comanda_da_mesa(mesa_id), mesa_id=mesa_id)


def pagina_atendente(numero_mesa_selecionada=None):
    user = usuario_atual()
    numero_mesa_selecionada = numero_mesa_selecionada if numero_mesa_selecionada is not None else request.args.get("comanda_id", type=int)
    mesas_ativas = sorted(
        (m for m in MESAS.values() if m["itens"] or m["ativa"]),
        key=lambda m: m["numero_mesa"],
    )
    return render_template(
        "menu_atendente.html",
        funcionario={"nome": user["name"]},
        comandas_abertas=mesas_ativas,
        comanda_selecionada=MESAS.get(numero_mesa_selecionada),
        cardapio=cardapio(),
    )


def apenas_atendente(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if usuario_atual()["role"] != "ATENDENTE":
            return redirect(url_for("home"))
        return f(*a, **kw)
    return wrapper


def apenas_admin(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if usuario_atual()["role"] != "ADMIN":
            return redirect(url_for("home"))
        return f(*a, **kw)
    return wrapper


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/api/status")
def status():
    return jsonify({"status": "ok"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or request.form or {}
    email, senha = (d.get("email") or "").strip(), (d.get("password") or "").strip()
    if not email or not senha:
        return jsonify({"success": False, "message": "Informe e-mail e senha."}), 400
    try:
        user = User.query.filter_by(email=email).first()
    except Exception:
        return jsonify({"success": False, "message": "Erro interno ao acessar o banco de dados."}), 500
    if not user:
        return jsonify({"success": False, "message": "Usuário não encontrado."}), 401
    if user.password != senha:
        return jsonify({"success": False, "message": "Senha incorreta."}), 401

    session["user"] = {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    

    if user.role == "ADMIN":
        redirect_url = "/admin"
    elif user.role == "ATENDENTE":
        redirect_url = "/atendente"
    else:
        redirect_url = "/cliente"
    
    return jsonify({
        "success": True, "message": "Login realizado com sucesso.", "user": user.to_dict(),
        "mesa_id": session.get("mesa_id"), "redirect_url": redirect_url,
    })


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    d = request.get_json(silent=True) or request.form or {}
    nome, email, senha = (d.get("username") or "").strip(), (d.get("email") or "").strip(), (d.get("password") or "").strip()
    if not nome or not email or not senha:
        return jsonify({"success": False, "message": "Preencha nome, e-mail e senha."}), 400
    try:
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "E-mail já cadastrado."}), 409
        user = User(name=nome, email=email, password=senha, role="CLIENTE")
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Erro interno ao acessar o banco de dados."}), 500

    session["user"] = {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    return jsonify({"success": True, "message": "Cadastro realizado com sucesso.", "mesa_id": session.get("mesa_id")}), 201

@app.route("/mesa/<int:mesa_id>")
def mesa_page(mesa_id):
    return pagina_cliente(mesa_id)



# Rotas de Cliente-----------------------------------------------------------------------------------------------------------
@app.route("/cliente/adicionar/<int:item_id>", methods=["POST"])
@app.route("/mesa/<int:mesa_id>/adicionar/<int:item_id>", methods=["POST"])
def adicionar_item(item_id, mesa_id=None):
    mesa_id = mesa_atual_id(mesa_id)
    item = cardapio_por_id().get(item_id)
    if not item:
        return redirect(url_for("cliente_page"))
    pedido = pedido_da_mesa(mesa_id)
    existente = next((e for e in pedido if e["id"] == item_id), None)
    if existente:
        existente["quantidade"] += 1
    else:
        pedido.append({"id": item_id, "nome": item["nome"], "preco": item["preco"], "quantidade": 1})
    comanda_da_mesa(mesa_id)
    return volta_para_mesa(mesa_id)


@app.route("/cliente/remover/<int:item_id>", methods=["POST"])
@app.route("/mesa/<int:mesa_id>/remover/<int:item_id>", methods=["POST"])
def remover_item(item_id, mesa_id=None):
    mesa_id = mesa_atual_id(mesa_id)
    pedido = pedido_da_mesa(mesa_id)
    for e in pedido:
        if e["id"] == item_id:
            e["quantidade"] -= 1
            if e["quantidade"] <= 0:
                pedido.remove(e)
            break
    comanda_da_mesa(mesa_id)
    return volta_para_mesa(mesa_id)


@app.route("/cliente/pagar", methods=["POST"])
@app.route("/mesa/<int:mesa_id>/pagar", methods=["POST"])
def solicitar_pagamento(mesa_id=None):
    try:
        if mesa_id is not None:
            mesa_numero = mesa_id
        else:
            mesa_numero = mesa_atual_id()

        mesa = get_or_criar_mesa(mesa_numero)

        if mesa:
            mesa["status"] = "aguardando_pagamento"
            return jsonify({"success": True, "message": "Atendente notificado para fechar a mesa"})
        return jsonify({"success": False, "message": "Mesa não encontrada"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


@app.route("/api/solicitar-pagamento", methods=["POST"])
def api_solicitar_pagamento():
    try:
        mesa_id = session.get("mesa_id")
        if not mesa_id:
            mesa_id = _fallback_mesa_id()
            session["mesa_id"] = mesa_id
        mesa = get_or_criar_mesa(mesa_id)
        mesa["status"] = "aguardando_pagamento"
        
        return jsonify({"success": True, "message": "Atendente notificado para fechar a mesa"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500

# Rotas de Atendente--------------------------------------------------------------------------------------------------------
@app.route("/atendente")
@app.route("/menu_atendente")
@apenas_atendente
def menu_atendente_page():
    return pagina_atendente()


@app.route("/api/mesas", methods=["GET"])
@apenas_atendente
def api_mesas():
    mesas_ativas = sorted(
        (m for m in MESAS.values() if m["itens"] or m["ativa"]),
        key=lambda m: m["numero_mesa"],
    )
    return jsonify({
        "success": True,
        "mesas": mesas_ativas
    })


@app.route("/atendente/comandas", methods=["POST"])
@apenas_atendente
def criar_comanda():
    numero_mesa = request.form.get("numero_mesa", "").strip()
    if not numero_mesa.isdigit():
        return redirect(url_for("menu_atendente_page"))
    numero_mesa = int(numero_mesa)
    get_or_criar_mesa(numero_mesa, ativa=True)
    return redirect(url_for("menu_atendente_page", comanda_id=numero_mesa))


@app.route("/atendente/comanda/<int:comanda_id>")
@apenas_atendente
def ver_painel_menu_atendente(comanda_id):
    return pagina_atendente(comanda_id)


@app.route("/atendente/comanda/<int:comanda_id>/itens", methods=["POST"])
@apenas_atendente
def menu_atendente_adicionar_item(comanda_id):
    mesa = MESAS.get(comanda_id)
    if not mesa:
        return redirect(url_for("menu_atendente_page"))
    produto_id = int(request.form.get("produto_id"))
    quantidade = max(1, int(request.form.get("quantidade", 1)))
    produto = cardapio_por_id().get(produto_id)
    if not produto:
        return redirect(url_for("ver_painel_menu_atendente", comanda_id=comanda_id))
    existente = next((e for e in mesa["itens"] if e["id"] == produto_id), None)
    if existente:
        existente["quantidade"] += quantidade
    else:
        mesa["itens"].append({"id": produto_id, "nome": produto["nome"], "preco": produto["preco"], "quantidade": quantidade})
    mesa["total"] = round(sum(e["preco"] * e["quantidade"] for e in mesa["itens"]), 2)
    return redirect(url_for("ver_painel_menu_atendente", comanda_id=comanda_id))


@app.route("/atendente/comanda/<int:comanda_id>/fechar", methods=["POST"])
@apenas_atendente
def fechar_comanda(comanda_id):
    from datetime import datetime
    
    mesa = MESAS.get(comanda_id)
    if not mesa:
        return jsonify({"success": False, "message": "Comanda não encontrada"}), 404

    payment_method = request.form.get("payment_method") or request.get_json(silent=True, force=True).get("payment_method")
    amount_received_str = request.form.get("amount_received") or request.get_json(silent=True, force=True).get("amount_received")

    if not payment_method:
        return jsonify({"success": False, "message": "Forma de pagamento é obrigatória"}), 400
    
    try:
        amount_received = float(amount_received_str or 0)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Valor recebido inválido"}), 400
    
    if amount_received < mesa["total"]:
        return jsonify({
            "success": False, 
            "message": f"Valor recebido (R$ {amount_received:.2f}) é menor que o total (R$ {mesa['total']:.2f})"
        }), 400
    
    troco = amount_received - mesa["total"]
    user = usuario_atual()
    
    try:
        order = Order(
            customer_id=user["id"] or 1,  
            created_by=user["id"] or 1,   
            closed_by=user["id"],
            paid_by=user["id"],
            status="PAID",
            total=mesa["total"],
            closed_at=datetime.now(),
            paid_at=datetime.now()
        )
        db.session.add(order)
        db.session.flush() 

        payment = Payment(
            order_id=order.id,
            payment_method=payment_method,
            total_amount=mesa["total"],
            amount_received=amount_received,
            change_amount=troco
        )
        db.session.add(payment)
        db.session.commit()
        MESAS.pop(comanda_id, None)
        
        return jsonify({
            "success": True, 
            "message": "Comanda fechada com sucesso",
            "payment_info": {
                "order_id": order.id,
                "total": float(order.total),
                "payment_method": payment_method,
                "amount_received": amount_received,
                "change_amount": troco
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False, 
            "message": f"Erro ao salvar pagamento: {str(e)}"
        }), 500


# Rotas Principais -----------------------------------------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/cliente")
def cliente_page():
    return pagina_cliente()




# Rotas de Admin--------------------------------------------------------------------------------------------------------

@app.route("/admin")
@app.route("/menu_admin")
@apenas_admin
def menu_admin_page():
    user = usuario_atual()
    return render_template(
        "menu_admin.html",
        admin={"nome": user["name"]}
    )


@app.route("/api/admin/dashboard", methods=["GET"])
@apenas_admin
def api_admin_dashboard():

    try:

        total_mesas = len(MESAS)
        mesas_ativas = sum(1 for m in MESAS.values() if m["itens"] or m["ativa"])
        total_vendido = sum(float(m["total"]) for m in MESAS.values())
        

        total_users = User.query.count()
        total_atendentes = User.query.filter_by(role="ATENDENTE").count()
        total_clientes = User.query.filter_by(role="CLIENTE").count()
        

        total_orders = Order.query.count()
        total_paid = Order.query.filter_by(status="PAID").count()
        

        total_revenue = 0.0
        try:
            payments = Payment.query.all()
            total_revenue = sum(float(p.total_amount) for p in payments)
        except Exception:
            pass
        
        return jsonify({
            "success": True,
            "dashboard": {
                "mesas": {
                    "total": total_mesas,
                    "ativas": mesas_ativas,
                    "total_vendido": round(total_vendido, 2)
                },
                "usuarios": {
                    "total": total_users,
                    "atendentes": total_atendentes,
                    "clientes": total_clientes,
                    "admins": User.query.filter_by(role="ADMIN").count()
                },
                "pedidos": {
                    "total": total_orders,
                    "pagos": total_paid,
                    "abertos": total_orders - total_paid
                },
                "vendas": {
                    "total": round(total_revenue, 2)
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/usuarios", methods=["GET"])
@apenas_admin
def api_admin_usuarios():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 20
        
        users = User.query.paginate(page=page, per_page=per_page)
        
        usuarios_list = [{
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "active": u.active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in users.items]
        
        return jsonify({
            "success": True,
            "usuarios": usuarios_list,
            "total": users.total,
            "pages": users.pages,
            "current_page": page
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/usuarios", methods=["POST"])
@apenas_admin
def api_admin_criar_usuario():
    data = request.form or request.get_json(silent=True) or {}
    nome = (data.get("name") or data.get("nome") or "").strip()
    email = (data.get("email") or "").strip()
    senha = (data.get("password") or "").strip()
    role = (data.get("role") or "ATENDENTE").strip().upper()

    if role not in {"CLIENTE", "ATENDENTE", "ADMIN"}:
        role = "ATENDENTE"

    if not nome or not email or not senha:
        return jsonify({"success": False, "message": "Preencha nome, e-mail e senha."}), 400

    try:
        if User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "E-mail já cadastrado."}), 409

        usuario = User(name=nome, email=email, password=senha, role=role, active=True)
        db.session.add(usuario)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuário criado com sucesso.", "usuario": usuario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao criar usuário: {e}"}), 500


@app.route("/api/admin/usuarios/<int:user_id>", methods=["DELETE"])
@apenas_admin
def api_admin_remover_usuario(user_id):
    try:
        usuario = User.query.get(user_id)
        if not usuario:
            return jsonify({"success": False, "message": "Usuário não encontrado."}), 404

        usuario_logado = session.get("user") or {}
        if usuario.id == usuario_logado.get("id"):
            return jsonify({"success": False, "message": "Você não pode remover o próprio usuário logado."}), 400

        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuário removido com sucesso."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao remover usuário: {e}"}), 500


@app.route("/api/admin/pedidos", methods=["GET"])
@apenas_admin
def api_admin_pedidos():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 20
        
        orders = Order.query.paginate(page=page, per_page=per_page)
        
        pedidos_list = [{
            "id": o.id,
            "status": o.status,
            "total": float(o.total),
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "closed_at": o.closed_at.isoformat() if o.closed_at else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None
        } for o in orders.items]
        
        return jsonify({
            "success": True,
            "pedidos": pedidos_list,
            "total": orders.total,
            "pages": orders.pages,
            "current_page": page
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/cardapio", methods=["GET"])
@apenas_admin
def api_admin_cardapio():
    try:
        itens = MenuItem.query.all()
        
        items_list = [{
            "id": i.id,
            "nome": i.name,
            "descricao": i.description,
            "preco": float(i.price),
            "disponivel": i.available,
            "created_at": i.created_at.isoformat() if i.created_at else None
        } for i in itens]
        
        return jsonify({
            "success": True,
            "items": items_list
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/admin/cardapio", methods=["POST"])
@apenas_admin
def api_admin_criar_item():
    data = request.form or request.get_json(silent=True) or {}
    nome = (data.get("name") or data.get("nome") or "").strip()
    descricao = (data.get("description") or data.get("descricao") or "").strip()
    preco_raw = data.get("price") or data.get("preco")
    disponivel_raw = data.get("disponivel", True)

    if isinstance(disponivel_raw, str):
        disponivel = disponivel_raw.strip().lower() in {"true", "1", "sim", "yes", "s"}
    else:
        disponivel = bool(disponivel_raw)

    if not nome or preco_raw is None:
        return jsonify({"success": False, "message": "Informe nome e preço do item."}), 400

    try:
        preco = Decimal(str(preco_raw))
    except (InvalidOperation, ValueError):
        return jsonify({"success": False, "message": "Preço inválido."}), 400

    try:
        item = MenuItem(name=nome, description=descricao or None, price=preco, available=disponivel)
        db.session.add(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Item adicionado ao cardápio.", "item": item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao criar item: {e}"}), 500


@app.route("/api/admin/cardapio/<int:item_id>", methods=["DELETE"])
@apenas_admin
def api_admin_remover_item(item_id):
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({"success": False, "message": "Item não encontrado."}), 404

        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Item removido com sucesso."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao remover item: {e}"}), 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/logo")
def serve_logo():
    return send_from_directory(os.path.join(PROJECT_ROOT, "imagens"), "logo.png")


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)