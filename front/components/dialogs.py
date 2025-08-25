import ttkbootstrap as tb
import tkinter as tk
from tkinter import messagebox
import hashlib
from back.utils import resource_path, center_window

class DialogSenhaAdmin:
    def __init__(self, parent, expected_admin_password_hash, on_success_callback=None):
        self.result = None
        self.parent = parent
        self.expected_admin_password_hash = expected_admin_password_hash
        self.on_success_callback = on_success_callback

        self.root = tk.Toplevel(parent)
        self.root.title("Senha de administrador")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.transient(parent)
        self.root.focus_set()
        self.root.resizable(False, False)
        self.root.grab_set()

        frame = tb.Frame(self.root, padding=20)
        frame.pack(expand=True, fill="both")

        tb.Label(frame, text="Digite a senha de administrador para acessar as configurações:").pack(pady=(0, 10))
        self.entry = tb.Entry(frame, show="*", width=25)
        self.entry.pack(pady=5)
        self.entry.focus_set()

        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="OK", width=10, command=self.ok).pack(side="left", padx=5)
        tb.Button(btn_frame, text="Cancelar", width=10, command=self.cancel).pack(side="left", padx=5)

        self.root.bind('<Return>', lambda event: self.ok())
        self.root.bind('<Escape>', lambda event: self.cancel())

        self.root.update_idletasks()
        center_window(self.root)

        self.root.wait_window()

    def ok(self):
        entered_password = self.entry.get()
        hashed_entered_password = hashlib.sha256(entered_password.encode()).hexdigest()

        if hashed_entered_password == self.expected_admin_password_hash:
            self.result = True
            if self.on_success_callback:
                self.on_success_callback()
            self.root.destroy()
        else:
            messagebox.showerror("Erro de Autenticação", "Senha de administrador incorreta.")
            self.entry.delete(0, tk.END)
            self.entry.focus_set()
            self.result = False

    def cancel(self):
        self.result = False
        self.root.destroy()

class chooseModuleDialog:
    def __init__(self, parent, printUser, hora, user):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Escolha o Módulo")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.transient(parent)
        self.root.grab_set()
        self.root.focus_set()
        self.root.geometry("300x150")
        self.root.resizable(False, False)

        self.printUser = printUser
        self.hora = hora
        self.user = user
        self.chosen_module = None
        

        frame = tb.Frame(self.root, padding=20)
        frame.pack(expand=True, fill="both")

        tb.Label(frame, text="Selecione o módulo:").pack(pady=(0, 10))

        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, width=15, text="Corporativo", command=self.set_corporativo).pack(side="left", padx=5)
        tb.Button(btn_frame, width=15, text="Varejo", command=self.set_varejo).pack(side="left", padx=5)

        self.root.update_idletasks()
        center_window(self.root)

        self.root.wait_window()

    def set_corporativo(self):
        self.chosen_module = 'Corporativo'
        self.root.destroy()

    def set_varejo(self):
        self.chosen_module = 'Varejo'
        self.root.destroy()

    def get_chosen_module(self):
        return self.chosen_module, self.printUser, self.hora