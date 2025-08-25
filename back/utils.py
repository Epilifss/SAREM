import sys
import os
import tkinter as tk

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def get_config_path():
    appdata = os.environ.get('APPDATA') or os.path.expanduser('~')
    config_dir = os.path.join(appdata, 'SAREM')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.ini')

def ajustar_tamanho_janela(self, ideal_width, px):
    self.geometry(f"{ideal_width}x{px}")

def center_window(window_obj: tk.Toplevel):
    window_obj.update_idletasks()

    width = window_obj.winfo_width()
    height = window_obj.winfo_height()

    screen_width = window_obj.winfo_screenwidth()
    screen_height = window_obj.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    window_obj.geometry(f'{width}x{height}+{x}+{y}')

def center_window_screen(win, width=350, height=100):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")