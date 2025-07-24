from back.utils import get_config_path
from tkinter import messagebox
import configparser

CONFIG_PATH = get_config_path()

def salvar_configuracoes(config: configparser.ConfigParser, entries_db: dict, entries_mik: dict, cancel_callback: callable):
    
    try:
        if "database" not in config:
            config["database"] = {}
        if "Protheus" not in config:
            config["Protheus"] = {}

        for campo, entry in entries_db.items():
            config["database"][campo] = entry.get()

        for campo, entry in entries_mik.items():
            config["Protheus"][campo] = entry.get()

        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)

        messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        cancel_callback()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
