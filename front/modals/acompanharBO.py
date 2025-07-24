import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from back.utils import resource_path, center_window

class acompanhar_Bo:
    def __init__(self, parent, tree, caller_id=None, user=None, refresh_callback=None):
        self.user = user
        self.parent = parent
        self.ultimo_modulo = caller_id
        self.tree = tree
        self.anexos = []
        self.loading_label = None
        self.max_anexos = 5
        self.max_tamanho_anexo = 50 * 1024 * 1024

        self.root = tk.Toplevel(parent)
        self.root.title("Acompanhar BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.transient(parent)
        self.root.grab_set()
        self.root.focus_set()

        canvas = tk.Canvas(self.root)
        v_scroll = tb.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="top", fill="both", expand=True)
        canvas.configure(yscrollcommand=v_scroll.set)

        scrollable_frame = tb.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        self.bo_dados = self.obter_dados_bo()
        self.secao_dados_gerais(scrollable_frame)
        self.secao_ocorrencia(scrollable_frame)
        self.secao_transporte(scrollable_frame)
        self.secao_itens(scrollable_frame)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.botao_salvar(self.root, refresh_callback)

        self.root.update_idletasks()
        ideal_width = scrollable_frame.winfo_reqwidth() + v_scroll.winfo_width() + 40
        self.root.geometry(f"{ideal_width}x600")
        center_window(self.root)

        self.root.update_idletasks()
        center_window(self.root)

        print (f"Acompanhar BO chamada através do módulo {self.ultimo_modulo} por {self.user}")

    def obter_dados_bo(self):
        selecionado = self.tree.selection()
        if not selecionado:
            return None
        valores = self.tree.item(selecionado, "values")
        return valores if valores else None

    def secao_dados_gerais(self, parent_frame):
        frame = tb.LabelFrame(parent_frame, text="Dados Gerais", padding=10)
        frame.pack(fill="x", padx=10, pady=10)

        labels = ["BO:", "OP:", "CLIENTE:", "EMISSÃO:"]
        for i, texto in enumerate(labels):
            tb.Label(frame, text=texto).grid(row=i, column=0, sticky="w")
            tb.Label(frame, text=self.bo_dados[i]).grid(row=i, column=1, sticky="w")

    def setores(self):
        from back.bo_service import obter_setores
        return obter_setores()

    def motivos(self):
        from back.bo_service import obter_motivos
        return obter_motivos()

    def secao_ocorrencia(self, parent_frame):
        frame = tb.LabelFrame(parent_frame, text="Detalhes da Ocorrência", padding=10)
        frame.pack(fill="x", padx=10, pady=10)

        campos = [
            ("Tipo de Ocorrência", tb.Entry),
            ("Setor Responsável", tb.Combobox, self.setores()),
            ("Descrição", tk.Text),
        ]

        self.entries_ocorrencia = {}
        for i, (label, widget, *args) in enumerate(campos):
            tb.Label(frame, text=f"{label}:").grid(row=i, column=0, sticky="w")
            if widget == tk.Text:
                w = widget(frame, width=30, height=5, font=("Arial", 8))
            elif widget == tb.Combobox:
                w = widget(frame, values=args[0])
            else:
                w = widget(frame)
            w.grid(row=i, column=1, sticky="ew")
            self.entries_ocorrencia[label] = w

    def secao_transporte(self, parent_frame):
        frame = tb.LabelFrame(parent_frame, text="Transporte", padding=10)
        frame.pack(fill="x", padx=10, pady=10)

        tb.Label(frame, text="Previsão de entrega:").grid(row=0, column=0, sticky="w")
        tb.Label(frame, text=self.bo_dados[5]).grid(row=0, column=1, sticky="w")

        tb.Label(frame, text="Frete:").grid(row=1, column=0, sticky="w")
        cb_frete = tb.Combobox(frame, values=["CIF", "FOB"], state="readonly")
        cb_frete.grid(row=1, column=1, sticky="w")
        self.entries_transporte = {"Frete": cb_frete}

    def secao_itens(self, parent_frame):
        frame = tb.LabelFrame(parent_frame, text="Itens da BO", padding=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Cabeçalho
        headers = ["CÓDIGO", "DESCRIÇÃO", "LINHA", "MOTIVO"]
        for col, header in enumerate(headers):
            tb.Label(frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=5, pady=2)

        item_selecionado2 = self.tree.selection()
        if not item_selecionado2:
            return

        valores2 = self.tree.item(item_selecionado2, "values")

        from back.bo_service import listar_itens_bo

        self.itens_bo = listar_itens_bo(valores2[1], valores2[0])

        # Campos de motivo
        self.entries_motivo_itens = []
        motivos = self.motivos()
        for idx, (cod, desc, linha) in enumerate(self.itens_bo, start=1):
            tb.Label(frame, text=cod).grid(row=idx, column=0, padx=5, pady=2)
            tb.Label(frame, text=desc).grid(row=idx, column=1, padx=5, pady=2)
            tb.Label(frame, text=linha).grid(row=idx, column=2, padx=5, pady=2)
            cb = tb.Combobox(frame, values=motivos, width=25)
            cb.grid(row=idx, column=3, padx=5, pady=2)
            self.entries_motivo_itens.append(cb)

    def botao_salvar(self, parent, refresh_callback):
        frame = tb.Frame(parent, padding=10)
        frame.pack(side="bottom", fill="x", padx=10, pady=10)
        tb.Button(frame, text="Salvar", command=lambda: self.salvar(self.bo_dados, self.entries_ocorrencia, self.entries_transporte, self.user, self.itens_bo, self.ultimo_modulo, refresh_callback)).pack(side=tk.RIGHT)

    def salvar(self, bo_dados, entries_ocorrencia, entries_transporte, user, itens_bo_original, ultimo_modulo, refresh_callback):
        from back.bo_service import salvar_bo
        try:

            ocorrencia_data = {
                "tipo_ocorrencia": entries_ocorrencia["Tipo de Ocorrência"].get(),
                "descricao": entries_ocorrencia["Descrição"].get("1.0", tk.END).strip(),
                "setor_responsavel": entries_ocorrencia["Setor Responsável"].get(),
            }

            transporte_data = {
                "frete": entries_transporte["Frete"].get()
            }

            itens_com_motivos = []
            for i, (cod, desc, linha) in enumerate(itens_bo_original):
                motivo_selecionado = self.entries_motivo_itens[i].get()
                itens_com_motivos.append({
                    "cod": cod,
                    "desc": desc,
                    "linha": linha,
                    "motivo": motivo_selecionado
                })

            salvar_bo(bo_dados=bo_dados, ocorrencia_data=ocorrencia_data, transporte_data=transporte_data, user_data=user, itens_com_motivos=itens_com_motivos, ultimo_modulo=ultimo_modulo)
            messagebox.showinfo("Sucesso", "BO salva com sucesso!")
            self.root.destroy()
            refresh_callback() if refresh_callback else None
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar BO: {str(e)}")