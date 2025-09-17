import tkinter as tk
import ttkbootstrap as tb
import webview
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from back.utils import resource_path, center_window

class EstatisticasView:
    def __init__(self, parent):
        self.root = tb.Toplevel(parent)
        self.root.title("estatísticas")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.state("zoomed")
        self.root.transient(parent)

        self.presenter = None
        self.webview_window = None

        main_frame = tb.Frame(self.root, padding=10)
        main_frame.pack(fill=tb.BOTH, expand=True)

        header = tb.Frame(main_frame)
        header.pack(fill=tb.X, pady=(0, 10))

        tb.Label(header, text='Ano').pack(side=tb.LEFT, padx=(0, 5))
        self.combo_anos = tb.Combobox(header, state="readonly")
        self.combo_anos.pack(side=tb.LEFT)
        self.combo_anos.set("Todos")

        self.content_frame = tb.Frame(main_frame, bootstyle="light") # type: ignore
        self.content_frame.pack(fill=tb.BOTH, expand=True)

        self.mensagem_label = tb.Label(self.content_frame, font=("Arial", 12), justify=tb.CENTER)

        center_window(self.root)
        self.root.focus_set()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_presenter(self, presenter):
        self.presenter = presenter
        self.combo_anos.bind("<<ComboboxSelected>>", self.presenter.handle_ano_selecionado)

    def set_anos_disponiveis(self, anos):
        self.combo_anos['values'] = anos
        if "Todos" in anos:
            self.combo_anos.set("Todos")
        elif anos:
            self.combo_anos.set(anos[0])
        
    def mostrar_grafico_seaborn(self, df, ano):
        self.mensagem_label.pack_forget()

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df, x='Setor', y='Contagem', ax=ax)

        ax.set_title(f"Contagem de BO's por setor ({ano})", fontsize=14)
        ax.set_xlabel("Setor Responsável")
        ax.set_ylabel("Número de BO's")
        ax.tick_params(axis='x', rotation=0)

        for i, row in df.iterrows():
            ax.text(
                i,
                row['Contagem'] + 0.5,
                str(row['Contagem']),
                ha='center', va='bottom', fontsize=10
            )

        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        plt.close(fig)

    def mostrar_mensagem(self, mensagem):
        if self.webview_window:
            self.webview_window.destroy()
            self.webview_window = None

        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.mensagem_label = tb.Label(self.content_frame, font=("Arial", 12), justify=tk.CENTER, text=mensagem)
        self.mensagem_label.pack(pady=20, expand=True)

    def on_close(self):
        if self.webview_window:
            self.webview_window.destroy()
        self.root.destroy()