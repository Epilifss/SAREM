import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox, filedialog
from datetime import datetime
from back.utils import resource_path
from front.components.treeview import listagemTreeview
from front.presenters.report_presenter import ReportPresenter
from theme import estilizar_treeview

class ReportView():
    def __init__(self, parent, caller_id=None):
        self.parent = parent
        self.root = tk.Toplevel(parent)
        self.root.title("Gerar Relatório")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.state('zoomed')
        self.root.transient(parent)

        self.ultimo_modulo = caller_id

        self.presenter = ReportPresenter(self)
        
        frame_param = tb.Frame(self.root)
        frame_param.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Cliente
        client_frame = tb.Frame(frame_param)
        client_frame.pack(side=tk.LEFT, fill=tk.X, pady=5)
        
        tk.Label(client_frame, text="Cliente:").pack(side=tk.LEFT, padx=5)
        self.clientes_cbmx = tb.Combobox(client_frame, state="readonly")
        self.clientes_cbmx.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.clientes_cbmx.set("Todos")

        # Setor
        sector_frame = tb.Frame(frame_param)
        sector_frame.pack(side=tk.LEFT, fill=tk.X, pady=5)
        
        tk.Label(sector_frame, text="Setor:").pack(side=tk.LEFT, padx=5)
        self.setores_cbmx = tb.Combobox(sector_frame, state="readonly")
        self.setores_cbmx.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.setores_cbmx.set("Todos")

        # Periodo
        periodo_frame = tb.Frame(frame_param)
        periodo_frame.pack(side=tk.LEFT, fill=tk.X, pady=5)

        hoje = datetime.today()
        primeiro_dia_mes = hoje.replace(day=1)

        tk.Label(periodo_frame, text="Período:").pack(side=tk.LEFT, padx=5)
        tk.Label(periodo_frame, text="De").pack(side=tk.LEFT, padx=(5, 2))
        self.data_inicio_entry = tb.DateEntry(
            periodo_frame,
            dateformat="%d/%m/%Y",
            startdate=primeiro_dia_mes,
            width=12,
        )
        self.data_inicio_entry.pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(periodo_frame, text="Até").pack(side=tk.LEFT, padx=(0, 2))
        self.data_fim_entry = tb.DateEntry(
            periodo_frame,
            dateformat="%d/%m/%Y",
            startdate=hoje,
            width=12,
        )
        self.data_fim_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Status
        status_frame = tb.Frame(frame_param)
        status_frame.pack(side=tk.LEFT, fill=tk.X, pady=5)

        tk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_cbmx = tb.Combobox(status_frame, state="readonly")
        self.status_cbmx.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.status_cbmx.set("Todos")

        # Botão
        btn_frame = tb.Frame(frame_param)
        btn_frame.pack(side=tk.LEFT, fill=tk.X,pady=5)

        tb.Button(btn_frame, text="Gerar Relatório", command=lambda: self.presenter.on_generate_report_click()).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Treeview
        self.treeview_component = listagemTreeview(
            self.root,
            columns=["BO", "OP", "CLIENTE", "TIPO DE OCORRÊNCIA", "SETOR RESPONSÁVEL", "STATUS", "DATA DE REGISTRO", "PRODUTOS / MOTIVOS"],
            show="headings"
        )
        self.treeview_component.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=(5, 15))
        self._configurar_colunas_relatorio()

        # Opções
        opt_frame = tb.Frame(self.root)
        opt_frame.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=(5, 60))

        # Botões de Exportação
        tb.Button(opt_frame, text="Imprimir", command=self.on_print).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tb.Button(opt_frame, text="Salvar PDF", command=self.on_export_pdf).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tb.Button(opt_frame, text="Salvar Excel", command=self.on_export_excel).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.presenter.initialize_view(self.ultimo_modulo)
    
    def on_export_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.presenter.on_export_pdf(file_path)

    def on_export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.presenter.on_export_excel(file_path)

    def on_print(self):
        self.presenter.on_print_report()

    def get_selected_client(self):
        return self.clientes_cbmx.get()
    
    def get_selected_sector(self):
        return self.setores_cbmx.get()

    def get_selected_start_date(self):
        return self.data_inicio_entry.get_date().date()

    def get_selected_end_date(self):
        return self.data_fim_entry.get_date().date()

    def get_selected_status(self):
        return self.status_cbmx.get()

    def get_modulo(self):
        return self.ultimo_modulo
    
    def set_clients_options(self, options):
        self.clientes_cbmx['values'] = options
        if "Todos" in options:
            self.clientes_cbmx.set("Todos")
        elif options:
            self.clientes_cbmx.set(options[0])

    def set_sectors_options(self, options):
        self.setores_cbmx['values'] = options
        if "Todos" in options:
            self.setores_cbmx.set("Todos")
        elif options:
            self.setores_cbmx.set(options[0])

    def set_status_options(self, options):
        self.status_cbmx['values'] = options
        if "Todos" in options:
            self.status_cbmx.set("Todos")
        elif options:
            self.status_cbmx.set(options[0])

    def display_report_data(self, data):
        tree = self.treeview_component.tree
        tree.delete(*tree.get_children())
        for row in data:
            bo = str(row[0]).strip() if row[0] is not None else ""
            op = str(row[1]).strip() if row[1] is not None else ""
            cliente = str(row[2]).strip() if row[2] is not None else ""
            tipo_ocorrencia = str(row[3]).strip() if row[3] is not None else ""
            setor_responsavel = str(row[4]).strip() if row[4] is not None else ""
            status = str(row[5]).strip() if row[5] is not None else ""
            produtos_motivos = str(row[7]).strip() if row[7] is not None else ""
            if row[6] is not None:
                try:
                    data_registro = row[6].strftime("%d/%m/%Y")
                except AttributeError:
                    data_registro = str(row[6]).strip()
            else:
                data_registro = ""

            tree.insert(
                "",
                "end",
                values=(bo, op, cliente, tipo_ocorrencia, setor_responsavel, status, data_registro, produtos_motivos)
            )
        estilizar_treeview(tree)
        self._configurar_colunas_relatorio()

    def _configurar_colunas_relatorio(self):
        tree = self.treeview_component.tree
        colunas_fixas = {
            "BO": 80,
            "OP": 80,
            "CLIENTE": 150,
            "TIPO DE OCORRÊNCIA": 150,
            "SETOR RESPONSÁVEL": 150,
            "STATUS": 110,
            "DATA DE REGISTRO": 130,
        }

        for coluna, largura in colunas_fixas.items():
            tree.column(coluna, width=largura, minwidth=largura, stretch=False, anchor=tk.W)

        tree.column("PRODUTOS / MOTIVOS", width=900, minwidth=320, stretch=True, anchor=tk.W)

    def get_report_table_data(self):
        tree = self.treeview_component.tree
        headers = [tree.heading(col, "text") for col in tree["columns"]]
        data = []
        for item in tree.get_children():
            values = list(tree.item(item, "values"))
            data.append(values)
        return headers, data

    def show_error(self, mensagem):
        messagebox.showerror("Erro", mensagem)

    def show_message(self, mensagem):
        messagebox.showinfo("Informação", mensagem)