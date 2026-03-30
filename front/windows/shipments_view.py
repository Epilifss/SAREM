import tkinter as tk
import ttkbootstrap as tb
from back.utils import resource_path

class ShipmentsView:
    def __init__(self, parent) -> None:
        self.root = tb.Toplevel(parent)
        self.root.title("Embarcados")
        self.root.iconbitmap(resource_path('SAREM.ico'))
        self.root.state("zoomed")
        self.root.transient(parent)
        