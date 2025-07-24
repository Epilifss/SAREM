import tkinter as tk
import ttkbootstrap as tb
import configparser
from back.utils import resource_path, get_config_path, center_window
from back.configdb_service import salvar_configuracoes

CONFIG_PATH = get_config_path()

class ConfigDBModal:
    def __init__(self, parent_login=None):
            self.parent_login = parent_login
            self.root = tk.Toplevel(parent_login)
            self.root.title("Configuração do Banco de Dados")
            self.root.iconbitmap(resource_path('SAREM.ico'))
            self.root.minsize(400, 300)
            self.root.resizable(False, False)
            self.root.transient(parent_login)
            self.root.grab_set()

            self.root.protocol("WM_DELETE_WINDOW", self.cancelar)

            self.config = configparser.ConfigParser()
            self.config.read(CONFIG_PATH)

            # Campos SAREM
            campos_db = [
                ("server", "Servidor"),
                ("database", "Banco de Dados"),
                ("user", "Usuário"),
                ("password", "Senha")
            ]
            # Campos Protheus
            campos_prot = [
                ("server", "Servidor"),
                ("database", "Banco"),
                ("user", "Usuário"),
                ("password", "Senha")
            ]
            self.entries_db = {}
            self.entries_mik = {}

            frame = tb.Frame(self.root, padding=20)
            frame.pack(expand=True, fill=tk.BOTH, anchor="center")

            # SAREM
            tb.Label(frame, text="Banco de Dados SAREM", font=("Arial", 10, "bold")).pack(pady=(0, 10))
            for campo, label in campos_db:
                row = tb.Frame(frame)
                row.pack(fill="x", pady=3)
                tb.Label(row, text=label + ":", width=15, anchor="w").pack(side="left")
                entry = tb.Entry(row, width=30, show="*" if campo == "password" else "")
                entry.pack(side="left", padx=5)
                self.entries_db[campo] = entry

            # Protheus
            tb.Label(frame, text="Banco Protheus", font=("Arial", 10, "bold")).pack(pady=(20, 10))
            for campo, label in campos_prot:
                row = tb.Frame(frame)
                row.pack(fill="x", pady=3)
                tb.Label(row, text=label + ":", width=15, anchor="w").pack(side="left")
                entry = tb.Entry(row, width=30, show="*" if campo == "password" else "")
                entry.pack(side="left", padx=5)
                self.entries_mik[campo] = entry

            # Carrega valores atuais
            if "database" in self.config:
                for campo in self.entries_db:
                    valor = self.config["database"].get(campo, "")
                    self.entries_db[campo].insert(0, valor)
            if "Protheus" in self.config:
                for campo in self.entries_mik:
                    valor = self.config["Protheus"].get(campo, "")
                    self.entries_mik[campo].insert(0, valor)

            # Botões
            btn_frame = tb.Frame(frame)
            btn_frame.pack(pady=15)
            tb.Button(btn_frame, text="Salvar", command=self.salvar, width=15).pack(side="left", padx=10)
            tb.Button(btn_frame, text="Cancelar", command=self.cancelar, width=15).pack(side="left", padx=10)

            center_window(self.root)
            self.root.update_idletasks()
            
            self.root.after(100, lambda: self.entries_db["server"].focus_set())

    def cancelar(self):
        self.root.destroy()
        try:
            if self.parent_login:
                self.parent_login.deiconify()
        except Exception:
            pass

    def salvar(self):
        salvar_configuracoes(self.config, self.entries_db, self.entries_mik, self.cancelar)