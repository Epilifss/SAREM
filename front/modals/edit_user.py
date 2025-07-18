import tkinter as tk
import ttkbootstrap as tb
import hashlib
from tkinter import messagebox
from back.utils import resource_path
from back.user_service import editar_usuario

class EditarUsuarioModal:
    def __init__(self, parent, admin_panel, user_data):
        self.root = tk.Toplevel(parent)
        self.root.title("Editar Usuário")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.grab_set()
        self.root.focus_set()
        self.admin_panel = admin_panel
        self.user_data = user_data

        campos = ["Usuário", "Senha", "Módulo", "Admin"]
        self.entries = {}

        content = tb.Frame(self.root, padding=20)
        content.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        print(f"user_data: {self.user_data}")

        for i, campo in enumerate(campos):
            tb.Label(content, text=f"{campo}:").grid(
            row=i, column=0, sticky=tk.W, padx=10, pady=8
            )

            if campo == "Admin":
                entry = tb.Combobox(content, values=["Sim", "Não"], state="readonly")
                entry.set(self.user_data[3])
            elif campo == "Senha":
                entry = tb.Entry(content, show="*")
            elif campo == "Módulo":
                entry = tb.Combobox(content, values=[
                    "Corporativo", "Varejo", "Exportação", "Comercial"], state="readonly")
                entry.set(self.user_data[2])
            elif campo == "Usuário":
                entry = tb.Entry(content)
                entry.insert(0, self.user_data[1])
            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[campo] = entry

        tb.Button(content, text="Salvar", command=self.salvar).grid(
            row=len(campos), column=0, columnspan=2, pady=(15, 0)
        )

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def salvar(self):
        username = self.entries["Usuário"].get()
        password = self.entries["Senha"].get()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest() if password else None
        module = self.entries["Módulo"].get()
        is_admin = 1 if self.entries["Admin"].get() == "Sim" else 0
        module = 0 if module == "Corporativo" else 1 if module == "Varejo" else 2 if module == "Exportação" else 3 if module == "Comercial" else 4

        try:
            editar_usuario(self.user_data[0], username, hashed_pw, module, is_admin)
            messagebox.showinfo("Sucesso", "Usuário editado com sucesso!")
            self.admin_panel.carregar_usuarios()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao editar usuário: {e}")