from back.models.estatisticas_model import EstatisticasModel
from front.windows.estatisticas_view import EstatisticasView
import threading

class EstatisticasPresenter:
    def __init__(self, parent, caller_id):
        self.model = EstatisticasModel(modulo=caller_id)
        self.view = EstatisticasView(parent)
        self.view.set_presenter(self)
        self.caller_id = caller_id
        
        print(f"Tela de estatísticas chamada pelo módulo: {self.caller_id}")

    def iniciar(self):
        # Mostra a janela imediatamente
        self.view.mostrar_mensagem("Carregando anos disponíveis...")

        def carregar_anos():
            anos = self.model.obter_anos_disponiveis()
            # Atualiza a interface na thread principal
            self.view.root.after(0, lambda: self._finalizar_carregamento_anos(anos))

        threading.Thread(target=carregar_anos, daemon=True).start()

    def _finalizar_carregamento_anos(self, anos):
        self.view.set_anos_disponiveis(anos)
        if self.view.combo_anos.get():
            self.handle_ano_selecionado()
        else:
            self.view.mostrar_mensagem("Não há dados disponíveis para gerar estatísticas.")

    def handle_ano_selecionado(self, event=None):
        ano_selecionado = self.view.combo_anos.get()
        self.view.mostrar_mensagem("Carregando Dados...")

        def carregar():
            df = self.model.obter_dados_grafico(ano_selecionado)
            # Atualiza a interface na thread principal
            if df.empty:
                self.view.root.after(0, lambda: self.view.mostrar_mensagem(f"Nenhum dado encontrado para o ano '{ano_selecionado}'."))
            else:
                self.view.root.after(0, lambda: self.view.mostrar_grafico_seaborn(df, ano_selecionado))

        threading.Thread(target=carregar, daemon=True).start()



