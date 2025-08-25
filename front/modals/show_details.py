import tkinter as tk
import ttkbootstrap as tb
from back.utils import resource_path, center_window
from front.modals.acompanharBO import acompanhar_Bo
from front.modals.edit_bo import editar_bo
from back.bo_service import excluir_bo

class exibir_detalhes():
    instance = None

    def __init__(self, parent, tree, caller_id=None, user=None, refresh_callback=None, buscar_call=None):
        self.user = user
        self.root = tk.Toplevel(parent)
        self.root.title("Detalhes BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.focus_set()

        self.root.transient(parent)
        self.root.grab_set()

        self.tree = tree
        self.ultimo_modulo = caller_id

        exibir_detalhes.instance = self

        from back.bo_service import verificar_bo_acompanhada

        item_selecionado = self.tree.selection()
        valores = self.tree.item(item_selecionado, "values") if item_selecionado else None
        if valores is None or len(valores) == 0:
            self.root.destroy()
            return
        bo = valores[0]

        self.bo_ja_acompanhada = verificar_bo_acompanhada(bo)

        if buscar_call == "buscarBO" and self.bo_ja_acompanhada:
            aviso_frame = tb.Frame(self.root)
            aviso_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
            aviso_label = tb.Label(
                aviso_frame,
                text="⚠️ Esta BO já está sendo acompanhada!",
                foreground="red",
                font=("Arial", 10, "bold")
            )
            aviso_label.pack(fill="x")

            detalhe_row = 1
        else:
            detalhe_row = 0

        self.detalhes_ocorrencia(row=detalhe_row, buscar_call=buscar_call, caller_id=caller_id)
        self.itens_bo(row=detalhe_row + 1, caller_id=caller_id, buscar_call=buscar_call)

        modulos = ["Corporativo", "Varejo", "Exportacao"]

        if not (self.bo_ja_acompanhada and (caller_id in modulos and buscar_call == "buscarBO")):
            self.opcoes_bo(row=detalhe_row + 2, caller_id=caller_id, refresh_callback=refresh_callback, buscar_call=buscar_call)

        self.root.update_idletasks()
        center_window(self.root)

    def detalhes_ocorrencia(self, row=0, buscar_call=None, caller_id=None):
        self.root.grid_rowconfigure(row, weight=3)
        self.root.grid_columnconfigure(0, weight=1)

        frame_sc5Detalhes = tb.LabelFrame(
            self.root, text="Detalhes da Ocorrência", padding=10)
        frame_sc5Detalhes.grid(
            row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_sc5Detalhes.grid_rowconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(0, weight=1)
        frame_sc5Detalhes.grid_columnconfigure(1, weight=2)

        item_selecionado = self.tree.selection()
        if not item_selecionado:
            return

        valores = self.tree.item(item_selecionado, "values")

        modulos = ["Corporativo", "Varejo", "Exportacao"]

        labels = ["BO:", "OP:", "CLIENTE:", "FILIAL:", "EMISSÃO:", "PREVISÃO DE ENTREGA:"]
        labels2 = ["BO:", "OP:", "CLIENTE:", "TIPO DE OCORRÊNCIA:", "PREVISÃO DE EMBARQUE:", "DESCRIÇÃO:", "FRETE:", "STATUS:"]
        if buscar_call == "buscarBO":
            for i, label_text in enumerate(labels if buscar_call == "buscarBO" else labels2):
                tb.Label(frame_sc5Detalhes, text=label_text).grid(
                    row=i, column=0, sticky="w", padx=5, pady=2)
                tb.Label(frame_sc5Detalhes, text=valores[i]).grid(
                    row=i, column=1, sticky="ew", padx=5, pady=2)
        elif caller_id in modulos:
            from back.bo_service import buscar_dados_bo
            bo_dados = buscar_dados_bo(valores[0])
            if bo_dados:
                for i, label_text in enumerate(labels2):
                    tb.Label(frame_sc5Detalhes, text=label_text).grid(
                        row=i, column=0, sticky="w", padx=5, pady=2)
                    tb.Label(frame_sc5Detalhes, text=bo_dados[i]).grid(
                        row=i, column=1, sticky="ew", padx=5, pady=2)

        self.root.update_idletasks()
        self.root.minsize(400, self.root.winfo_height())

    def itens_bo(self, row=1, caller_id=None, buscar_call=None):
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_itensBo = tb.LabelFrame(
            self.root, text="Itens da BO", padding=10)
        frame_itensBo.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_itensBo.grid_rowconfigure(0, weight=1)
        for i in range(3):
            frame_itensBo.grid_columnconfigure(i, weight=1)

        labels = ["CÓDIGO", "DESCRIÇÃO", "LINHA"]
        labels2 = ["CÓDIGO", "DESCRIÇÃO", "LINHA", "MOTIVO"]

        item_selecionado2 = self.tree.selection()
        if not item_selecionado2:
            return

        valores2 = self.tree.item(item_selecionado2, "values")

        from back.bo_service import listar_itens_bo, listar_itens_SAREM

        if buscar_call == "buscarBO":
            itens_bo = listar_itens_bo(valores2[1], valores2[0])
        else:
            itens_bo = listar_itens_SAREM(valores2[0], valores2[1])

        for i, label_txt in enumerate(labels if buscar_call == "buscarBO" else labels2):
            label = tb.Label(frame_itensBo, text=label_txt)
            label.grid(row=0, column=i, sticky="w", padx=5, pady=2)
            frame_itensBo.grid_columnconfigure(i, weight=1)

        if itens_bo is not None:
            for idx, item in enumerate(itens_bo):
                for col, value in enumerate(item):
                    label = tb.Label(frame_itensBo, text=value)
                    label.grid(row=idx + 1, column=col, sticky="w", padx=5, pady=2)
                    frame_itensBo.grid_columnconfigure(col, weight=1)

        self.root.update_idletasks()
        self.root.geometry("")

    def opcoes_bo(self, row=2, caller_id=None, refresh_callback=None, buscar_call=None):
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        frame_opcoesBo = tb.LabelFrame(
            self.root, text="Opções da BO", padding=10)
        frame_opcoesBo.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        frame_opcoesBo.grid_rowconfigure(0, weight=1)
        frame_opcoesBo.grid_columnconfigure(0, weight=1)

        modulos = ["Corporativo", "Varejo", "Exportacao"]

        if buscar_call == "buscarBO":
            tb.Button(frame_opcoesBo, text="Acompanhar BO", command=lambda: acompanhar_Bo(self.root, self.tree, caller_id=self.ultimo_modulo, user=self.user, refresh_callback=refresh_callback)).pack(pady=5, side=tk.RIGHT)
        elif caller_id in modulos:
            tb.Button(frame_opcoesBo, text="Excluir BO", command=lambda: self.excluir(refresh_callback)).pack(pady=5, padx=5, side=tk.RIGHT)
            tb.Button(frame_opcoesBo, text="Editar BO", command=lambda: self.abrir_editar_bo(refresh_callback)).pack(pady=5, padx=5, side=tk.RIGHT)

    def excluir(self, refresh_callback):
        excluir = excluir_bo(self)
        self.root.wait_window(excluir)
        if refresh_callback:
            refresh_callback()
        self.root.destroy()

    def abrir_editar_bo(self, refresh_callback):
        janela = editar_bo(self.root, self.tree, caller_id=self.ultimo_modulo, user=self.user)
        self.root.wait_window(janela.root)
        if refresh_callback:
            refresh_callback()
        self.root.destroy()