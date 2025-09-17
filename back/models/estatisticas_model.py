import pandas as pd
from sqlalchemy import text
from back.database import create_connection_alchemy

class EstatisticasModel:
    def __init__(self, modulo):
        self.modulo = modulo

    def obter_anos_disponiveis(self):
        engine = create_connection_alchemy()
        
        query = """
            SELECT DISTINCT YEAR(emissao_totvs) AS ano 
            FROM bo_records 
            WHERE emissao_totvs IS NOT NULL AND modulo LIKE ? 
            ORDER BY ano DESC
        """

        try:
            df = pd.read_sql_query(query, engine, params=(self.modulo,))
            anos = df['ano'].tolist()
            return anos if anos else ["Todos"]
        except Exception as e:
            print(f"Erro ao obter anos disponíveis: {e}")
            return ["Todos"]

    def obter_dados_grafico(self, ano, engine=None):
        if engine is None:
            engine = create_connection_alchemy()
        
        params = {"modulo": f"%{self.modulo}%"}
        if ano != "todos":
            params["ano"] = str(ano)
        else:
            params["ano"] = ""

        query = text("""
            SELECT 
                CASE 
                    WHEN setor_responsavel IS NULL OR LTRIM(RTRIM(setor_responsavel)) = '' THEN 'Não especificado'
                    ELSE setor_responsavel
                END AS Setor,
                COUNT(*) AS Contagem
            FROM bo_records 
            WHERE (:ano IS NULL OR YEAR(emissao_totvs) = :ano)
            AND modulo LIKE :modulo
            GROUP BY 
                CASE 
                    WHEN setor_responsavel IS NULL OR LTRIM(RTRIM(setor_responsavel)) = '' THEN 'Não especificado'
                    ELSE setor_responsavel
                END
        """)

        try:
            with engine.begin() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            print(f"Erro ao obter dados do gráfico: {e}")
            return pd.DataFrame()