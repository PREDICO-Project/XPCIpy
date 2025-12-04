import tkinter as tk
from GUI.ui.styles import Styles as stl
from GUI.ui.widgets import Widget as wg
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfilename
import os
import tifffile
from PIL import Image
#import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
import src.PCSim.Objects as obj
import src.PCSim.Geometry as geom
import json
import src.PCSim.experiments as exp
import src.PCSim.source as source 
from src.PCSim.TL_conf import TL_CONFIG
import src.PCSim.detector as detector
import src.PCSim.check_Talbot as check_Talbot
from GUI.pages.TLRec_gui import TLRec_GUI
from GUI.text import check_TL_text
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.ui.widgets import ToggleButton
import zipfile
import datetime
import io
import traceback
from tkinter import messagebox
import sys
from GUI.utils import resource_path
import threading
from src.PCSim import utils as pcsim_utils
from GUI.ui.tooltips import ToolTip
from GUI.pages.help_window import HelpWindow
from GUI.pages.info_windows import LicenseWindow, CiteWindow

class PCSim_gui:

    def __init__(self, master):

        # OLD
        #self.parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        #self.granpa_path = os.path.abspath(os.path.join(self.parent_path, os.pardir))
        #self.granpa2_path = os.path.abspath(os.path.join(self.granpa_path, os.pardir))
        #self.root_path = os.path.abspath(os.path.join(self.granpa2_path, os.pardir)) # Not used really

        self.master = master

        stl.configure_style()

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)

        # --- STATUS BAR ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.master,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        status_bar.grid(row=1, column=0, sticky="ew")
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self.master,
            variable=self.progress_var,
            maximum=100,
            mode="determinate"
        )
        self.master.grid_rowconfigure(2, weight=0)
        self.progress_bar.grid(row=2, column=0, sticky="ew")
        
        # --- LOADING OVERLAY ---
        self.overlay = None
        self.overlay_label = None
        self.overlay_progress = None
        self.overlay_progress_var = None

        # --- NOTEBOOK ---
        self.tab_container = ttk.Notebook(self.master)
    
        self.tab_container.grid(row=0, column=0, sticky="nsew")
        
        # HELP
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help / User Guide", command=self.open_help_window)
        help_menu.add_command(label="How to cite XPCIpy", command=self.open_cite_window)
        help_menu.add_command(label="License", command=self.open_license_window)
        
        menubar.add_cascade(label="Help", menu=help_menu)
        

        global Beam_Shape_OPTIONS, Beam_Spectrum_OPTIONS, Object_OPTIONS, Image_OPTIONS
        #spectra_path = os.path.join(self.parent_path, 'Resources', 'Spectra') # OLD
        spectra_path = resource_path("Resources/Spectra")
        Beam_Spectrum_OPTIONS = sorted([f for f in os.listdir(spectra_path)
                                        if os.path.isfile(os.path.join(spectra_path, f))])
        Beam_Spectrum_OPTIONS.append("Monoenergetic")
        Beam_Shape_OPTIONS = ["Plane", "Conical"]
        Object_OPTIONS = ["Sphere", "Cylinder"]
        Image_OPTIONS = ["Ideal", "Realistic"]

        self.initialize_vars()
        self.create_tabs()
        
    def close_app(self):
        self.master.quit()
        self.master.destroy()
        sys.exit(0)
        
    def open_help_window(self):
        HelpWindow(self.master)
        
    def open_license_window(self):
        LicenseWindow(self.master)

    def open_cite_window(self):
        CiteWindow(self.master)
        
    def create_tabs(self):
        # Create a Frame for each tab
        self.TLRec_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.inline_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.check_TL_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.TL_tab = ttk.Frame(self.tab_container, style="TFrame")

        # Add tabs to the tabs container
        self.tab_container.add(self.TLRec_tab, text = 'TLRec')
        self.tab_container.add(self.inline_tab, text="Inline Simulation")
        self.tab_container.add(self.check_TL_tab, text="Check Talbot-Lau effect")
        self.tab_container.add(self.TL_tab, text="Talbot Lau Phase Contrast Simulation")

        self.populate_TLRec_tab()
        self.populate_inline_tab()
        self.populate_checkTL_tab()
        self.populate_TL_tab()
        
    def populate_TLRec_tab(self):
        scrollframe = vsf(self.TLRec_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior
        self.TLRec_tab.grid_rowconfigure(0, weight=1)
        self.TLRec_tab.grid_columnconfigure(0, weight=1)
        #self.TLRec_tab.grid_rowconfigure(0, weight=1)
        #self.TLRec_tab.grid_columnconfigure(0, weight=1)
        #scrollframe = vsf(self.TLRec_tab)
        #scrollframe.grid(row=0, column=0, sticky="nsew")
        self.tlrec_gui = TLRec_GUI(container, status_var=self.status_var)
        #TLRec_GUI(self.TLRec_tab)

    def populate_inline_tab(self):
        
        scrollframe = vsf(self.inline_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior
        
        self.inline_tab.grid_rowconfigure(0, weight=1)
        self.inline_tab.grid_columnconfigure(0, weight=1)
        self.inline_tab.grid_columnconfigure(1, weight=0)
        self.inline_tab.grid_columnconfigure(2, weight=1)
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_columnconfigure(2, weight=2)
        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.grid(row = 0, column = 0, columnspan=2,  sticky='nsew')
        
        #parameters_frame.grid_rowconfigure(0, weight=1)
        #parameters_frame.grid_columnconfigure(0, weight=1)

        self.i_results_frame = ttk.Frame(container, style='TFrame')
        self.i_results_frame.grid(row = 0, column = 2, rowspan=12,  sticky='nsew')
        self.i_results_frame.grid_rowconfigure(0, weight=1)
        self.i_results_frame.grid_columnconfigure(0, weight=1)

        self.initialize_Figure(self.i_results_frame, (3,3), 0,0)

        nLabel, _ = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0,textvariable=self.i_n,padx = 20)
        pxLabel, _ = wg.create_label_entry(parameters_frame, 'Pixel size (micrometer)', 1, 0,textvariable=self.i_pixel_size,padx = 20)
        DODLabel,_ = wg.create_label_entry(parameters_frame, 'Distance Object Detector (cm)', 2, 0,textvariable=self.i_DOD,padx = 20)
        self.DSOLabel,_ = wg.create_label_entry(parameters_frame, 'Distance Source-Object (cm)', 3, 0,textvariable=self.i_DSO,padx = 20)
        self.FWHMSouLabel,_ = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 4, 0,textvariable=self.i_FWHM_source,padx = 20)
        self.BeamShapeLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Beam Shape',row = 5 ,column =0, textvariable = self.i_Beam_Shape, names = Beam_Shape_OPTIONS)
        self.BeamSpectrumLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Spectrum',row = 6 ,column =0, textvariable = self.i_Beam_Spectrum,names = Beam_Spectrum_OPTIONS)
        self.BeamEnergyL,_ = wg.create_label_entry(parameters_frame, 'Energy (keV, necessary to initialize the variable)', row=7, column=0, textvariable=self.i_beam_energy, padx = 20)
        self.ObjectLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Object',row = 8 ,column =0, textvariable = self.i_Object,names = Object_OPTIONS)
        wg.create_button(parameters_frame, 'Set Object Parameters', 9, 0, command = self.open_params)
        self.DetectorL,_ = wg.create_label_combobox(parameters_frame, label_text='Image',row = 10 ,column =0, textvariable = self.i_image_option,names = Image_OPTIONS)
        self.PixelDetectorL,_ = wg.create_label_entry(parameters_frame, 'Detector Pixel Size (microns)', 11, 0,textvariable=self.i_detector_pixel_size,padx = 20)
        self.ResolutionL,_ = wg.create_label_entry(parameters_frame, 'Detector Resolution (FWHM microns)', 12, 0,textvariable=self.i_FWHM_detector,padx = 20)
        #self.zip_checkbox_inline = wg.create_checkbox(parameters_frame, text="Create ZIP with simulation data", row=13, column=0, variable=self.i_zip_var, sticky="w")
        ToggleButton(parameters_frame, text="Create ZIP with simulation data", variable=self.i_zip_var).grid(row=13, column=0, pady=5)
        self.RunButton = wg.create_button(parameters_frame, 'Run', 14,0,command = self.RunInline)
        
        wg.create_button(parameters_frame, "Save preset", 15, 0, command=self.save_preset_Inline)
        wg.create_button(parameters_frame, "Load preset", 15, 1, command=self.load_preset_Inline)

        ExitButton = wg.create_button(parameters_frame, "Exit", 16, 0, padx = 60, command=self.close_app)
        
        
        self.add_tooltip(nLabel, "Number of pixels of the simulated wavefront (n x n).")
        self.add_tooltip(pxLabel, "Pixel size of the wavefront grid in micrometers.")
        self.add_tooltip(self.BeamShapeLabel, "Beam geometry: 'Plane' = parallel beam, 'Conical' = diverging cone.")
        self.add_tooltip(self.BeamSpectrumLabel, "Select a spectrum file or 'Monoenergetic' for a single energy.")
        self.add_tooltip(self.DSOLabel, "Distance from the source to the object in centimeters.")
        self.add_tooltip(self.FWHMSouLabel, "Full Width at Half Maximum (FWHM) of the source in micrometers.")
        self.add_tooltip(self.BeamEnergyL, "Energy of the beam in keV. Used for wavelength-dependent calculations.")
        self.add_tooltip(self.ObjectLabel, "Type of object to simulate: 'Sphere' or 'Cylinder'.")
        self.add_tooltip(self.DetectorL, "Type of image to simulate: 'Ideal' (perfect detector) or 'Realistic' (with detector effects).")
        self.add_tooltip(self.PixelDetectorL, "Pixel size of the detector in micrometers.")
        self.add_tooltip(self.ResolutionL, "Detector resolution specified as Full Width at Half Maximum (FWHM) in micrometers.")
        self.add_tooltip(self.RunButton, "Start the inline phase contrast simulation with the specified parameters.")

    def populate_checkTL_tab(self):
        
        scrollframe = vsf(self.check_TL_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior
        
        self.check_TL_tab.grid_rowconfigure(0, weight=1)
        self.check_TL_tab.grid_columnconfigure(0, weight=0)
        self.check_TL_tab.grid_columnconfigure(1, weight=0)
        self.check_TL_tab.grid_columnconfigure(2, weight=1)
        Grating_OPTIONS = ["Custom", "Phase pi/2", "Phase pi"]

        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.bind("<Button-1>", self.modify_TL_dist)
        parameters_frame.grid(row = 0, column = 0, columnspan=2,  sticky='nsew')

        self.c_results_frame = ttk.Frame(container, style='TFrame')
        self.c_results_frame.grid(row = 0, column = 2, rowspan=12,  sticky='nsew')

        self.initialize_Figure(self.c_results_frame, (3,3), 0,0)

        nLabel, _ = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0,textvariable=self.c_n,padx = 20)
        pxLabel, _ = wg.create_label_entry(parameters_frame, 'Pixel size (micrometer)', 1, 0,textvariable=self.c_pixel_size,padx = 20)
        FWHMSouLabel,_ = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 2, 0,textvariable=self.c_FWHM_source,padx = 20)
        EnergyL,_ = wg.create_label_entry(parameters_frame, 'DEsign Energy (keV)', 3, 0,textvariable=self.c_energy,padx = 20)
        PeriodL,_ = wg.create_label_entry(parameters_frame, 'Grating Period (microns)', 4, 0,textvariable=self.c_period,padx = 20)
        DCL,_ = wg.create_label_entry(parameters_frame, 'Duty Cycle', 5, 0,textvariable=self.c_DC,padx = 20)
        materialL,_ = wg.create_label_entry(parameters_frame, 'Material (just used for custom grating)', 6, 0,textvariable=self.c_material,padx = 20)
        barHeightL,_ = wg.create_label_entry(parameters_frame, 'Bar height (micrometer, just for custom grating)', 7, 0,textvariable=self.c_bar_height,padx = 20)
        gratigL,_ = wg.create_label_combobox(parameters_frame, label_text='Grating Type',row = 8 ,column =0, textvariable = self.c_grating_def, names = Grating_OPTIONS)
        multiplesL,_ = wg.create_label_entry(parameters_frame, 'Multiples of Talbot distance to be represented', row=9, column=0, textvariable=self.c_multiple, padx = 20)
        iterationsL,_ = wg.create_label_entry(parameters_frame, 'Number of calculations performed', row=10, column=0, textvariable=self.c_iterations, padx = 20)
        TLDist,_ = wg.create_label_entry(parameters_frame, 'Talbot Distance (cm)', 11, 0,textvariable=self.c_Talbot_distance,padx = 20, state='disable')
        #iterationsL,_ = wg.create_label_combobox(parameters_frame, label_text='Image',row = 8 ,column =0, textvariable = self.c_image_option,names = Image_OPTIONS)
        #self.ResolutionL,_ = wg.create_label_entry(parameters_frame, 'Detector Resolution (pixel Size in microns)', 9, 0,textvariable=self.c_resolution,padx = 20)
        self.RunButton = wg.create_button(parameters_frame, 'Run', 12,0,command = self.RunCheckTL)

        ExitButton = wg.create_button(parameters_frame, "Exit", 13, 0, padx = 60, command=self.close_app)
        
        self.add_tooltip(nLabel, "Number of pixels of the simulated wavefront (n x n).")
        self.add_tooltip(pxLabel, "Pixel size of the wavefront grid in micrometers.")
        self.add_tooltip(FWHMSouLabel, "Full Width at Half Maximum (FWHM) of the source in micrometers.")
        self.add_tooltip(EnergyL, "Design energy of the setup in keV.")
        self.add_tooltip(PeriodL, "Period of the gratings in micrometers.")
        self.add_tooltip(DCL, "Duty Cycle (DC) of the gratings, defined as the ratio between the bar width and the grating period.")
        self.add_tooltip(materialL, "Material of the grating bars (only used for 'Custom' grating type).")
        self.add_tooltip(barHeightL, "Height of the grating bars in micrometers (only used for 'Custom' grating type).")
        self.add_tooltip(gratigL, "Type of grating: 'Custom' allows user-defined parameters, 'Phase pi/2' and 'Phase pi' are standard phase gratings.")
        self.add_tooltip(multiplesL, "Multiple of Talbot distance (maximum distance).")
        self.add_tooltip(iterationsL, "Number of distances calculated.")
        self.add_tooltip(self.RunButton, "Start the Talbot-Lau effect check simulation with the specified parameters.")
        # Add informational text box
        font = {'family': 'serif',
        'color':  'lightgray',
        'weight': 'normal',
        'size': 10,
        }
        fig_text = Figure(figsize=(5,4))
        fig_text.set_facecolor("#333333")
        canvas = FigureCanvasTkAgg(fig_text, parameters_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row = 11, column = 0, columnspan=3)
        text = fig_text.text(0.5, 0.5,check_TL_text, ha='center', va='center', bbox=dict(facecolor='#333333', alpha=0.5), fontdict=font)
        canvas.figure = fig_text
        canvas.draw()
 
        
    def populate_TL_tab(self):
        
        Grating_OPTIONS = ["Phase pi/2", "Phase pi"]
        Movable_OPTIONS = ["G1", "G2"]
        
        scrollframe = vsf(self.TL_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        
        container = scrollframe.interior
        
        self.TL_tab.grid_rowconfigure(0, weight=1)
        self.TL_tab.grid_columnconfigure(0, weight=0)
        self.TL_tab.grid_columnconfigure(1, weight=0)
        self.TL_tab.grid_columnconfigure(2, weight=1)
        
        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.grid(row = 0, column = 0, columnspan=2,  sticky='nsew')
        #parameters_frame.bind("<Button-1>", self.modify_DOD)
        
        self.TL_results_frame = ttk.Frame(container, style='TFrame')
        self.TL_results_frame.grid(row = 0, column = 2, rowspan=12,  sticky='nsew')

        self.initialize_Figure(self.TL_results_frame, (3,3), 0,0)
        
        nLabel, _ = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0,textvariable=self.TL_n,padx = 20)
        pxLabel, _ = wg.create_label_entry(parameters_frame, 'Pixel size (microns)', 1, 0,textvariable=self.TL_pixel_size,padx = 20)
        sourceLabel,_ = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 2, 0,textvariable=self.TL_FWHM_source,padx = 20)
        beamShapeLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Beam Shape',row = 3 ,column =0, textvariable = self.TL_BeamShape, names = Beam_Shape_OPTIONS)
        spectrumLabel, _ =wg.create_label_combobox(parameters_frame, label_text='Spectrum',row = 4 ,column =0, textvariable = self.TL_Beam_Spectrum,names = Beam_Spectrum_OPTIONS)
        energyLabel,_ = wg.create_label_entry(parameters_frame, 'Design Energy (keV)', row=5, column=0, textvariable=self.TL_beam_energy, padx = 20)
        DSG1Label,_ = wg.create_label_entry(parameters_frame, 'Distance Source-G1 (cm)', 6, 0,textvariable=self.TL_DSO,padx = 20)
        DOG1Label,_ = wg.create_label_entry(parameters_frame, 'Distance Object-G1 (cm)', 7, 0,textvariable=self.TL_DOG1,padx = 20)
        multiplesLabel,_ =wg.create_label_entry(parameters_frame, 'Multiple of Talbot distance', 8, 0,textvariable=self.TL_TLmultiple,padx = 20)
        TalbotDistanceLabel,_ = wg.create_label_entry(parameters_frame, 'Talbot Distance (cm)', 9, 0,textvariable=self.TL_Talbot_distance,padx = 20, state='disable')
        Magnification,_ = wg.create_label_entry(parameters_frame, 'Magnification', 10, 0,textvariable=self.TL_M,padx = 20, state='disable')
        DG1G1Label,_ = wg.create_label_entry(parameters_frame, 'Distance G1-G2 (cm)', 11, 0,textvariable=self.TL_DOD,padx = 20, state='disable')
        G1PeriodLabel,_ = wg.create_label_entry(parameters_frame, 'G1 Period (microns)', 12, 0,textvariable=self.TL_Period_G1,padx = 20)
        G2PeriodLabel,_ = wg.create_label_entry(parameters_frame, 'G2 Period (microns)', 13, 0,textvariable=self.TL_Period_G2,padx = 20, state = 'disable')
        G1PhaseLabel,_ = wg.create_label_combobox(parameters_frame, label_text='G1 Phase',row = 14 ,column =0, textvariable = self.TL_G1_Phase,names = Grating_OPTIONS)
        MovableLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Movable Grating',row = 15 ,column =0, textvariable = self.TL_MovableGrating, names = Movable_OPTIONS)
        NumberStepsLabel,_ = wg.create_label_entry(parameters_frame, 'Number of steps (int)', 16, 0,textvariable=self.TL_steps,padx = 20)
        StepLenghtLabel,_ = wg.create_label_entry(parameters_frame, 'Step Length (microns)', 17, 0,textvariable=self.TL_step_length,padx = 20)
        ObjectLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Object',row = 18 ,column =0, textvariable = self.TL_Object,names = Object_OPTIONS)
        wg.create_button(parameters_frame, 'Set Object Parameters', 19, 0, command = self.open_params_TL)
        ImageOptionLabel,_ = wg.create_label_combobox(parameters_frame, label_text='Image',row = 20 ,column =0, textvariable = self.TL_image_option,names = Image_OPTIONS)
        DetectorPXLabel,_ = wg.create_label_entry(parameters_frame, 'Detector Pixel Size (microns)', 21, 0,textvariable=self.TL_detector_pixel_size,padx = 20)
        DetectorResolutionLabel,_ =wg.create_label_entry(parameters_frame, 'Detector Resolution (pixel Size in microns)', 22, 0,textvariable=self.TL_resolution,padx = 20)
        ToggleButton(parameters_frame, text="Create ZIP with simulation data", variable=self.TL_zip_var).grid(row=23, column=0, pady=5)
        
        RunBtton = wg.create_button(parameters_frame, 'Run', 24,0,command = self.RunTL)
        
        wg.create_button(parameters_frame, "Save preset", 25, 0, command=self.save_preset_TL)
        wg.create_button(parameters_frame, "Load preset", 25, 1, command=self.load_preset_TL)

        ExitButton = wg.create_button(parameters_frame, "Exit", 26, 0, padx = 60, command=self.close_app)
        
        self.add_tooltip(nLabel, "Number of pixels of the simulated wavefront (n x n).")
        self.add_tooltip(pxLabel, "Pixel size of the wavefront grid in micrometers.")
        self.add_tooltip(beamShapeLabel, "Beam geometry: 'Plane' = parallel beam, 'Conical' = diverging cone.")
        self.add_tooltip(spectrumLabel, "Select a spectrum file or 'Monoenergetic' for a single energy.")
        self.add_tooltip(DSG1Label, "Distance from the source to the first grating (G1) in centimeters.")
        self.add_tooltip(DOG1Label, "Distance from the object to the first grating (G1) in centimeters.")
        self.add_tooltip(multiplesLabel, "Multiple of Talbot distance (maximum distance).")
        self.add_tooltip(G1PeriodLabel, "Period of the first grating (G1) in micrometers.")
        self.add_tooltip(G1PhaseLabel, "Phase shift introduced by the first grating (G1).")
        self.add_tooltip(MovableLabel, "Select which grating (G1 or G2) will be moved during the phase stepping simulation.")
        self.add_tooltip(NumberStepsLabel, "Number of discrete steps in the phase stepping process.")
        self.add_tooltip(StepLenghtLabel, "Length of each step in micrometers.")
        self.add_tooltip(ObjectLabel, "Type of object to simulate: 'Sphere' or 'Cylinder'.")
        self.add_tooltip(ImageOptionLabel, "Type of image to simulate: 'Ideal' (perfect detector) or 'Realistic' (with detector effects).")
        self.add_tooltip(DetectorPXLabel, "Pixel size of the detector in micrometers.")
        self.add_tooltip(DetectorResolutionLabel, "Detector resolution specified as pixel size in micrometers.")
        self.add_tooltip(RunBtton, "Start the Talbot-Lau phase contrast simulation with the specified parameters.")
        
        def _auto_update_TL(*args):
            self.modify_DOD()

        for var in (
            self.TL_DSO,
            self.TL_TLmultiple,
            self.TL_Period_G1,
            self.TL_beam_energy,
            self.TL_BeamShape,
            self.TL_Beam_Spectrum,
            self.TL_G1_Phase,
        ):
            try:
                var.trace_add("write", _auto_update_TL)
            except Exception:
                pass

        self.modify_DOD()

    def initialize_vars(self):

        # OLD
        #config_path  = os.path.join(os.path.dirname(__file__), "config")
        config_path = resource_path("GUI/config/config_inline.json")

         # Inline
        self.i_n= tk.IntVar()
        self.i_pixel_size= tk.DoubleVar()
        self.i_DSO= tk.DoubleVar()
        self.i_DOD= tk.DoubleVar()
        self.i_FWHM_source = tk.DoubleVar()
        self.i_Beam_Shape= tk.StringVar()
        self.i_Beam_Spectrum= tk.StringVar()
        self.i_beam_energy = tk.DoubleVar()
        self.i_Object = tk.StringVar()
        self.i_image_option = tk.StringVar()
        self.i_resolution = tk.IntVar()

        self.i_radius = tk.DoubleVar()
        self.i_inner_radius = tk.DoubleVar()
        self.i_xshift = tk.IntVar()
        self.i_yshift = tk.IntVar()
        self.i_material = tk.StringVar()
        self.i_orientation = tk.StringVar()
        self.i_FWHM_detector = tk.DoubleVar()
        self.i_detector_pixel_size = tk.DoubleVar()
        self.i_zip_var = tk.BooleanVar(value=False)

        with open(config_path) as json_path:
            #default_TLRec_conf = json.load(os.path.join(config_path, 'config_inline.json'))

            default_inline_conf = json.load(json_path)
        

            self.i_n.set(default_inline_conf['n'])
            self.i_pixel_size.set(default_inline_conf['pixel_size'])
            self.i_DSO.set(default_inline_conf['DSO'])
            self.i_DOD.set(default_inline_conf['DOD'])
            self.i_FWHM_source.set(default_inline_conf['FWHM_source'])
            self.i_Beam_Shape.set(default_inline_conf['Beam_Shape'])
            self.i_Beam_Spectrum.set(default_inline_conf['Beam_Spectrum'])
            self.i_beam_energy.set(default_inline_conf['energy'])
            self.i_Object.set(default_inline_conf['Object'])
            self.i_radius.set(default_inline_conf['radius'])
            self.i_inner_radius.set(default_inline_conf['inner_radius'])
            self.i_xshift.set(default_inline_conf['xshift'])
            self.i_yshift.set(default_inline_conf['yshift'])
            self.i_material.set(default_inline_conf['material'])
            self.i_image_option.set(default_inline_conf['image_option'])
            self.i_orientation.set(default_inline_conf['orientation'])
            self.i_resolution.set(default_inline_conf['resolution'])
            self.i_FWHM_detector.set(default_inline_conf['FWHM_detector'])
            self.i_detector_pixel_size.set(default_inline_conf['detector_pixel_size']) #um

        # Check TL

        self.c_n = tk.IntVar()
        self.c_pixel_size = tk.DoubleVar()
        self.c_FWHM_source = tk.DoubleVar()
        self.c_energy = tk.DoubleVar()
        self.c_period = tk.DoubleVar()
        self.c_DC = tk.DoubleVar()
        self.c_material = tk.StringVar()
        self.c_bar_height = tk.DoubleVar()
        self.c_multiple = tk.IntVar()
        self.c_iterations = tk.IntVar()
        self.c_grating_def = tk.StringVar()
        self.c_Talbot_distance = tk.DoubleVar()
        self.c_zip_var = tk.BooleanVar(value=False)
        #self.c_image_option = tk.StringVar()
        #self.c_resolution = tk.IntVar()
        
        config_path_checkTL = resource_path("GUI/config/config_checkTL.json")

        with open(config_path_checkTL) as json_path:
            #default_TLRec_conf = json.load(os.path.join(config_path, 'config_inline.json'))

            default_checkTL_conf = json.load(json_path)
            self.c_n.set(default_checkTL_conf['n'])
            self.c_pixel_size.set(default_checkTL_conf['pixel_size'])
            self.c_FWHM_source.set(10.)
            self.c_energy.set(default_checkTL_conf['energy'])
            self.c_period.set(default_checkTL_conf['period'])
            self.c_DC.set(default_checkTL_conf['DC'])
            self.c_material.set(default_checkTL_conf['material'])
            self.c_bar_height.set(default_checkTL_conf['bar_height'])
            self.c_multiple.set(default_checkTL_conf['multiples'])
            self.c_iterations.set(default_checkTL_conf['iterations'])
            self.c_grating_def.set(default_checkTL_conf['grating_option'])
            #self.c_image_option.set(default_checkTL_conf['image_option'])
            #self.c_resolution.set(default_checkTL_conf['resolution'])

        # Talbot Lau
        self.TL_n = tk.IntVar()
        self.TL_pixel_size = tk.DoubleVar()

        self.TL_FWHM_source = tk.DoubleVar()
        self.TL_BeamShape = tk.StringVar()
        self.TL_Beam_Spectrum= tk.StringVar()
        self.TL_beam_energy = tk.DoubleVar()

        self.TL_DSO = tk.DoubleVar()
        self.TL_DOG1 = tk.DoubleVar()
        self.TL_DOD = tk.DoubleVar()
        self.TL_Talbot_distance = tk.DoubleVar()
        self.TL_M = tk.DoubleVar()
        self.TL_TLmultiple = tk.IntVar()

        self.TL_Object = tk.StringVar()
        self.TL_radius = tk.DoubleVar()
        self.TL_inner_radius = tk.DoubleVar()
        self.TL_material= tk.StringVar()
        self.TL_xshift = tk.IntVar()
        self.TL_yshift = tk.IntVar()
        self.TL_orientation = tk.StringVar()

        self.TL_Period_G1 = tk.DoubleVar() 
        self.TL_Period_G2 = tk.DoubleVar()
        self.TL_ThicknessG1 = tk.DoubleVar() #um
        self.TL_ThicknessG2 = tk.DoubleVar() #um
        self.TL_G1_Phase = tk.StringVar()
        self.TL_MovableGrating = tk.StringVar()
        self.TL_steps = tk.IntVar()
        self.TL_step_length = tk.DoubleVar()

        self.TL_resolution = tk.DoubleVar() #um
        self.TL_detector_pixel_size = tk.IntVar()
        self.TL_image_option = tk.StringVar()
        self.TL_zip_var = tk.BooleanVar(value=False)
        
        config_path_TLSim = resource_path("GUI/config/config_TLSim.json")

        with open(config_path_TLSim) as json_path:
            #default_TLRec_conf = json.load(os.path.join(config_path, 'config_inline.json'))

            default_TL_conf = json.load(json_path)
            self.TL_n.set(default_TL_conf['n'])
            self.TL_FWHM_source.set(10.)
            self.TL_pixel_size.set(default_TL_conf['pixel_size'])

            self.TL_BeamShape.set(default_TL_conf['Beam_Shape'])
            self.TL_Beam_Spectrum.set(default_TL_conf['Beam_Spectrum'])
            self.TL_beam_energy.set(default_TL_conf['energy'])

            self.TL_DSO.set(default_TL_conf['DSG1'])
            self.TL_DOG1.set(default_TL_conf['DOG1'])
            #self.TL_DOD.set(default_TL_conf['DOD'])
            self.TL_TLmultiple.set(default_TL_conf['TLmultiple'])

            self.TL_Object.set(default_TL_conf['Object'])
            self.TL_radius.set(default_TL_conf['radius'])
            self.TL_inner_radius.set(0.)
            self.TL_material.set(default_TL_conf['material'])
            self.TL_xshift.set(default_TL_conf['xshift'])
            self.TL_yshift.set(default_TL_conf['yshift'])
            self.TL_orientation.set(default_TL_conf['orientation'])

            self.TL_Period_G1.set(default_TL_conf['period_G1'])
            self.TL_ThicknessG1.set(default_TL_conf['thickness_G1'])
            self.TL_ThicknessG2.set(default_TL_conf['thickness_G2'])
            self.TL_G1_Phase.set(default_TL_conf['G1_Phase'])
            self.TL_MovableGrating.set(default_TL_conf['MovableGrating'])
            self.TL_steps.set(default_TL_conf['steps'])
            self.TL_step_length.set(default_TL_conf['step_length'])

            self.TL_image_option.set(default_TL_conf['image_option'])
            self.TL_resolution.set(default_TL_conf['resolution'])
            self.TL_detector_pixel_size.set(default_TL_conf['detector_pixel_size'])


        
    def RunInline(self):
        
        def _run():
            
            if not self.verify_physical_values_inline():
                self.set_status("Error in physical values for Inline simulation.")
                return
            
            self.set_status("Running inline simulation...")
            n = self.i_n.get()
            DSO = self.i_DSO.get()
            DOD = self.i_DOD.get()
            pixel_size = self.i_pixel_size.get()
            Beam_Shape = self.i_Beam_Shape.get()
            FWHM_source = self.i_FWHM_source.get()
            Beam_Spectrum = os.path.splitext(self.i_Beam_Spectrum.get())[0]
            beam_energy = self.i_beam_energy.get()
            Object = self.i_Object.get()

            Material = os.path.splitext(self.i_material.get())[0]
            image_option = self.i_image_option.get()
            FWHM_detector = self.i_FWHM_detector.get()
            detector_pixel_size = self.i_detector_pixel_size.get()
            
            #try:
            #   resolution = self.i_resolution.get()
            #except:
            #   resolution = 1

            if Object == 'Sphere':
                radius = self.i_radius.get()
                x_shift =  self.i_xshift.get() 
                y_shift =  self.i_yshift.get()
                MyObject1 = obj.Sphere(n, radius, pixel_size, Material, DSO, x_shift, y_shift)
            
            elif Object == 'Cylinder':
                outer_radius = self.i_radius.get()
                inner_radius = self.i_inner_radius.get()
                x_shift =  self.i_xshift.get() 
                y_shift =  self.i_yshift.get()
                Orientation = self.i_orientation.get()
                MyObject1 = obj.Cylinder(n, outer_radius, inner_radius, Orientation, pixel_size, Material, DSO, x_shift, y_shift)
            
            if Beam_Spectrum == 'Monoenergetic':
                Beam_Spectrum = 'Mono'
        
            MySource = source.Source((FWHM_source, FWHM_source),Beam_Spectrum, beam_energy, Beam_Shape, pixel_size)
            MyDetector = detector.Detector(image_option, detector_pixel_size, FWHM_detector, 'gaussian', pixel_size)
            MyGeometry = geom.Geometry(DSO+DOD)

            #PSF_source = MySource.Source_PSF((n,n), M)

            Sample = [MyObject1]
            progress_cb = self.make_progress_callback("Inline simulation")
            Intensity = exp.Experiment_Inline(n, MyGeometry, MySource, MyDetector, Sample, progress_cb=progress_cb)
            
            def update_gui():
                self.clear_frame(self.i_results_frame)
                self.Plot_Figure(self.i_results_frame, Intensity, 0, 0, (3, 3), 'Inline Simulation')
                wg.create_button(self.i_results_frame, 'Save Image', 1, 0,
                                command=lambda: self.save_image(Intensity))

                if self.i_zip_var.get():
                    self.export_inline_zip(Intensity)

            self.master.after(0, update_gui)
            
            '''
            self.clear_frame(self.i_results_frame)
            self.Plot_Figure(self.i_results_frame, Intensity,0,0, (3,3), 'Inline Simulation')
            bt1 = wg.create_button(self.i_results_frame, 'Save Image', 1,0, command=  lambda : self.save_image(Intensity))
            
            #
            if self.i_zip_var.get():
                self.export_inline_zip(Intensity)
                
            self.set_status("Inline simulation finished!")
            '''

        self.run_with_error_handling(_run, "Running Inline simulation...")
        
    def RunCheckTL(self):
        def _run():
            #self.set_status("Running Talbot carpet simulation...")
            if not self.verify_physical_values_checkTL():
                self.set_status("Error in physical values for Talbot carpet simulation.")
                return
            n = self.c_n.get()
            pixel_size = self.c_pixel_size.get() #um
            FWHM_source = self.c_FWHM_source.get()
            Energy = self.c_energy.get() #keV
            Period = self.c_period.get() # um
            DC = self.c_DC.get()
            Material = self.c_material.get()
            bar_height = self.c_bar_height.get()
            multiples = self.c_multiple.get()#Multiples of Talbot Distance defined as Dt = 2*p**2/wavelength
            iterations = self.c_iterations.get()
            grating_option = self.c_grating_def.get()
            wavelength = 1.23984193/(1000*Energy) # in um

            MySource = source.Source((FWHM_source, FWHM_source),'Mono', Energy, 'Plane', pixel_size)
            
            if grating_option == 'Custom':
                grating_type = 'custom'
                title = 'Custom Grating'
            elif grating_option == 'Phase pi':
                grating_type = 'phase_pi'
                bar_height = None
                Material = None
                title = 'pi-phase Grating'
            elif grating_option == 'Phase pi/2':
                grating_type = 'phase_pi_2'
                bar_height = None
                Material = None
                title = 'pi/2-phase Grating'

            
            Intensities= check_Talbot.Talbot_carpet(n, MySource, Period, DC, multiples, iterations, grating_type,pixel_size, Energy, material=Material, grating_height= bar_height)
            def update_gui():
                self.clear_frame(self.c_results_frame)
                self.Plot_check_TL(self.c_results_frame, Intensities, 0, 0, (3,3), title, multiples, n)
                wg.create_button(self.c_results_frame, 'Save Image', 1,0, command=  lambda : self.save_image(Intensities))
            
            self.master.after(0, update_gui)
            
            '''
            self.master.after(0, update_gui)
            self.clear_frame(self.c_results_frame)
            self.Plot_check_TL(self.c_results_frame, Intensities, 0, 0, (3,3), title, multiples, n)
            bt1 = wg.create_button(self.c_results_frame, 'Save Image', 1,0, command=  lambda : self.save_image(Intensities))
            '''
        
        self.run_with_error_handling(_run, "Running Talbot carpet simulation...")
        #self.set_status("Talbot carpet simulation finished!")

    def RunTL(self):
        def _run():
            
            if not self.verify_physical_values_TL():
                self.set_status("Error in physical values for Talbot-Lau simulation.")
                return
            
            #self.set_status("Running Talbot-Lau simulation...")
            n = self.TL_n.get()
            pixel_size = self.TL_pixel_size.get()
            FWHM_source = self.TL_FWHM_source.get()
            Beam_Shape = self.TL_BeamShape.get()
            Beam_Spectrum = os.path.splitext(self.TL_Beam_Spectrum.get())[0]
            design_energy = self.TL_beam_energy.get()

            DSG1 = self.TL_DSO.get()
            DOG1 = self.TL_DOG1.get()
            object = self.TL_Object.get()
            radius = self.TL_radius.get()
            inner_radius = self.TL_inner_radius.get()
            material= os.path.splitext(self.TL_material.get())[0]
            Period_G1 = self.TL_Period_G1.get()
            G1_Phase = self.TL_G1_Phase.get()
            FWHM_detector = self.TL_resolution.get()
            detector_pixel_size = self.TL_detector_pixel_size.get()
            xshift = self.TL_xshift.get()
            yshift = self.TL_yshift.get()
            image_option = self.TL_image_option.get()
            DSO = DSG1-DOG1
            angle = 0


            Objects=[]
            if Beam_Spectrum == 'Monoenergetic':
                Beam_Spectrum = 'Mono'
            if G1_Phase == 'Phase pi/2':
                G1_type = 'phase_pi_2'
            elif G1_Phase == 'Phase pi':
                G1_type = 'phase_pi'

            MySource = source.Source((FWHM_source, FWHM_source),Beam_Spectrum, design_energy, Beam_Shape, pixel_size)
            mean_energy = MySource.mean_energy
            mean_wavelength = 1.23984193/(mean_energy*1000)
            MyDetector = detector.Detector(image_option, detector_pixel_size, FWHM_detector, 'gaussian', pixel_size)

            configuration = TL_CONFIG(Design_energy = design_energy, G1_Period = Period_G1, DSG1=DSG1, Movable_Grating = self.TL_MovableGrating.get(),
                                    G1_type = G1_type, TL_multiple = self.TL_TLmultiple.get(), 
                                    Number_steps = self.TL_steps.get(), Step_length = self.TL_step_length.get(), pixel_size = pixel_size, angle = 0, resolution = FWHM_detector, 
                                    pixel_detector = detector_pixel_size)


            if object == 'Sphere':
                object1 = obj.Sphere(n, radius, pixel_size, material, DSG1-DOG1, xshift,yshift)
            
            elif object == 'Cylinder':
                orientation = self.TL_orientation.get()
                object1 = obj.Cylinder(n, radius, inner_radius,orientation,pixel_size, material, DSO = DSG1-DOG1, x_shift_px=xshift, y_shift_px=yshift)
                
            Objects=[object1]
            
            pixel_size = configuration.pixel_size
            geometry = geom.Geometry()  
            distance, G2Period = geometry.calculate_Talbot_distance_and_G2period(MySource, configuration)
            geometry.DSD  = DSG1+distance
            configuration.G2_Period = G2Period
            
            if DSO -  distance <= 0:
                # It should not happen in any case due to the calculation of distance, but just in case
                self.TL_Talbot_distance.set(0.0)
                self.TL_DOD.set(0.0)
                self.TL_M.set(0.0)
                self.TL_Period_G2.set(0.0)
                self.set_status("Talbot configuration not physically valid for these parameters.")
                return

            G1 = obj.Grating(n , Period_G1, 0.5, pixel_size, 'Si', DSG1, grating_type = G1_type, design_energy = design_energy)
            G2 = obj.Grating(n , G2Period, 0.5, pixel_size, 'Au', DSG1+distance, 40,grating_type = 'custom', design_energy = design_energy)
            self.gui_check_grating_sampling(Period_G1 / pixel_size)
            self.gui_check_grating_sampling(G2Period / pixel_size)
            self.gui_check_phase_stepping(self.TL_steps.get(), G2Period / pixel_size,self.TL_step_length.get() / pixel_size)
            
            progress_cb = self.make_progress_callback("TL simulation")
            i, ir = exp.Experiment_Phase_Stepping(n, MyDetector, MySource, geometry, Objects, G1, G2, configuration, padding = 0, progress_cb=progress_cb)
            
            def update_gui():
                self.clear_frame(self.TL_results_frame)
                self.Plot_Modulation_Curve(self.TL_results_frame, i, ir, 0, 0, (3,3), 'Phase Stepping Curve', columnspan=2)
                self.Plot_Figure(self.TL_results_frame, i[0,:,:], 1, 0, (3,3), 'One Projection', columnspan=2)
                wg.create_button(self.TL_results_frame, 'Save Stack Object Images', 2,0, command=  lambda : self.save_stack_image(i))
                wg.create_button(self.TL_results_frame, 'Save Stack Reference Images', 2,1, command=  lambda : self.save_stack_image(ir))
                bt3 = wg.create_button(self.TL_results_frame, 'Send to TLRec', 3, 0,command=lambda: self.send_to_TLREC(i, ir))
            
                if self.TL_zip_var.get():
                    self.export_TL_zip(i, ir)
                
            self.master.after(0, update_gui)
            
            '''
            self.clear_frame(self.TL_results_frame)
            self.Plot_Modulation_Curve(self.TL_results_frame, i, ir, 0, 0, (3,3), 'Phase Stepping Curve', columnspan=2)
            self.Plot_Figure(self.TL_results_frame, i[0,:,:], 1, 0, (3,3), 'One Projection', columnspan=2)
            bt1 = wg.create_button(self.TL_results_frame, 'Save Stack Object Images', 2,0, command=  lambda : self.save_stack_image(i))
            bt2 = wg.create_button(self.TL_results_frame, 'Save Stack Reference Images', 2,1, command=  lambda : self.save_stack_image(ir))
            
            if self.TL_zip_var.get():
                self.export_TL_zip(i, ir)
            '''
        
        self.run_with_error_handling(_run, "Running Talbot-Lau simulation...")
        
        
        #self.set_status("Talbot-Lau simulation finished!")
        #DPC, Phase, At, Transmission, DF = DPC_Retrieval(ib, ibr, G2Period, DSO, distance,0,mean_energy)

    def modify_DOD(self, event=None):
        #print('Hola')
        DSO = self.TL_DSO.get()
        Period_G1 = self.TL_Period_G1.get()
        Talbot_multiple = self.TL_TLmultiple.get()
        FWHM_source = self.TL_FWHM_source.get()
        Spectrum = os.path.splitext(self.TL_Beam_Spectrum.get())[0]
        energy = self.TL_beam_energy.get()
        pixel_size = self.TL_pixel_size.get()
        G1_Phase = self.TL_G1_Phase.get()
        Beam_Shape = self.TL_BeamShape.get()
        
        if Period_G1 <= 0 or energy <= 0 or DSO <= 0 or Talbot_multiple <= 0:
            #print('Nope')
            return

        if Spectrum == 'Monoenergetic':
            Spectrum = 'Mono'

        Source = source.Source((FWHM_source, FWHM_source),Spectrum, energy, Beam_Shape, pixel_size)
       
        mean_energy = Source.mean_energy
        mean_wavelength = 1.23984193/(mean_energy*1000)
        
        if Beam_Shape == 'Conical':
            if G1_Phase == 'Phase pi':
            
                distance_Talbot = Period_G1**2/(8*mean_wavelength)*10**(-4)
                distance = DSO*Talbot_multiple*distance_Talbot/(DSO-Talbot_multiple*distance_Talbot)
                M = (DSO+distance)/DSO
                G2Period =Period_G1*M/2 # pi
            elif G1_Phase == 'Phase pi/2':
                distance_Talbot = Period_G1**2/(2*mean_wavelength)*10**(-4) #pi/2
                distance = DSO*Talbot_multiple*distance_Talbot/(DSO-Talbot_multiple*distance_Talbot)
                M = (DSO+distance)/DSO
                G2Period =Period_G1*M # pi/2
                
            else:
                return

        if Beam_Shape == 'Plane': 
            M =1
            if G1_Phase == 'Phase pi':
                G2Period = Period_G1/2
                distance = Period_G1**2/(8*mean_wavelength)*10**(-4)
                distance_Talbot = distance
            elif G1_Phase == 'Phase pi/2':
                G2Period = Period_G1
                distance = Period_G1**2/(2*mean_wavelength)*10**(-4)
                distance_Talbot = distance
            else:
                return
        else:
            return

        self.TL_Talbot_distance.set(distance_Talbot)
        self.TL_Period_G2.set(G2Period)
        self.TL_DOD.set(distance)
        self.TL_M.set(M)

    def modify_TL_dist(self, event):
        
        Period_G1 = self.c_period.get()

        energy = self.c_energy.get()
        grating = self.c_grating_def.get()
        mean_wavelength = 1.23984193/(energy*1000)
        
        if grating == 'Absorption':
            G2Period = Period_G1
            distance = 2*Period_G1**2/(mean_wavelength)*10**(-4)
            distance_Talbot = distance

        elif grating == 'Phase pi':
            G2Period = Period_G1/2
            distance = Period_G1**2/(8*mean_wavelength)*10**(-4)
            distance_Talbot = distance
        elif grating == 'Phase pi/2':
            G2Period = Period_G1
            distance = Period_G1**2/(2*mean_wavelength)*10**(-4)
            distance_Talbot = distance

        self.c_Talbot_distance.set(distance_Talbot)
        #self.c_Period_G2.set(G2Period)



    def Plot_Modulation_Curve(self, frame, image, image_reference,row, column, figsize, title, columnspan=1):
        
        params = {"text.color" : "white",
          "xtick.color" : "white",
          "ytick.color" : "white",
          "axes.labelcolor": "white",
          "axes.grid": True,
          #"legend.labelcolor": 'black'
          }
        rcParams.update(params)
        
        fig=Figure(figsize=figsize)
        fig.set_facecolor("#333333")
        ax = fig.add_subplot(1,1,1)
        
        im = ax.plot(image[:, image.shape[1]//2, image.shape[2]//2], color = 'red', label='Object')
        im = ax.plot(image_reference[:, image_reference.shape[1]//2, image_reference.shape[2]//2], color='blue', label='Reference')
        ax.legend()
        ax.set_title(title)
        ax.set_xlabel('Phase Stepping')
        fig
        #plt.show()
        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column,columnspan=columnspan,ipadx=90, ipady=20)
        #toolbarFrame1 = tk.Frame(master=frame)
        #toolbarFrame1.grid(row=row+1,column=column)

    def Plot_check_TL(self, frame, image, row, column, figsize, title, multiples, n):
        
        params = {"text.color" : "white",
          "xtick.color" : "white",
          "ytick.color" : "white",
          "axes.grid": False,
          "axes.labelcolor": "white"}
        rcParams.update(params)

        fig=Figure(figsize=figsize)
        fig.set_facecolor("#333333")
        ax = fig.add_subplot(1,1,1)
        
        im = ax.imshow(image,"gray",interpolation='none', extent=[0,multiples,n,0], aspect='auto')
        ax.set_title(title)
        ax.set_xlabel('Multiples of Talbot distance')
        fig.colorbar(im,ax=ax)
        fig.tight_layout()

        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column, ipadx=90, ipady=20)

    
    def initialize_Figure(self, frame, figsize, row, column):

        fig = Figure(figsize = figsize)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        fig.set_facecolor("#333333")

        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=column, ipadx=60, ipady=50,sticky='nsew')


    def Plot_Figure(self, frame, image, row, column, figsize, title, columnspan=1):
        
        params = {
        "text.color": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "axes.grid": False,
        "axes.labelcolor": "white",
        }
        rcParams.update(params)

        fig = Figure(figsize=figsize)
        fig.set_facecolor("#333333")
        ax = fig.add_subplot(1, 1, 1)

        im = ax.imshow(image, "gray")
        ax.set_title(title)
        fig.colorbar(im, ax=ax)
        fig.tight_layout()

        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column, columnspan=columnspan, ipadx=90, ipady=20)
        
        '''
        plt.close()
        params = {"text.color" : "white",
          "xtick.color" : "white",
          "ytick.color" : "white",
          "axes.grid": False,
          "axes.labelcolor": "white"}
        plt.rcParams.update(params)
        plt.tight_layout()

        fig=Figure(figsize=figsize)
        fig.set_facecolor("#333333")
        ax = fig.add_subplot(1,1,1)
        
        im = ax.imshow(image,"gray")
        ax.set_title(title)
        fig.colorbar(im,ax=ax)
        #plt.show()
        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column, columnspan=columnspan, ipadx=90, ipady=20)
        toolbarFrame1 = tk.Frame(master=frame)
        toolbarFrame1.grid(row=row+1,column=column)
        '''

    def open_params(self):

        global params_window
        params_window = tk.Toplevel()
        params_window.title("Object Parameters")

        paramsFrame = ttk.Frame(params_window)
        paramsFrame.grid(row=0, column=0, sticky="ns")
        
        if self.i_Object.get() == 'Sphere':
            radiusL,_ = wg.create_label_entry(paramsFrame, "Radius (micrometer):", 0, 0,textvariable=self.i_radius)
            xshiftL,_ = wg.create_label_entry(paramsFrame, "X-direction shift (pixels):", 1, 0,textvariable=self.i_xshift)
            yshiftL,_ = wg.create_label_entry(paramsFrame, "Y-direction shift (pixels):", 2, 0,textvariable=self.i_yshift)

        elif self.i_Object.get() == 'Cylinder':
            ORIENTATION_OPTIONS = ['Horizontal', 'Vertical']
            radiusL,_ = wg.create_label_entry(paramsFrame, "Outer radius (micrometer):", 0, 0,textvariable=self.i_radius)
            IradiusL,_ = wg.create_label_entry(paramsFrame, "Inner radius (micrometer):", 1, 0,textvariable=self.i_inner_radius)
            xshiftL,_ = wg.create_label_entry(paramsFrame, "X-direction shift (pixels):", 2, 0,textvariable=self.i_xshift)
            yshiftL,_ = wg.create_label_entry(paramsFrame, "Y-direction shift (pixels):", 3, 0,textvariable=self.i_yshift)
            orientationL,_ = wg.create_label_combobox(paramsFrame, 'Orientation', ORIENTATION_OPTIONS, 4,0,textvariable=self.i_orientation)
            
        
        complex_refractive_index_path = resource_path("Resources/complex_refractive_index")
        materialL,_ = wg.create_label_file_combobox(paramsFrame,'Material', complex_refractive_index_path,5,0, self.i_material)
        

        ApplyButton = wg.create_button(paramsFrame, 'Apply Changes', 9,0 ,padx = 20, pady= 10, command = self.apply_changes)
        
    def apply_changes(self):
        params_window.destroy()

    def open_params_TL(self):
        global params_window
        params_window = tk.Toplevel()
        params_window.title("Object Parameters")
        paramsFrame = ttk.Frame(params_window)
        paramsFrame.grid(row=0, column=0, sticky="ns")

        if self.TL_Object.get() == 'Sphere':
            radiusL,_ = wg.create_label_entry(paramsFrame, "Radius (micrometer):", 0, 0,textvariable=self.TL_radius)
            xshiftL,_ = wg.create_label_entry(paramsFrame, "X-direction shift (pixels):", 1, 0,textvariable=self.TL_xshift)
            yshiftL,_ = wg.create_label_entry(paramsFrame, "Y-direction shift (pixels):", 2, 0,textvariable=self.TL_yshift)
        elif self.TL_Object.get() == 'Cylinder':
            ORIENTATION_OPTIONS = ['Horizontal', 'Vertical']
            radiusL,_ = wg.create_label_entry(paramsFrame, "Outer radius (micrometer):", 0, 0,textvariable=self.TL_radius)
            radiusL,_ = wg.create_label_entry(paramsFrame, "Inner radius (micrometer):", 1, 0,textvariable=self.TL_inner_radius)
            xshiftL,_ = wg.create_label_entry(paramsFrame, "X-direction shift (pixels):", 2, 0,textvariable=self.TL_xshift)
            yshiftL,_ = wg.create_label_entry(paramsFrame, "Y-direction shift (pixels):", 3, 0,textvariable=self.TL_yshift)
            orientationL,_ = wg.create_label_combobox(paramsFrame, 'Orientation', ORIENTATION_OPTIONS, 4,0,textvariable=self.TL_orientation)

        complex_refractive_index_path = resource_path("Resources/complex_refractive_index")
        materialL,_ = wg.create_label_file_combobox(paramsFrame,'Material', complex_refractive_index_path,5,0, self.TL_material)
        ApplyButton = wg.create_button(paramsFrame, 'Apply Changes', 9,0 ,padx = 20, pady= 10, command = self.apply_changes)
        
    def save_preset_TL(self):
        params = {
            "type": "TL_SIM",
            "n": self.TL_n.get(),
            "pixel_size": self.TL_pixel_size.get(),
            "FWHM_source": self.TL_FWHM_source.get(),
            "Beam_Shape": self.TL_BeamShape.get(),
            "Beam_Spectrum": self.TL_Beam_Spectrum.get(),
            "energy": self.TL_beam_energy.get(),
            "DSO": self.TL_DSO.get(),
            "DOG1": self.TL_DOG1.get(),
            "Period_G1": self.TL_Period_G1.get(),
            "G1_Phase": self.TL_G1_Phase.get(),
            "steps": self.TL_steps.get(),
            "step_length": self.TL_step_length.get(),
            "Object": self.TL_Object.get(),
            "radius": self.TL_radius.get(),
            "material": self.TL_material.get()
        }

        filename = asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, "w") as f:
                json.dump(params, f, indent=4)
            self.set_status("Preset saved successfully.")
            
    def save_preset_Inline(self):
        params = {
            "type": "Inline_SIM",
            "n": self.i_n.get(),
            "pixel_size": self.i_pixel_size.get(),
            "FWHM_source": self.i_FWHM_source.get(),
            "Beam_Shape": self.i_Beam_Shape.get(),
            "Beam_Spectrum": self.i_Beam_Spectrum.get(),
            "energy": self.i_beam_energy.get(),
            "DSO": self.i_DSO.get(),
            "DOD": self.i_DOD.get(),
            "Period_G1": self.TL_Period_G1.get(),
            "Object": self.i_Object.get(),
            "radius": self.i_radius.get(),
            "material": self.i_material.get(),
            "image_option": self.i_image_option.get(),
            "resolution": self.i_resolution.get(),
            "inner_radius": self.i_inner_radius.get(),
            "xshift": self.i_xshift.get(),
            "yshift": self.i_yshift.get(),
            "orientation": self.i_orientation.get(),
            "FWHM_detector": self.i_FWHM_detector.get(),
            "detector_pixel_size": self.i_detector_pixel_size.get()
            
        }
        filename = asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, "w") as f:
                json.dump(params, f, indent=4)
            self.set_status("Preset saved successfully.")
            
            
    def load_preset_TL(self):
        filename = askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return

        with open(filename, "r") as f:
            params = json.load(f)

        p = params

        self.TL_n.set(p["n"])
        self.TL_pixel_size.set(p["pixel_size"])
        self.TL_FWHM_source.set(p["FWHM_source"])
        self.TL_BeamShape.set(p["Beam_Shape"])
        self.TL_Beam_Spectrum.set(p["Beam_Spectrum"])
        self.TL_beam_energy.set(p["energy"])
        self.TL_DSO.set(p["DSO"])
        self.TL_DOG1.set(p["DOG1"])
        self.TL_Period_G1.set(p["Period_G1"])
        self.TL_G1_Phase.set(p["G1_Phase"])
        self.TL_steps.set(p["steps"])
        self.TL_step_length.set(p["step_length"])
        self.TL_Object.set(p["Object"])
        self.TL_radius.set(p["radius"])
        self.TL_material.set(p["material"])

        self.set_status("Preset loaded successfully.")
    
    def load_preset_Inline(self):
        filename = askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return

        with open(filename, "r") as f:
            params = json.load(f)

        p = params

        self.i_n.set(p["n"])
        self.i_pixel_size.set(p["pixel_size"])
        self.i_FWHM_source.set(p["FWHM_source"])
        self.i_Beam_Shape.set(p["Beam_Shape"])
        self.i_Beam_Spectrum.set(p["Beam_Spectrum"])
        self.i_beam_energy.set(p["energy"])
        self.i_DSO.set(p["DSO"])
        self.i_DOD.set(p["DOD"])
        self.i_Object.set(p["Object"])
        self.i_radius.set(p["radius"])
        self.i_material.set(p["material"])
        self.i_image_option.set(p["image_option"])
        self.i_resolution.set(p["resolution"])
        self.i_inner_radius.set(p["inner_radius"])
        self.i_xshift.set(p["xshift"])
        self.i_yshift.set(p["yshift"])
        self.i_orientation.set(p["orientation"])
        self.i_FWHM_detector.set(p["FWHM_detector"])
        self.i_detector_pixel_size.set(p["detector_pixel_size"])

        self.set_status("Preset loaded successfully.")
        
    def get_inline_config(self):
        return {
            "n": self.i_n.get(),
            "pixel_size": self.i_pixel_size.get(),
            "DSO": self.i_DSO.get(),
            "DOD": self.i_DOD.get(),
            "FWHM_source": self.i_FWHM_source.get(),
            "Beam_Shape": self.i_Beam_Shape.get(),
            "Beam_Spectrum": self.i_Beam_Spectrum.get(),
            "beam_energy": self.i_beam_energy.get(),
            "Object": self.i_Object.get(),
            "radius": self.i_radius.get(),
            "inner_radius": self.i_inner_radius.get(),
            "xshift": self.i_xshift.get(),
            "yshift": self.i_yshift.get(),
            "material": self.i_material.get(),
            "image_option": self.i_image_option.get(),
            "detector_pixel_size": self.i_detector_pixel_size.get(),
            "FWHM_detector": self.i_FWHM_detector.get(),
            "resolution": self.i_resolution.get(),
        }
        
    def get_TL_config(self):
        return {
            "n": self.TL_n.get(),
            "pixel_size": self.TL_pixel_size.get(),
            "DSO": self.TL_DSO.get(),
            "DOG1": self.TL_DOG1.get(),
            "FWHM_source": self.TL_FWHM_source.get(),
            "Beam_Shape": self.TL_BeamShape.get(),
            "Beam_Spectrum": self.TL_Beam_Spectrum.get(),
            "beam_energy": self.TL_beam_energy.get(),
            "Period_G1": self.TL_Period_G1.get(),
            "G1_Phase": self.TL_G1_Phase.get(),
            "steps": self.TL_steps.get(),
            "step_length": self.TL_step_length.get(),
            "Object": self.TL_Object.get(),
            "radius": self.TL_radius.get(),
            "inner_radius": self.TL_inner_radius.get(),
            "xshift": self.TL_xshift.get(),
            "yshift": self.TL_yshift.get(),
            "material": self.TL_material.get(),
            "image_option": self.TL_image_option.get(),
            "detector_pixel_size": self.TL_detector_pixel_size.get(),
            "resolution": self.TL_resolution.get(),
        }

    def save_image(self, data):
        files = [('All Files', '*.*'), 
                    ('Python Files', '*.py'),
                    ('HDF5 File', '*.hdf5'),
                    ('Tiff File', '*.tif')]
        file = asksaveasfilename(filetypes = files, defaultextension = '.tif')
            #file = asksaveasfilename()
        if not file: 
            return
        
        im = Image.fromarray(data)
        sv = im.save(file)

    def save_stack_image(self, data):
        files = [('All Files', '*.*'), 
                    ('Python Files', '*.py'),
                    ('HDF5 File', '*.hdf5'),
                    ('Tiff File', '*.tif')]
        file = asksaveasfilename(filetypes = files, defaultextension = '.tif')
            #file = asksaveasfilename()
        if not file: 
            return
        
        data = np.stack(data, axis =0)
        tifffile.imwrite(file, data.astype(np.float32), photometric='minisblack')
        #imageio.volwrite(file,im)
    
    def set_status(self, text):
        self.status_var.set(text)
        self.master.update_idletasks()
        
    def set_status_threadsafe(self, text):
        self.master.after(0, self.set_status, text)
        
    def set_progress(self, value):
        self.progress_var.set(value)
        self.master.update_idletasks()
        
    def set_progress_threadsafe(self, value):
        self.master.after(0, lambda: self.set_progress(value))

    def reset_progress(self):
        self.set_progress(0.0)
        
    def reset_progress_threadsafe(self):
        self.master.after(0, self.reset_progress)
    
    def make_progress_callback(self, prefix):
        def cb(fraction):
            try:
                frac = float(fraction)
            except Exception:
                frac = 0.0
            frac = max(0.0, min(1.0, frac))
            percent = frac * 100.0

            def _update():
                self.set_progress(percent)
                self.update_loading_overlay(percent, prefix=prefix)
                self.set_status(f"{prefix}... {int(percent)} %")

            self.master.after(0, _update)

        return cb

    
    def export_inline_zip(self, intensity_array):
        """Export inline simulation config + result as a ZIP."""

        zip_path = asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")])
        if not zip_path:
            return

        config = self.get_inline_config()
        config_json = json.dumps(config, indent=2)

        tiff_buffer = io.BytesIO()
        tifffile.imwrite(tiff_buffer, intensity_array.astype(np.float32))
        tiff_buffer.seek(0)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        readme = (
            "XPCIpy Inline Simulation\n"
            f"Timestamp: {timestamp}\n\n"
            "This ZIP contains:\n"
            "- inline_config.json -> simulation parameters\n"
            "- intensity.tif-> output intensity image\n"
        )

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("inline_config.json", config_json)
            zf.writestr("README.txt", readme)
            zf.writestr("intensity.tif", tiff_buffer.getvalue())
            
    def export_TL_zip(self, i_stack, ir_stack):
        """Export Talbot-Lau simulation config + result as a ZIP."""

        zip_path = asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")])
        if not zip_path:
            return

        config = self.get_TL_config()
        config_json = json.dumps(config, indent=2)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        i_arr = np.asarray(i_stack)
        ir_arr = np.asarray(ir_stack)

        if i_arr.ndim == 2:
            i_arr = i_arr[np.newaxis, ...]
        if ir_arr.ndim == 2:
            ir_arr = ir_arr[np.newaxis, ...]

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("TL_config.json", config_json)
            
            buf_obj = io.BytesIO()
            tifffile.imwrite(buf_obj, i_arr.astype(np.float32), photometric="minisblack")
            zf.writestr("object_stack.tif", buf_obj.getvalue())

            buf_ref = io.BytesIO()
            tifffile.imwrite(buf_ref, ir_arr.astype(np.float32), photometric="minisblack")
            zf.writestr("reference_stack.tif", buf_ref.getvalue())

            readme_text = (
                "Talbot-Lau phase-contrast simulation results\n"
                f"Timestamp: {timestamp}\n\n"
                "Files:\n"
                "  - TL_config.json: simulation parameters\n"
                "  - object_stack.tif: phase-stepping stack with object\n"
                "  - reference_stack.tif: phase-stepping stack without object\n"
            )
            zf.writestr("README.txt", readme_text)

    def run_with_error_handling(self, func, status_text):
        def worker():
            try:
                self.set_status_threadsafe(status_text)
                self.reset_progress_threadsafe()
                base_text = status_text.replace("...", "")
                self.update_loading_overlay_threadsafe(0.0, prefix=base_text or "Loading")
        
                func()
                self.set_progress_threadsafe(100.0)
                self.update_loading_overlay_threadsafe(100.0, prefix=base_text or "Loading")
                self.set_status_threadsafe(status_text.replace("...", " finished!"))
            except Exception as e:
                traceback.print_exc()
                self.set_status_threadsafe("Error.")
                self.reset_progress_threadsafe()
                self.show_error_threadsafe(e)
            finally:
                self.set_ui_busy_threadsafe(False)
                self.hide_loading_overlay_threadsafe()

        self.set_ui_busy(True)
        base_text = status_text.replace("...", "")
        self.show_loading_overlay_threadsafe(base_text if base_text else "Loading")
        threading.Thread(target=worker, daemon=True).start() # Run in daemon thread
        
    def show_error_threadsafe(self, e):
        def _show():
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        self.master.after(0, _show)
            
    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()
            
    def set_ui_busy(self, busy: bool):
        """
        busy = True  -> disable
        busy = False -> normal
        """
        state = "disabled" if busy else "normal"
        
        INTERACTIVE_TYPES = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            ttk.Combobox,
            tk.Checkbutton, ttk.Checkbutton,
            tk.Radiobutton, ttk.Radiobutton,
            tk.Spinbox,
            ToggleButton,
        )

        def recurse(widget):
            for child in widget.winfo_children():
                if isinstance(child, INTERACTIVE_TYPES):
                    try:
                        child.configure(state=state)
                    except tk.TclError:
                        pass
                recurse(child)

        recurse(self.master)

        try:
            self.master.configure(cursor="watch" if busy else "")
        except tk.TclError:
            pass
        
    def set_ui_busy_threadsafe(self, busy: bool):
        self.master.after(0, lambda: self.set_ui_busy(busy))
        
    #Transparent Loading Screen
    
    def _sync_overlay_to_master(self, event=None):
        if self.overlay is None:
            return

        try:
            self.overlay.deiconify()
            self.overlay.lift(self.master)
        except tk.TclError:
            return

        self.master.update_idletasks()
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        if w <= 1 or h <= 1:
            return

        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        self.overlay.geometry(f"{w}x{h}+{x}+{y}")
    
    def show_loading_overlay(self, message="Loading"):

        if self.overlay is not None and self.overlay.winfo_exists():
            try:
                self.overlay.lift(self.master)
            except tk.TclError:
                pass
            return

        self.master.update_idletasks()
        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        w = self.master.winfo_width()
        h = self.master.winfo_height()

        overlay = tk.Toplevel(self.master)
        overlay.overrideredirect(True)
        overlay.attributes("-alpha", 0.75)
        overlay.configure(background="#000000")
        overlay.geometry(f"{w}x{h}+{x}+{y}")
        overlay.lift(self.master)
        overlay.transient(self.master)

        frame = tk.Frame(overlay, bg="#000000")
        frame.pack(expand=True, fill="both")

        label = tk.Label(
            frame,
            text=message,
            fg="white",
            bg="#000000",
            font=("Segoe UI", 16, "bold")
        )
        label.pack(pady=10)

        pb_var = tk.DoubleVar(value=0.0)
        pb = ttk.Progressbar(
            frame,
            variable=pb_var,
            maximum=100,
            mode="determinate",
            length=250
        )
        pb.pack(pady=10)

        self.overlay = overlay
        self.overlay_label = label
        self.overlay_progress = pb
        self.overlay_progress_var = pb_var

        overlay.update_idletasks()
        
    def show_loading_overlay_threadsafe(self, message="Loading"):
        self.master.after(0, lambda: self.show_loading_overlay(message))

    def update_loading_overlay(self, percent, prefix="Loading"):
        if self.overlay is None or not self.overlay.winfo_exists():
            self.show_loading_overlay(prefix)

        try:
            if self.overlay_label is not None:
                self.overlay_label.config(text=f"{prefix}... {int(percent)} %")
            if self.overlay_progress_var is not None:
                self.overlay_progress_var.set(percent)

            self.overlay.lift(self.master)
        except tk.TclError:
            pass
            
    def update_loading_overlay_threadsafe(self, percent, prefix="Loading"):
        self.master.after(0, lambda: self.update_loading_overlay(percent, prefix))

    def hide_loading_overlay(self):
        if self.overlay is not None:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass

        self.overlay = None
        self.overlay_label = None
        self.overlay_progress = None
        self.overlay_progress_var = None
        
    def hide_loading_overlay_threadsafe(self):
        self.master.after(0, self.hide_loading_overlay)
        
    def send_to_TLREC(self, i_stack, ir_stack):
        if not hasattr(self, "tlrec_gui"):
            self.set_status("TLRec GUI is not available.")
            return
        
        self.tab_container.select(self.TLRec_tab)
        self.tlrec_gui.load_from_arrays(i_stack, ir_stack, label="Simulation")
        
    def gui_check_grating_sampling(self, period_px):
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf

        pcsim_utils.check_grating_sampling(period_px)

        sys.stdout = old_stdout
        msg = buf.getvalue().strip()

        if "WARNING" in msg:
            messagebox.showwarning("Grating Sampling Warning", msg)

    def gui_check_phase_stepping(self, steps, period_px, step_size_px):
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf

        pcsim_utils.check_phase_stepping(steps, period_px, step_size_px)

        sys.stdout = old_stdout
        msg = buf.getvalue().strip()

        if "WARNING" in msg:
            messagebox.showwarning("Phase Stepping Warning", msg)
            
    def verify_physical_values_TL(self):
        Period_G1 = self.TL_Period_G1.get()
        Talbot_multiple = self.TL_TLmultiple.get()
        FWHM_source = self.TL_FWHM_source.get()
        energy = self.TL_beam_energy.get()
        n = self.TL_n.get()
        pixel_size = self.TL_pixel_size.get()
        FWHM_source = self.TL_FWHM_source.get()
        DSG1 = self.TL_DSO.get()
        DOG1 = self.TL_DOG1.get()
        object = self.TL_Object.get()
        radius = self.TL_radius.get()
        inner_radius = self.TL_inner_radius.get()
        FWHM_detector = self.TL_resolution.get()
        detector_pixel_size = self.TL_detector_pixel_size.get()
        DSO = DSG1-DOG1
        
        
        if Period_G1 <= 0 or energy <= 0  or Talbot_multiple <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Period G1, Energy and Talbot Multiple are positive values.")
            return False
        
        if FWHM_source <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        
        if object == "Sphere":
            if radius <= 0:
                messagebox.showerror("Invalid Parameter", "Sphere radius must be > 0.")
                return False

        if object == "Cylinder":
            if radius <= 0:
                messagebox.showerror("Invalid Parameter", "Cylinder outer radius must be > 0.")
                return False

            if inner_radius < 0:
                messagebox.showerror("Invalid Parameter", "Cylinder inner radius cannot be negative.")
                return False

            if inner_radius >= radius:
                messagebox.showerror("Invalid Parameter", "Cylinder inner radius must be smaller than outer radius.")
                return False
        
        if n <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        
        if detector_pixel_size <=0 or FWHM_detector <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Detector Pixel Size and Detector FWHM are positive values.")
            return False
        if DSO <=0 or DOG1 <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that DSO and DOG1 are positive values.")
            return False
        if pixel_size <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        
        return True
    
    def verify_physical_values_inline(self):
    
        n = self.i_n.get()
        DSO = self.i_DSO.get()
        DOD = self.i_DOD.get()
        pixel_size = self.i_pixel_size.get()
        FWHM_source = self.i_FWHM_source.get()
        Object = self.i_Object.get()
        FWHM_detector = self.i_FWHM_detector.get()
        detector_pixel_size = self.i_detector_pixel_size.get()
        radius = self.i_radius.get()
        inner_radius = self.i_inner_radius.get()
        
        if n <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        if DSO <=0 or DOD <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that DSO and DOD are positive values.")
            return False
        if pixel_size <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        if FWHM_source <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        if detector_pixel_size <=0 or FWHM_detector <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Detector Pixel Size and Detector FWHM are positive values.")
            return False
        if Object == "Sphere":
            if radius <= 0:
                messagebox.showerror("Invalid Parameter", "Sphere radius must be > 0.")
                return False

        if Object == "Cylinder":
            if radius <= 0:
                messagebox.showerror("Invalid Parameter", "Cylinder outer radius must be > 0.")
                return False

            if inner_radius < 0:
                messagebox.showerror("Invalid Parameter", "Cylinder inner radius cannot be negative.")
                return False

            if inner_radius >= radius:
                messagebox.showerror("Invalid Parameter", "Cylinder inner radius must be smaller than outer radius.")
                return False
        return True
    
    def verify_physical_values_checkTL(self):
        
        n = self.c_n.get()
        pixel_size = self.c_pixel_size.get() #um
        FWHM_source = self.c_FWHM_source.get()
        Energy = self.c_energy.get() #keV
        Period = self.c_period.get() # um
        DC = self.c_DC.get()
        bar_height = self.c_bar_height.get()
        multiples = self.c_multiple.get()
        iterations = self.c_iterations.get()
        grating_opt = self.c_grating_option.get()
        
        if n <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        if pixel_size <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        if FWHM_source <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        if Energy <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Energy is a positive value.")
            return False
        if Period <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Grating Period is a positive value.")
            return False
        if DC <=0 or DC >1:
            messagebox.showerror("Invalid Parameters", "Please ensure that Duty Cycle is between 0 and 1.")
            return False
        if grating_opt == "Custom":
            if bar_height <= 0:
                messagebox.showerror("Invalid Parameter", "For a custom grating, bar height must be > 0 µm.")
                return False
        if multiples <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Talbot multiples is a positive value.")
            return False
        if iterations <=0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of calculations (iterations) is a positive value.")
            return False
        return True
    
    def add_tooltip(self, widget, text):
        ToolTip(widget, text)
    