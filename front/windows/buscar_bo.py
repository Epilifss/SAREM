import tkinter as tk
import ttkbootstrap as tb
from functools import partial
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
        pesq = pesquisar_bo_protheus(self.search_bar.search_entry.get())
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
        self.carregar_bos()  # Recarrega os BOs