import tkinter as tk
import ttkbootstrap as tb
from back.utils import center_window, limitar_janela_tela, resource_path


class ChangelogWindow:
    def __init__(self, parent, versao_atual, changelog_data):
        self.root = tk.Toplevel(parent)
        self.root.title("Novidades da versao")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.transient(parent)
        self.root.grab_set()
        self.root.focus_set()

        self._build_ui(versao_atual, changelog_data)

        self.root.update_idletasks()
        limitar_janela_tela(self.root, width_ratio=0.65, height_ratio=0.8)
        center_window(self.root)
        self.root.wait_window()

    def _build_ui(self, versao_atual, changelog_data):
        container = tb.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        tb.Label(container, text=f"Novidades da versao {versao_atual}", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 8))
        tb.Label(container, text=changelog_data.get("titulo", "Atualizacoes"), font=("Arial", 11)).pack(anchor="w", pady=(0, 10))

        # Area rolavel apenas para o conteudo das novidades.
        content_area = tb.Frame(container)
        content_area.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(content_area, highlightthickness=0)
        scrollbar = tb.Scrollbar(content_area, orient="vertical", command=canvas.yview)
        body = tb.Frame(canvas)

        self.canvas = canvas

        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._section(body, "Novas funcionalidades", changelog_data.get("novidades", []))
        self._section(body, "Correcoes", changelog_data.get("correcoes", []))
        self._section(body, "Melhorias", changelog_data.get("melhorias", []))

        self._bind_mousewheel(canvas, body)

        # Rodape fixo: nao faz parte da area de scroll.
        footer = tb.Frame(container)
        footer.pack(fill=tk.X, pady=(12, 0), side=tk.BOTTOM)
        tb.Button(footer, text="Continuar", command=self.root.destroy).pack(side=tk.RIGHT)

    def _bind_mousewheel(self, canvas, body):
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-event.delta / 120), "units")
            elif getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")

        def _bind_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_recursive(child)

        for widget in (canvas, body):
            _bind_recursive(widget)

    def _section(self, parent, title, items):
        frame = tb.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill=tk.X, pady=(0, 8))

        if not items:
            tb.Label(frame, text="- Sem itens nesta secao.", justify="left").pack(anchor="w")
            return

        for item in items:
            tb.Label(frame, text=f"- {item}", justify="left", wraplength=760, anchor="w").pack(fill=tk.X, anchor="w", pady=1)
