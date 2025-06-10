from funcoes import *
from database import garantir_config_ini

def mostrar_splash(root):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x200")
    splash.configure(bg="white")

    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - 200
    y = (splash.winfo_screenheight() // 2) - 100
    splash.geometry(f"+{x}+{y}")

    try:
        img = Image.open(resource_path('SAREM PNG.png'))
        img = img.resize((300, 100), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label_img = tk.Label(splash, image=photo, bg="white")
        label_img.image = photo
        label_img.pack(pady=(30, 10))
    except Exception:
        tk.Label(splash, text="SAREM", font=("Arial", 24), bg="white").pack(pady=(60, 10))

    tk.Label(splash, text="Powered by Epilifss", font=("Arial", 12), bg="white").pack()

    return splash

garantir_config_ini()

root = tk.Tk()
root.overrideredirect(True)
root.geometry('0x0+0+0')

splash = mostrar_splash(root)
root.update()

root.after(3000, splash.destroy)

root.after(3050, lambda: iniciar_app(root))

def iniciar_app(root):
    deve_continuar = verificar_e_att(root)
    if deve_continuar:
        login_window = LoginWindow(root)
        root.after(100, login_window.root.focus_force)
        root.after(100, login_window.username.focus_force)
        root.mainloop()

root.mainloop()