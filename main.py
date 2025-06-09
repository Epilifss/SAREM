from funcoes import *
from database import garantir_config_ini

garantir_config_ini()

root = tk.Tk()
root.overrideredirect(True)
root.geometry('0x0+0+0')


deve_continuar = verificar_e_att(root)
if deve_continuar:
    login_window = LoginWindow(root)
    root.after(100, login_window.root.focus_force)
    root.after(100, login_window.username.focus_force)
    root.mainloop()