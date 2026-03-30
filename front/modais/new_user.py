import tkinter as tk
import ttkbootstrap as tb
import hashlib
from tkinter import messagebox
from back.utils import resource_path, limitar_janela_tela
from back.user_service import criar_usuario

class NovoUsuarioModal:
    def __init__(self, parent, admin_panel):
            self.root = tk.Toplevel(parent)
            self.root.title("Novo Usuário")
            self.root.iconbitmap(resource_path('SAREM.ico'))
            self.root.transient(parent)
            self.root.grab_set()
            self.root.focus_set()

            self.admin_panel = admin_panel

            campos = ["Usuário", "Senha", "Módulo", "Perfil", "Admin", "Pode Editar BO", "Pode Excluir BO", "Pode Acompanhar BO"]
            self.entries = {}

            content = tb.Frame(self.root, padding=20)
            content.grid(row=0, column=0, sticky="nsew")
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            for i, campo in enumerate(campos):
                tb.Label(content, text=f"{campo}:").grid(
                row=i, column=0, sticky=tk.W, padx=10, pady=8
                )
                if campo == "Senha":
                    entry = tb.Entry(content, show="*")
                elif campo == "Perfil":
                    entry = tb.Combobox(content, values=["Somente Leitura", "Operador", "Supervisor", "Administrador"], state="readonly")
                    entry.set("Operador")
                elif campo == "Admin":
                    entry = tb.Combobox(content, values=["Sim", "Não"], state="readonly")
                    entry.set("Não")
                elif campo in ("Pode Editar BO", "Pode Excluir BO", "Pode Acompanhar BO"):
                    entry = tb.Combobox(content, values=["Sim", "Não"], state="readonly")
                    entry.set("Sim")
                elif campo == "Módulo":
                    entry = tb.Combobox(content, values=[
                    "Corporativo", "Varejo", "Exportação", "Comercial", "Todos"], state="readonly")
                else:
                    entry = tb.Entry(content)

                entry.grid(row=i, column=1, padx=10, pady=8)
                self.entries[campo] = entry

            self.entries["Perfil"].bind("<<ComboboxSelected>>", self.aplicar_perfil)
            self.entries["Admin"].bind("<<ComboboxSelected>>", self.on_admin_change)

            self.aplicar_perfil()

            tb.Button(content, text="Salvar", command=self.salvar).grid(
                row=len(campos), column=0, columnspan=2, pady=(15, 0)
            )

            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            limitar_janela_tela(self.root)


    def salvar(self):
        username = self.entries["Usuário"].get()
        password = self.entries["Senha"].get()

        if not username or not password:
            messagebox.showwarning("Atenção", "Usuário e Senha são campos obrigatórios.")
            return

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        module_str = self.entries["Módulo"].get()
        is_admin = 1 if self.entries["Admin"].get() == "Sim" else 0
        can_edit_bo = 1 if self.entries["Pode Editar BO"].get() == "Sim" else 0
        can_delete_bo = 1 if self.entries["Pode Excluir BO"].get() == "Sim" else 0
        can_track_bo = 1 if self.entries["Pode Acompanhar BO"].get() == "Sim" else 0

        if is_admin:
            can_edit_bo = 1
            can_delete_bo = 1
            can_track_bo = 1

        module_map = {
            "Corporativo": 0, "Varejo": 1, "Exportação": 2, "Comercial": 3, "Todos": 4
        }
        module = module_map.get(module_str, 4) # 4 é o valor padrão caso não encontre

        try:
            criar_usuario(username, hashed_pw, module, is_admin, can_edit_bo, can_delete_bo, can_track_bo)
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
            self.admin_panel.carregar_usuarios()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar usuário: {e}")

    def aplicar_perfil(self, event=None):
        perfil = self.entries["Perfil"].get()

        presets = {
            "Somente Leitura": ("Não", "Não", "Não", "Não"),
            "Operador": ("Não", "Não", "Não", "Sim"),
            "Supervisor": ("Não", "Sim", "Sim", "Sim"),
            "Administrador": ("Sim", "Sim", "Sim", "Sim"),
        }
        admin, editar, excluir, acompanhar = presets.get(perfil, presets["Operador"])

        self.entries["Admin"].set(admin)
        self.entries["Pode Editar BO"].set(editar)
        self.entries["Pode Excluir BO"].set(excluir)
        self.entries["Pode Acompanhar BO"].set(acompanhar)

    def on_admin_change(self, event=None):
        if self.entries["Admin"].get() == "Sim":
            self.entries["Perfil"].set("Administrador")
            self.entries["Pode Editar BO"].set("Sim")
            self.entries["Pode Excluir BO"].set("Sim")
            self.entries["Pode Acompanhar BO"].set("Sim")