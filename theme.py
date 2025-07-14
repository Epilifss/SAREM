import ttkbootstrap as tb

def temas():
    style = tb.Style()
    style.configure('TButton', background='#24577f', foreground='white', borderwidth=0)
    style.configure('custom.TButton', background="#7f2424", foreground='white', borderwidth=0)
    style.map('TButton', background=[('active', "#3175aa"), ('focus', '#24577f')])

def estilizar_treeview(tree):
    import ttkbootstrap as tb
    style = tb.Style()

    # Cor do cabeçalho
    style.configure("Treeview.Heading", background="#24577f", foreground="white", font=('Arial', 9, 'bold'))

    # Linhas zebra
    tree.tag_configure('oddrow', background='#F2F2F2')
    tree.tag_configure('evenrow', background='#E0E0E0')

    # Aplicar tags zebra
    for i, item in enumerate(tree.get_children()):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        tree.item(item, tags=(tag,))

def ajustar_largura_colunas(tree):
    for col in tree["columns"]:
        max_width = max(
            [len(str(tree.set(k, col))) for k in tree.get_children()] + [len(col)]
        )
        tree.column(col, width=(max_width * 10 + 30))  # Ajuste o multiplicador conforme necessário