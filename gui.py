'''
Script to run the Graphical User Interface (GUI)
'''

import tkinter as tk
from GUI.PCSim_gui import PCSim_gui
from GUI.styles import Styles as stl

def create_main_menu():

    root = tk.Tk()
    root.title("Talbot Lau Environment")
    
    # Style
    stl.configure_style()
    
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0) # status bar
    root.grid_columnconfigure(0, weight=1)


    PCSim_gui(root)
    
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    root.minsize(w, h) 

    root.protocol("WM_DELETE_WINDOW", root.destroy)

    try:
        root.state('zoomed') # works on Windows
    except tk.TclError:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    create_main_menu()