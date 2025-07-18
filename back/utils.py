import sys
import os
import threading
import time
import datetime
import requests
import tempfile
import subprocess
import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from back.database import create_connection, create_connection_Protheus

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_path():
    appdata = os.environ.get('APPDATA') or os.path.expanduser('~')
    config_dir = os.path.join(appdata, 'SAREM')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.ini')

# Exemplo de como center_window deve ser em back/utils.py
import tkinter as tk

def center_window(window_obj: tk.Toplevel):
    window_obj.update_idletasks()

    # Obtém as dimensões da janela
    width = window_obj.winfo_width()
    height = window_obj.winfo_height()

    # Obtém as dimensões da tela
    screen_width = window_obj.winfo_screenwidth()
    screen_height = window_obj.winfo_screenheight()

    # Calcula as coordenadas X e Y para centralizar
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Define a geometria da janela
    window_obj.geometry(f'{width}x{height}+{x}+{y}')

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

VERSAO_ATUAL = "1.0.3"
URL_VERSAO = "https://dl.dropboxusercontent.com/scl/fi/dh936k1ph0m2eq5low9gn/versao.txt?rlkey=fnyxw89yee7ai571ue3znbaiv&st=xd9f26ij&dl=0"
URL_LINK_TXT = "https://dl.dropboxusercontent.com/scl/fi/9hu4p9wo6ydqiit7zfp1b/linknovaversao.txt?rlkey=yubwve92t8qpr2bxd13lsvqij&st=vs0ddwfv&dl=0"

def get_download_url():
    try:
        resposta = requests.get(URL_LINK_TXT, timeout=5)
        if resposta.status_code == 200:
            return resposta.text.strip()
    except Exception as e:
        print("Erro ao obter link do instalador:", e)
    return None

def center_window_screen(win, width=350, height=100):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

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

                url_download = get_download_url()
                if not url_download:
                    messagebox.showerror("Erro", "Não foi possível obter o link do instalador.")
                    return True

                # Janela de progresso
                progress_win = tk.Toplevel(parent)
                progress_win.title("Baixando atualização")
                progress_win.iconbitmap(resource_path('SAREM.ico'))
                progress_win.geometry("350x100")
                progress_win.transient(parent)
                progress_win.grab_set()
                tb.Label(progress_win, text="Baixando nova versão...").pack(pady=10)
                progress = tb.Progressbar(progress_win, orient="horizontal", length=300, mode="determinate")
                progress.pack(pady=10)
                progress["value"] = 0

                center_window_screen(progress_win, 350, 100)

                temp_dir = tempfile.gettempdir()
                caminho_instalador = os.path.join(temp_dir, "atualizacao.exe")
                r = requests.get(url_download, stream=True)
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

monitorar_bo_event = threading.Event()

def monitorar_bo_embarcadas():
    def tarefa():
        while not monitorar_bo_event.is_set():
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
                        messagebox.showinfo("BO Liberada para Embarque", f"A {bo_number} foi liberada para embarque.")
                        print(f"BO {bo_number} marcada como Embarcada.")

                        try:
                            from modulos.corporativo import CorporativoModule
                            if hasattr(CorporativoModule, "instance") and CorporativoModule.instance is not None:
                                CorporativoModule.instance.atualizar_bos()
                        except Exception:
                            pass
                        try:
                            from modulos.varejo import VarejoModule
                            if hasattr(VarejoModule, "instance") and VarejoModule.instance is not None:
                                VarejoModule.instance.atualizar_bos()
                        except Exception:
                            pass
                        try:
                            from modulos.exportacao import ExportacaoModule
                            if hasattr(ExportacaoModule, "instance") and ExportacaoModule.instance is not None:
                                ExportacaoModule.instance.atualizar_bos()
                        except Exception:
                            pass

                cursor.close()
                conn.close()
                conn_Protheus.close()
            except Exception as e:
                print(f"Erro ao monitorar BOs embarcadas: {e}")
            if monitorar_bo_event.wait(60):
                print("Monitoramento de BOs embarcadas interrompido.")
                break

    monitorar_bo_event.clear()
    threading.Thread(target=tarefa, daemon=True).start()