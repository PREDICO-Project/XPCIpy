'''
Script to run the Graphical User Interface (GUI)
'''

import tkinter as tk
from GUI.pages.PCSim_gui import PCSim_gui
from GUI.ui.styles import Styles as stl
from GUI.utils import resource_path
import sys

def create_main_menu():

    root = tk.Tk()
    root.title("XPCIpy Environment")

    logo_ico = resource_path("GUI/assets/logo.ico")
    root.iconbitmap(logo_ico)
    # Style
    stl.configure_style()
    
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0) # status bar
    root.grid_columnconfigure(0, weight=1)


    PCSim_gui(root)
    
    def on_close():
        root.quit()
        root.destroy()
        sys.exit(0)
        
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    root.minsize(w, h) 

    root.protocol("WM_DELETE_WINDOW", on_close)

    try:
        root.state('zoomed') # works on Windows
    except tk.TclError:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    create_main_menu()