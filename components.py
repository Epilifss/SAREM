import tkinter as tk
import pyodbc
import ttkbootstrap as tb
from tkinter import messagebox
from database import create_connection

# Cabeçalho dos módulos


class Header:
    def __init__(self, parent, user, caller_id=None, tree=None):
        self.user = user
        self.parent = parent

        self.ultimo_modulo = caller_id
        self.tree = tree

        header = tb.Frame(self.parent)
        header.pack(fill=tk.X)

        tb.Button(header, text="Embarcados", command=self.abrir_embarcados).pack(side=tk.LEFT)
        tb.Button(header, text="Estatísticas", command=self.abrir_estatisticas).pack(side=tk.LEFT)
        tb.Button(header, text="Gerar Relatório", command=self.abrir_relatorios).pack(side=tk.LEFT)
        # tb.Button(header, text="Gerar Nova BO", command=self.abrir_gerar_bo).pack(side=tk.LEFT)
        tb.Button(header, text="Atualizar", command=lambda: self.carregar_bos()).pack(side=tk.LEFT)
        tb.Button(header, text="Acompanhar uma BO", command=self.abrir_buscar_bo).pack(side=tk.LEFT)
        tb.Button(header, text="Logoff", command=self.logoff).pack(side=tk.RIGHT)

    def abrir_embarcados(self):
        from funcoes import Embarcados
        janela = Embarcados(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_estatisticas(self):
        from funcoes import Estatisticas
        janela = Estatisticas(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_relatorios(self):
        from funcoes import Relatorios
        janela = Relatorios(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_gerar_bo(self):
        from funcoes import gerarBO
        janela = gerarBO(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_buscar_bo(self):
        from funcoes import buscarBo
        janela = buscarBo(self.parent, caller_id=self.ultimo_modulo, user=self.user)
        self.parent.wait_window(janela.root)

    def carregar_bos(self):
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            query = ("SELECT bo_number, op, status, tipo_ocorrencia, setor_responsavel, motivo FROM bo_records WHERE status NOT LIKE 'Embarcado' AND modulo LIKE ? AND D_E_L_E_T_ <> '*'")
            cursor.execute(query, self.ultimo_modulo)
            rows = cursor.fetchall()

            # Remove todos os itens atuais da Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insere os dados "limpos" na Treeview
            for row in rows:
                # Converte cada valor para string (se não for None) e aplica strip para remover caracteres indesejados.
                bo = str(row[0]).strip("(' ,)") if row[0] is not None else ""
                op = str(row[1]).strip("(' ,)") if row[1] is not None else ""
                status = str(row[2]).strip("(' ,)") if row[2] is not None else ""
                tipo_ocorrencia = str(row[3]).strip("(' ,)") if row[3] is not None else ""
                setor_responsavel = str(row[4]).strip("(' ,)") if row[4] is not None else ""
                motivo = str(row[5]).strip("(' ,)") if row[5] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, status, tipo_ocorrencia, setor_responsavel, motivo))
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def logoff(self):
        root_principal = self.parent.master
        self.parent.destroy()
        from funcoes import LoginWindow, monitorar_bo_event
        monitorar_bo_event.set()
        login = LoginWindow(root_principal)
        login.root.after(100, login.root.focus_force)
        login.root.after(100, login.username.focus_force)
        

    def buscar_bo(self):
        from funcoes import buscarBo
        obj = buscarBo(parent=self.parent, caller_id=self.ultimo_modulo)
        resultado = obj.identificar_chamador()
        print(resultado)


class SearchBar:
    def __init__(self, parent, search_command, clear_command):
        self.parent = parent
        self.search_command = search_command
        self.clear_command = clear_command

        self.frame = tb.Frame(self.parent)
        self.frame.pack(fill=tk.X)

        self.search_entry = tb.Entry(self.frame)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.search_button = tb.Button(
            self.frame, text="Buscar", command=self.search_command)
        self.search_button.pack(side=tk.LEFT)

        self.clear_button = tb.Button(
            self.frame, text="Limpar", command=self.clear_command)
        self.clear_button.pack_forget()

        self.search_entry.bind('<KeyRelease>', self.update_buttons)
        self.search_entry.bind('<Return>', self.search_command)

    def update_buttons(self, event=None):
        termo = self.search_entry.get()
        if termo:
            self.search_button.pack_forget()  # Oculta o botão "Pesquisar"
            self.clear_button.pack(side=tk.LEFT)  # Exibe o botão "Limpar"
        else:
            self.clear_button.pack_forget()  # Oculta o botão "Limpar"
            self.search_button.pack(side=tk.LEFT)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.update_buttons()  # Atualiza os botões após limpar
        self.search_command()  # Recarrega os BOs
