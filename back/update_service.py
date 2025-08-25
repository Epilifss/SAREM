import requests
import tempfile
import subprocess
import os
import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from back.utils import resource_path, center_window_screen
from front import versao

VERSAO_ATUAL = versao
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

def verificar_e_att(parent):
    try:
        resposta = requests.get(URL_VERSAO, timeout=5)
        if resposta.status_code == 200:
            versao_remota = resposta.text.strip()
            if versao_remota > VERSAO_ATUAL:
                resp = messagebox.askyesno(
                    "SAREM - Atualização disponível",
                    f"Uma nova versão está disponível.\\nDeseja atualizar agora?"
                )
                if not resp:
                    return True

                url_download = get_download_url()
                if not url_download:
                    messagebox.showerror("Erro", "Não foi possível obter o link do instalador.")
                    return True

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
                                messagebox.showerror("Erro", f"Não foi possível abrir o instalador:\\n{e}")
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
