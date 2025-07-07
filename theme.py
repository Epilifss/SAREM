import ttkbootstrap as tb

def temas():
    style = tb.Style()
    style.configure('TButton', background='#24577f', foreground='white', borderwidth=0)
    style.map('TButton', background=[('active', "#3175aa"), ('focus', '#24577f')])