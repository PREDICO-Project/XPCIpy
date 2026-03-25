import tkinter as tk
from GUI.utils import resource_path
from GUI.__init__ import __version__

class LoadingScreen(tk.Toplevel):
    def __init__(self, master, duration=1500, on_finish=None):
        super().__init__(master)

        self._on_finish = on_finish
        self._finished = False
        self._after_id = None

        self.overrideredirect(True)
        self.config(bg="#4E95D9")
        
        container = tk.Frame(self, bg="#4E95D9")
        container.grid(row=0, column=0, sticky="nsew")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        container.grid_columnconfigure(0, weight=1)
        #4E95D9 # Blue
        #222222 # Gray

        try:
            from PIL import Image, ImageTk
            logo_path = resource_path("GUI/assets/logo.png")
            img = Image.open(logo_path).resize((400, 400))
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(container, image=self.logo, bg="#4E95D9").grid(row=0, column=0, pady=(20,10))
        except Exception:
            tk.Label(container, text="XPCIpy", fg="white", bg="#4E95D9",
                     font=("Arial", 32, "bold")).grid(row=0, column=0, pady=(20,10))

        tk.Label(container, text="Loading XPCIpy…", fg="white", bg="#4E95D9",
                 font=("Arial", 12)).grid(row=1, column=0)
        
        tk.Label(container, text= f"v.{__version__}", fg="white", bg="#4E95D9",
                 font=("Arial", 10)).grid(row=2, column=0, pady=(10,20))

        self.update_idletasks()
        w, h = 500, 500
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Allow users to skip the splash quickly via click or key press.
        self.bind("<Button-1>", self._finish)
        self.bind("<Key>", self._finish)
        self.focus_force()

        self._after_id = self.after(duration, self._finish)

    def _finish(self, _event=None):
        if self._finished:
            return
        self._finished = True

        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

        if callable(self._on_finish):
            self._on_finish()

        if self.winfo_exists():
            self.destroy()