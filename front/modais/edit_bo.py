import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from back.utils import resource_path, center_window, ajustar_tamanho_janela, limitar_janela_tela, wraplength_responsivo
from back.bo_service import obter_detalhes_ocorrencia, listar_itens_SAREM, obter_motivos, atualizar_bo

class editar_bo():
    def __init__(self, parent, tree, caller_id=None, user=None) -> None:
        self.user = user
        self.tree = tree
        self.ultimo_modulo = caller_id

        if not self._can_edit_bo():
            messagebox.showerror("Permissão negada", "Você não possui permissão para editar BO.")
            self.root = tk.Toplevel(parent)
            self.root.withdraw()
            self.root.after(0, self.root.destroy)
            return

        self.root = tk.Toplevel(parent)
        self.root.title("Editar BO")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.wraplength_valor = wraplength_responsivo(self.root, fraction=0.5)
        self.root.minsize(400, 300)
        self.root.resizable(False, False)
        self.root.focus_set()

        self.root.transient(parent)
        self.root.grab_set()

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

        item_selecionado = tree.selection()
        if not item_selecionado:
            self.root.destroy()
            return

        valores = tree.item(item_selecionado, "values")
        self.bo_number = valores[0]

        self.detalhes_ocorrencia(valores, scrollable_frame)
        self.editaveis(scrollable_frame)
        self.obter_itens_bo(scrollable_frame)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.opcoes_editor(self.root)

        self.root.update_idletasks()
        ideal_width = scrollable_frame.winfo_reqwidth() + v_scroll.winfo_width() + 40
        ajustar_tamanho_janela(self.root, ideal_width, 600)
        limitar_janela_tela(self.root)
        center_window(self.root)

    def _can_edit_bo(self):
        if not self.user:
            return False
        if hasattr(self.user, "can_edit"):
            return self.user.can_edit()
        if hasattr(self.user, "is_admin"):
            return bool(self.user.is_admin)
        return True

    def detalhes_ocorrencia(self, valores, parent_frame):
        parent_frame.grid_rowconfigure(0, weight=3)
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        frame_detalhes_ocorrencia = tb.LabelFrame(
            parent_frame, text="Detalhes da Ocorrência", padding=10)
        frame_detalhes_ocorrencia.grid(
            row=0, column=0, sticky="nsew", padx=10, pady=10)

        frame_detalhes_ocorrencia.grid_rowconfigure(0, weight=1)
        frame_detalhes_ocorrencia.grid_columnconfigure(0, weight=1)
        frame_detalhes_ocorrencia.grid_columnconfigure(1, weight=2)

        item_selecionado = self.tree.selection()
        if not item_selecionado:
            return

        valores = self.tree.item(item_selecionado, "values")

        itens_bo = obter_detalhes_ocorrencia(valores[0])

        labels = ["BO:", "OP:", "CLIENTE:", "PREVISÃO DE EMBARQUE:", "STATUS:"]
        if itens_bo:
            for i, label_text in enumerate(labels):
                tb.Label(frame_detalhes_ocorrencia, text=label_text).grid(
                    row=i, column=0, sticky="w", padx=5, pady=2)
                tb.Label(frame_detalhes_ocorrencia, text=itens_bo[0][i], wraplength=self.wraplength_valor, justify="left", anchor="w").grid(
                    row=i, column=1, sticky="ew", padx=5, pady=2)

        self.root.update_idletasks()
        self.root.minsize(400, self.root.winfo_height())

    def editaveis(self, parent_frame):
        parent_frame.grid_rowconfigure(0, weight=1)

        self.entries = {}
        campos = [
            ("tipo_ocorrencia", "Tipo de Ocorrência"),
            ("descricao", "Descrição"),
            ("setor_responsavel", "Setor Responsável"),
            ("frete", "Frete"),
        ]

        frame_editaveis = tb.LabelFrame(parent_frame, text="Campos Editáveis", padding=20)
        frame_editaveis.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        from back.bo_service import obter_campos_editaveis, obter_setores
        campos_editaveis = obter_campos_editaveis(self.bo_number)

        campos = [
            ("tipo_ocorrencia", "Tipo de Ocorrência"),
            ("descricao", "Descrição"),
            ("setor_responsavel", "Setor Responsável"),
            ("frete", "Frete"),
        ]

        for i, (campo, label_text) in enumerate(campos):
            tb.Label(frame_editaveis, text=label_text + ":").grid(
                row=i, column=0, sticky=tk.W, pady=5)
            if campo == "frete":
                entry = tb.Combobox(frame_editaveis, values=["CIF", "FOB"], state="readonly")
            elif campo == "setor_responsavel":
                setores = obter_setores() or []
                entry = tb.Combobox(frame_editaveis, values=setores, state="readonly")
            elif campo == "descricao":
                entry = tk.Text(frame_editaveis, width=30, height=5, font=("Arial", 8))
            else:
                entry = tb.Entry(frame_editaveis, width=30)
            if campos_editaveis and len(campos_editaveis) > i:
                valor = campos_editaveis[i]
                if campo == "frete":
                    entry.set(valor if valor else "") # pyright: ignore[reportAttributeAccessIssue]
                elif campo == "descricao":
                    entry.insert("1.0", valor if valor else "")
                else:
                    if isinstance(entry, tb.Combobox):
                        entry.set(valor if valor else "")
                    elif isinstance(entry, tb.Entry):
                        entry.insert(0, valor if valor else "")
            entry.grid(row=i, column=1, pady=5, sticky="ew")
            self.entries[campo] = entry

    def obter_itens_bo(self, parent_frame):
        parent_frame.grid_rowconfigure(0, weight=3)
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        frame_itensBo = tb.LabelFrame(
            parent_frame, text="Itens da BO", padding=10)
        frame_itensBo.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        frame_itensBo.grid_rowconfigure(0, weight=1)
        for i in range(3):
            frame_itensBo.grid_columnconfigure(i, weight=1)

        labels = ["CÓDIGO", "DESCRIÇÃO", "LINHA", "MOTIVO"]

        item_selecionado2 = self.tree.selection()
        if not item_selecionado2:
            return

        valores2 = self.tree.item(item_selecionado2, "values")

        cod_bo = valores2[0]
        op_bo = valores2[1]

        itens_bo = listar_itens_SAREM(cod_bo, op_bo)

        for i, label_txt in enumerate(labels):
            label = tb.Label(frame_itensBo, text=label_txt)
            label.grid(row=0, column=i, sticky="w", padx=5, pady=2)
            frame_itensBo.grid_columnconfigure(i, weight=1)

        # Para guardar os widgets de motivo
        self.entries_motivo_itens = []

        # Linhas dos itens
        motivos_opcoes = obter_motivos()
        if motivos_opcoes and itens_bo:
            for idx, (cod, desc, linha, motivo) in enumerate(itens_bo):
                tb.Label(frame_itensBo, text=cod).grid(row=idx+1, column=0, padx=5, pady=2)
                tb.Label(frame_itensBo, text=desc, wraplength=self.wraplength_valor, justify="left", anchor="w").grid(row=idx+1, column=1, padx=5, pady=2)
                tb.Label(frame_itensBo, text=linha).grid(row=idx+1, column=2, padx=5, pady=2)
                entry_motivo = tb.Combobox(frame_itensBo, values=motivos_opcoes, width=25)
                entry_motivo.set(motivo if motivo else "")
                entry_motivo.grid(row=idx+1, column=3, padx=5, pady=2)
                self.entries_motivo_itens.append((cod, entry_motivo))

    def opcoes_editor(self, parent):
        frame = tb.LabelFrame(parent, text="Opções", padding=10)
        frame.pack(side="bottom", fill="x", padx=10, pady=10)

        tb.Button(frame, text="Salvar", command=self.salvar).pack(side="left", padx=5)
        tb.Button(frame, text="Cancelar", command=self.cancelar).pack(side="left", padx=5)

    def salvar(self):
        dados_bo = [
            self.entries["tipo_ocorrencia"].get(),
            self.entries["descricao"].get("1.0", tk.END).strip(),
            self.entries["setor_responsavel"].get(),
            self.entries["frete"].get()
        ]
        print("Dados da BO: ", dados_bo)

        dados_itens = [
            (entry_motivo.get(), self.bo_number, cod) for cod, entry_motivo in self.entries_motivo_itens
        ]

        atualizar_bo(self.bo_number, dados_bo, dados_itens, self.user)
        self.root.destroy()

    def cancelar(self):
        self.root.destroy()