import pandas as pd
from sqlalchemy import create_engine, inspect, text
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
SUPABASE_LOCAL_URL = "postgresql://postgres:postgres@192.168.0.97:56002/postgres"

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
        {"src": "bo_records", "dest": "bo_records", "key_column": "bo_number", "deduplicate": True},
        {"src": "BO_ITENS", "dest": "bo_itens", "key_column": "bo_ref", "deduplicate": False}
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

            destination_columns = {
                column['name']
                for column in inspect(dest_engine).get_columns(dest_table, schema='public')
            }
            ignored_columns = sorted(set(df.columns) - destination_columns)
            if ignored_columns:
                print(f"⚠️ Colunas ignoradas (não existem no destino): {', '.join(ignored_columns)}")
                df = df[[column for column in df.columns if column in destination_columns]]

            key_column = table.get('key_column')
            if key_column in df.columns:
                df[key_column] = df[key_column].astype('string').str.strip()
                if table.get('deduplicate'):
                    duplicate_count = int(df.duplicated(subset=[key_column]).sum())
                    if duplicate_count:
                        print(f"⚠️ Registros duplicados por {key_column} removidos: {duplicate_count}")
                        df = df.drop_duplicates(subset=[key_column], keep='first')

            print(f"⏳ Inserindo {len(df)} registros na tabela '{dest_table}' do Supabase...")

            # Mantém a tabela criada pelas migrations: recriá-la removeria suas
            # políticas, triggers e quebraria objetos dependentes.
            if 'id' in df.columns:
                df = df.drop(columns=['id'])

            with dest_engine.begin() as connection:
                connection.execute(text(f'DELETE FROM public."{dest_table}"'))
                df.to_sql(
                    name=dest_table,
                    con=connection,
                    schema='public',
                    if_exists='append',
                    index=False,
                    chunksize=100,
                    method='multi'
                )

            print(f"✅ Tabela '{dest_table}' migrada com sucesso!")

        except Exception as e:
            database_error = e
            while hasattr(database_error, 'orig'):
                database_error = database_error.orig
            diagnostic = getattr(database_error, 'diag', None)
            error_message = getattr(diagnostic, 'message_primary', None)
            if not error_message:
                error_message = str(database_error).splitlines()[0]
            error_detail = getattr(diagnostic, 'message_detail', None)
            print(
                f"❌ Erro ao migrar a tabela '{src_table}': "
                f"{type(database_error).__name__}: {error_message}"
            )
            if error_detail:
                print(f"   Detalhe: {error_detail}")

if __name__ == "__main__":
    migrate_tables()