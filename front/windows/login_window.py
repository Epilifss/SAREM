import ttkbootstrap as tb
import tkinter as tk
import hashlib
from tkinter import messagebox
from PIL import Image, ImageTk
import datetime
import configparser

from back.utils import resource_path, get_config_path
from back.bo_monitor import monitorar_bo_embarcadas
from back.user_service import autenticar_usuario
from front.windows.admin_panel import AdminPanel
from front.components.dialogs import DialogSenhaAdmin, chooseModuleDialog
from front.modais.config_db import ConfigDBModal
from front.windows.corporativo_view import CorporativoModule
from front.windows.varejo_view import VarejoModule
from front.windows.exportacao_view import ExportacaoModule
from front.windows.changelog_window import ChangelogWindow
from front.changelog_data import get_changelog_for_version
from front import versao

VERSAO_ATUAL = versao
CONFIG_PATH = get_config_path()

class LoginWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("SAREM")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.state('zoomed')
        self.root.focus_set()
        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)
        if 'Admin' not in self.config:
            self.config['Admin'] = {
                'password': hashlib.sha256('4dmin123@4'.encode()).hexdigest()
            }
            with open(CONFIG_PATH, "w") as configfile:
                self.config.write(configfile)

        self.frame = tb.Frame(self.root, padding=10)
        self.frame.pack(expand=True, fill="both")

        campos_frame = tb.Frame(self.frame)
        campos_frame.pack(pady=200, expand=True, anchor="center")
        rodape_frame = tb.Frame(self.frame)
        rodape_frame.pack(pady=0, expand=True, anchor="se")
        tb.Label(rodape_frame, text=f"Versão {VERSAO_ATUAL}").pack(side="right", padx=5)

        logo_img = Image.open(resource_path('SAREM PNG.png'))
        logo_img = logo_img.resize((250, 80), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        tb.Label(campos_frame, image=self.logo_photo).pack(pady=(0, 10))

        user_text = tb.Frame(campos_frame)
        user_text.pack(fill="both", pady=1, expand=True, side="top")
        tb.Label(user_text, text="Usuário:", width=10, anchor="w").pack(side="left", padx=0)
        user_entry = tb.Frame(campos_frame)
        user_entry.pack(fill="both", pady=1, expand=True)
        self.username = tb.Entry(user_entry, width=40)
        self.username.pack(side="left", padx=0)

        pass_text = tb.Frame(campos_frame)
        pass_text.pack(fill="both", pady=1, expand=True, side="top")
        tb.Label(pass_text, text="Senha:", width=10, anchor="w").pack(side="left")
        pass_entry = tb.Frame(campos_frame)
        pass_entry.pack(fill="both", pady=1)
        self.password = tb.Entry(pass_entry, show="*", width=40)
        self.password.pack(side="left", padx=0)

        btn_frame = tb.Frame(campos_frame)
        btn_frame.pack(pady=5, expand=True, anchor="center")
        self.login_btn = tb.Button(btn_frame, text="Login", width=17, command=self.login)
        self.login_btn.pack(side="left", padx=1)
        self.config_btn = tb.Button(btn_frame, text="Configurar Banco", width=17, command=self.abrir_config)
        self.config_btn.pack(side="right", padx=1)

        self.username.focus_set()
        self.root.bind('<Return>', self.login)

    def abrir_config(self):
        admin_password_hash = self.config['Admin']['password']
        DialogSenhaAdmin(self.root,
                         expected_admin_password_hash=admin_password_hash,
                         on_success_callback=self._open_config_modal)

    def _open_config_modal(self):
        ConfigDBModal(parent_login=self.root)

    def admin_login(self):
        self.username.delete(0, tk.END)
        self.password.delete(0, tk.END)
    
    def login(self, event=None):
        username = self.username.get()
        password = self.password.get()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        user = autenticar_usuario(username, hashed_pw)
        if user is None:
            messagebox.showerror("Erro", "Credenciais inválidas")
            return

        printUser = f"Usuário {user.username} logou no "
        hora = datetime.datetime.now().strftime("às %H:%M")

        if user.is_admin:
            self._mostrar_changelog_se_necessario(user.username)
            print(printUser + "painel de administração " + hora)
            AdminPanel(self.parent)
            self.root.destroy()
        else:
            allowed_modules = user.get_allowed_modules() if hasattr(user, "get_allowed_modules") else []
            if not allowed_modules:
                messagebox.showerror("Erro", "Módulo do usuário não encontrado. Contate o administrador.")
                return

            if len(allowed_modules) == 1:
                chosen_module_type = allowed_modules[0]
            else:
                dialog = chooseModuleDialog(self.root, printUser, hora, user, allowed_modules=allowed_modules)
                chosen_module_type, chosen_print_user, chosen_hora = dialog.get_chosen_module()

                if not chosen_module_type:
                    return
                printUser = chosen_print_user
                hora = chosen_hora

            self._mostrar_changelog_se_necessario(user.username)
            self.root.destroy()
            self._open_module(chosen_module_type, user, printUser, hora)

    def _mostrar_changelog_se_necessario(self, username):
        if not username:
            return

        self.config.read(CONFIG_PATH)
        if 'Changelog' not in self.config:
            self.config['Changelog'] = {}

        user_key = username.strip().lower()
        versao_ja_vista = self.config['Changelog'].get(user_key, "")

        if versao_ja_vista == VERSAO_ATUAL:
            return

        changelog_data = get_changelog_for_version(VERSAO_ATUAL)
        ChangelogWindow(self.root, VERSAO_ATUAL, changelog_data)

        self.config['Changelog'][user_key] = VERSAO_ATUAL
        with open(CONFIG_PATH, "w") as configfile:
            self.config.write(configfile)

    def _open_module(self, chosen_module_type, user, printUser, hora):
        if chosen_module_type == 'Corporativo':
            print(f"{printUser}módulo Corporativo {hora}")
            monitorar_bo_embarcadas()
            CorporativoModule(user, self.parent)
        elif chosen_module_type == 'Varejo':
            print(f"{printUser} módulo Varejo {hora}")
            monitorar_bo_embarcadas()
            VarejoModule(user, self.parent)
        elif chosen_module_type == 'Exportação':
            print(f"{printUser} módulo Exportação {hora}")
            monitorar_bo_embarcadas()
            ExportacaoModule(user, self.parent)
        else:
            messagebox.showerror("Erro", "Módulo selecionado inválido. Contate o administrador.")