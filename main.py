from funcoes import *
from database import garantir_config_ini

garantir_config_ini()

root = tk.Tk()
root.overrideredirect(True)
root.geometry('0x0+0+0')


deve_continuar = verificar_e_att(root)
if deve_continuar:
    LoginWindow(root)
    root.mainloop()