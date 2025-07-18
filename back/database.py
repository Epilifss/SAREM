import configparser
import os
import pyodbc
import hashlib

def garantir_config_ini():
    config_path = get_config_path()
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        config['database'] = {
            'driver': 'ODBC Driver 17 for SQL Server',
            'server': '',
            'database': '',
            'user': '',
            'password': ''
        }
        config['Protheus'] = {
            'driver': 'ODBC Driver 17 for SQL Server',
            'server': '',
            'database': '',
            'user': '',
            'password': ''
        }
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(config_path)
        alterado = False
        if 'database' not in config:
            config['database'] = {}
            alterado = True
        if 'driver' not in config['database']:
            config['database']['driver'] = 'ODBC Driver 17 for SQL Server'
            alterado = True
        if 'Protheus' not in config['Protheus']:
            config['Protheus']['driver'] = 'ODBC Driver 17 for SQL Server'
            alterado = True
        if alterado:
            with open(config_path, 'w') as configfile:
                config.write(configfile)

def get_config_path():
    appdata = os.environ.get('APPDATA') or os.path.expanduser('~')
    config_dir = os.path.join(appdata, 'SAREM')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.ini')

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

def get_db_config():
    config = configparser.ConfigParser()
    config.read(get_config_path())
    return config['database']

def get_db_config_Protheus():
    config = configparser.ConfigParser()
    config.read(get_config_path())
    return config['Protheus']

def ensure_database_exists():
    db = get_db_config()
    conn_str = (
        f"DRIVER={{{db['driver']}}};"
        f"SERVER={db['server']};"
        f"DATABASE=master;"
        f"UID={db['user']};"
        f"PWD={db['password']};"
    )
    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(f"IF DB_ID('{db['database']}') IS NULL CREATE DATABASE [{db['database']}]")
    except Exception as e:
        print(f"Erro ao garantir existência do banco de dados: {e}")

def ensure_tables_exist():
    db = get_db_config()
    conn_str = (
        f"DRIVER={{{db['driver']}}};"
        f"SERVER={db['server']};"
        f"DATABASE={db['database']};"
        f"UID={db['user']};"
        f"PWD={db['password']};"
    )
    try:
        with pyodbc.connect(conn_str, autocommit=True) as conn:
            cursor = conn.cursor()
            # Exemplo de criação de tabela bo_records
            cursor.execute("""
                IF OBJECT_ID('dbo.bo_records', 'U') IS NULL
                CREATE TABLE dbo.bo_records (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    bo_number VARCHAR(20) UNIQUE NOT NULL,
                    op VARCHAR (30) NULL,
                    loja VARCHAR(100),
                    emissao_totvs VARCHAR(50),
                    tipo_ocorrencia VARCHAR(100),
                    motivo VARCHAR(100),
                    frete VARCHAR(50),
                    setor_responsavel VARCHAR(100),
                    status VARCHAR(50),
                    previsao_embarque DATE,
                    descricao TEXT,
                    created_at DATETIME DEFAULT GETDATE(),
                    dt_embarque DATE,
                    modulo VARCHAR(50),
                    filial VARCHAR(15),
                    D_E_L_E_T_ CHAR(1) DEFAULT ' ',
                    user_delet VARCHAR(50) DEFAULT NULL,
                    deleted_at DATETIME DEFAULT NULL
                )
            """)

            cursor.execute("""
                IF OBJECT_ID('dbo.users', 'U') IS NULL
                CREATE TABLE dbo.users (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    module VARCHAR(50),
                    is_admin BIT DEFAULT 0
                )
            """)

            cursor.execute("""
                IF OBJECT_ID('dbo.BO_ITENS', 'U') IS NULL
                CREATE TABLE [dbo].[BO_ITENS] (
                    [ID] INT IDENTITY (1, 1) NOT NULL,
                    [BO_REF] VARCHAR (20)  NULL,
                    [COD]    VARCHAR (10)  NULL,
                    [DESC]   VARCHAR (200) NULL,
                    [LINHA]  VARCHAR (50)  NULL,
                    [MOTIVO] VARCHAR (200) NULL
                )
            """)

            admin_password = hashlib.sha256("4dmin123@4".encode()).hexdigest()
            cursor.execute('''
                IF NOT EXISTS (SELECT * FROM users WHERE username = 'TI')
                INSERT INTO users (username, password_hash, is_admin)
                VALUES (?, ?, 1)
            ''', ("TI", admin_password))
    except Exception as e:
        print(f"Erro ao garantir existência das tabelas: {e}")

def create_connection():
    ensure_database_exists()
    ensure_tables_exist()
    try:
        db = get_db_config()
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

def create_connection_Protheus():
    try:
        db = get_db_config_Protheus()
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