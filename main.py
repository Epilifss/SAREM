import tkinter as tk
import ttkbootstrap as tb
import os
import sys
import atexit
import psutil
import tempfile
from theme import temas

root = tb.Window()
temas()

root.overrideredirect(True)
root.geometry('0x0+0+0')

def mostrar_splash(root):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x200")
    splash.configure(bg="white")
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - 200
    y = (splash.winfo_screenheight() // 2) - 100
    splash.geometry(f"+{x}+{y}")
    try:
        from PIL import Image, ImageTk
        from funcoes import resource_path
        img = Image.open(resource_path('SAREM PNG.png'))
        img = img.resize((300, 100), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label_img = tk.Label(splash, image=photo, bg="white")
        label_img.image = photo
        label_img.pack(pady=(30, 10))
    except Exception:
        tk.Label(splash, text="SAREM", font=("Arial", 24), bg="white").pack(pady=(60, 10))
    tk.Label(splash, text="Powered by Epilifss", font=("Arial", 12), bg="white").pack()
    return splash

splash = mostrar_splash(root)
root.update()

# from funcoes import *
from front.windows.login_window import LoginWindow
from back.update_service import verificar_e_att
from back.database import garantir_config_ini

LOCKFILE = os.path.join(tempfile.gettempdir(), 'sarem_app.lock')

def check_single_instance():
    if os.path.exists(LOCKFILE):
        try:
            with open(LOCKFILE, 'r') as f:
                pid = int(f.read())
            # Verifica se o processo ainda existe
            if psutil.pid_exists(pid):
                from tkinter import messagebox, Tk
                root = Tk()
                root.withdraw()
                messagebox.showerror("SAREM", "O sistema já está aberto!\nFeche a outra janela antes de abrir novamente.")
                sys.exit(0)
            else:
                # Processo não existe mais, remove lockfile órfão
                os.remove(LOCKFILE)
        except Exception:
            os.remove(LOCKFILE)
    with open(LOCKFILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_lockfile():
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
    except Exception:
        pass

check_single_instance()
atexit.register(remove_lockfile)

garantir_config_ini()

root.after(2000, splash.destroy)
root.after(2050, lambda: iniciar_app(root))

def iniciar_app(root):
    deve_continuar = verificar_e_att(root)
    if deve_continuar:
        login_window = LoginWindow(root)
        root.after(100, login_window.root.focus_force)
        root.after(100, login_window.username.focus_force)
        root.mainloop()

root.mainloop()