Site utiliza Flask e SQLAlchemy, pymysql.

Testado em um ambiente virtual controlado: venv python3.

Comandos Linux:

sudo apt update

# Python 3
sudo apt install -y python3 (ou python) python3-pip

# MySQL
sudo apt install -y mysql-server

# VS Code
sudo snap install code --classic

# criar venv
python -m venv .venv <-- .venv é o nome que eu dei para minha venv

# Python-Flask <-- dentro da venv
pip (ou pip3) install flask sqlalchemy pymysql

# Python-Alchemy <-- dentro da venv
pip install flask flask-sqlalchemy pymysql

# Preparando database
SOURCE (caminho)/restauranteMobonga.sql
(crie um usuário chamado flask, senha para ele: FragilX)
sudo mysql -e "GRANT ALL PRIVILEGES ON restauranteMobonga.* TO 'flask'@'localhost'; FLUSH PRIVILEGES; SHOW GRANTS FOR 'flask'@'localhost';"


## Importante: Preparando para rodar o server:
(caminho) source .venv/bin/activate
(caminho) cd backend && python3 app.py

