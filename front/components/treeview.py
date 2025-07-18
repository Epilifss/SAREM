import ttkbootstrap as tb
import tkinter as tk

def on_double_click(self, callback):
    def wrapper():
        selected = self.tree.selection()
        if selected:
            callback()
    return wrapper
        
def on_click(event, tree):
    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        tree.selection_remove(tree.selection())

class listagemTreeview:
    def __init__(self, parent, columns, show="headings", on_double_click=None):
        self.tree = tb.Treeview(parent, columns=columns, show=show)
        for col in columns:
            self.tree.heading(col, text=col.upper())
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.tree.bind("<Button-1>", lambda event: on_click(event, self.tree))

        if on_double_click:
            self.tree.bind("<Double-1>", lambda event: on_double_click(parent, self.tree))