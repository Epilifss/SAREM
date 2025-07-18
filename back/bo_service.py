from back.database import create_connection
from tkinter import messagebox
from models.bo import BO
import pyodbc

def listar_bos(modulo):
    conn = create_connection()
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

def pesquisar_bo(modulo, termo):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bo_number, op, status, tipo_ocorrencia, setor_responsavel, loja FROM bo_records WHERE modulo LIKE ? AND status NOT LIKE 'Embarcado' AND bo_number LIKE ? AND D_E_L_E_T_ <> '*'", (modulo, f"%{termo}%",))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def excluir_bo(self):
        print(f"Usuário {self.user[1]} solicitou a exclusão da BO.")

        resposta = messagebox.askyesno("Confirmação",
            "Você tem certeza que deseja excluir esta BO? Esta ação não pode ser desfeita.",
            icon=messagebox.WARNING
        )

        item_selecionado = self.tree.selection()
        if not item_selecionado:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")
            return
        
        valores = self.tree.item(item_selecionado, "values")
        bo_number = valores[0]

        
        if resposta is True:
            try:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE bo_records
                    SET D_E_L_E_T_ = '*', user_delet = ?, deleted_at = GETDATE()
                    WHERE bo_number = ?
                """, (self.user[1]), str(bo_number,))
                conn.commit()
                messagebox.showinfo("Sucesso", f"{bo_number} excluída com sucesso!")
                self.root.destroy()
            except pyodbc.Error as e:
                messagebox.showerror("Erro", f"Erro ao excluir BO: {e}")
                self.root.destroy()
            finally:
                if conn:
                    cursor.close()
                    conn.close()

            if self.ultimo_modulo == "Corporativo":
                from modulos.corporativo import CorporativoModule
                if CorporativoModule.instance is not None:
                    if CorporativoModule.instance is not None:
                        CorporativoModule.instance.atualizar_bos()
                    else:
                        print("Instância do módulo corporativo não encontrada.")
                else:
                    pass
            elif self.ultimo_modulo == "Varejo":
                from modulos.varejo import VarejoModule
                if VarejoModule.instance is not None:
                    if VarejoModule.instance is not None:
                        VarejoModule.instance.atualizar_bos()
                    else:
                        print("Instância do módulo varejo não encontrada.")
                else:
                    pass
            elif self.ultimo_modulo == "Exportacao":
                from modulos.exportacao import ExportacaoModule
                if ExportacaoModule.instance is not None:
                    if ExportacaoModule.instance is not None:
                        ExportacaoModule.instance.atualizar_bos()
                    else:
                        print("Instância do módulo exportacao não encontrada.")
                else:
                    pass
        else:
            pass