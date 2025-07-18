# File: back/configdb_service.py
from back.utils import get_config_path
from tkinter import messagebox
import configparser # Importar configparser para tipagem e clareza

CONFIG_PATH = get_config_path()

def salvar_configuracoes(config: configparser.ConfigParser, entries_db: dict, entries_mik: dict, cancel_callback: callable):
    
    try:
        # Garante que as seções existam
        if "database" not in config:
            config["database"] = {}
        if "Protheus" not in config:
            config["Protheus"] = {}

        # Coleta os valores dos campos SAREM
        for campo, entry in entries_db.items():
            config["database"][campo] = entry.get()

        # Coleta os valores dos campos Protheus
        for campo, entry in entries_mik.items():
            config["Protheus"][campo] = entry.get()

        # Escreve as configurações no arquivo
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)

        messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        cancel_callback() # Chama o callback para fechar a janela
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

# Se 'carregar_configuracoes' também for uma função de serviço, ela deveria ter uma assinatura similar
# Exemplo (se necessário):
# def carregar_configuracoes(config: configparser.ConfigParser, entries_db: dict, entries_mik: dict):
#     if "database" in config:
#         for campo in entries_db:
#             valor = config["database"].get(campo, "")
#             entries_db[campo].insert(0, valor)
#     if "Protheus" in config:
#         for campo in entries_mik:
#             valor = config["Protheus"].get(campo, "")
#             entries_mik[campo].insert(0, valor)
