from back.report_service import (
    generate_report, get_all_clients, get_all_setores, get_all_status,
    export_to_pdf, export_to_excel, print_report
)

class ReportPresenter:
    def __init__(self, view):
        self.view = view

    def initialize_view(self, ultimo_modulo):
        try:
            clients = get_all_clients(ultimo_modulo=ultimo_modulo)
            self.view.set_clients_options(clients)
            sectors = get_all_setores(ultimo_modulo=ultimo_modulo)
            self.view.set_sectors_options(sectors)
            status_options = get_all_status(ultimo_modulo=ultimo_modulo)
            self.view.set_status_options(status_options)
        except Exception as e:
            self.view.show_error(f"Erro ao inicializar filtros: {str(e)}")

    def on_generate_report_click(self):
        try:
            modulo = self.view.get_modulo()
            cliente = self.view.get_selected_client()
            setor = self.view.get_selected_sector()
            data_inicio = self.view.get_selected_start_date()
            data_fim = self.view.get_selected_end_date()
            status = self.view.get_selected_status()

            if data_inicio > data_fim:
                self.view.show_error("A data inicial não pode ser maior que a data final.")
                return

            report_data = generate_report(modulo, cliente, setor, data_inicio, data_fim, status)
            self.view.display_report_data(report_data)
        except Exception as e:
            self.view.show_error(f"Erro ao gerar o relatório: {str(e)}")

    def on_export_pdf(self, file_path):
        try:
            headers, data = self.view.get_report_table_data()
            export_to_pdf(data, headers, file_path)
            self.view.show_message(f"PDF exportado para {file_path}")
        except Exception as e:
            self.view.show_error(f"Erro ao exportar PDF: {str(e)}")

    def on_export_excel(self, file_path):
        try:
            headers, data = self.view.get_report_table_data()
            export_to_excel(data, headers, file_path)
            self.view.show_message(f"Excel exportado para {file_path}")
        except Exception as e:
            self.view.show_error(f"Erro ao exportar Excel: {str(e)}")

    def on_print_report(self, file_path):
        try:
            headers, data = self.view.get_report_table_data()
            print_report(data, headers, file_path)
            self.view.show_message("Relatório enviado para impressão!")
        except Exception as e:
            self.view.show_error(f"Erro ao imprimir: {str(e)}")