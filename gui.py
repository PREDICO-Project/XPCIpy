import tkinter as tk
import sys
from GUI.ui.styles import Styles as stl
from GUI.pages.PCSim_gui import PCSim_gui
from GUI.utils import resource_path
from GUI.pages.loading_window import LoadingScreen
from tkinterdnd2  import TkinterDnD
from GUI.__init__ import __version__

def create_main_menu():

    #root = tk.Tk()
    root = TkinterDnD.Tk()
    root.withdraw()

    root.title("XPCIpy Environment - v"+__version__)
    logo_ico = resource_path("GUI/assets/logo.ico")
    try:
        root.iconbitmap(logo_ico)
    except Exception:
        pass

    stl.configure_style()

    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_columnconfigure(0, weight=1)

    def show_main_gui():
        PCSim_gui(root)

        root.deiconify()

        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        root.minsize(w, h)

        try:
            root.state('zoomed')
        except tk.TclError:
            pass


    LoadingScreen(root, duration=1800)
    root.after(1800, show_main_gui)

    def on_close():
        root.quit()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()


if __name__ == "__main__":
    create_main_menu()
