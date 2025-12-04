import tkinter as tk
from tkinter import ttk

class HelpWindow:
    
    def __init__(self, master):
        self.master = master
        self.build_window()

    def build_window(self):
        self.win = tk.Toplevel(self.master)
        self.win.title("XPCIpy - Help / User Guide")
        self.win.geometry("800x600")

        notebook = ttk.Notebook(self.win)
        notebook.pack(fill="both", expand=True)

        self.tab_sim = ttk.Frame(notebook)
        self.tab_rec = ttk.Frame(notebook)
        self.tab_about = ttk.Frame(notebook)
        self.tab_license = ttk.Frame(notebook)
        

        notebook.add(self.tab_sim, text="Simulation Guide")
        notebook.add(self.tab_rec, text="Reconstruction Guide")
        notebook.add(self.tab_about, text="About")

        # Fill content
        self._populate_simulation_guide()
        self._populate_reconstruction_guide()
        self._populate_about_tab()
  
    def _make_text_widget(self, parent):
        text = tk.Text(parent, wrap="word", bg="#222222", fg="white")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        text.tag_configure("title", font=("Arial", 14, "bold"), foreground="#ffd966")
        text.tag_configure("subtitle", font=("Arial", 12, "bold"), foreground="#ffffff")
        text.tag_configure("bullet", lmargin1=25, lmargin2=40)

        return text

    def _populate_simulation_guide(self):
        text = self._make_text_widget(self.tab_sim)

        text.insert("end", "Simulation Modules\n", "title")

        text.insert("end", "\nInline Simulation\n", "subtitle")
        text.insert("end",
            "This module simulates propagation-based (inline) phase-contrast imaging.\n"
            "This simulation follows the Fresnel formalism.\n"
            "Main parameters:\n"
        )
        text.insert("end", " - n: Grid size.\n", "bullet")
        text.insert("end", " - Grid Pixel size (µm).\n", "bullet")
        text.insert("end", " - DSO / DOD distances (cm).\n", "bullet")
        text.insert("end", " - Source FWHM.\n", "bullet")
        text.insert("end", " - Beam Spectrum (monochromatic / polychromatic).\n", "bullet")
        text.insert("end", " - Object selection.\n", "bullet")
        text.insert("end", " - Detector parameters (pixel size, resolution).\n", "bullet")

        text.insert("end", "\nTalbot-Lau Simulation\n", "subtitle")
        text.insert("end",
            "Simulates a Talbot-Lau interferometer with G1 and G2 gratings.\n"
            "It simulates the phase stepping method to generate the object and reference image stacks.\n"
            "Parameters include:\n"
        )
        text.insert("end", " - Design energy.\n", "bullet")
        text.insert("end", " - G1 period and phase (π, π/2).\n", "bullet")
        text.insert("end", " - Number of phase steps.\n", "bullet")
        text.insert("end", " - Step size (in µm).\n", "bullet")
        text.insert("end", " - Source parameters (FWHM, Spectra).\n", "bullet")
        text.insert("end", " - Object selection.\n", "bullet")
        text.insert("end", " - Detector parameters (pixel size, resolution).\n", "bullet")

        text.insert("end", "\nCheck Talbot Effect\n", "subtitle")
        text.insert("end",
            "Visualizes the Talbot carpet for different gratings configuration.\n"
        )

        text.config(state="disabled")

    def _populate_reconstruction_guide(self):
        text = self._make_text_widget(self.tab_rec)

        text.insert("end", "Reconstruction (TLRec)\n", "title")
        text.insert("end", "\nWorkflow:\n", "subtitle")

        text.insert("end", " - Load reference stack.\n", "bullet")
        text.insert("end", " - Load object stack.\n", "bullet")
        text.insert("end", " - Choose algorithm (FFT, Fast FFT, Least Squares...)\n", "bullet")
        text.insert("end", " - Retrieve DPC, Phase, Transmission, Dark Field.\n", "bullet")

        text.insert("end", "\nInteractive Tools\n", "subtitle")
        text.insert("end",
            " - Click images to inspect modulation curve at a pixel.\n", "bullet"
        )
        text.insert("end",
            " - Window/Level adjustment per reconstructed image.\n", "bullet"
        )

        text.config(state="disabled")

    def _populate_about_tab(self):
        text = self._make_text_widget(self.tab_about)

        text.insert("end", "About XPCIpy GUI\n", "title")
        text.insert("end",
            "\nXPCIpy is a toolkit for X-ray phase-contrast imaging simulations "
            "and reconstruction.\n"
            "You may found more information at: https://doi.org/10.1364/OE.573918\n"
        )

        text.insert("end", "\nModules\n", "subtitle")
        text.insert("end",
            " PCSim: inline + Talbot-Lau simulations\n"
            " TLRec: phase retrieval with multiple algorithms\n"
        )

        text.insert("end", "\nAuthor\n", "subtitle")
        text.insert("end", "  Víctor Sánchez Lara\n")
        text.insert("end", "  Email: vicsan05@ucm.es\n")
    
        text.insert("end", "\nProject\n", "subtitle")
        text.insert("end", " This work is englobed in the PREDICO project, funded by the Spanish Ministry of Science and Innovation (PID2021-123390OB-C22).\n")

        text.config(state="disabled")
        
