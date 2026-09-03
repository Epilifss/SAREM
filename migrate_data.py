import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

# ==============================================================================
# CONFIGURAÇÕES DE CONEXÃO
# ==============================================================================

# 1. Configurações do Banco de Origem (SQL Server)
SQL_SERVER_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',  # Ex: 'ODBC Driver 17 for SQL Server' ou 'SQL Server'
    'server': '192.168.0.10',                  # Ex: 'localhost', '192.168.1.100' ou 'SERVIDOR\\INSTANCIA'
    'database': 'SAREM_DB',
    'user': 'Totvs',
    'password': 'totvs'
}

# 2. Configurações do Banco de Destino (Supabase CLI Local)
# Obtenha a URL rodando 'supabase status' no terminal.
# Padrão CLI: postgresql://postgres:postgres@localhost:54322/postgres
SUPABASE_LOCAL_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

# ==============================================================================
# FUNÇÕES DE CONEXÃO
# ==============================================================================

def get_sql_server_engine():
    """Cria a conexão com o SQL Server utilizando os parâmetros acima."""
    params = (
        f"DRIVER={{{SQL_SERVER_CONFIG['driver']}}};"
        f"SERVER={SQL_SERVER_CONFIG['server']};"
        f"DATABASE={SQL_SERVER_CONFIG['database']};"
        f"UID={SQL_SERVER_CONFIG['user']};"
        f"PWD={SQL_SERVER_CONFIG['password']};"
    )
    odbc_str = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(params)
    return create_engine(odbc_str)

def get_supabase_engine():
    """Cria a conexão com o Postgres do Supabase CLI."""
    return create_engine(SUPABASE_LOCAL_URL)

# ==============================================================================
# EXECUÇÃO DA MIGRAÇÃO
# ==============================================================================

def migrate_tables():
    src_engine = get_sql_server_engine()
    dest_engine = get_supabase_engine()

    # Mapeamento: "src" (Nome no SQL Server) -> "dest" (Nome no Supabase)
    tables_to_migrate = [
        {"src": "bo_records", "dest": "bo_records"}
    ]

    print("🚀 Iniciando migração do SQL Server diretamente para o Supabase CLI...")

    for table in tables_to_migrate:
        src_table = table["src"]
        dest_table = table["dest"]

        try:
            print(f"\n📦 Lendo dados da tabela '{src_table}' no SQL Server...")
            
            # Carrega os dados da tabela em um DataFrame Pandas
            df = pd.read_sql_table(src_table, con=src_engine)

            if df.empty:
                print(f"⚠️ Tabela '{src_table}' está vazia. Pulando...")
                continue

            # Normaliza os nomes das colunas para letras minúsculas (compatibilidade Postgres)
            df.columns = [c.lower() for c in df.columns]

            print(f"⏳ Inserindo {len(df)} registros na tabela '{dest_table}' do Supabase...")

            # Grava no Supabase (se a coluna de ID for incremental/ identity, ela será inserida com os valores do SQL Server)
            df.to_sql(
                name=dest_table,
                con=dest_engine,
                schema='public',
                if_exists='replace',
                index=False,
                chunksize=100,
                method='multi'
            )

            print(f"✅ Tabela '{dest_table}' migrada com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao migrar a tabela '{src_table}': {e}")

if __name__ == "__main__":
    migrate_tables()