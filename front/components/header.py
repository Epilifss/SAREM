from tkinter import messagebox
import pyodbc
import ttkbootstrap as tb
import tkinter as tk
from back.database import create_connection
from theme import estilizar_treeview, ajustar_largura_colunas

class Header:
    def __init__(self, parent, user, caller_id=None, tree=None, refresh_callback=None):
        self.user = user
        self.parent = parent

        self.ultimo_modulo = caller_id
        self.tree = tree

        header = tb.Frame(self.parent)
        header.pack(fill=tk.X)

        tb.Button(header, text="Embarcados", command=self.abrir_embarcados).pack(side=tk.LEFT)
        tb.Button(header, text="Estatísticas", command=self.abrir_estatisticas).pack(side=tk.LEFT)
        tb.Button(header, text="Gerar Relatório", command=self.abrir_relatorios).pack(side=tk.LEFT)
        # tb.Button(header, text="Gerar Nova BO", command=self.abrir_gerar_bo).pack(side=tk.LEFT)
        tb.Button(header, text="Atualizar", command=lambda: refresh_callback() if refresh_callback else None).pack(side=tk.LEFT)
        tb.Button(header, text="Acompanhar uma BO", command=lambda: self.abrir_buscar_bo(refresh_callback)).pack(side=tk.LEFT)
        if self._has_multiple_modules():
            tb.Button(header, text="Trocar Módulo", command=self.trocar_modulo).pack(side=tk.RIGHT, padx=5)
        tb.Button(header, text="Logoff", command=self.logoff, style="custom.TButton").pack(side=tk.RIGHT, padx=5)

    def _allowed_modules(self):
        if hasattr(self.user, "get_allowed_modules"):
            return self.user.get_allowed_modules()
        return []

    def _has_multiple_modules(self):
        if hasattr(self.user, "has_multiple_modules"):
            return self.user.has_multiple_modules()
        return False

    def _normalize_module_name(self, module_name):
        if module_name == "Exportacao":
            return "Exportação"
        return module_name

    def abrir_embarcados(self):
        from funcoes import Embarcados
        janela = Embarcados(self.parent, self.user, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_estatisticas(self):
        from front.presenters.estatisticas_presenter import EstatisticasPresenter
        presenter = EstatisticasPresenter(self.parent, caller_id=self.ultimo_modulo)
        presenter.iniciar()
        self.parent.wait_window(presenter.view.root)

    def abrir_relatorios(self):
        from front.windows.report import ReportView
        janela = ReportView(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_gerar_bo(self):
        from funcoes import gerarBO
        janela = gerarBO(self.parent, caller_id=self.ultimo_modulo)
        self.parent.wait_window(janela.root)

    def abrir_buscar_bo(self, refresh_callback=None):
        from front.windows.buscar_bo import BuscarBOView
        janela = BuscarBOView(self.parent, caller_id=self.ultimo_modulo, user=self.user, refresh_callback=refresh_callback)
        self.parent.wait_window(janela.root)

    def carregar_bos(self):
        conn = create_connection()
        if conn is None:
            return

        cursor = None
        try:
            cursor = conn.cursor()
            query = ("SELECT bo_number, op, status, tipo_ocorrencia, setor_responsavel, loja FROM bo_records WHERE status NOT LIKE 'Embarcado' AND modulo LIKE ? AND D_E_L_E_T_ <> '*'")
            cursor.execute(query, self.ultimo_modulo)
            rows = cursor.fetchall()

            # Remove todos os itens atuais da Treeview
            if self.tree is not None:
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Insere os dados "limpos" na Treeview
                for row in rows:
                    # Converte cada valor para string (se não for None) e aplica strip para remover caracteres indesejados.
                    bo = str(row[0]).strip("(' ,)") if row[0] is not None else ""
                    op = str(row[1]).strip("(' ,)") if row[1] is not None else ""
                    status = str(row[2]).strip("(' ,)") if row[2] is not None else ""
                    tipo_ocorrencia = str(row[3]).strip("(' ,)") if row[3] is not None else ""
                    setor_responsavel = str(row[4]).strip("(' ,)") if row[4] is not None else ""
                    loja = str(row[5]).strip("(' ,)") if row[5] is not None else ""

                    self.tree.insert("", tk.END, values=(
                        bo, op, status, tipo_ocorrencia, setor_responsavel, loja))
                    
                estilizar_treeview(self.tree)
                ajustar_largura_colunas(self.tree)
        except pyodbc.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar BOs: {e}")
        finally:
            if conn:
                conn.close()
            if cursor:
                cursor.close()

    def logoff(self):
        root_principal = self.parent.master
        self.parent.destroy()
        from front.windows.login_window import LoginWindow
        from back.bo_monitor import monitorar_bo_event
        monitorar_bo_event.set()
        login = LoginWindow(root_principal)
        login.root.after(100, login.root.focus_force)
        login.root.after(100, login.username.focus_force)

    def trocar_modulo(self):
        from front.components.dialogs import chooseModuleDialog
        from front.windows.corporativo_view import CorporativoModule
        from front.windows.varejo_view import VarejoModule
        from front.windows.exportacao_view import ExportacaoModule

        allowed_modules = self._allowed_modules()
        if len(allowed_modules) <= 1:
            return

        dialog = chooseModuleDialog(self.parent, "", "", self.user, allowed_modules=allowed_modules)
        chosen_module_type, _, _ = dialog.get_chosen_module()

        if not chosen_module_type:
            return

        current_module = self._normalize_module_name(self.ultimo_modulo)
        if chosen_module_type == current_module:
            return

        root_principal = self.parent.master
        self.parent.destroy()

        if chosen_module_type == "Corporativo":
            CorporativoModule(self.user, root_principal)
        elif chosen_module_type == "Varejo":
            VarejoModule(self.user, root_principal)
        elif chosen_module_type == "Exportação":
            ExportacaoModule(self.user, root_principal)
        

    def buscar_bo(self):
        from funcoes import buscarBo
        obj = buscarBo(parent=self.parent, caller_id=self.ultimo_modulo)
        resultado = obj.identificar_chamador()
        print(resultado)