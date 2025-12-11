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
        self.tab_rec_batch = ttk.Frame(notebook)
        self.tab_about = ttk.Frame(notebook)
        self.tab_license = ttk.Frame(notebook)
        

        notebook.add(self.tab_sim, text="Simulation Guide")
        notebook.add(self.tab_rec, text="Reconstruction Guide")
        notebook.add(self.tab_rec_batch, text="Batch Reconstruction Guide")
        notebook.add(self.tab_about, text="About")

        # Fill content
        self._populate_simulation_guide()
        self._populate_reconstruction_guide()
        self._populate_reconstruction_batch()
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
        text.insert("end", "This module simulates propagation-based (inline) phase-contrast imaging.\n"
            "This simulation follows the Fresnel formalism.\n"
            "Main parameters:\n")
        
        text.insert("end", " - n: Grid size.\n", "bullet")
        text.insert("end", " - Grid Pixel size (µm).\n", "bullet")
        text.insert("end", " - DSO / DOD distances (cm).\n", "bullet")
        text.insert("end", " - Source FWHM.\n", "bullet")
        text.insert("end", " - Beam Spectrum (monochromatic / polychromatic).\n", "bullet")
        text.insert("end", " - Object selection.\n", "bullet")
        text.insert("end", " - Detector parameters (pixel size, resolution).\n", "bullet")

        text.insert("end", "\nTalbot-Lau Simulation\n", "subtitle")
        text.insert("end", "Simulates a Talbot-Lau interferometer with G1 and G2 gratings.\n"
            "It simulates the phase stepping method to generate the object and reference image stacks.\n"
            "Parameters include:\n")
        
        text.insert("end", " - Design energy.\n", "bullet")
        text.insert("end", " - G1 period and phase (π, π/2).\n", "bullet")
        text.insert("end", " - Number of phase steps.\n", "bullet")
        text.insert("end", " - Step size (in µm).\n", "bullet")
        text.insert("end", " - Source parameters (FWHM, Spectra).\n", "bullet")
        text.insert("end", " - Object selection.\n", "bullet")
        text.insert("end", " - Detector parameters (pixel size, resolution).\n", "bullet")

        text.insert("end", "\nCheck Talbot Effect\n", "subtitle")
        text.insert("end", "Visualizes the Talbot carpet for different gratings configuration.\n")

        text.config(state="disabled")

    def _populate_reconstruction_guide(self):
        text = self._make_text_widget(self.tab_rec)

        text.insert("end", "Talbot Lau Reconstruction (TLRec)\n", "title")

        text.insert("end", "\nPhase Stepping Retrieval Workflow\n", "subtitle")
        text.insert("end","The reconstruction process uses the image stacks obtained via phase stepping to fit the intensity-phase curve at each pixel, extracting the object parameters.\n")
        text.insert("end", " - Load Image Stacks (Reference and Object). Make sure that the Modulation Curve covers exactly one period.\n", "bullet")
        text.insert("end", " - Fitting Algorithm: Reconstruction involves fitting the modulation curves to a sinusoidal function. Common options include FFT (for uniform $N$) or Least Squares.\n", "bullet")
        text.insert("end", " - Retrieved Channels:\n", "bullet")
        text.insert("end", "   * **Attenuation (Transmission)**: Standard absorption image ($I_0$).\n", "bullet")
        text.insert("end", "   * **Differential Phase Contrast (DPC)**: Measures the angular deflection of the beam, allowing for the reconstruction of the accumulated phase ($\phi$).\n", "bullet")
        text.insert("end", "   * **Dark Field Imaging (DF)**: Measures sub-pixel scattering, related to unresolved microstructures within the object.\n", "bullet")

        text.insert("end", "\nInteractive Tools and Diagnostics\n", "subtitle")
        text.insert("end","These tools help verify the quality of the raw data and the reconstruction:\n")
        text.insert("end", " - **Modulation Curve Plot**: Clicking an image displays the Intensity vs. Phase Step graph for that pixel. Use this to diagnose signal quality and noise.\n", "bullet")
        text.insert("end", " - **Window/Level Adjustment**: Adjust the contrast and brightness of the reconstructed image for specific detail visualization.\n", "bullet")

        text.config(state="disabled")
        
    def _populate_reconstruction_batch(self):
        text = self._make_text_widget(self.tab_rec_batch)
        text.insert("end", "\nBatch Reconstruction Tool\n", "title")

        text.insert("end", "\nOverview\n", "subtitle")
        text.insert("end","The Batch Reconstruction tool allows you to automatically process multiple "
            "acquisitions without loading them manually into the TLRec GUI. It is ideal "
            "for large datasets, repeated measurements, or scanning workflows.\n")

        text.insert("end", "\nRequired Folder Structure\n", "subtitle")
        text.insert("end","Inside the selected **Acquisitions** folder, each dataset must follow this structure:\n")
        
        text.insert("end", " - **Acquisitions/AcquisitionX/Object/** -> contains the object TIFF stack.\n", "bullet")
        text.insert("end", " - **Acquisitions/AcquisitionX/Reference/** -> optional local reference stack.\n", "bullet")
        text.insert("end", " - **Acquisitions/Acquisitions/Reference/** -> optional global reference used when a local one is not available.\n", "bullet")

        text.insert("end","If a local *Acquisitions/Reference/* folder exists inside an acquisition, it is used.\n"
            "If not, the Batch tool falls back to the global reference.\n")

        text.insert("end", "\nWhat the Tool Does\n", "subtitle")
        text.insert("end", "For each valid acquisition folder:\n")
        text.insert("end", " - Loads the first TIFF stack inside **Object/**.\n", "bullet")
        text.insert("end", " - Selects the reference: **local** if available, otherwise **global**.\n", "bullet")
        text.insert("end", " - Runs the selected phase-retrieval algorithm using TLRec parameters.\n", "bullet")
        text.insert("end", " - Applies the Wiener filter to the differential phase.\n", "bullet")
        text.insert("end", " - Saves the reconstructed channels under:\n", "bullet")
        text.insert("end", "     *Acquisitions/AcquisitionX/Retrieved/*\n")

        text.insert("end", "\nSaved Outputs\n", "subtitle")
        text.insert("end", " - **DPC.tif** — Differential Phase Contrast\n", "bullet")
        text.insert("end", " - **Phase.tif** — Integrated Phase after Wiener filtering\n", "bullet")
        text.insert("end", " - **Transmission.tif** — Absorption image\n", "bullet")
        text.insert("end", " - **DarkField.tif** — Dark-field / scattering signal\n", "bullet")

        text.insert("end", "\nHow to Use the Batch GUI\n", "subtitle")
        text.insert("end", " - Select the **Acquisitions** folder.\n", "bullet")
        text.insert("end", " - Choose a reconstruction algorithm.\n", "bullet")
        text.insert("end", " - Click **Run batch**.\n", "bullet")
        text.insert("end","The log window will report: detected acquisitions, reference type used, "
            "and the output folder for each processed dataset.\n")

        text.insert("end", "\nNotes & Recommendations\n", "subtitle")
        text.insert("end", " - Only multi-page TIFF stacks are supported.\n", "bullet")
        text.insert("end", " - If multiple TIFFs exist, the first one alphabetically is selected.\n", "bullet")
        text.insert("end", " - Original data is never modified; all results are stored under *Retrieved/*.\n", "bullet")
        text.insert("end", " - Acquisitions lacking an *Object/* folder are skipped.\n", "bullet")
        
        text.config(state="disabled")

    def _populate_about_tab(self):
        text = self._make_text_widget(self.tab_about)

        text.insert("end", "About XPCIpy GUI\n", "title")
        text.insert("end",
            "\nXPCIpy is a toolkit for X-ray phase-contrast imaging simulations "
            "and reconstruction.\n"
            "You may found more information at: https://doi.org/10.1364/OE.573918\n")

        text.insert("end", "\nModules\n", "subtitle")
        text.insert("end"," PCSim: inline + Talbot-Lau simulations\n"
            " TLRec: phase retrieval with multiple algorithms\n")

        text.insert("end", "\nAuthor\n", "subtitle")
        text.insert("end", "  Víctor Sánchez Lara\n")
        text.insert("end", "  Email: vicsan05@ucm.es\n")
    
        text.insert("end", "\nProject\n", "subtitle")
        text.insert("end", " This work is englobed in the PREDICO project, funded by the Spanish Ministry of Science and Innovation (PID2021-123390OB-C22).\n")

        text.config(state="disabled")
        
