from back.bo_service import listar_bos, pesquisar_bo
from back.utils import resource_path
from front.components.header import Header
from front.components.searchbar import SearchBar
from front.components.treeview import listagemTreeview
from front.modais.show_details import exibir_detalhes
from functools import partial
from theme import estilizar_treeview, ajustar_largura_colunas
import tkinter as tk

class VarejoModule:
    instance = None # Var de class que armazena a instância atual

    def __init__(self, user, parent):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("SAREM - Módulo Varejo")
        self.root.state('zoomed')

        self.root.iconbitmap(resource_path('SAREM.ico'))  # Define o ícone da janela

        self.root.protocol("WM_DELETE_WINDOW", parent.destroy)

        VarejoModule.instance = self

        # Cabeçalho
        self.header = Header(self.root, self.user, caller_id="Varejo", tree=None, refresh_callback=self.carregar_bos)

        # Barra de pesquisa
        self.search_bar = SearchBar(self.root, self.pesquisar_bo, self.clear_search)

        # Lista de BOs

        self.treeview = listagemTreeview(
            self.root,
            columns=["BO", "OP", "STATUS", "TIPO DE OCORRÊNCIA", "SETOR RESPONSÁVEL", "CLIENTE"],
            on_double_click=partial(exibir_detalhes, caller_id="Varejo", user=self.user, refresh_callback=self.carregar_bos)
        )
        self.tree = self.treeview.tree
        self.header.tree = self.tree

        self.carregar_bos()
        self.search_bar.search_entry.bind('<Return>', self.pesquisar_bo)
        self.root.mainloop()

    def carregar_bos(self):
        bos = listar_bos("Varejo")
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
        pesq = pesquisar_bo('Varejo', self.search_bar.search_entry.get())
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
        self.carregar_bos()  # Recarrega os BOs