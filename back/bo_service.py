from back.database import create_connection, create_connection_Protheus
from tkinter import messagebox
from back.models.bo import BO
from back.models.bo_protheus import BO_protheus
import pyodbc
import tkinter as tk


def _get_username(user):
    if hasattr(user, "username"):
        return user.username
    return str(user) if user is not None else ""


def _can_delete_bo(user):
    if user is None:
        return False
    if hasattr(user, "can_delete"):
        return user.can_delete()
    if hasattr(user, "is_admin"):
        return bool(user.is_admin)
    return True


def _can_track_bo(user):
    if user is None:
        return False
    if hasattr(user, "can_track"):
        return user.can_track()
    if hasattr(user, "is_admin"):
        return bool(user.is_admin)
    return True

def listar_bos(modulo):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    query = """
        SELECT bo_number, op, loja, filial, emissao_totvs, tipo_ocorrencia, descricao, setor_responsavel, frete, previsao_embarque, modulo, status, user_include
        FROM bo_records
        WHERE status NOT LIKE 'Embarcado' AND D_E_L_E_T_ <> '*' AND modulo LIKE ?
    """
    cursor.execute(query, modulo)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [BO(*row) for row in rows]

def listar_bo_protheus():
    conn = create_connection_Protheus()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("""
                SELECT C5_PEDREPR, C5_NUM, C5_NOME, IIF(C5_FILIAL='0101','TIDELLI','NAUTICA') AS FILIAL, CONVERT(VARCHAR,CONVERT(DATETIME,C5_EMISSAO),103) as EMISSAO, CONVERT(VARCHAR,CONVERT(DATETIME,C5_ENTREGA),103) as PREVISAO_ENTREGA
                FROM SC5010 SC5
                WHERE SC5.D_E_L_E_T_ <> '*'
                        AND SC5.C5_NOTA = ''
                        AND PATINDEX('BO[0-9]%', SC5.C5_PEDREPR) > 0
                        AND C5_FILIAL IN ('0101','0201')
                ORDER BY C5_EMISSAO DESC
            """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [BO_protheus(*row) for row in rows]
    
def pesquisar_bo(modulo, termo):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT bo_number, op, status, tipo_ocorrencia, setor_responsavel, loja FROM bo_records WHERE modulo LIKE ? AND status NOT LIKE 'Embarcado' AND bo_number LIKE ? AND D_E_L_E_T_ <> '*'", (modulo, f"%{termo}%",))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def pesquisar_bo_protheus(termo):
    conn = create_connection_Protheus()
    if conn is None:
        return None
    cursor = conn.cursor()
    like_termo = f"%{termo}%"
    query = """
        SELECT C5_PEDREPR, C5_NUM, C5_NOME, IIF(C5_FILIAL='0101','TIDELLI','NAUTICA') AS FILIAL, CONVERT(VARCHAR,CONVERT(DATETIME,C5_EMISSAO),103) AS EMISSAO, CONVERT(VARCHAR,CONVERT(DATETIME,C5_ENTREGA),103) AS PREVISAO_ENTREGA
        FROM SC5010 SC5
        WHERE SC5.D_E_L_E_T_ <> '*'
            AND SC5.C5_NOTA = ''
            AND C5_PEDREPR LIKE 'BO%'  -- Garante que o campo começa com "BO"
            AND (C5_PEDREPR LIKE ?  -- Permite que o termo apareça após o "BO"
                OR UPPER(C5_NUM) LIKE UPPER(?)
                OR UPPER(C5_NOME) LIKE UPPER(?))
            AND C5_FILIAL IN ('0101','0201')
        ORDER BY C5_EMISSAO DESC
        """
    cursor.execute(query, (like_termo, like_termo, like_termo))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def excluir_bo(self, refresh_callback=None):
    conn = None
    cursor = None

    if not _can_delete_bo(self.user):
        messagebox.showerror("Permissão negada", "Você não possui permissão para excluir BO.")
        return

    item_selecionado = self.tree.selection()
    if not item_selecionado:
        messagebox.showwarning("Aviso", "Nenhum item selecionado.")
        return

    valores = self.tree.item(item_selecionado, "values")
    bo_number = valores[0]

    username = _get_username(self.user)

    print(f"Usuário {username} solicitou a exclusão da {bo_number}.")

    resposta = messagebox.askyesno(
        "Confirmação",
        "Você tem certeza que deseja excluir esta BO? Esta ação não pode ser desfeita.",
        icon=messagebox.WARNING
    )

    if resposta is True:
        try:
            conn = create_connection()
            if conn is None:
                return None
            cursor = conn.cursor()
            cursor.execute(
                """
                    UPDATE bo_records
                    SET D_E_L_E_T_ = '*', user_delet = ?, deleted_at = GETDATE()
                    WHERE bo_number = ?
                """,
                (username, str(bo_number))
            )
            conn.commit()
            messagebox.showinfo("Sucesso", f"{bo_number} excluída com sucesso!")
            if refresh_callback:
                refresh_callback()
            print(f"{username} excluiu a {bo_number}.")
            self.root.destroy()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao excluir BO: {e}")
            self.root.destroy()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        print(f"{username} não excluiu a {bo_number}.")

def verificar_bo_acompanhada(bo_number):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM bo_records WHERE bo_number = ? AND D_E_L_E_T_ <> '*'", (bo_number,))
    exists = cursor.fetchone()
    return exists is not None

def listar_itens_bo(valor1, valor2):
    conn = create_connection_Protheus()
    if conn is None:
        return None
    cursor = conn.cursor()

    query = """SELECT SC6.C6_CODTIDI, SC6.C6_DESCRI, SC6.C6_LINHA
        FROM SC6010 SC6
        INNER JOIN SC5010 SC5 ON (SC5.C5_NUM = SC6.C6_NUM AND SC5.C5_FILIAL = SC6.C6_FILIAL AND SC5.D_E_L_E_T_ <> '*')
        WHERE SC6.C6_NUM LIKE ? AND SC5.C5_PEDREPR LIKE ? AND SC5.C5_PEDREPR LIKE ?"""

    cursor.execute(query, (f"%{valor1}%", "%BO%", f"%{valor2}%"))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def listar_itens_SAREM(valor1, valor2):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()

    query = """SELECT COD, [DESC], LINHA, BI.MOTIVO
        FROM BO_ITENS as BI
        INNER JOIN bo_records AS BR ON BR.bo_number = BI.BO_REF
        WHERE BR.bo_number LIKE ? AND BR.op LIKE ? AND BR.D_E_L_E_T_ <> '*'"""

    cursor.execute(query, (f"%{valor1}%", f"%{valor2}%"))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def obter_setores():
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT setor_responsavel FROM bo_records "
        "WHERE setor_responsavel IS NOT NULL AND setor_responsavel NOT LIKE ''"
    )
    rows = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows

def obter_motivos():
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT MOTIVO FROM BO_ITENS "
        "WHERE MOTIVO IS NOT NULL AND MOTIVO NOT LIKE ''"
    )
    rows = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows

def obter_detalhes_ocorrencia(bo_number):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    
    query = """SELECT bo_number, op, loja, CONVERT(VARCHAR,CONVERT(DATETIME,previsao_embarque),103), [status]
        FROM bo_records
        WHERE bo_number LIKE ? AND D_E_L_E_T_ <> '*'"""

    cursor.execute(query, (f"%{bo_number}%",))
    itens_bo = cursor.fetchall()
    cursor.close()
    conn.close()
    return itens_bo if itens_bo else None

def obter_campos_editaveis(bo_number):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()

    cursor.execute("SELECT tipo_ocorrencia, descricao, setor_responsavel, frete FROM bo_records WHERE bo_number = ? AND D_E_L_E_T_ <> '*'", (bo_number,))
    campos_editaveis = cursor.fetchone()
    cursor.close()
    conn.close()
    return campos_editaveis if campos_editaveis else None

def salvar_bo(bo_dados, ocorrencia_data, transporte_data, user_data, itens_com_motivos, ultimo_modulo):
    conn = None 
    cursor = None
    try:
        if not _can_track_bo(user_data):
            raise PermissionError("Você não possui permissão para acompanhar BO.")

        conn = create_connection()
        if conn is None:
            return None
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM bo_records WHERE bo_number = ? AND D_E_L_E_T_ <> '*'", (bo_dados[0],))
        if cursor.fetchone():
            messagebox.showerror("Erro", "BO já existe.")
            return

        insert_bo_records_query = """
            INSERT INTO bo_records (
                bo_number, op, loja, filial, emissao_totvs,
                tipo_ocorrencia, descricao, setor_responsavel,
                frete, previsao_embarque, modulo, status, user_include
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        username = _get_username(user_data)

        insert_bo_records_values = (
            bo_dados[0], # bo_number
            bo_dados[1], # op
            bo_dados[2], # loja
            bo_dados[3], # filial
            bo_dados[4], # emissao_totvs
            ocorrencia_data['tipo_ocorrencia'],
            ocorrencia_data['descricao'],
            ocorrencia_data['setor_responsavel'],
            transporte_data['frete'],
            bo_dados[5], # previsao_embarque
            ultimo_modulo,
            'Em Andamento', # status
            username # user_include
        )
        
        cursor.execute(insert_bo_records_query, insert_bo_records_values)

        cursor.execute("DELETE FROM BO_ITENS WHERE BO_REF = ?", (bo_dados[0],))

        insert_bo_itens_query = """
            INSERT INTO BO_ITENS (BO_REF, COD, [DESC], LINHA, MOTIVO)
            VALUES (?, ?, ?, ?, ?)
        """
        for item in itens_com_motivos:
            cursor.execute(insert_bo_itens_query, (
                bo_dados[0], # BO_REF
                item['cod'],
                item['desc'],
                item['linha'],
                item['motivo']
            ))

        conn.commit()
        
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def atualizar_bo(bo_number, dados_bo, dados_itens, user_data):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()

    username = _get_username(user_data)

    update_query = """
                UPDATE bo_records
                SET tipo_ocorrencia = ?,
                    descricao = ?,
                    setor_responsavel = ?,
                    frete = ?,
                    user_edit = ?,
                    edited_at = GETDATE()
                WHERE bo_number = ?
            """

    try:
        print(*dados_bo)
        cursor.execute(
            update_query, (*dados_bo, username, bo_number))
        
        cursor.executemany("""
                UPDATE BO_ITENS
                SET MOTIVO = ?
                WHERE BO_REF = ? AND COD = ?
            """, dados_itens)
        
        conn.commit()
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def buscar_dados_bo(bo_number):
    conn = create_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    query = """SELECT bo_number, op, loja, tipo_ocorrencia, CONVERT(VARCHAR,CONVERT(DATETIME,previsao_embarque),103), descricao, frete, [status]
        FROM bo_records
        WHERE bo_number LIKE ? AND D_E_L_E_T_ <> '*'"""
    cursor.execute(query, bo_number)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row if row else None