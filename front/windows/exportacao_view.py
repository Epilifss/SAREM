from back.bo_service import listar_bos, pesquisar_bo
from back.utils import resource_path
from front.components.header import Header
from front.components.searchbar import SearchBar
from front.components.treeview import listagemTreeview
from front.modais.show_details import exibir_detalhes
from functools import partial
from theme import estilizar_treeview, ajustar_largura_colunas
import tkinter as tk
from datetime import datetime
import ttkbootstrap as tb

class ExportacaoModule:
    instance = None

    def __init__(self, user, parent):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("SAREM - Módulo Exportação")
        self.root.state('zoomed')

        self.root.iconbitmap(resource_path('SAREM.ico'))

        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        ExportacaoModule.instance = self

        # Cabeçalho
        self.header = Header(self.root, self.user, caller_id="Exportacao", tree=None, refresh_callback=self.carregar_bos)

        # Barra de pesquisa
        self.search_bar = SearchBar(self.root, self.pesquisar_bo, self.clear_search)
        self._criar_filtro_periodo()

        # Lista de BOs

        self.treeview = listagemTreeview(
            self.root,
            columns=["BO", "OP", "STATUS", "TIPO DE OCORRÊNCIA", "SETOR RESPONSÁVEL", "CLIENTE"],
            on_double_click=partial(exibir_detalhes, caller_id="Exportacao", user=self.user, refresh_callback=self.carregar_bos)
        )
        self.tree = self.treeview.tree
        self.header.tree = self.tree

        self.carregar_bos()
        self.search_bar.search_entry.bind('<Return>', self.pesquisar_bo)
        self.root.mainloop()

    def _criar_filtro_periodo(self):
        self.filtro_data_ativo = False
        self.filtro_frame = tb.Frame(self.root)
        self.filtro_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        hoje = datetime.today()
        primeiro_dia_mes = hoje.replace(day=1)

        tb.Label(self.filtro_frame, text="Período:").pack(side=tk.LEFT, padx=(0, 5))
        tb.Label(self.filtro_frame, text="De").pack(side=tk.LEFT, padx=(0, 2))
        self.data_inicio_entry = tb.DateEntry(
            self.filtro_frame,
            dateformat="%d/%m/%Y",
            startdate=primeiro_dia_mes,
            width=12,
        )
        self.data_inicio_entry.pack(side=tk.LEFT, padx=(0, 6))

        tb.Label(self.filtro_frame, text="Até").pack(side=tk.LEFT, padx=(0, 2))
        self.data_fim_entry = tb.DateEntry(
            self.filtro_frame,
            dateformat="%d/%m/%Y",
            startdate=hoje,
            width=12,
        )
        self.data_fim_entry.pack(side=tk.LEFT, padx=(0, 8))

        tb.Button(self.filtro_frame, text="Aplicar período", command=self.aplicar_filtro_data).pack(side=tk.LEFT, padx=(0, 5))
        tb.Button(self.filtro_frame, text="Remover período", command=self.remover_filtro_data).pack(side=tk.LEFT)

    def _obter_periodo(self):
        if not self.filtro_data_ativo:
            return None, None
        data_inicio = self.data_inicio_entry.get_date().date()
        data_fim = self.data_fim_entry.get_date().date()
        return data_inicio, data_fim

    def aplicar_filtro_data(self):
        self.filtro_data_ativo = True
        self.pesquisar_bo()

    def remover_filtro_data(self):
        self.filtro_data_ativo = False
        self.pesquisar_bo()

    def carregar_bos(self):
        data_inicio, data_fim = self._obter_periodo()
        bos = listar_bos("Exportacao", data_inicio, data_fim)
        self.tree.delete(*self.tree.get_children())
        if bos:
            for bo in bos:
                self.tree.insert(
                    '', 'end',
                    values=(
                        bo.bo_number, bo.op, bo.status, bo.tipo_ocorrencia,
                        bo.setor_responsavel, bo.loja
                    )
                )
        estilizar_treeview(self.tree)
        ajustar_largura_colunas(self.tree)

    def pesquisar_bo(self, event=None):
        termo = self.search_bar.search_entry.get().strip()
        data_inicio, data_fim = self._obter_periodo()

        if not termo and not self.filtro_data_ativo:
            self.carregar_bos()
            return

        pesq = pesquisar_bo('Exportacao', termo, data_inicio, data_fim)
        self.tree.delete(*self.tree.get_children())
        if pesq:
            for row in pesq:
                self.tree.insert(
                    '', 'end',
                    values=(
                        row[0], row[1], row[2], row[3],
                        row[4], row[5]
                    )
                )

    def clear_search(self):
        self.search_bar.search_entry.delete(0, tk.END)
        self.search_bar.update_buttons()  # Atualiza os botões após limpar
        self.pesquisar_bo()  # Recarrega os BOs respeitando filtro de período