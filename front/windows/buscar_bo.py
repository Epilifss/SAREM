import tkinter as tk
import ttkbootstrap as tb
from functools import partial
from datetime import datetime
from back.utils import resource_path, center_window
from back.bo_service import pesquisar_bo_protheus
from front.modais.show_details import exibir_detalhes
from front.components.searchbar import SearchBar
from front.components.treeview import listagemTreeview
from theme import estilizar_treeview, ajustar_largura_colunas

class BuscarBOView:
    def __init__(self, parent, caller_id=None, user=None, refresh_callback=None):
        self.user = user
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Acompanhar uma BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.state('zoomed')

        self.root.transient(parent)

        self.ultimo_modulo = caller_id

        # Cabeçalho
        header = tb.Frame(self.root)
        header.pack(fill=tk.X, padx=5, pady=5)

        tb.Button(header, text="Fechar",
                   command=lambda: self.root.destroy(), style="custom.TButton").pack(side=tk.RIGHT)

        # Barra de pesquisa
        self.search_bar = SearchBar(self.root, self.pesquisar_bo, self.clear_search)
        self._criar_filtro_periodo()
        
        # lista de BOs Treeview
        self.treeview = listagemTreeview(
            self.root,
            columns=["BO", "OP", "CLIENTE", "EMPRESA", "EMISSÃO", "PREVISÃO DE ENTREGA"],
            on_double_click=partial(exibir_detalhes, self.root, caller_id=self.ultimo_modulo, user=self.user)
        )

        self.treeview.frame.pack(expand=True, fill=tk.BOTH, pady=(5, 60))

        self.treeview.tree.bind("<Double-1>", lambda event: exibir_detalhes(self.root,
                       self.treeview.tree, caller_id=self.ultimo_modulo, user=self.user, refresh_callback=refresh_callback, buscar_call="buscarBO"))

        self.carregar_bos()
        self.search_bar.search_entry.bind('<Return>', self.pesquisar_bo)

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
        from back.bo_service import listar_bo_protheus
        bos = listar_bo_protheus()
        self.treeview.tree.delete(*self.treeview.tree.get_children())
        
        if bos:
            if isinstance(bos, list):
                for bo in bos:
                    self.treeview.tree.insert(
                        '', 'end',
                        values=(
                            bo.bo,
                            bo.op,
                            bo.cliente,
                            bo.empresa,
                            bo.emissao,
                            bo.previsao_entrega

                        )
                    )
            else:
                self.treeview.tree.insert(
                    '', 'end',
                    values=(
                        bo.bo, # type: ignore
                        bo.op, # pyright: ignore[reportUnboundVariable] # type: ignore
                        bo.cliente, # type: ignore
                        bo.empresa, # type: ignore
                        bo.emissao, # type: ignore
                        bo.previsao_entrega # type: ignore
                    )
                )
                
        estilizar_treeview(self.treeview.tree)
        ajustar_largura_colunas(self.treeview.tree)

    def pesquisar_bo(self, event=None):
        termo = self.search_bar.search_entry.get().strip()
        data_inicio, data_fim = self._obter_periodo()

        if not termo and not self.filtro_data_ativo:
            self.carregar_bos()
            return

        pesq = pesquisar_bo_protheus(termo, data_inicio, data_fim)
        self.treeview.tree.delete(*self.treeview.tree.get_children())
        if pesq:
            for row in pesq:
                self.treeview.tree.insert(
                    '', 'end',
                    values=(
                        row[0], row[1], row[2], row[3],
                        row[4], row[5]
                    )
                )
        estilizar_treeview(self.treeview.tree)
        ajustar_largura_colunas(self.treeview.tree)

    def clear_search(self):
        self.search_bar.search_entry.delete(0, tk.END)
        self.search_bar.update_buttons()  # Atualiza os botões após limpar
        self.pesquisar_bo()  # Recarrega os BOs respeitando filtro de período