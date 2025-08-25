import ttkbootstrap as tb
import tkinter as tk
from tkinter import messagebox

from back.utils import resource_path
from back.user_service import listar_usuarios, excluir_usuario, criar_usuario, editar_usuario
from front.modals.new_user import NovoUsuarioModal
from front.modals.edit_user import EditarUsuarioModal
from theme import ajustar_largura_colunas, estilizar_treeview

class AdminPanel:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title("Painel de Administração")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)
        self.root.state('zoomed')

        self.notebook = tb.Notebook(self.root)
        self.user_frame = tb.Frame(self.notebook)
        self.notebook.add(self.user_frame, text="Usuários")
        self.notebook.pack(expand=True, fill=tk.BOTH)

        header = tb.Frame(self.user_frame)
        header.pack(fill=tk.X)
        tb.Button(header, text="Novo Usuário", command=lambda: NovoUsuarioModal(self.root, self)).pack(side=tk.LEFT)
        tb.Button(header, text="Excluir Usuário", command=self.excluir_usuario).pack(side=tk.LEFT)
        tb.Button(header, text="Editar Usuário", command=self.editar_usuario).pack(side=tk.LEFT)
        tb.Button(header, text="Logoff", command=self.logoff).pack(side=tk.RIGHT)

        self.tree = tb.Treeview(self.user_frame, columns=("Usuário", "Módulo", "Admin"), show="headings")
        for col in ("Usuário", "Módulo", "Admin"):
            self.tree.heading(col, text=col)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.tree.bind("<<TreeviewSelect>>", self.atualizar_selecao)

        self.carregar_usuarios()

    def carregar_usuarios(self):
        self.tree.delete(*self.tree.get_children())
        usuarios = listar_usuarios()
        for row in usuarios:
            # row[0] é o id, não exibido, mas armazenado como 'iid' do item
            valores_formatados = [str(item) for item in row[1:]]
            self.tree.insert("", tk.END, iid=str(row[0]), values=valores_formatados)
        estilizar_treeview(self.tree)
        ajustar_largura_colunas(self.tree)

    def atualizar_selecao(self, event=None):
        selected_items = self.tree.selection()
        if selected_items:
            item_id = selected_items[0]
            valores = self.tree.item(item_id, "values")
            self.usuario_selecionado = valores[0]
            self.nome_usuario = valores[1]
        else:
            self.usuario_selecionado = None

    def excluir_usuario(self):
        if not hasattr(self, 'usuario_selecionado') or not self.usuario_selecionado:
            messagebox.showerror("Erro", "Nenhum usuário selecionado")
            return
        resposta = messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir o usuário {self.nome_usuario}?")
        if not resposta:
            return
        excluir_usuario(self.usuario_selecionado)
        self.carregar_usuarios()
        self.usuario_selecionado = None

    def editar_usuario(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Atenção", "Selecione um usuário para editar.")
            return

        item_id = selected_items[0]
        user_data = self.tree.item(item_id, "values")
        EditarUsuarioModal(self.root, self, (item_id, *user_data))

    def logoff(self, parent=None):
        from front.windows.login_window import LoginWindow
        if parent is None:
            parent = self.root
        self.root.destroy()
        login_win = LoginWindow(parent.master if hasattr(parent, 'master') else parent)
        login_win.root.after(100, lambda: (login_win.root.focus_force(), login_win.username.focus_set()))