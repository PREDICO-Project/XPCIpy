import tkinter as tk
from GUI.utils import resource_path
from GUI.__init__ import __version__

class LoadingScreen(tk.Toplevel):
    def __init__(self, master, duration=1500):
        super().__init__(master)

        self.overrideredirect(True)
        self.config(bg="#222222")

        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("GUI/assets/logo.png")
            img = Image.open(logo_path).resize((260, 260))
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(self, image=self.logo, bg="#222222").pack(pady=10)
        except Exception:
            tk.Label(self, text="XPCIpy", fg="white", bg="#222222",
                     font=("Arial", 32, "bold")).pack(pady=20)

        tk.Label(self, text="Loading XPCIpy…", fg="white", bg="#222222",
                 font=("Arial", 12)).pack()
        
        tk.Label(self, text= f"v.{__version__}", fg="white", bg="#222222",
                 font=("Arial", 10)).pack(pady=(0, 10))

        self.update_idletasks()
        w, h = 300, 330
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.after(duration, self.destroy)