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


def limitar_janela_tela(window_obj: tk.Toplevel, width_ratio: float = 0.9, height_ratio: float = 0.9):
    window_obj.update_idletasks()

    screen_width = window_obj.winfo_screenwidth()
    screen_height = window_obj.winfo_screenheight()
    max_w = max(320, int(screen_width * width_ratio))
    max_h = max(240, int(screen_height * height_ratio))

    current_w = window_obj.winfo_width()
    current_h = window_obj.winfo_height()
    final_w = min(current_w, max_w)
    final_h = min(current_h, max_h)

    window_obj.maxsize(max_w, max_h)
    window_obj.geometry(f"{final_w}x{final_h}")


def wraplength_responsivo(window_obj: tk.Toplevel, fraction: float = 0.45, min_px: int = 180, max_px: int = 700) -> int:
    window_obj.update_idletasks()
    largura = window_obj.winfo_width() or window_obj.winfo_screenwidth()
    calculado = int(largura * fraction)
    return max(min_px, min(calculado, max_px))

def center_window_screen(win, width=350, height=100):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")