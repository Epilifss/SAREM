# Bibliotecas
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import pyodbc
import hashlib
import sys
import os
import subprocess
import tempfile
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import configparser
import requests
from moviepy import VideoFileClip
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph
from reportlab.lib.units import cm
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from textwrap import wrap

# Componentes
from components import *

# Modulos
from modulos.corporativo import CorporativoModule
from modulos.varejo import VarejoModule
from modulos.exportacao import ExportacaoModule

# Banco de dados
from database import create_connection_Protheus
from database import create_connection

# Estilos


# Funções

def center_window_screen(win, width=350, height=100):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

VERSAO_ATUAL = "1.0.1"
URL_VERSAO = "https://dl.dropboxusercontent.com/scl/fi/dh936k1ph0m2eq5low9gn/versao.txt?rlkey=fnyxw89yee7ai571ue3znbaiv&st=xd9f26ij&dl=0"
URL_DOWNLOAD = "https://dl.dropboxusercontent.com/scl/fi/lm41ku5uvts7nsa6we01w/Instalador_SAREM.exe?rlkey=2jwgcq2pst9i8xoo5r8l1cxtg&st=yzzgbd9k&dl=0"

def verificar_e_att(parent):
    try:
        resposta = requests.get(URL_VERSAO, timeout=5)
        if resposta.status_code == 200:
            versao_remota = resposta.text.strip()
            if versao_remota > VERSAO_ATUAL:
                resp = messagebox.askyesno(
                    "SAREM - Atualização disponível",
                    f"Uma nova versão está disponível.\nDeseja atualizar agora?"
                )
                if not resp:
                    return True

                # Janela de progresso
                progress_win = tk.Toplevel(parent)
                progress_win.title("Baixando atualização")
                progress_win.iconbitmap(resource_path('SAREM.ico'))
                progress_win.geometry("350x100")
                progress_win.transient(parent)
                progress_win.grab_set()
                ttk.Label(progress_win, text="Baixando nova versão...").pack(pady=10)
                progress = ttk.Progressbar(progress_win, orient="horizontal", length=300, mode="determinate")
                progress.pack(pady=10)
                progress["value"] = 0

                center_window_screen(progress_win, 350, 100)

                temp_dir = tempfile.gettempdir()
                caminho_instalador = os.path.join(temp_dir, "atualizacao.exe")
                r = requests.get(URL_DOWNLOAD, stream=True)
                total = int(r.headers.get('content-length', 0))
                chunk_size = 8192
                baixado = 0
                f = open(caminho_instalador, 'wb')
                chunks = r.iter_content(chunk_size=chunk_size)

                def baixar_pedaco():
                    nonlocal baixado
                    try:
                        chunk = next(chunks)
                        if chunk:
                            f.write(chunk)
                            baixado += len(chunk)
                            if total:
                                valor = (baixado / total) * 100
                                progress["value"] = valor
                            progress_win.update_idletasks()
                        progress_win.after(1, baixar_pedaco)
                    except StopIteration:
                        f.close()
                        progress_win.destroy()
                        if os.path.exists(caminho_instalador):
                            messagebox.showinfo("Atualização", "Download concluído! O instalador será aberto.")
                            print(f"Tentando abrir o instalador: {caminho_instalador}")
                            try:
                                subprocess.Popen(['explorer', caminho_instalador])
                            except Exception as e:
                                messagebox.showerror("Erro", f"Não foi possível abrir o instalador:\n{e}")
                            parent.quit()
                        else:
                            messagebox.showerror("Erro", "O instalador não foi baixado corretamente.")

                baixar_pedaco()
                progress_win.transient()
                progress_win.grab_set()
                progress_win.wait_window()
                return False

        return True
    except requests.RequestException as e:
        print(f"Erro ao verificar atualização: {e}")
        return True


def monitorar_bo_embarcadas():
    def tarefa():
        while True:
            try:
                horario = datetime.datetime.now()
                hora = (f"as {horario.hour}:{horario.minute}")

                print("Monitorando BOs embarcadas " + hora)
                conn = create_connection()
                conn_Protheus = create_connection_Protheus()
                if conn is None or conn_Protheus is None:
                    print("Erro de conexão com o banco.")
                    time.sleep(60)
                    continue

                cursor = conn.cursor()
                cursor.execute("SELECT bo_number, op FROM bo_records WHERE status <> 'Embarcado'")
                bos = cursor.fetchall()

                for bo_number, op in bos:
                    cursor_mik = conn_Protheus.cursor()
                    cursor_mik.execute("""
                        SELECT COUNT(*) FROM SC6010
                        WHERE C6_NUM = ? AND C6_BLQ = '' AND D_E_L_E_T_ <> '*'
                    """, str(op))
                    total_itens = cursor_mik.fetchone()[0]

                    cursor_mik.execute("""
                        SELECT COUNT(*) FROM SC6010
                        WHERE C6_NUM = ? AND C6_BLQ = '' AND D_E_L_E_T_ <> '*' AND C6_NOTA <> ''
                    """, str(op))
                    itens_com_nota = cursor_mik.fetchone()[0]
                    cursor_mik.close()

                    if total_itens > 0 and total_itens == itens_com_nota:
                        cursor.execute("UPDATE bo_records SET status = 'Embarcado' WHERE bo_number = ?", bo_number)
                        conn.commit()
                        print(f"BO {bo_number} marcada como Embarcada.")

                cursor.close()
                conn.close()
                conn_Protheus.close()
            except Exception as e:
                print(f"Erro ao monitorar BOs embarcadas: {e}")
            time.sleep(60)

    threading.Thread(target=tarefa, daemon=True).start()

def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

def center_window_child(child, parent):
    child.update_idletasks()
    width = child.winfo_width()
    height = child.winfo_height()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    x = parent_x + (parent_width // 2) - (width // 2)
    y = parent_y + (parent_height // 2) - (height // 2)
    child.geometry(f"{width}x{height}+{x}+{y}")

class TreeViewHelper:
    def ajustar_colunas(self):
        for col in self.tree["columns"]:
            valores = [self.tree.set(item, col) for item in self.tree.get_children()]
        if not valores:
            largura = 50  # valor padrão mínimo
        else:
            largura = max(len(str(valor)) for valor in valores) * 10
        self.tree.column(col, width=largura) 

def get_config_path():
    appdata = os.environ.get('APPDATA') or os.path.expanduser('~')
    config_dir = os.path.join(appdata, 'SAREM')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.ini')

CONFIG_PATH = get_config_path()

class ConfigEditor:
    def __init__(self, parent_login=None):
        self.parent_login = parent_login
        self.root = tk.Tk()
        self.root.title("Configuração do Banco de Dados")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.focus_set()

        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)
        with open(CONFIG_PATH, "w") as configfile:
            self.config.write(configfile)

        # Campos para o banco SAREM
        campos_db = [
            ("server", "Servidor"),
            ("database", "Banco de Dados"),
            ("user", "Usuário"),
            ("password", "Senha")
        ]
        # Campos para o banco Protheus
        campos_prot = [
            ("server", "Servidor"),
            ("database", "Banco"),
            ("user", "Usuário"),
            ("password", "Senha")
        ]
        self.entries_db = {}
        self.entries_mik = {}

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text="Banco de Dados SAREM", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        for i, (campo, label) in enumerate(campos_db):
            ttk.Label(frame, text=label + ":").grid(row=i+1, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if campo == "password" else "")
            entry.grid(row=i+1, column=1, pady=5)
            self.entries_db[campo] = entry

        ttk.Label(frame, text="Banco Protheus", font=("Arial", 10, "bold")).grid(row=len(campos_db)+1, column=0, columnspan=2, pady=(20, 10))
        for i, (campo, label) in enumerate(campos_prot):
            ttk.Label(frame, text=label + ":").grid(row=len(campos_db)+2+i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if campo == "password" else "")
            entry.grid(row=len(campos_db)+2+i, column=1, pady=5)
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

        row_btn = len(campos_db) + len(campos_prot) + 2
        ttk.Button(frame, text="Salvar", command=self.salvar).grid(row=row_btn, column=0, pady=15, sticky="ew")
        ttk.Button(frame, text="Cancelar", command=self.cancelar).grid(row=row_btn, column=1, pady=15, sticky="ew")

        center_window(self)

    def cancelar(self):
        self.root.destroy()
        try:
            if hasattr(self, 'parent_login') and self.parent_login:
                self.parent_login.deiconify()
        except Exception:
            pass

    def salvar(self):
        if "database" not in self.config:
            self.config["database"] = {}
        if "Protheus" not in self.config:
            self.config["Protheus"] = {}
        for campo, entry in self.entries_db.items():
            self.config["database"][campo] = entry.get()
        for campo, entry in self.entries_mik.items():
            self.config["Protheus"][campo] = entry.get()
        try:
            with open(CONFIG_PATH, "w") as configfile:
                self.config.write(configfile)
            messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
            self.root.destroy()
            try:
                if hasattr(self, 'parent_login') and self.parent_login:
                    self.parent_login.deiconify()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

class LoginWindow:
    def __init__(self, parent):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("SAREM")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.geometry("300x200")
        self.root.focus_set()

        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.pack(expand=True)

        logo_img = Image.open(resource_path('SAREM PNG.png'))
        logo_img = logo_img.resize((150, 50), Image.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_img)
        ttk.Label(self.frame, image=self.logo_photo).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Label(self.frame, text="Usuário:").grid(
            row=1, column=0, sticky=tk.W)
        self.username = ttk.Entry(self.frame)
        self.username.grid(row=1, column=1)

        ttk.Label(self.frame, text="Senha:").grid(row=2, column=0, sticky=tk.W)
        self.password = ttk.Entry(self.frame, show="*")
        self.password.grid(row=2, column=1)

        self.login_btn = ttk.Button(self.frame, text="Login", command=self.login)
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=5)

        self.config_btn = ttk.Button(
            self.frame, text="Configurar Banco", command=self.abrir_config)
        self.config_btn.grid(row=4, column=0, columnspan=2, pady=5)

        center_window(self)
        self.username.focus_set()
        self.root.bind('<Return>', self.login)

    def abrir_config(self):
        self.root.withdraw()
        editor = ConfigEditor(self.root)
        self.root.wait_window(editor.root)
        try:
            self.root.deiconify()
        except tk.TclError:
            pass
    
    def admin_login(self):
        self.username.delete(0, tk.END)
        self.password.delete(0, tk.END)

    def login(self, event=None):
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        campos_obrigatorios = ["server", "database", "user", "password"]
        if "database" not in config or any(not config["database"].get(campo, "").strip() for campo in campos_obrigatorios):
            messagebox.showwarning(
                "Configuração necessária",
                "Preencha as configurações do banco de dados antes de fazer login."
            )
            self.abrir_config()
            return

        username = self.username.get()
        password = self.password.get()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        

        conn = create_connection()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username COLLATE Latin1_General_BIN=? AND password_hash COLLATE Latin1_General_BIN=?", (username, hashed_pw))
            user = cursor.fetchone()
            

            if user:
                printUser = (f"Usuário {user[1]} logou no ")

                horario = datetime.datetime.now()
                hora = (f"as {horario.hour}:{horario.minute}")

                if user[4]:  # is_admin
                    self.root.destroy()
                    print(printUser + "painel de administração " + hora)
                    AdminPanel(self.parent)
                else:
                    module = user[3]
                    if (module) == '0':
                        self.root.destroy()
                        print(printUser + "módulo Corporativo " + hora)
                        monitorar_bo_embarcadas()
                        CorporativoModule(user, self.parent)
                    elif (module) == '1':
                        self.root.destroy()
                        print(printUser + "módulo Varejo " + hora)
                        monitorar_bo_embarcadas()
                        VarejoModule(user, self.parent)
                    elif (module) == '2':
                        self.root.destroy()
                        print(printUser + "módulo Exportação " + hora)
                        monitorar_bo_embarcadas()
                        ExportacaoModule(user, self.parent)
                    else:
                        messagebox.showerror(
                            "Erro", "Módulo do usuário não encontrado. Contate o administrador.")
            else:
                messagebox.showerror("Erro", "Credenciais inválidas")
        except pyodbc.Error as e:
            messagebox.showerror(
                "Erro", f"Erro ao consultar o banco de dados: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()


class AdminPanel:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title("Painel de Administração")
        self.root.iconbitmap(resource_path('SAREM.ico'))

        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        self.root.state('zoomed')

        # Abas
        self.notebook = ttk.Notebook(self.root)

        # Aba de Usuários
        self.user_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.user_frame, text="Usuários")

        header = ttk.Frame(self.user_frame)
        header.pack(fill=tk.X)

        ttk.Button(header, text="Novo Usuário",
                   command=self.novo_usuario).pack(side=tk.LEFT)
        ttk.Button(header, text="Excluir Usuário",
                   command=self.excluir_usuario).pack(side=tk.LEFT)
        ttk.Button(header, text="Editar Usuário",
                   command=self.editar_usuario).pack(side=tk.LEFT)
        ttk.Button(header, text="Logoff",
                   command=self.logoff).pack(side=tk.RIGHT)
        
        # Lista de usuários
        self.tree = ttk.Treeview(self.user_frame, columns=(
            "ID", "Usuário", "Módulo", "Admin"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Usuário", text="Usuário")
        self.tree.heading("Módulo", text="Módulo")
        self.tree.heading("Admin", text="Admin")
        self.tree.column("ID", width=0, stretch=False)
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.tree.bind("<<TreeviewSelect>>", self.atualizar_selecao)

        # Aba de Database
        self.db_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.db_frame, text="Banco de Dados")
        self.criar_formulario_db()

        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.carregar_usuarios()

    def carregar_usuarios(self):
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, IIF(module='0','Corporativo',IIF(module='1','Varejo',IIF(module='2', 'Exportação', ''))), IIF(is_admin='True', 'Sim', 'Não') FROM users")
            rows = cursor.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                valores_formatados = [str(item) for item in row]
                self.tree.insert("", tk.END, values=valores_formatados)
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def atualizar_selecao(self, event=None):
        selected_items = self.tree.selection()
        if selected_items:
            item_id = selected_items[0]
            valores = self.tree.item(item_id, "values")
            self.usuario_selecionado = valores[0]
            self.nome_usuario = valores[1]
        else:
            self.usuario_selecionado = None

    def novo_usuario(self):
        NovoUsuarioWindow(self.root, self)

    def excluir_usuario(self):
        if not hasattr(self, 'usuario_selecionado') or not self.usuario_selecionado:
            messagebox.showerror("Erro", "Nenhum usuário selecionado")
            return

        resposta = messagebox.askyesno(
            "Confirmar", f"Tem certeza que deseja excluir o usuário {self.nome_usuario}?")
        if not resposta:
            return

        conn = create_connection()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        try:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE id=?",
                           (self.usuario_selecionado,))
            usuario_existente = cursor.fetchone()

            if not usuario_existente:
                messagebox.showerror(
                    "Erro", f"O usuário '{self.usuario_selecionado}' não foi encontrado no banco de dados.")
                return

            usuario_formatado = self.usuario_selecionado.strip()

            print(f"Excluindo usuário: {usuario_formatado}")

            cursor.execute("DELETE FROM users WHERE id=?",
                           (self.usuario_selecionado,))
            conn.commit()

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Erro", "Nenhum registro foi excluído. Verifique se o usuário existe.")
            else:
                messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")

            self.carregar_usuarios()
            self.usuario_selecionado = None

        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao excluir usuário: {e}")

        finally:
            if conn:
                cursor.close()
                conn.close()

    def editar_usuario(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Atenção", "Selecione um usuário para editar.")
            return

        user_data = self.tree.item(selected_items[0], "values")
        EditarUsuarioWindow(self.root, self, user_data)

    def criar_formulario_db(self):
        CONFIG_PATH = get_config_path()
        self.db_config = configparser.ConfigParser()
        self.db_config.read(CONFIG_PATH)

        campos_db = [
            ("server", "Servidor"),
            ("database", "Banco de Dados"),
            ("user", "Usuário"),
            ("password", "Senha")
        ]
        campos_prot = [
            ("server", "Servidor"),
            ("database", "Banco"),
            ("user", "Usuário"),
            ("password", "Senha")
        ]
        self.db_entries = {}
        self.mik_entries = {}

        frame = ttk.Frame(self.db_frame, padding=20)
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text="Banco de Dados SAREM", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        for i, (campo, label) in enumerate(campos_db):
            ttk.Label(frame, text=label + ":").grid(row=i+1, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if campo == "password" else "")
            entry.grid(row=i+1, column=1, pady=5)
            self.db_entries[campo] = entry

        ttk.Label(frame, text="Banco Protheus", font=("Arial", 10, "bold")).grid(row=len(campos_db)+1, column=0, columnspan=2, pady=(20, 10))
        for i, (campo, label) in enumerate(campos_prot):
            ttk.Label(frame, text=label + ":").grid(row=len(campos_db)+2+i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if campo == "password" else "")
            entry.grid(row=len(campos_db)+2+i, column=1, pady=5)
            self.mik_entries[campo] = entry

        if "database" in self.db_config:
            for campo in self.db_entries:
                valor = self.db_config["database"].get(campo, "")
                self.db_entries[campo].insert(0, valor)
        if "Protheus" in self.db_config:
            for campo in self.mik_entries:
                valor = self.db_config["Protheus"].get(campo, "")
                self.mik_entries[campo].insert(0, valor)

        row_btn = len(campos_db) + len(campos_prot) + 2
        ttk.Button(frame, text="Salvar", command=self.salvar_config_db).grid(row=row_btn, column=0, pady=15, sticky="ew")
        ttk.Button(frame, text="Cancelar", command=self.cancelar_config_db).grid(row=row_btn, column=1, pady=15, sticky="ew")

    def salvar_config_db(self):
        CONFIG_PATH = get_config_path()
        if "database" not in self.db_config:
            self.db_config["database"] = {}
        if "Protheus" not in self.db_config:
            self.db_config["Protheus"] = {}
        for campo, entry in self.db_entries.items():
            self.db_config["database"][campo] = entry.get()
        for campo, entry in self.mik_entries.items():
            self.db_config["Protheus"][campo] = entry.get()
        try:
            with open(CONFIG_PATH, "w") as configfile:
                self.db_config.write(configfile)
            messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def cancelar_config_db(self):
        for campo, entry in self.db_entries.items():
            entry.delete(0, tk.END)
            valor = self.db_config["database"].get(campo, "")
            entry.insert(0, valor)
        for campo, entry in self.mik_entries.items():
            entry.delete(0, tk.END)
            valor = self.db_config["Protheus"].get(campo, "")
            entry.insert(0, valor)

    def logoff(self):
        self.root.destroy()
        LoginWindow()


class NovoUsuarioWindow:
    def __init__(self, parent, admin_panel):
        self.root = tk.Toplevel(parent)
        self.root.title("Novo Usuário")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.grab_set()
        self.root.focus_set()

        self.admin_panel = admin_panel

        campos = ["Usuário", "Senha", "Módulo", "Admin"]
        self.entries = {}

        content = ttk.Frame(self.root, padding=20)
        content.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        for i, campo in enumerate(campos):
            ttk.Label(content, text=f"{campo}:").grid(
            row=i, column=0, sticky=tk.W, padx=10, pady=8
            )
            if campo == "Senha":
                entry = ttk.Entry(content, show="*")
            elif campo == "Admin":
                entry = ttk.Combobox(content, values=["Sim", "Não"], state="readonly")
            elif campo == "Módulo":
                entry = ttk.Combobox(content, values=[
                "Corporativo", "Varejo", "Exportação"], state="readonly")
            else:
                entry = ttk.Entry(content)

            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[campo] = entry

        ttk.Button(content, text="Salvar", command=self.salvar).grid(
            row=len(campos), column=0, columnspan=2, pady=(15, 0)
        )

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def salvar(self):
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            username = self.entries["Usuário"].get()
            password = self.entries["Senha"].get()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            module = self.entries["Módulo"].get()
            is_admin = 1 if self.entries["Admin"].get() == "Sim" else 0
            module = 0 if self.entries["Módulo"].get(
            ) == "Corporativo" else 1 if self.entries["Módulo"].get() == "Varejo" else 2

            cursor.execute('''
                INSERT INTO users (username, password_hash, module, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_pw, module, is_admin))

            conn.commit()
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
            self.root.destroy()

            self.admin_panel.carregar_usuarios()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao salvar usuário: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()


class EditarUsuarioWindow:
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

        content = ttk.Frame(self.root, padding=20)
        content.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        for i, campo in enumerate(campos):
            ttk.Label(content, text=f"{campo}:").grid(
            row=i, column=0, sticky=tk.W, padx=10, pady=8
            )

            if campo == "Admin":
                entry = ttk.Combobox(content, values=["Sim", "Não"], state="readonly")
                entry.set("Sim" if self.user_data[3] == "Sim" else "Não")
            elif campo == "Senha":
                entry = ttk.Entry(content, show="*")
            elif campo == "Módulo":
                entry = ttk.Combobox(content, values=[
                    "Corporativo", "Varejo", "Exportação"], state="readonly")
                entry.set(self.user_data[2])
            else:
                entry = ttk.Entry(content)
            if campo == "Usuário":
                entry.insert(0, self.user_data[1])
            entry.grid(row=i, column=1, padx=10, pady=8)
            self.entries[campo] = entry

        ttk.Button(content, text="Salvar", command=self.salvar).grid(
            row=len(campos), column=0, columnspan=2, pady=(15, 0)
        )

        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def salvar(self):
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            username = self.entries["Usuário"].get()
            new_password = self.entries["Senha"].get()
            module = self.entries["Módulo"].get()
            is_admin = 1 if self.entries["Admin"].get() == "Sim" else 0
            module = 0 if self.entries["Módulo"].get(
            ) == "Corporativo" else 1 if self.entries["Módulo"].get() == "Varejo" else 2

            if new_password:
                hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute('''
                    UPDATE users
                    SET username = ?, password_hash = ?, module = ?, is_admin = ?
                    WHERE id = ?
                ''', (username, hashed_pw, module, is_admin, self.user_data[0]))  # ID está no índice 0
            else:
                cursor.execute('''
                    UPDATE users
                    SET username = ?, module = ?, is_admin = ?
                    WHERE id = ?
                ''', (username, module, is_admin, self.user_data[0]))  # ID está no índice 0

            conn.commit()
            messagebox.showinfo("Sucesso", "Usuário editado com sucesso!")
            self.root.destroy()

            self.admin_panel.carregar_usuarios()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao editar usuário: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()


if __name__ == "__main__":
    LoginWindow()


class Embarcados(TreeViewHelper):
    def __init__(self, parent, caller_id=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Embarcados")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.geometry("1000x600")

        self.root.transient(parent)
        center_window_child(self.root, parent)

        self.ultimo_modulo = caller_id
        print(self.identificar_chamador())

        # Cabeçalho
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X)

        ttk.Button(header, text="Fechar",
                   command=lambda: self.root.destroy()).pack(side=tk.RIGHT)

        # Barra de pesquisa
        self.search_bar = SearchBar(
            self.root, self.pesquisar_bo, self.clear_search)

        # Lista de BOs
        self.tree = ttk.Treeview(self.root, columns=(
            "BO", "OP", "Status", "tipo_ocorrencia", "dt_embarque"), show="headings")
        self.tree.heading("BO", text="BO")
        self.tree.heading("OP", text="OP")
        self.tree.heading("Status", text="Status")
        self.tree.heading("tipo_ocorrencia", text="Tipo de Ocorrência")
        self.tree.heading("dt_embarque", text="Data de Embarque")

        self.tree.pack(expand=True, fill=tk.BOTH)

        self.tree.bind("<Double-1>", lambda event: exibir_detalhes_acompanhando(self.root,
                       self.tree, caller_id="Corporativo"))

        self.carregar_bos()

    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de embarcados chamada pelo módulo: {self.ultimo_modulo}"

    def carregar_bos(self):
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            query = """
                SELECT bo_number, op, status, tipo_ocorrencia, dt_embarque FROM bo_records WHERE status LIKE 'Embarcado' AND modulo LIKE ?
            """
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
                status = str(row[2]).strip(
                    "(' ,)") if row[2] is not None else ""
                tipo_ocorrencia = str(row[3]).strip(
                    "(' ,)") if row[3] is not None else ""
                motivo = str(row[4]).strip(
                    "(' ,)") if row[4] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, status, tipo_ocorrencia, motivo))

            self.ajustar_colunas()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

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
                "SELECT bo_number, op, status, tipo_ocorrencia, motivo FROM bo_records WHERE bo_number LIKE ?", (f"%{termo}%",))
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
                dt_embarque = str(row[4]).strip(
                    "(' ,)") if row[4] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, status, tipo_ocorrencia, dt_embarque))
                
            self.ajustar_colunas()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def clear_search(self):
        self.search_bar.search_entry.delete(0, tk.END)
        self.search_bar.update_buttons()
        self.carregar_bos()

class Estatisticas:
    def __init__(self, parent, caller_id=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Estatísticas")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.geometry("800x500")
        self.root.state('zoomed')

        self.root.transient(parent)
        center_window_child(self.root, parent)

        self.ultimo_modulo = caller_id
        print(self.identificar_chamador())
        
        self.anos = self.obter_anos()
        self.setores = self.obter_setores("Todos")
        self.contagens = self.obter_contagens_por_setor()
        self.ano_atual = "Todos"

        # Cabeçalho
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(header, text="Ano: ").pack(side=tk.LEFT)
        self.listaAnos = ttk.Combobox(header, values=self.anos, state="readonly")
        self.listaAnos.pack(side=tk.LEFT)
        self.listaAnos.set(self.ano_atual)
        self.listaAnos.bind("<<ComboboxSelected>>", self.atualizar_grafico)
        
        ttk.Button(header, text="Fechar",
                   command=lambda: self.root.destroy()).pack(side=tk.RIGHT)
        
        # Gráfico
        self.frame = ttk.Frame(self.root, padding="3 3 12 12")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.atualizar_grafico()

        
    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de estatísticas chamada pelo módulo: {self.ultimo_modulo}"

    def obter_anos(self):
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT DISTINCT YEAR(emissao_totvs) AS ano FROM bo_records WHERE emissao_totvs IS NOT NULL AND modulo like ? ORDER BY ano DESC", (self.ultimo_modulo,))
        anos = ["Todos"] + [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return anos
        
    def obter_setores(self, ano):
        conn = create_connection()
        cursor = conn.cursor()

        if ano == "Todos":
            query = ("SELECT COALESCE(setor_responsavel, 'Não especificado') FROM bo_records WHERE modulo like ?")
            cursor.execute(query, self.ultimo_modulo)
        else:
            query = ("SELECT COALESCE(setor_responsavel, 'Não especificado') FROM bo_records WHERE YEAR(emissao_totvs) = ? AND modulo like ? ORDER BY COALESCE(setor_responsavel, 'Não especificado')")
            cursor.execute(query, (ano, self.ultimo_modulo))
        setores = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return setores
        
    def obter_contagens_por_setor(self):
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COALESCE(setor_responsavel, 'Não especificado'), COUNT(*) FROM bo_records GROUP BY setor_responsavel")
        contagens = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        conn.close()

        return contagens

    def atualizar_grafico(self, event=None):
        self.ano_atual = self.listaAnos.get()
        self.setores = self.obter_setores(self.ano_atual)  # Obter setores com base no filtro selecionado
        self.contagens = self.obter_contagens_por_setor_por_ano(self.ano_atual)  # Obter contagens com base no filtro selecionado
        self.ax.clear()
        contagens_completo = [self.contagens.get(sector, 0) for sector in self.setores]
        self.ax.bar(self.setores, contagens_completo, color='green')
        self.ax.set_title(f"Contagem de BO's por setor ({self.ano_atual})")
        self.ax.set_xlabel("Setor")
        self.ax.set_ylabel("Contagem")

        formatter = FuncFormatter(lambda x, _: int(x))
        self.ax.yaxis.set_major_formatter(formatter)

        plt.xticks(rotation=45)
        self.canvas.draw()

    def obter_contagens_por_setor_por_ano(self, ano):
        conn = create_connection()
        cursor = conn.cursor()

        if ano == "Todos":
            cursor.execute(f"SELECT COALESCE(setor_responsavel, 'Não especificado'), COUNT(*) FROM bo_records WHERE modulo like ? GROUP BY setor_responsavel", (self.ultimo_modulo,))
        else:
            query = ("SELECT COALESCE(setor_responsavel, 'Não especificado'), COUNT(*) FROM bo_records WHERE YEAR(emissao_totvs) = ? AND modulo like ? GROUP BY setor_responsavel")
            cursor.execute(query, (ano, self.ultimo_modulo))
        contagens = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.close()
        conn.close()

        return contagens   

class Relatorios(TreeViewHelper):
    def __init__(self, parent, caller_id=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Gerar Relatório")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.geometry("800x500")
        self.root.state('zoomed')

        self.root.transient(parent)
        center_window_child(self.root, parent)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.ultimo_modulo = caller_id
        print(self.identificar_chamador())

        self.setores = self.setor()
        self.motivos = self.motivo()
        self.clientes = self.cliente()

        frame_relat = ttk.Labelframe(self.root, text="Critérios de Busca", padding=10)
        frame_relat.grid(row=0, column=0, sticky="n", padx=10, pady=10)

        frame_relat.grid_rowconfigure(0, weight=1)
        frame_relat.grid_columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(self.root)
        tree_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Lista de BOs Treeview
        self.tree = ttk.Treeview(tree_frame, columns=(
            "BO", "OP", "loja", "tipo_ocorrencia", "setor_responsavel", "motivo"), show="headings")
        self.tree.heading("BO", text="BO")
        self.tree.heading("OP", text="OP")
        self.tree.heading("loja", text="Cliente")
        self.tree.heading("tipo_ocorrencia", text="Tipo de Ocorrência")
        self.tree.heading("setor_responsavel", text="Setor Responsável")
        self.tree.heading("motivo", text="Motivo")

        # Barra de rolagem vertical
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Campos de Filtros

        # Clientes
        tk.Label(frame_relat, text="Cliente:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.clientes_combobox = ttk.Combobox(frame_relat, values=self.clientes, state="readonly")
        self.clientes_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.clientes_combobox.set("Todos")

        # Setores
        tk.Label(frame_relat, text="Setor:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.setores_combobox = ttk.Combobox(frame_relat, values=self.setores, state="readonly")
        self.setores_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.setores_combobox.set("Todos")

        # Motivos
        tk.Label(frame_relat, text="Motivo:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.motivos_combobox = ttk.Combobox(frame_relat, values=self.motivos, state="readonly")
        self.motivos_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.motivos_combobox.set("Todos")

        # Botão Gerar Relatório
        ttk.Button(frame_relat, text="Gerar Relatório", command=self.gerar_relatorios).grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(frame_relat, text="Imprimir", command=self.imprimir_relatorio).grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(frame_relat, text="Salvar PDF", command=self.exportar_para_pdf).grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(frame_relat, text="Salvar Excel", command=self.exportar_para_excel).grid(row=6, column=0, columnspan=2, pady=10)

        
    def gerar_relatorios(self):
        conn = create_connection()
        cursor = conn.cursor()
        
        cliente = self.clientes_combobox.get()
        setor = self.setores_combobox.get()
        motivo = self.motivos_combobox.get()
        
        try:
            # Limpa os dados existentes na Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Base da consulta SQL
            query = "SELECT * FROM bo_records WHERE modulo LIKE ? AND D_E_L_E_T_ <> '*'"
            params = [self.ultimo_modulo]

            # Adiciona condições dinamicamente com base nos filtros
            if cliente != "Todos":
                query += " AND loja = ?"
                params.append(cliente)
            if setor != "Todos":
                query += " AND setor_responsavel = ?"
                params.append(setor)
            if motivo != "Todos":
                query += " AND motivo = ?"
                params.append(motivo)

            # Executa a consulta
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Insere os resultados na Treeview
            for row in rows:
                bo = str(row[1]).strip() if row[1] is not None else ""
                op = str(row[2]).strip() if row[2] is not None else ""
                cliente = str(row[3]).strip() if row[3] is not None else ""
                tipo_ocorrencia = str(row[5]).strip() if row[5] is not None else ""
                setor_responsavel = str(row[8]).strip() if row[8] is not None else ""
                motivo = str(row[6]).strip() if row[6] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, cliente, tipo_ocorrencia, setor_responsavel, motivo))
                
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
        self.ajustar_colunas()

    def exportar_para_pdf(self, file_path=None):
        if file_path is None:
            # Abre uma janela para salvar o arquivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if not file_path:
                return

        # Configurações do documento
        doc = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            leftMargin=1*cm,
            rightMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        elements = []

        # Estilo dos parágrafos
        styleSheet = getSampleStyleSheet()
        style = styleSheet['Normal']
        style.alignment = TA_LEFT
        style.fontSize = 10
        style.leading = 12

        # Obter dados da tabela
        headers = [self.tree.heading(col, "text") for col in self.tree["columns"]]
        data = [headers]
        
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            # Converter valores para parágrafos com quebra de linha
            formatted_values = []
            for value in values:
                # Limitar linha a 30 caracteres e quebrar texto
                wrapped_text = '\n'.join(wrap(str(value), 30))
                formatted_values.append(Paragraph(wrapped_text, style))
            data.append(formatted_values)

        # Criar tabela com larguras automáticas
        col_widths = [None] * len(headers)  # Larguras automáticas
        t = Table(data, colWidths=col_widths, repeatRows=1)

        # Estilo da tabela
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ])
        t.setStyle(style)

        elements.append(t)
        doc.build(elements)
        messagebox.showinfo("Sucesso", f"Relatório exportado para {file_path} com sucesso!")

    def exportar_para_excel(self, file_path=None):
        if file_path is None:
            # Abre uma janela para salvar o arquivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return
        
        try:
            # Extrai dados da Treeview
            headers = [self.tree.heading(col, "text") for col in self.tree["columns"]]
            data = []
            
            for item in self.tree.get_children():
                values = list(self.tree.item(item, "values"))
                formatted_values = []
                for value in values:
                    # Quebra texto em linhas de até 30 caracteres
                    wrapped_text = '\n'.join(wrap(str(value), 30))
                    formatted_values.append(wrapped_text)
                data.append(formatted_values)

            # Cria DataFrame e exporta para Excel
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(file_path, index=False)

            # Carrega workbook para formatação avançada
            wb = load_workbook(file_path)
            ws = wb.active

            # Formatação de células
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="C0C0C0", end_color="C0C0C0", fill_type="solid")
            row_fills = [PatternFill(start_color="FFFFFF", fill_type="solid"),
                        PatternFill(start_color="FFFFE0", fill_type="solid")]
            border = Border(left=Side(style='thin'),
                            right=Side(style='thin'),
                            top=Side(style='thin'),
                            bottom=Side(style='thin'))

            # Aplica formatação
            for row_idx, row in enumerate(ws.iter_rows(), start=1):
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(wrap_text=True, vertical='center')
                    
                    if row_idx == 1:  # Cabeçalho
                        cell.font = header_font
                        cell.fill = header_fill
                    else:  # Linhas alternadas
                        cell.fill = row_fills[(row_idx - 2) % 2]

            # Ajusta largura das colunas
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    if cell.value:
                        lines = str(cell.value).split('\n')
                        current_length = max(len(line) for line in lines)
                        if current_length > max_length:
                            max_length = current_length
                ws.column_dimensions[column].width = max_length + 2

            # Salva as alterações
            wb.save(file_path)
            messagebox.showinfo("Sucesso", f"Arquivo exportado para:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar:\n{str(e)}")

    def imprimir_relatorio(self):
        try:
            # Gera o PDF temporariamente
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            # Exporta para o PDF temporário usando a função existente
            self.exportar_para_pdf(temp_pdf.name)
            
            # Abre a janela de impressão
            if sys.platform == "win32":
                os.startfile(temp_pdf.name, "print")
            else:
                # Para macOS e Linux
                subprocess.run(["lp", temp_pdf.name])
            
            # Aguarda um breve período para garantir que a impressão tenha sido processada
            time.sleep(5)
            
            # Remove o arquivo temporário após a impressão
            if os.path.exists(temp_pdf.name):
                os.unlink(temp_pdf.name)
            messagebox.showinfo("Sucesso", "Relatório enviado para impressão!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir: {str(e)}")

    def cliente(self):
        conn = create_connection()
        cursor = conn.cursor()

        query = ("SELECT COALESCE(loja, 'Não especificado') AS Setor FROM bo_records WHERE loja IS NOT NULL AND loja NOT LIKE '' AND modulo LIKE ? GROUP BY loja")
        cursor.execute(query, (self.ultimo_modulo))
        cliente = ["Todos"] + [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return cliente
    
    def setor(self):
        conn = create_connection()
        cursor = conn.cursor()

        query = ("SELECT COALESCE(setor_responsavel, 'Não especificado') AS Setor FROM bo_records WHERE setor_responsavel IS NOT NULL AND setor_responsavel NOT LIKE '' AND modulo LIKE ? GROUP BY setor_responsavel")
        cursor.execute(query, (self.ultimo_modulo))
        setores = ["Todos"] + [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return setores

    def motivo(self):
        conn = create_connection()
        cursor = conn.cursor()

        query = ("SELECT COALESCE(motivo, 'Não especificado') AS Setor FROM bo_records WHERE motivo IS NOT NULL AND motivo NOT LIKE '' AND modulo LIKE ? GROUP BY motivo")
        cursor.execute(query, (self.ultimo_modulo))
        motivos = ["Todos"] + [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return motivos

    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de Relatórios chamada pelo módulo: {self.ultimo_modulo}"
    
class gerarBO():
    def __init__(self, parent, caller_id=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Solicitação de nova BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.focus_set()

        self.root.transient(parent)

        self.ultimo_modulo = caller_id
        print(self.identificar_chamador())

        campos = [
            ("cliente", "Cliente"),
            ("loja", "Loja"),
            ("n_de_bo", "Número de BO"),
            ("n_de_pedido", "Número de Pedido"),
            ("endereco", "Endereço"),
            ("invoice_inicial", "Invoice Inicial"),
            ("nf_de_fabrica", "NF de Fábrica"),
            ("data_emissao", "Data de Emissão"),
            ("nf_envio", "NF de Envio"),
        ]
        self.entries = {}

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text="Boletim de Ocorrência", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        for i, (campo, label) in enumerate(campos):
            ttk.Label(frame, text=label + ":").grid(row=i+1, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(frame, width=30, show="*" if campo == "password" else "")
            entry.grid(row=i+1, column=1, pady=5)
            self.entries[campo] = entry

        # row_btn = len(campos) + 2
        # ttk.Button(frame, text="Salvar", command=self.salvar).grid(row=row_btn, column=0, pady=15, sticky="ew")
        # ttk.Button(frame, text="Cancelar", command=self.cancelar).grid(row=row_btn, column=1, pady=15, sticky="ew")

        self.root.update_idletasks()
        largura = self.root.winfo_reqwidth()
        altura = self.root.winfo_reqheight()
        self.root.geometry(f"{largura}x{altura}")
        center_window_child(self.root, parent)

    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de Gerar BO chamada pelo módulo: {self.ultimo_modulo}"

class buscarBo(TreeViewHelper):
    def __init__(self, parent, caller_id=None, user=None):
        self.user = user
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Buscar BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.geometry("1000x600")
        self.root.state('zoomed')

        self.root.transient(parent)

        self.ultimo_modulo = caller_id

        # Cabeçalho
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(header, text="Fechar",
                   command=lambda: self.root.destroy()).pack(side=tk.RIGHT)

        # Barra de pesquisa
        self.search_bar = SearchBar(
            self.root, self.pesquisar_bo, self.clear_search)

        # Frame para Treeview e barra de rolagem
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        # lista de BOs Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("C5_PEDREPR", "C5_NUM", "C5_NOME",
                     "C5_FILIAL", "C5_EMISSAO", "C5_ENTREGA"),
            show="headings"
        )
        self.tree.heading("C5_PEDREPR", text="BO")
        self.tree.heading("C5_NUM", text="OP")
        self.tree.heading("C5_NOME", text="CLIENTE")
        self.tree.heading("C5_FILIAL", text="EMPRESA")
        self.tree.heading("C5_EMISSAO", text="EMISSÃO")
        self.tree.heading("C5_ENTREGA", text="PREVISÃO DE ENTREGA")

        # Barra de rolagem vertical
        v_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.configure(yscrollcommand=v_scrollbar.set)
        self.tree.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        self.tree.bind("<Double-1>", lambda event: exibir_detalhes(self.root,
                       self.tree, caller_id=self.ultimo_modulo, user=self.user))

        center_window(self)
        self.carregar_bos()
        self.search_bar.search_entry.bind('<Return>', self.pesquisar_bo)


    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de Buscar BO chamada pelo módulo: {self.ultimo_modulo}"

    def carregar_bos(self):
        conn = create_connection_Protheus()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT C5_PEDREPR, C5_NUM, C5_NOME, IIF(C5_FILIAL='0101','TIDELLI','NAUTICA') AS FILIAL, CONVERT(VARCHAR,CONVERT(DATETIME,C5_EMISSAO),103) as EMISSAO, CONVERT(VARCHAR,CONVERT(DATETIME,C5_ENTREGA),103) as PREVISAO_ENTREGA
                FROM SC5010 SC5
                WHERE SC5.D_E_L_E_T_ <> '*'
                        AND SC5.C5_NOTA = ''
                        AND PATINDEX('BO[0-9]%', SC5.C5_PEDREPR) > 0
                        AND C5_FILIAL IN ('0101','0201')
                ORDER BY C5_EMISSAO DESC
            """)
            rows = cursor.fetchall()

            # Remove todos os itens atuais da Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insere os dados na Treeview
            for row in rows:
                bo = str(row[0]).strip() if row[0] is not None else ""
                op = str(row[1]).strip() if row[1] is not None else ""
                cliente = str(row[2]).strip() if row[2] is not None else ""
                filial = str(row[3]).strip() if row[3] is not None else ""
                emissao = str(row[4]).strip() if row[4] is not None else ""
                previsao_entrega = str(
                    row[5]).strip() if row[5] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, cliente, filial, emissao, previsao_entrega))
                
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
        self.ajustar_colunas()

    def pesquisar_bo(self, event=None):
        termo = self.search_bar.search_entry.get()
        if not termo:
            return

        conn = create_connection_Protheus()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        try:
            cursor = conn.cursor()
            query = """
                SELECT C5_PEDREPR, C5_NUM, C5_NOME, IIF(C5_FILIAL='0101','TIDELLI','NAUTICA') AS FILIAL, CONVERT(VARCHAR,CONVERT(DATETIME,C5_EMISSAO),103) AS EMISSAO, CONVERT(VARCHAR,CONVERT(DATETIME,C5_ENTREGA),103) AS PREVISAO_ENTREGA
                FROM SC5010 SC5
                WHERE SC5.D_E_L_E_T_ <> '*'
                    AND SC5.C5_NOTA = ''
                    AND C5_PEDREPR LIKE 'BO%'  -- Garante que o campo começa com "BO"
                    AND (C5_PEDREPR LIKE 'BO%' + ?  -- Permite que o termo apareça após o "BO"
                        OR UPPER(C5_NUM) LIKE UPPER(?)
                        OR UPPER(C5_NOME) LIKE UPPER(?))
                    AND C5_FILIAL IN ('0101','0201')
                ORDER BY C5_EMISSAO DESC
                """

            cursor.execute(
                query, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))
            rows = cursor.fetchall()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                bo = str(row[0]).strip() if row[0] is not None else ""
                op = str(row[1]).strip() if row[1] is not None else ""
                cliente = str(row[2]).strip() if row[2] is not None else ""
                filial = str(row[3]).strip() if row[3] is not None else ""
                emissao = str(row[4]).strip() if row[4] is not None else ""
                previsao_entrega = str(
                    row[5]).strip() if row[5] is not None else ""

                self.tree.insert("", tk.END, values=(
                    bo, op, cliente, filial, emissao, previsao_entrega))
                
            self.ajustar_colunas()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar BOs: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def clear_search(self):
        self.search_bar.search_entry.delete(0, tk.END)
        self.search_bar.update_buttons()  # Atualiza os botões após limpar
        self.carregar_bos()  # Recarrega os BOs

    def update_buttons(self, event=None):
        termo = self.search_entry.get()
        if termo:
            self.search_button.pack_forget()  # Oculta o botão "Pesquisar"
            self.clear_button.pack(side=tk.LEFT)  # Exibe o botão "Limpar"
        else:
            self.clear_button.pack_forget()  # Oculta o botão "Limpar"
            self.search_button.pack(side=tk.LEFT)


class exibir_detalhes():
    instance = None

    def __init__(self, parent, tree, caller_id=None, user=None):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("Detalhes BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.grab_set()
        self.root.focus_set()

        self.root.transient(parent)
        self.root.grab_set()

        self.tree = tree
        self.ultimo_modulo = caller_id

        exibir_detalhes.instance = self

        # Verifica se a BO já existe no banco de dados
        self.bo_ja_acompanhada = self.verificar_bo_acompanhada()

        # Se já está sendo acompanhada, exibe aviso no topo
        if self.bo_ja_acompanhada:
            aviso_frame = ttk.Frame(self.root)
            aviso_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
            aviso_label = ttk.Label(
                aviso_frame,
                text="⚠️ Esta BO já está sendo acompanhada!",
                foreground="red",
                font=("Arial", 10, "bold")
            )
            aviso_label.pack(fill="x")

            detalhe_row = 1
        else:
            detalhe_row = 0

        self.sc5_detalhes(row=detalhe_row)
        self.itens_bo(row=detalhe_row + 1)
        self.opcoes_bo(row=detalhe_row + 2)

        self.root.update_idletasks()
        center_window_child(self.root, parent)

    def verificar_bo_acompanhada(self):
        item_selecionado = self.tree.selection()
        if not item_selecionado:
            return False
        valores = self.tree.item(item_selecionado, "values")
        if not valores or not valores[0]:
            return False
        bo_number = valores[0]
        conn = create_connection()
        if conn is None:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM bo_records WHERE bo_number = ? AND D_E_L_E_T_ <> '*'", (bo_number,))
            exists = cursor.fetchone()
            return exists is not None
        except Exception:
            return False
        finally:
            if conn:
                cursor.close()
                conn.close()

    def sc5_detalhes(self, row=0):
        self.root.grid_rowconfigure(row, weight=3)
        self.root.grid_columnconfigure(0, weight=1)

        frame_sc5Detalhes = ttk.LabelFrame(
            self.root, text="Detalhes da Ocorrência", padding=10)
        frame_sc5Detalhes.grid(
            row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_sc5Detalhes.grid_rowconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(1, weight=2)

        # Obtém o item selecionado no Treeview
        item_selecionado = self.tree.selection()
        if not item_selecionado:
            return

        # Obtém os valores do item selecionado
        valores = self.tree.item(item_selecionado, "values")

        # Criando as labels
        labels = ["BO:", "OP:", "CLIENTE:", "FILIAL:",
                  "EMISSÃO:", "PREVISÃO DE ENTREGA:"]
        for i, label_text in enumerate(labels):
            ttk.Label(frame_sc5Detalhes, text=label_text).grid(
                row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(frame_sc5Detalhes, text=valores[i]).grid(
                row=i, column=1, sticky="ew", padx=5, pady=2)

        self.root.update_idletasks()
        self.root.minsize(400, self.root.winfo_height())

    def itens_bo(self, row=1):
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_itensBo = ttk.LabelFrame(
            self.root, text="Itens da BO", padding=10)
        frame_itensBo.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_itensBo.grid_rowconfigure(0, weight=1)
        for i in range(3):
            frame_itensBo.grid_columnconfigure(i, weight=1)

        labels = ["CÓDIGO", "DESCRIÇÃO", "LINHA"]

        item_selecionado2 = self.tree.selection()
        if not item_selecionado2:
            return

        valores2 = self.tree.item(item_selecionado2, "values")

        conn = create_connection_Protheus()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        cursor = conn.cursor()

        query = """SELECT SC6.C6_CODTIDI, SC6.C6_DESCRI, SC6.C6_LINHA
        FROM SC6010 SC6
        INNER JOIN SC5010 SC5 ON (SC5.C5_NUM = SC6.C6_NUM AND SC5.C5_FILIAL = SC6.C6_FILIAL AND SC5.D_E_L_E_T_ <> '*')
        WHERE SC6.C6_NUM LIKE ? AND SC5.C5_PEDREPR LIKE ? AND SC5.C5_PEDREPR LIKE ?"""

        try:
            cursor.execute(
                query, (f"%{valores2[1]}%", "%BO%", f"%{valores2[0]}%"))
            itens_bo = cursor.fetchall()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao executar a consulta: {e}")
            return
        finally:
            cursor.close()
            conn.close()

        for i, label_txt in enumerate(labels):
            label = ttk.Label(frame_itensBo, text=label_txt)
            label.grid(row=0, column=i, sticky="w", padx=5, pady=2)
            frame_itensBo.grid_columnconfigure(i, weight=1)

        for idx, item in enumerate(itens_bo):
            for col, value in enumerate(item):
                label = ttk.Label(frame_itensBo, text=value)
                label.grid(row=idx + 1, column=col, sticky="w", padx=5, pady=2)
                frame_itensBo.grid_columnconfigure(col, weight=1)

        self.root.update_idletasks()
        self.root.geometry("")

    def opcoes_bo(self, row=2):
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_opcoesBo = ttk.LabelFrame(
            self.root, text="Opções", padding=10)
        frame_opcoesBo.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_opcoesBo.grid_rowconfigure(0, weight=1)
        frame_opcoesBo.grid_columnconfigure(2, weight=1)

        ttk.Button(frame_opcoesBo, text="Acompanhar BO", command=self.acompanhar_bo).grid(
            row=0, column=0, sticky="e", padx=5, pady=2)

    def acompanhar_bo(self):
        obj = acompanhar_Bo(self.root, self.tree,
                            caller_id=self.ultimo_modulo, user=self.user)
        resultado = obj.identificar_chamador()
        print(resultado)

class exibir_detalhes_acompanhando():
    instance = None

    def __init__(self, parent, tree, caller_id=None, user=None):
        self.parent = parent
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("Detalhes BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.grab_set()
        self.root.focus_set()

        self.root.transient(parent)
        self.root.grab_set()

        self.tree = tree
        self.ultimo_modulo = caller_id

        exibir_detalhes_acompanhando.instance = self

        self.sc5_detalhes()
        self.itens_bo()
        self.opcoes_bo()

        self.root.update_idletasks()
        center_window_child(self.root, parent)

    def sc5_detalhes(self):
        self.root.grid_rowconfigure(0, weight=3)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_sc5Detalhes = ttk.LabelFrame(
            self.root, text="Detalhes da Ocorrência", padding=10)
        frame_sc5Detalhes.grid(
            row=0, column=0, sticky="nsew", padx=10, pady=10)

        frame_sc5Detalhes.grid_rowconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(1, weight=2)

        # Obtém o item selecionado no Treeview
        item_selecionado = self.tree.selection()
        if not item_selecionado:
            return

        # Obtém os valores do item selecionado
        valores = self.tree.item(item_selecionado, "values")

        conn = create_connection()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        cursor = conn.cursor()

        query = """SELECT bo_number, op, loja, tipo_ocorrencia, motivo, CONVERT(VARCHAR,CONVERT(DATETIME,previsao_embarque),103), descricao, frete, [status]
        FROM bo_records
        WHERE bo_number LIKE ?"""

        try:
            cursor.execute(
                query, (f"%{valores[0]}%"))
            itens_bo = cursor.fetchall()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao executar a consulta: {e}")
            return
        finally:
            cursor.close()
            conn.close()

        # Criando as labels
        labels = ["BO:", "OP:", "CLIENTE:", "TIPO DE OCORRÊNCIA:",
                  "MOTIVO:", "PREVISÃO DE EMBARQUE:", "DESCRIÇÃO:", "FRETE", "STATUS:"]
        if itens_bo:
            for i, label_text in enumerate(labels):
                ttk.Label(frame_sc5Detalhes, text=label_text).grid(
                    row=i, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(frame_sc5Detalhes, text=itens_bo[0][i]).grid(
                    row=i, column=1, sticky="ew", padx=5, pady=2)
        else:
            messagebox.showinfo("Aviso", "Nenhum detalhe encontrado para este BO.")

        self.root.update_idletasks()
        self.root.minsize(400, self.root.winfo_height())

    def itens_bo(self):
        self.root.grid_rowconfigure(0, weight=3)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_itensBo = ttk.LabelFrame(
            self.root, text="Itens da BO", padding=10)
        frame_itensBo.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        frame_itensBo.grid_rowconfigure(0, weight=1)
        for i in range(3):
            frame_itensBo.grid_columnconfigure(i, weight=1)

        labels = ["CÓDIGO", "DESCRIÇÃO", "LINHA"]

        item_selecionado2 = self.tree.selection()
        if not item_selecionado2:
            return

        valores2 = self.tree.item(item_selecionado2, "values")

        conn = create_connection_Protheus()
        if conn is None:
            messagebox.showerror("Erro", "Falha ao conectar ao banco de dados")
            return

        cursor = conn.cursor()

        query = """SELECT SC6.C6_CODTIDI, SC6.C6_DESCRI, SC6.C6_LINHA
        FROM SC6010 SC6
        INNER JOIN SC5010 SC5 ON (SC5.C5_NUM = SC6.C6_NUM AND SC5.C5_FILIAL = SC6.C6_FILIAL AND SC5.D_E_L_E_T_ <> '*')
        WHERE SC6.C6_NUM LIKE ? AND SC5.C5_PEDREPR LIKE ? AND SC5.C5_PEDREPR LIKE ?"""

        try:
            cursor.execute(
                query, (f"%{valores2[1]}%", "%BO%", f"%{valores2[0]}%"))
            itens_bo = cursor.fetchall()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao executar a consulta: {e}")
            return
        finally:
            cursor.close()
            conn.close()

        for i, label_txt in enumerate(labels):
            label = ttk.Label(frame_itensBo, text=label_txt)
            label.grid(row=0, column=i, sticky="w", padx=5, pady=2)
            frame_itensBo.grid_columnconfigure(i, weight=1)

        for idx, item in enumerate(itens_bo):
            for col, value in enumerate(item):
                label = ttk.Label(frame_itensBo, text=value)
                label.grid(row=idx + 1, column=col, sticky="w", padx=5, pady=2)
                frame_itensBo.grid_columnconfigure(col, weight=1)

        self.root.update_idletasks()
        self.root.geometry("")

    def opcoes_bo(self, row=2):
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_opcoesBo = ttk.LabelFrame(
            self.root, text="Opções", padding=10)
        frame_opcoesBo.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_opcoesBo.grid_rowconfigure(0, weight=1)
        frame_opcoesBo.grid_columnconfigure(2, weight=1)

        ttk.Button(frame_opcoesBo, text="Editar BO", command=self.editar_bo).grid(
            row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Button(frame_opcoesBo, text="Excluir BO", command=self.excluir_bo).grid(
            row=0, column=1, sticky="e", padx=5, pady=2)

    def editar_bo(self):
        self.root.withdraw()
        editor = editar_Bo(self.parent, self.tree, caller_id=self.ultimo_modulo, user=self.user)
        self.root.wait_window(editor.root)
        try:
            self.root.deiconify()
        except tk.TclError:
            pass
        

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

class editar_Bo():
    def __init__(self, parent, tree, caller_id=None, user=None):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("Editar BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.transient(parent)
        self.root.grab_set()
        self.root.focus_set()

        self.ultimo_modulo = caller_id

        item_selecionado = tree.selection()
        if not item_selecionado:
            messagebox.showwarning("Aviso", "Nenhum item selecionado.")
            return
        
        valores = tree.item(item_selecionado, "values")
        self.bo_number = valores[0]

        print(f"Usuário {self.user[1]} solicitou a edição da {self.bo_number} no módulo {self.ultimo_modulo}.")

        tk.Label(self.root, text=f"Editando BO: {self.bo_number}").pack(pady=10)
        self.entries = {}

        campos = [
            ("tipo_ocorrencia", "Tipo de Ocorrência"),
            ("motivo", "Motivo"),
            ("descricao", "Descrição"),
            ("setor_responsavel", "Setor Responsável"),
            ("frete", "Frete"),
            ]
        
        frame_editaveis = ttk.Frame(self.root, padding=20)
        frame_editaveis.pack(expand=True, fill=tk.BOTH)

        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bo_records WHERE bo_number = ?", (self.bo_number,))
            self.valores = cursor.fetchone()
            if self.valores is None:
                messagebox.showerror("Erro", f"BO {self.bo_number} não encontrada.")
                self.root.destroy()
                return
            cursor.close()
            conn.close()
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
            self.root.destroy()
            return

        # print(f"Valores obtidos do banco: {self.valores}")

        for i, (campo, label_text) in enumerate(campos):
            ttk.Label(frame_editaveis, text=label_text + ":").grid(
                row=i, column=0, sticky=tk.W, pady=5)
            if campo == "frete":
                entry = ttk.Combobox(frame_editaveis, values=["CIF", "FOB"], state="readonly")
            elif campo == "motivo":
                entry = ttk.Combobox(frame_editaveis, values=self.obter_motivos())
            elif campo == "setor_responsavel":
                entry = ttk.Combobox(frame_editaveis, values=self.obter_setores())
            elif campo == "descricao":
                entry = tk.Text(frame_editaveis, width=30, height=5, font=("Arial", 8))
            else:
                entry = ttk.Entry(frame_editaveis, width=30)
            valor_idx = {
                "tipo_ocorrencia": 5,
                "motivo": 6,
                "descricao": 11,
                "setor_responsavel": 8,
                "frete": 7
            }
            idx = valor_idx.get(campo)
            if idx is not None and self.valores and len(self.valores) > idx:
                if campo == "frete":
                    entry.set(self.valores[idx])
                elif campo == "descricao":
                    entry.insert("1.0", self.valores[idx])
                elif campo == "motivo":
                    entry.insert(0, self.valores[idx])
                elif campo == "setor_responsavel":
                    entry.insert(0, self.valores[idx])
                else:
                    entry.insert(0, self.valores[idx])
            entry.grid(row=i, column=1, pady=5, sticky="ew")
            self.entries[campo] = entry

        ttk.Button(frame_editaveis, text="Salvar", command=self.salvar).grid(
            row=len(campos), column=0, pady=15, sticky="ew")
        ttk.Button(frame_editaveis, text="Cancelar", command=self.cancel).grid(
            row=len(campos), column=1, pady=15, sticky="ew")

        self.root.update_idletasks()

        center_window_child(self.root, parent)

    def obter_setores(self):
        conn = create_connection()
        cursor = conn.cursor()
    
        cursor.execute("SELECT DISTINCT setor_responsavel FROM bo_records WHERE setor_responsavel IS NOT NULL AND setor_responsavel NOT LIKE ''")
        setores = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return setores
        
    def obter_motivos(self):
        conn = create_connection()
        cursor = conn.cursor()
    
        cursor.execute("SELECT DISTINCT motivo FROM bo_records WHERE motivo IS NOT NULL AND motivo NOT LIKE ''")
        motivos = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return motivos

    def salvar(self):
        try:
            conn = create_connection()
            cursor = conn.cursor()

            update_query = """
                UPDATE bo_records
                SET tipo_ocorrencia = ?, motivo = ?, descricao = ?, setor_responsavel = ?, frete = ?
                WHERE bo_number = ?
            """
            cursor.execute(update_query, (
                self.entries["tipo_ocorrencia"].get(),
                self.entries["motivo"].get(),
                self.entries["descricao"].get("1.0", tk.END),
                self.entries["setor_responsavel"].get(),
                self.entries["frete"].get(),
                self.bo_number
            ))

            conn.commit()
            messagebox.showinfo("Sucesso", f"BO {self.bo_number} atualizada com sucesso!")
            self.root.destroy()
            exibir_detalhes_acompanhando.instance.root.destroy()

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

        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar BO: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def cancel(self):
        self.root.destroy()
        
class acompanhar_Bo:
    def __init__(self, parent, tree, caller_id=None, user=None):
        self.user = user
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Acompanhar BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        
        self.root.transient(parent)
        center_window_child(self.root, parent)
        self.root.grab_set()
        self.root.focus_set()

        self.tree = tree
        self.ultimo_modulo = caller_id
        self.anexos = []
        self.loading_label = None
        self.max_anexos = 5
        self.max_tamanho_anexo = 50 * 1024 * 1024

        self.bo_dados = self.obter_dados_bo()
        self.secao_dados_gerais()
        self.secao_ocorrencia()
        self.secao_transporte()
        # self.secao_anexo()
        self.botao_salvar()

        self.ajustar_tamanho_janela()

    def ajustar_tamanho_janela(self):
        self.root.update_idletasks()

        largura = self.root.winfo_reqwidth()
        altura = self.root.winfo_reqheight()

        self.root.geometry(f"{largura}x{altura}")

        center_window(self)

    def secao_dados_gerais(self):
        """Cria a seção de dados gerais da BO."""
        frame_dados_gerais = ttk.LabelFrame(
            self.root, text="Dados Gerais", padding=10)
        frame_dados_gerais.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # BO e OP
        ttk.Label(frame_dados_gerais, text="BO:").grid(
            row=0, column=0, sticky=tk.W)
        ttk.Label(frame_dados_gerais, text=self.bo_dados[0]).grid(
            row=0, column=1, sticky=tk.W)
        ttk.Label(frame_dados_gerais, text="OP:").grid(
            row=1, column=0, sticky=tk.W)
        ttk.Label(frame_dados_gerais, text=self.bo_dados[1]).grid(
            row=1, column=1, sticky=tk.W)

        # Cliente
        ttk.Label(frame_dados_gerais, text="CLIENTE:").grid(
            row=2, column=0, sticky=tk.W)
        ttk.Label(frame_dados_gerais, text=self.bo_dados[2]).grid(
            row=2, column=1, sticky=tk.W)
        
        # Data de Emissão
        ttk.Label(frame_dados_gerais, text="EMISSÃO:").grid(
            row=3, column=0, sticky=tk.W)
        ttk.Label(frame_dados_gerais, text=self.bo_dados[4]).grid(
            row=3, column=1, sticky=tk.W)
        
    def obter_setores(self):
        conn = create_connection()
        cursor = conn.cursor()
    
        cursor.execute("SELECT DISTINCT setor_responsavel FROM bo_records WHERE setor_responsavel IS NOT NULL")
        setores = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return setores
        
    def obter_motivos(self):
        conn = create_connection()
        cursor = conn.cursor()
    
        cursor.execute("SELECT DISTINCT motivo FROM bo_records WHERE motivo IS NOT NULL")
        motivos = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return motivos

    def secao_ocorrencia(self):
        # Cria a seção de detalhes da ocorrência.
        frame_ocorrencia = ttk.LabelFrame(
            self.root, text="Detalhes da Ocorrência", padding=10)
        frame_ocorrencia.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        

        campos_ocorrencia = [
            ("Tipo de Ocorrência", ttk.Entry),
            ("Motivo", ttk.Combobox, self.obter_motivos()),
            ("Setor Responsável", ttk.Combobox, self.obter_setores()),
            ("Descrição", tk.Text, 1, 5),
        ]

        self.entries_ocorrencia = {}
        for i, (campo, widget, *args) in enumerate(campos_ocorrencia):
            ttk.Label(frame_ocorrencia, text=f"{campo}:").grid(
                row=i, column=0, sticky=tk.W)
            if widget == ttk.Combobox:
                entry = widget(frame_ocorrencia, values=args[0])
            else:
                entry = widget(frame_ocorrencia)
            entry.grid(row=i, column=1, sticky="ew")
            self.entries_ocorrencia[campo] = entry

    def secao_transporte(self):
        """Cria a seção de detalhes do transporte."""
        frame_transporte = ttk.LabelFrame(
            self.root, text="Transporte", padding=10)
        frame_transporte.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        ttk.Label(frame_transporte, text="Previsão de entrega:").grid(
            row=0, column=0, sticky=tk.W)
        ttk.Label(frame_transporte, text=self.bo_dados[5]).grid(
            row=0, column=1, sticky=tk.W)

        campos_transporte = [
            ("Frete", ttk.Combobox, ["CIF", "FOB"])
        ]

        self.entries_transporte = {}
        for i, (campo, widget, *args) in enumerate(campos_transporte, start=1):
            ttk.Label(frame_transporte, text=f"{campo}:").grid(
                row=i, column=0, sticky=tk.W)
            if widget == ttk.Combobox:
                entry = widget(frame_transporte, values=args[0], state="readonly")
            else:
                entry = widget(frame_transporte)
            entry.grid(row=i, column=1, sticky="ew")
            self.entries_transporte[campo] = entry

    def secao_anexo(self):
        """Cria a seção de anexos."""
        frame_anexo = ttk.LabelFrame(
            self.root, text="Documentos", padding=10)
        frame_anexo.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        self.anexo_container = ttk.Frame(frame_anexo)
        self.anexo_container.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.anexo_button = ttk.Button(
            frame_anexo, text="Anexar Arquivos", command=self.anexar_arquivo)
        self.anexo_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    def anexar_arquivo(self):
        file_paths = filedialog.askopenfilenames(filetypes=[
            ("Compatível", "*.jpg;*.jpeg;*.png;*.mp4;*.avi"), ("Todos os Arquivos", "*.*")])

        total_size = sum(os.path.getsize(path) for path in self.anexos)
        for file_path in file_paths:
            total_size += os.path.getsize(file_path)
            if total_size > self.max_tamanho_anexo:
                messagebox.showerror(
                    "Erro", "Você excedeu o limite de 50MB total de anexo.")
                return

        if len(self.anexos) + len(file_paths) > self.max_anexos:
            messagebox.showerror(
                "Erro", f"Você não pode anexar mais do que {self.max_anexos} arquivos.")
            return

        self.mostrar_texto_carregamento()
        threading.Thread(target=self.processar_anexos,
                         args=(file_paths,)).start()

    def mostrar_texto_carregamento(self):
        # Remover o frame de carregamento, se já existir
        for widget in self.anexo_container.winfo_children():
            widget.destroy()

        # Criar um widget para o texto de carregamento
        self.loading_widget = ttk.Label(
            self.anexo_container, text="Carregando anexo...", font=("Arial", 11))
        self.loading_widget.grid(row=0, column=0, padx=5, pady=5)
        print("Texto de carregamento sendo exibido")

    def processar_anexos(self, file_paths):
        for file_path in file_paths:
            time.sleep(2)  # Simula o tempo de processamento
            self.anexos.append(file_path)

        self.parent.after(100, self.finalizar_carregamento)

    def finalizar_carregamento(self):
        if self.loading_widget and self.loading_widget.winfo_exists():
            self.loading_widget.destroy()
        self.atualizar_anexo_exibicao()
        print("Texto de carregamento sendo removido")

    def atualizar_anexo_exibicao(self):
        """Atualiza a exibição dos anexos."""
        for widget in self.anexo_container.winfo_children():
            widget.destroy()

        if self.anexos:
            for i, file_path in enumerate(self.anexos):
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.exibir_imagem(file_path, i)
                elif file_path.lower().endswith(('.mp4', '.avi')):
                    self.exibir_video(file_path, i)
        else:
            label = ttk.Label(self.anexo_container,
                              text="Nenhum Arquivo Anexado.")

            label.pack()

    def exibir_imagem(self, file_patch, index):
        img = Image.open(file_patch)
        img.thumbnail((100, 100))
        img = ImageTk.PhotoImage(img)

        label = ttk.Label(self.anexo_container, image=img)
        label.image = img
        label.grid(row=index * 2, column=0, padx=5, pady=5)

        self.lixeira_icone = ImageTk.PhotoImage(
            Image.open("./images/lixeira.png").resize((20, 20)))
        remove_button = ttk.Button(self.anexo_container, image=self.lixeira_icone,
                                   command=lambda img=file_patch: self.remover_imagem(img))
        remove_button.image = self.lixeira_icone
        remove_button.grid(row=index * 2, column=1, padx=5, pady=5)

    def remover_imagem(self, file_path):
        """Remove a imagem e o botão de remoção do container."""
        if file_path in self.anexos:
            self.anexos.remove(file_path)
            self.atualizar_anexo_exibicao()
            print(f"Arquivo removido: {file_path}")
        else:
            print("Arquivo não encontrado na lista de anexos.")

    def exibir_video(self, file_path, index):
        try:
            clip = VideoFileClip(file_path)
            frame = clip.get_frame(0)  # Pega o primeiro frame do vídeo
            clip.close()

            # Converta o frame para um formato exibível
            img = Image.fromarray(frame)
            img.thumbnail((100, 100))
            img = ImageTk.PhotoImage(img)

            # Crie um rótulo para exibir a miniatura
            label = ttk.Label(self.anexo_container, image=img)
            label.image = img
            label.grid(row=index * 2, column=0, padx=5, pady=5)

            # Adicione o botão de remoção
            self.lixeira_icone = ImageTk.PhotoImage(
                Image.open("./images/lixeira.png").resize((20, 20)))
            remove_button = ttk.Button(self.anexo_container, image=self.lixeira_icone,
                                       command=lambda img=file_path: self.remover_imagem(img))
            remove_button.image = self.lixeira_icone
            remove_button.grid(row=index * 2, column=1, padx=5, pady=5)

        except Exception as e:
            print(f"Erro ao exibir vídeo: {e}")
            label = ttk.Label(self.anexo_container,
                              text="Vídeo não pode ser exibido.")
            label.grid(row=index * 2, column=0, padx=5, pady=5)

    def fechar_janela_video(self, window, player):
        player.stop()  # Pare o vídeo
        window.destroy()  # Destrua a janela

    def botao_salvar(self):
        """Cria o botão de salvar."""
        frame_botoes = ttk.Frame(self.root, padding=10)
        frame_botoes.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        ttk.Button(frame_botoes, text="Salvar",
                   command=self.salvar).pack(side=tk.RIGHT)

    def motivos(self):
        """Retorna uma lista de motivos."""
        return [
            "Pé quebrado",
            "Tela rasgada",
            "Outro"
        ]

    def identificar_chamador(self):
        if self.ultimo_modulo is None:
            raise ValueError(
                "É necessário informar o identificador do módulo que chamou a função")
        return f"Tela de acompanhar BO chamada pelo módulo: {self.ultimo_modulo}"

    def obter_dados_bo(self):
        """Obtém os dados da BO selecionada na Treeview."""
        selecionado = self.tree.selection()
        if not selecionado:
            return None

        valores = self.tree.item(selecionado, "values")
        if valores:
            return valores
        return None

    def salvar(self):
        # Salva a BO no banco e só então incrementa o número da sequência.
        conn = create_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()

            # Coleta os valores dos campos
            valores = [
                self.bo_dados[0],  # BO
                self.bo_dados[1],  # OP
                self.bo_dados[2],  # Cliente
                self.bo_dados[3],  # Filial
                self.bo_dados[4],  # Emissão
                # Tipo de Ocorrência
                self.entries_ocorrencia["Tipo de Ocorrência"].get(),
                self.entries_ocorrencia["Motivo"].get(),  # Motivo
                self.entries_ocorrencia["Descrição"].get(),  # Descrição
                self.entries_ocorrencia["Setor Responsável"].get(),  # Descrição
                self.entries_transporte["Frete"].get(),  # Frete
                self.bo_dados[5],  # Previsão de Embarque
                self.ultimo_modulo,  # Módulo que chamou a função
                'Em Andamento',  # Status
                self.user[1]  # Usuário que incluiu
            ]

            # Primeiro, verifica se o BO já existe
            cursor.execute(
                "SELECT 1 FROM bo_records WHERE bo_number = ? AND D_E_L_E_T_ <> '*'", (self.bo_dados[0],))
            exists = cursor.fetchone()

            if not exists:
                # Agora, insere os dados
                cursor.execute('''
                    INSERT INTO bo_records (
                        bo_number, op, loja, filial, emissao_totvs, tipo_ocorrencia, motivo, descricao, setor_responsavel,
                        frete, previsao_embarque, modulo, status, user_include
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', valores)
                conn.commit()
            else:
                messagebox.showerror("Erro", "BO já cadastrada!")
                self.root.destroy()
                exibir_detalhes.instance.root.destroy()
                return

            messagebox.showinfo("Sucesso", "BO salva com sucesso!")
            exibir_detalhes.instance.root.destroy()

            # Atualiza a lista de BOs no módulo que chamou
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

            self.root.destroy()

        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao salvar BO: {e}")
            print(e)
        finally:
            if conn:
                cursor.close()
                conn.close()