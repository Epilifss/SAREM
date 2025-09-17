from back.database import create_connection
from back.models.user import User


def autenticar_usuario(username, password_hash):
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, module, is_admin FROM users WHERE username COLLATE Latin1_General_BIN=? AND password_hash COLLATE Latin1_General_BIN=?",
        (username, password_hash)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return User(*row)
    return None

# def autenticar_admin_config_db(username, password_hash):

def listar_usuarios():
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, IIF(module='0','Corporativo',IIF(module='1','Varejo',IIF(module='2', 'Exportação', IIF(module='3', 'Comercial', '')))), IIF(is_admin='True', 'Sim', 'Não') FROM users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def excluir_usuario(user_id):
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


def criar_usuario(username, password_hash, module, is_admin):
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, module, is_admin) VALUES (?, ?, ?, ?)",
        (username, password_hash, module, is_admin)
    )
    conn.commit()
    cursor.close()
    conn.close()


def editar_usuario(user_id, username, password_hash, module, is_admin):
    conn = create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    if password_hash:
        cursor.execute(
            "UPDATE users SET username=?, password_hash=?, module=?, is_admin=? WHERE id=?",
            (username, password_hash, module, is_admin, user_id)
        )
    else:
        cursor.execute(
            "UPDATE users SET username=?, module=?, is_admin=? WHERE id=?",
            (username, module, is_admin, user_id)
        )
    conn.commit()
    cursor.close()
    conn.close()
