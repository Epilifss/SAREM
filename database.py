import configparser
import os
import pyodbc

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

def create_connection():
    try:
        db = config['database']
        conn = pyodbc.connect(
            f"DRIVER={{{db['driver']}}};"
            f"SERVER={db['server']};"
            f"DATABASE={db['database']};"
            f"UID={db['user']};"
            f"PWD={db['password']};"
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def create_connection_mikonos():
    try:
        db = config['mikonos']
        conn = pyodbc.connect(
            f"DRIVER={{{db['driver']}}};"
            f"SERVER={db['server']};"
            f"DATABASE={db['database']};"
            f"UID={db['user']};"
            f"PWD={db['password']};"
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None