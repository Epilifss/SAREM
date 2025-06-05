import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
from funcoes import *
from components import *
from database import create_connection

def resource_path(relative_path):
    """Retorna o caminho absoluto para o recurso, funciona para dev e PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class VarejoModule:
    instance = None # Var de class que armazena a instância atual

    def __init__(self, user, parent):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("SAREM - Módulo Varejo")
        self.root.iconbitmap(resource_path('SAREM.ico'))

        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        self.root.state('zoomed')

        VarejoModule.instance = self

        from funcoes import exibir_detalhes_acompanhando

        # Lista de BOs
        self.tree = ttk.Treeview(self.root, columns=(
            "BO", "OP", "Status", "tipo_ocorrencia", "setor_responsavel", "motivo"), show="headings")
        self.tree.heading("BO", text="BO")
        self.tree.heading("OP", text="OP")
        self.tree.heading("Status", text="Status")
        self.tree.heading("tipo_ocorrencia", text="Tipo de Ocorrência")
        self.tree.heading("setor_responsavel", text="Setor Responsável")
        self.tree.heading("motivo", text="Motivo")

        self.tree.bind("<Double-1>", lambda event: exibir_detalhes_acompanhando(self.root,
                       self.tree, caller_id="Varejo", user=self.user))

        # Cabeçalho
        self.header = Header(self.root, self.user, caller_id="Varejo", tree=self.tree)

        # Barra de pesquisa
        self.search_bar = SearchBar(self.root, self.pesquisar_bo, self.clear_search)

        self.tree.pack(expand=True, fill=tk.BOTH)

        self.header.carregar_bos()
        self.search_bar.search_entry.bind('<Return>', self.pesquisar_bo)
        self.root.mainloop()

    def atualizar_bos(self):
        if self.header is not None:
            self.header.carregar_bos()
        else:
            print("Header não inicializado.")

    def pesquisar_bo(self, event=None):
        termo = self.search_bar.search_entry.get()
        if not termo:
            return

        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT bo_number, op, status, tipo_ocorrencia, setor_responsavel, motivo FROM bo_records WHERE modulo LIKE 'varejo' AND status NOT LIKE 'Embarcado' AND bo_number LIKE ? AND D_E_L_E_T_ <> '*'", (f"%{termo}%",))
            rows = cursor.fetchall()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                # Converte cada valor para string (se não for None) e aplica strip para remover caracteres indesejados.
                bo = str(row[0]).strip("(' ,)") if row[0] is not None else ""
                op = str(row[1]).strip("(' ,)") if row[1] is not None else ""
                status = str(row[2]).strip(
                    "(' ,)") if row[2] is not None else ""
                tipo_ocorrencia = str(row[3]).strip(
                    "(' ,)") if row[3] is not None else ""
                setor_responsavel = str(row[4]).strip(
                    "(' ,)") if row[4] is not None else ""
                motivo = str(row[5]).strip(
                    "(' ,)") if row[5] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, status, tipo_ocorrencia, setor_responsavel, motivo))
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def clear_search(self):
        self.search_bar.search_entry.delete(0, tk.END)
        self.search_bar.update_buttons()  # Atualiza os botões após limpar
        self.header.carregar_bos()  # Recarrega os BOs