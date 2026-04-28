import os
import json
import copy
import sys
import threading
import traceback

import numpy as np
import tifffile
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename
from PIL import Image, ImageTk

from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from GUI.ui.styles import Styles as stl
from GUI.ui.widgets import Widget as wg
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.ui.widgets import ToggleButton
from GUI.ui.tooltips import ToolTip
from GUI.utils import resource_path

from GUI.pages.help_window import HelpWindow
from GUI.pages.info_windows import LicenseWindow, CiteWindow
import src.PCSim.detector as detector
import src.PCSim.Objects as obj
from src.PCSim.material import list_available_materials
from GUI.pages.tabs.inline_tab import InlineTab
from GUI.pages.tabs.checktl_tab import CheckTLTab
from GUI.pages.tabs.tl_tab import TLTab
from GUI.pages.tabs.sns_tab import SNSTab
from GUI.pages.tabs.tlrec_tab import TLRecTab

class PCSim_gui(InlineTab, TLTab, CheckTLTab, SNSTab, TLRecTab):

    def __init__(self, master):

        self.master = master

        stl.configure_style()

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)

        # --- STATUS BAR ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.master, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.grid(row=1, column=0, sticky="ew")

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(self.master, variable=self.progress_var, maximum=100,
            mode="determinate")
        
        self.master.grid_rowconfigure(2, weight=0)
        self.progress_bar.grid(row=2, column=0, sticky="ew")

        # OVERLAY
        self.overlay = None
        self.overlay_label = None
        self.overlay_progress = None
        self.overlay_progress_var = None

        #NOTEBOOK
        self.tab_container = ttk.Notebook(self.master)
        self.tab_container.grid(row=0, column=0, sticky="nsew")

        #HELP MENU-
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help / User Guide", command=self.open_help_window)
        help_menu.add_command(label="How to cite XPCIpy", command=self.open_cite_window)
        help_menu.add_command(label="License", command=self.open_license_window)
        menubar.add_cascade(label="Help", menu=help_menu)

        #LISTS
        spectra_path = resource_path("Resources/Spectra")
        self.Beam_Spectrum_OPTIONS = sorted([
            f for f in os.listdir(spectra_path)
            if os.path.isfile(os.path.join(spectra_path, f))])
        
        self.Beam_Spectrum_OPTIONS.append("Monoenergetic")
        self.Beam_Shape_OPTIONS = ["Plane", "Conical"]
        self.Object_OPTIONS = ["Sphere", "Cylinder"]
        self.Image_OPTIONS = ["Ideal", "Realistic"]
        materials_path = resource_path("Resources/complex_refractive_index")
        self.material_file_options = sorted([
            f for f in os.listdir(materials_path)
            if os.path.isfile(os.path.join(materials_path, f))
        ])

        self.initialize_vars()
        self.create_tabs()
        self._ui_busy = False
        self.configure_shortcuts()

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

    def configure_shortcuts(self):
        self.master.bind_all("<Return>", self._on_shortcut_run)
        self.master.bind_all("<KP_Enter>", self._on_shortcut_run)
        self.master.bind_all("<Control-Return>", self._on_shortcut_run)
        self.master.bind_all("<Control-s>", self._on_shortcut_save)
        self.master.bind_all("<Control-S>", self._on_shortcut_save)
        self.master.bind_all("<Control-Shift-S>", self._on_shortcut_save_preset)
        self.master.bind_all("<F1>", self._on_shortcut_help)
        self.master.bind_all("<Control-q>", self._on_shortcut_exit)
        self.master.bind_all("<Control-Q>", self._on_shortcut_exit)

    def _active_tab_widget(self):
        try:
            tab_id = self.tab_container.select()
            return self.master.nametowidget(tab_id)
        except Exception:
            return None

    def _on_shortcut_run(self, _event=None):
        if self._ui_busy:
            return "break"
        active = self._active_tab_widget()
        if active is self.inline_tab:
            self.RunInline()
        elif active is self.sns_tab:
            self.RunSimpleNumerical()
        elif active is self.check_TL_tab:
            self.RunCheckTL()
        elif active is self.TL_tab:
            self.RunTL()
        else:
            self.set_status("No run action available for this tab.")
        return "break"

    def _on_shortcut_save(self, _event=None):
        active = self._active_tab_widget()
        if active is self.inline_tab:
            if hasattr(self, "inline_display_intensity"):
                self.save_image(self.inline_display_intensity)
            else:
                self.set_status("Run Inline simulation first to save an image.")
        elif active is self.sns_tab:
            if hasattr(self, "sns_last_display"):
                self.save_image(self.sns_last_display)
            else:
                self.set_status("Run Simple Numerical simulation first to save an image.")
        elif active is self.check_TL_tab:
            if hasattr(self, "check_tl_intensities"):
                self.save_image(self.check_tl_intensities)
            else:
                self.set_status("Run Check Talbot-Lau first to save an image.")
        elif active is self.TL_tab:
            if hasattr(self, "TL_i_display"):
                self.save_stack_image(self.TL_i_display)
            else:
                self.set_status("Run TL simulation first to save images.")
        else:
            self.set_status("No save action available for this tab.")
        return "break"

    def _on_shortcut_save_preset(self, _event=None):
        active = self._active_tab_widget()
        if active is self.inline_tab:
            self.save_preset_Inline()
        elif active is self.sns_tab:
            self.save_preset_SNS()
        elif active is self.TL_tab:
            self.save_preset_TL()
        else:
            self.set_status("No preset save action for this tab.")
        return "break"

    def _on_shortcut_help(self, _event=None):
        self.open_help_window()
        return "break"

    def _on_shortcut_exit(self, _event=None):
        self.close_app()
        return "break"

    def create_tabs(self):
        self.TLRec_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.inline_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.sns_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.check_TL_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.TL_tab = ttk.Frame(self.tab_container, style="TFrame")
        self.TL_batch_tab = ttk.Frame(self.tab_container, style="TFrame")

        self.tab_container.add(self.TLRec_tab, text='TLRec')
        self.tab_container.add(self.inline_tab, text="Inline Simulation")
        self.tab_container.add(self.sns_tab, text="Simple Numerical Simulation")
        self.tab_container.add(self.check_TL_tab, text="Check Talbot-Lau effect")
        self.tab_container.add(self.TL_tab, text="Talbot Lau Phase Contrast Simulation")
        self.tab_container.add(self.TL_batch_tab, text="TLRec batch (in develop)")

        self.populate_TLRec_tab()
        self.populate_inline_tab()
        self.populate_sns_tab()
        self.populate_checkTL_tab()
        self.populate_TL_tab()
        self.populate_TLRec_batch_tab()

    def initialize_vars(self):

        config_path = resource_path("GUI/config/config_inline.json")

        # Inline
        self.i_n = tk.IntVar()
        self.i_pixel_size = tk.DoubleVar()
        self.i_DSO = tk.DoubleVar()
        self.i_DOD = tk.DoubleVar()
        self.i_FWHM_source = tk.DoubleVar()
        self.i_Beam_Shape = tk.StringVar()
        self.i_Beam_Spectrum = tk.StringVar()
        self.i_beam_energy = tk.DoubleVar()
        self.i_Object = tk.StringVar()
        self.i_image_option = tk.StringVar()
        self.i_resolution = tk.IntVar()
        self.i_outer_radius = tk.DoubleVar()
        self.i_inner_radius = tk.DoubleVar()
        self.i_xshift = tk.IntVar()
        self.i_yshift = tk.IntVar()
        self.i_material = tk.StringVar()
        self.i_orientation = tk.StringVar()
        self.i_FWHM_detector = tk.DoubleVar()
        self.i_detector_pixel_size = tk.DoubleVar()
        self.i_zip_var = tk.BooleanVar(value=False)
        self.inline_objects_summary_var = tk.StringVar(value="No objects configured.")

        with open(config_path) as json_path:
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
            self.i_outer_radius.set(default_inline_conf['outer_radius'])
            self.i_inner_radius.set(default_inline_conf['inner_radius'])
            self.i_xshift.set(default_inline_conf['xshift'])
            self.i_yshift.set(default_inline_conf['yshift'])
            self.i_material.set(default_inline_conf['material'])
            self.i_image_option.set(default_inline_conf['image_option'])
            self.i_orientation.set(default_inline_conf['orientation'])
            self.i_resolution.set(default_inline_conf['resolution'])
            self.i_FWHM_detector.set(default_inline_conf['FWHM_detector'])
            self.i_detector_pixel_size.set(default_inline_conf['detector_pixel_size'])

        self.inline_objects_data = self._normalize_object_specs([
            self._legacy_inline_object_spec()
        ], mode="inline")
        self._sync_inline_legacy_from_objects()

        # Simple Numerical Simulation
        self.sns_n = tk.IntVar(value=512)
        self.sns_pixel_size = tk.DoubleVar(value=1.0)
        self.sns_delta = tk.DoubleVar(value=1e-2)
        self.sns_beta = tk.DoubleVar(value=1e-6)
        self.sns_energy = tk.DoubleVar(value=20.0)
        self.sns_phase_steps = tk.IntVar(value=20)
        self.sns_noise_mean = tk.DoubleVar(value=0.0)
        self.sns_error_steps_mean = tk.DoubleVar(value=0.0)
        self.sns_error_dose_mean = tk.DoubleVar(value=0.0)
        self.sns_moire = tk.BooleanVar(value=False)
        self.sns_moire_fringes = tk.IntVar(value=10)
        self.sns_moire_profile = tk.StringVar(value='linear')
        self.sns_moire_direction = tk.StringVar(value='x')
        self.sns_moire_phase_scale = tk.DoubleVar(value=1.0)
        self.sns_moire_phase_offset = tk.DoubleVar(value=0.0)
        self.sns_axis = tk.IntVar(value=1)
        self.sns_df_strength = tk.DoubleVar(value=0.15)
        self.sns_geometry_type = tk.StringVar(value='sphere')
        self.sns_geometry_params = tk.StringVar(value='{"radius": 120.0}')
        self.sns_scene_json_path = tk.StringVar(value='')
        self.sns_zip_var = tk.BooleanVar(value=False)
        self.sns_layer_type = tk.StringVar(value='sphere')
        self.sns_layer_mode = tk.StringVar(value='add')
        self.sns_layer_shift_x = tk.DoubleVar(value=0.0)
        self.sns_layer_shift_y = tk.DoubleVar(value=0.0)
        self.sns_layer_angle = tk.DoubleVar(value=0.0)
        self.sns_layer_params = tk.StringVar(value='{"radius": 120.0}')
        self.sns_layer_optics_mode = tk.StringVar(value='global')
        self.sns_layer_material = tk.StringVar(value='Water')
        self.sns_layer_delta = tk.DoubleVar(value=1e-2)
        self.sns_layer_beta = tk.DoubleVar(value=1e-6)
        self.sns_material_options = sorted(list_available_materials(None))
        if self.sns_material_options and self.sns_layer_material.get() not in self.sns_material_options:
            self.sns_layer_material.set(self.sns_material_options[0])
        self.sns_layers_data = []
        self.sns_selected_layer_index = None

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

        config_path_checkTL = resource_path("GUI/config/config_checkTL.json")
        with open(config_path_checkTL) as json_path:
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

        # Talbot Lau
        self.TL_n = tk.IntVar()
        self.TL_pixel_size = tk.DoubleVar()
        self.TL_FWHM_source = tk.DoubleVar()
        self.TL_BeamShape = tk.StringVar()
        self.TL_Beam_Spectrum = tk.StringVar()
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
        self.TL_material = tk.StringVar()
        self.TL_xshift = tk.IntVar()
        self.TL_yshift = tk.IntVar()
        self.TL_orientation = tk.StringVar()
        self.TL_Period_G1 = tk.DoubleVar()
        self.TL_Period_G2 = tk.DoubleVar()
        self.TL_ThicknessG1 = tk.DoubleVar()
        self.TL_ThicknessG2 = tk.DoubleVar()
        self.TL_G1_Phase = tk.StringVar()
        self.TL_MovableGrating = tk.StringVar()
        self.TL_steps = tk.IntVar()
        self.TL_step_length = tk.DoubleVar()
        self.TL_resolution = tk.DoubleVar()
        self.TL_detector_pixel_size = tk.IntVar()
        self.TL_image_option = tk.StringVar()
        self.TL_zip_var = tk.BooleanVar(value=False)
        self.tl_objects_summary_var = tk.StringVar(value="No objects configured.")

        config_path_TLSim = resource_path("GUI/config/config_TLSim.json")
        with open(config_path_TLSim) as json_path:
            default_TL_conf = json.load(json_path)
            self.TL_n.set(default_TL_conf['n'])
            self.TL_FWHM_source.set(10.)
            self.TL_pixel_size.set(default_TL_conf['pixel_size'])
            self.TL_BeamShape.set(default_TL_conf['Beam_Shape'])
            self.TL_Beam_Spectrum.set(default_TL_conf['Beam_Spectrum'])
            self.TL_beam_energy.set(default_TL_conf['energy'])
            self.TL_DSO.set(default_TL_conf['DSG1'])
            self.TL_DOG1.set(default_TL_conf['DOG1'])
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

        self.tl_objects_data = self._normalize_object_specs([
            self._legacy_tl_object_spec()
        ], mode="tl")
        self._sync_tl_legacy_from_objects()

        # Detector post-processing (shared by inline + TL tabs)
        self.dp_pixel_det_um = tk.DoubleVar(value=0.0)
        self.dp_fwhm_det_um = tk.DoubleVar(value=0.0)
        self.dp_noise_type = tk.StringVar(value="gaussian")
        self.dp_gauss_sigma = tk.DoubleVar(value=0.0)
        self.dp_poisson_N0 = tk.DoubleVar(value=1e5)
        self.dp_random_seed = tk.StringVar(value="")


    def apply_changes(self):
        self._params_window.destroy()

    def _default_material_name(self):
        if self.material_file_options:
            return self.material_file_options[0]
        return "None"

    def _normalize_material_name(self, material_name):
        return os.path.splitext(str(material_name).strip())[0]

    def _legacy_inline_object_spec(self):
        return {
            "type": self.i_Object.get() or "Sphere",
            "position_cm": float(self.i_DSO.get()),
            "outer_radius": float(self.i_outer_radius.get()),
            "inner_radius": float(self.i_inner_radius.get()),
            "xshift": int(self.i_xshift.get()),
            "yshift": int(self.i_yshift.get()),
            "material": self.i_material.get() or self._default_material_name(),
            "orientation": self.i_orientation.get() or "Vertical",
            "is_insert": False,
        }

    def _legacy_tl_object_spec(self):
        return {
            "type": self.TL_Object.get() or "Sphere",
            "distance_to_g1_cm": float(self.TL_DOG1.get()),
            "outer_radius": float(self.TL_radius.get()),
            "inner_radius": float(self.TL_inner_radius.get()),
            "xshift": int(self.TL_xshift.get()),
            "yshift": int(self.TL_yshift.get()),
            "material": self.TL_material.get() or self._default_material_name(),
            "orientation": self.TL_orientation.get() or "Vertical",
            "is_insert": False,
        }

    def _sort_object_specs(self, objects_data, mode):
        objects_copy = copy.deepcopy(objects_data)
        if mode == "inline":
            return sorted(objects_copy, key=lambda item: float(item.get("position_cm", 0.0)))
        return sorted(objects_copy, key=lambda item: -float(item.get("distance_to_g1_cm", 0.0)))

    def _normalize_object_specs(self, objects_data, mode):
        if mode == "inline":
            fallback = self._legacy_inline_object_spec()
            position_key = "position_cm"
        else:
            fallback = self._legacy_tl_object_spec()
            position_key = "distance_to_g1_cm"

        normalized = []
        for raw in objects_data or []:
            if not isinstance(raw, dict):
                continue
            normalized.append({
                "type": str(raw.get("type", fallback["type"])).strip() or fallback["type"],
                position_key: float(raw.get(position_key, fallback[position_key])),
                "outer_radius": float(raw.get("outer_radius", fallback["outer_radius"])),
                "inner_radius": float(raw.get("inner_radius", fallback["inner_radius"])),
                "xshift": int(raw.get("xshift", fallback["xshift"])),
                "yshift": int(raw.get("yshift", fallback["yshift"])),
                "material": str(raw.get("material", fallback["material"])).strip() or fallback["material"],
                "orientation": str(raw.get("orientation", fallback["orientation"])).strip() or fallback["orientation"],
                "is_insert": bool(raw.get("is_insert", fallback.get("is_insert", False))),
            })

        if not normalized:
            normalized = [fallback]

        return self._sort_object_specs(normalized, mode)

    def _format_sim_object_display(self, spec, idx, mode):
        object_type = spec.get("type", "Sphere")
        material = self._normalize_material_name(spec.get("material", "")) or "?"
        radius = float(spec.get("outer_radius", 0.0))
        if object_type == "Cylinder":
            geometry_txt = (
                f"Cylinder Ro={radius:.2f} um, Ri={float(spec.get('inner_radius', 0.0)):.2f} um, "
                f"{spec.get('orientation', 'Vertical')}"
            )
        else:
            geometry_txt = f"Sphere R={radius:.2f} um"

        if mode == "inline":
            position_txt = f"z={float(spec.get('position_cm', 0.0)):.3f} cm"
        else:
            position_txt = f"DOG1={float(spec.get('distance_to_g1_cm', 0.0)):.3f} cm"

        insert_tag = " | insert" if bool(spec.get("is_insert", False)) else ""
        return f"{idx + 1:02d} | {position_txt} | {geometry_txt} | {material}{insert_tag}"

    def _objects_summary_text(self, objects_data, mode):
        if not objects_data:
            return "No objects configured."
        if len(objects_data) == 1:
            return self._format_sim_object_display(objects_data[0], 0, mode)
        return f"{len(objects_data)} objects. First: {self._format_sim_object_display(objects_data[0], 0, mode)}"

    def _sync_inline_legacy_from_objects(self):
        self.inline_objects_data = self._normalize_object_specs(self.inline_objects_data, mode="inline")
        primary = self.inline_objects_data[0]
        self.i_Object.set(primary["type"])
        self.i_DSO.set(float(primary["position_cm"]))
        self.i_outer_radius.set(float(primary["outer_radius"]))
        self.i_inner_radius.set(float(primary["inner_radius"]))
        self.i_xshift.set(int(primary["xshift"]))
        self.i_yshift.set(int(primary["yshift"]))
        self.i_material.set(primary["material"])
        self.i_orientation.set(primary["orientation"])
        self.inline_objects_summary_var.set(self._objects_summary_text(self.inline_objects_data, mode="inline"))

    def _sync_tl_legacy_from_objects(self):
        self.tl_objects_data = self._normalize_object_specs(self.tl_objects_data, mode="tl")
        primary = self.tl_objects_data[0]
        self.TL_Object.set(primary["type"])
        self.TL_DOG1.set(float(primary["distance_to_g1_cm"]))
        self.TL_radius.set(float(primary["outer_radius"]))
        self.TL_inner_radius.set(float(primary["inner_radius"]))
        self.TL_xshift.set(int(primary["xshift"]))
        self.TL_yshift.set(int(primary["yshift"]))
        self.TL_material.set(primary["material"])
        self.TL_orientation.set(primary["orientation"])
        self.tl_objects_summary_var.set(self._objects_summary_text(self.tl_objects_data, mode="tl"))

    def _validate_object_spec(self, spec, mode):
        object_type = str(spec.get("type", "")).strip()
        outer_radius = float(spec.get("outer_radius", 0.0))
        inner_radius = float(spec.get("inner_radius", 0.0))
        material = str(spec.get("material", "")).strip()

        if object_type not in self.Object_OPTIONS:
            raise ValueError(f"Unsupported object type: {object_type}")
        if not material or material == "None":
            raise ValueError("Each object requires a material.")

        if mode == "inline":
            position_cm = float(spec.get("position_cm", 0.0))
            detector_z = float(self.i_DSO.get()) + float(self.i_DOD.get())
            if position_cm <= 0:
                raise ValueError("Inline object position must be > 0 cm.")
            if detector_z > 0 and position_cm >= detector_z:
                raise ValueError("Inline object position must be before the detector plane.")
        else:
            dog1_cm = float(spec.get("distance_to_g1_cm", 0.0))
            dsg1_cm = float(self.TL_DSO.get())
            if dog1_cm <= 0:
                raise ValueError("TL object distance to G1 must be > 0 cm.")
            if dsg1_cm > 0 and dog1_cm >= dsg1_cm:
                raise ValueError("TL object distance to G1 must be smaller than Source-G1 distance.")

        if object_type == "Sphere":
            if outer_radius <= 0:
                raise ValueError("Sphere radius must be > 0.")
            if inner_radius < 0:
                raise ValueError("Sphere inner radius cannot be negative.")
            if inner_radius >= outer_radius:
                raise ValueError("Sphere inner radius must be smaller than outer radius.")
            return

        if outer_radius <= 0:
            raise ValueError("Cylinder outer radius must be > 0.")
        if inner_radius < 0:
            raise ValueError("Cylinder inner radius cannot be negative.")
        if inner_radius >= outer_radius:
            raise ValueError("Cylinder inner radius must be smaller than outer radius.")
        if str(spec.get("orientation", "")).strip() not in ("Horizontal", "Vertical"):
            raise ValueError("Cylinder orientation must be Horizontal or Vertical.")

    def _validate_object_collection(self, objects_data, mode):
        if not objects_data:
            raise ValueError("Configure at least one object.")
        for spec in self._normalize_object_specs(objects_data, mode):
            self._validate_object_spec(spec, mode)

    def _build_inline_objects(self, n, pixel_size):
        objects = []
        for spec in self._normalize_object_specs(self.inline_objects_data, mode="inline"):
            material = self._normalize_material_name(spec["material"])
            if spec["type"] == "Sphere":
                current = obj.Sphere(
                    n, spec["inner_radius"], spec["outer_radius"], pixel_size, material,
                    spec["position_cm"], spec["xshift"], spec["yshift"],
                )
            else:
                current = obj.Cylinder(
                    n, spec["outer_radius"], spec["inner_radius"], spec["orientation"],
                    pixel_size, material, spec["position_cm"], spec["xshift"], spec["yshift"],
                )
            current.is_insert = bool(spec.get("is_insert", False))
            objects.append(current)
        return objects

    def _build_tl_objects(self, n, pixel_size, dsg1_cm):
        objects = []
        for spec in self._normalize_object_specs(self.tl_objects_data, mode="tl"):
            material = self._normalize_material_name(spec["material"])
            dso_cm = float(dsg1_cm) - float(spec["distance_to_g1_cm"])
            if spec["type"] == "Sphere":
                current = obj.Sphere(
                    n, spec["inner_radius"], spec["outer_radius"], pixel_size, material,
                    dso_cm, spec["xshift"], spec["yshift"],
                )
            else:
                current = obj.Cylinder(
                    n, spec["outer_radius"], spec["inner_radius"], spec["orientation"],
                    pixel_size, material, dso_cm, spec["xshift"], spec["yshift"],
                )
            current.is_insert = bool(spec.get("is_insert", False))
            objects.append(current)
        return objects

    def _open_object_manager(self, mode):
        if mode == "inline":
            title = "Inline Object Manager"
            position_label = "Position from source (cm)"
            position_key = "position_cm"
            working_objects = self._normalize_object_specs(self.inline_objects_data, mode="inline")
            commit_changes = lambda data: self._commit_inline_objects(data)
            fallback_spec = self._legacy_inline_object_spec()
        else:
            title = "TL Object Manager"
            position_label = "Distance Object-G1 (cm)"
            position_key = "distance_to_g1_cm"
            working_objects = self._normalize_object_specs(self.tl_objects_data, mode="tl")
            commit_changes = lambda data: self._commit_tl_objects(data)
            fallback_spec = self._legacy_tl_object_spec()

        window = tk.Toplevel(self.master)
        window.title(title)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)

        root = ttk.Frame(window, padding=10)
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(root, text="Configured objects", padding=8)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            list_frame,
            height=10,
            exportselection=False,
            bg="#2a2a2a",
            fg="white",
            selectbackground="#555555",
            selectforeground="white",
        )
        listbox.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

        editor = ttk.LabelFrame(root, text="Object editor", padding=8)
        editor.grid(row=0, column=1, sticky="nsew")
        editor.grid_columnconfigure(1, weight=1)

        type_var = tk.StringVar(value=fallback_spec["type"])
        position_var = tk.DoubleVar(value=float(fallback_spec[position_key]))
        outer_radius_var = tk.DoubleVar(value=float(fallback_spec["outer_radius"]))
        inner_radius_var = tk.DoubleVar(value=float(fallback_spec["inner_radius"]))
        xshift_var = tk.IntVar(value=int(fallback_spec["xshift"]))
        yshift_var = tk.IntVar(value=int(fallback_spec["yshift"]))
        material_var = tk.StringVar(value=fallback_spec["material"] or self._default_material_name())
        orientation_var = tk.StringVar(value=fallback_spec["orientation"])
        is_insert_var = tk.BooleanVar(value=bool(fallback_spec.get("is_insert", False)))

        wg.create_label_combobox(editor, "Geometry", self.Object_OPTIONS, 0, 0, textvariable=type_var)
        wg.create_label_entry(editor, position_label, 1, 0, textvariable=position_var)
        wg.create_label_entry(editor, "Radius / outer radius (um)", 2, 0, textvariable=outer_radius_var)
        wg.create_label_entry(editor, "Inner radius (um)", 3, 0, textvariable=inner_radius_var)
        wg.create_label_combobox(editor, "Orientation", ["Horizontal", "Vertical"], 4, 0, textvariable=orientation_var)
        wg.create_label_entry(editor, "X shift (pixels)", 5, 0, textvariable=xshift_var)
        wg.create_label_entry(editor, "Y shift (pixels)", 6, 0, textvariable=yshift_var)
        wg.create_label_combobox(editor, "Material", self.material_file_options, 7, 0, textvariable=material_var)
        ttk.Checkbutton(editor, text="Use as insert (replace base thickness)", variable=is_insert_var).grid(
            row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0)
        )

        validation_var = tk.StringVar(value="")
        validation_lbl = ttk.Label(
            editor, textvariable=validation_var,
            foreground="tomato", wraplength=230, justify="left"
        )
        validation_lbl.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 0))

        selected_index = {"value": 0 if working_objects else None}

        def editor_from_spec(spec):
            type_var.set(spec.get("type", fallback_spec["type"]))
            position_var.set(float(spec.get(position_key, fallback_spec[position_key])))
            outer_radius_var.set(float(spec.get("outer_radius", fallback_spec["outer_radius"])))
            inner_radius_var.set(float(spec.get("inner_radius", fallback_spec["inner_radius"])))
            xshift_var.set(int(spec.get("xshift", fallback_spec["xshift"])))
            yshift_var.set(int(spec.get("yshift", fallback_spec["yshift"])))
            material_var.set(spec.get("material", fallback_spec["material"]))
            orientation_var.set(spec.get("orientation", fallback_spec["orientation"]))
            is_insert_var.set(bool(spec.get("is_insert", fallback_spec.get("is_insert", False))))

        def spec_from_editor():
            return {
                "type": type_var.get().strip() or fallback_spec["type"],
                position_key: float(position_var.get()),
                "outer_radius": float(outer_radius_var.get()),
                "inner_radius": float(inner_radius_var.get()),
                "xshift": int(xshift_var.get()),
                "yshift": int(yshift_var.get()),
                "material": material_var.get().strip() or self._default_material_name(),
                "orientation": orientation_var.get().strip() or "Vertical",
                "is_insert": bool(is_insert_var.get()),
            }

        def refresh_listbox():
            nonlocal working_objects
            working_objects = self._sort_object_specs(working_objects, mode)
            listbox.delete(0, tk.END)
            for idx, spec in enumerate(working_objects):
                listbox.insert(tk.END, self._format_sim_object_display(spec, idx, mode))
            if working_objects:
                current = selected_index["value"]
                if current is None or current >= len(working_objects):
                    current = 0
                selected_index["value"] = current
                listbox.selection_clear(0, tk.END)
                listbox.selection_set(current)
                listbox.activate(current)
                editor_from_spec(working_objects[current])
            else:
                selected_index["value"] = None
                editor_from_spec(fallback_spec)

        def add_object():
            try:
                spec = spec_from_editor()
                self._validate_object_spec(spec, mode)
            except Exception as exc:
                messagebox.showerror("Object error", str(exc), parent=window)
                return
            working_objects.append(spec)
            selected_index["value"] = len(working_objects) - 1
            refresh_listbox()

        def update_object():
            if selected_index["value"] is None:
                messagebox.showwarning("Object manager", "Select an object first.", parent=window)
                return
            try:
                spec = spec_from_editor()
                self._validate_object_spec(spec, mode)
            except Exception as exc:
                messagebox.showerror("Object error", str(exc), parent=window)
                return
            working_objects[selected_index["value"]] = spec
            refresh_listbox()

        def remove_object():
            if selected_index["value"] is None:
                return
            del working_objects[selected_index["value"]]
            refresh_listbox()

        def on_select(_event=None):
            selection = listbox.curselection()
            if not selection:
                return
            selected_index["value"] = int(selection[0])
            editor_from_spec(working_objects[selected_index["value"]])

        def apply_manager_changes():
            try:
                self._validate_object_collection(working_objects, mode)
            except Exception as exc:
                messagebox.showerror("Object error", str(exc), parent=window)
                return
            commit_changes(working_objects)
            window.destroy()

        listbox.bind("<<ListboxSelect>>", on_select)
        btn_add = wg.create_button(list_frame, "Add", 1, 0, command=add_object)
        btn_update = wg.create_button(list_frame, "Update", 1, 1, command=update_object)
        wg.create_button(list_frame, "Remove", 2, 0, command=remove_object)
        wg.create_button(list_frame, "Apply", 2, 1, command=apply_manager_changes)

        def _validate_editor(*_):
            try:
                spec = spec_from_editor()
                self._validate_object_spec(spec, mode)
                validation_var.set("")
                btn_add.state(["!disabled"])
                btn_update.state(["!disabled"])
            except Exception as exc:
                validation_var.set(str(exc))
                btn_add.state(["disabled"])
                btn_update.state(["disabled"])

        for _v in (type_var, position_var, outer_radius_var, inner_radius_var,
                 xshift_var, yshift_var, material_var, orientation_var, is_insert_var):
            _v.trace_add("write", _validate_editor)

        refresh_listbox()
        _validate_editor()

    def _commit_inline_objects(self, objects_data):
        self.inline_objects_data = self._normalize_object_specs(objects_data, mode="inline")
        self._sync_inline_legacy_from_objects()

    def _commit_tl_objects(self, objects_data):
        self.tl_objects_data = self._normalize_object_specs(objects_data, mode="tl")
        self._sync_tl_legacy_from_objects()


    def initialize_Figure(self, frame, figsize, row, column, columnspan=1):
        fig = Figure(figsize=figsize)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        fig.set_facecolor("#333333")
        canvas.draw()
        w = canvas.get_tk_widget()
        w.grid(row=row, column=column, columnspan=columnspan, padx=5, pady=5, sticky='nsew')
        frame.grid_rowconfigure(row, weight=1)
        frame.grid_columnconfigure(column, weight=1)

    def Plot_Figure(self, frame, image, row, column, figsize, title, columnspan=1):
        for w in frame.winfo_children():
            if isinstance(w, tk.Canvas):
                w.destroy()

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
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()

        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        w = canvas1.get_tk_widget()
        w.grid(row=row, column=column, columnspan=columnspan, padx=5, pady=5, sticky="nsew")

        frame.grid_rowconfigure(row, weight=1)
        frame.grid_columnconfigure(column, weight=1)
        frame.update_idletasks()

        def _redraw(evt=None):
            try:
                canvas1.draw_idle()
            except Exception:
                pass

        frame.update_idletasks()
        frame.after_idle(_redraw)

        if not getattr(frame, "_mpl_cfg_bound", False):
            frame.bind("<Configure>", _redraw)
            frame._mpl_cfg_bound = True

    def save_image(self, data):
        files = [('All Files', '*.*'), ('Tiff File', '*.tif')]
        file = asksaveasfilename(filetypes=files, defaultextension='.tif')
        if not file:
            return
        im = Image.fromarray(data)
        im.save(file)

    def save_stack_image(self, data):
        files = [('All Files', '*.*'), ('Tiff File', '*.tif')]
        file = asksaveasfilename(filetypes=files, defaultextension='.tif')
        if not file:
            return
        data = np.stack(data, axis=0)
        tifffile.imwrite(file, data.astype(np.float32), photometric='minisblack')

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
        threading.Thread(target=worker, daemon=True).start()

    def show_error_threadsafe(self, e):
        def _show():
            messagebox.showerror("Error", f"An error occurred:\n{e}")
        self.master.after(0, _show)

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def set_ui_busy(self, busy: bool):
        self._ui_busy = bool(busy)

        INTERACTIVE_TYPES = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            ttk.Combobox,
            tk.Checkbutton, ttk.Checkbutton,
            tk.Radiobutton, ttk.Radiobutton,
            tk.Spinbox,
            ToggleButton,
        )

        def get_state(w):
            if hasattr(w, "instate") and hasattr(w, "state"):
                st = w.state()
                return "disabled" if "disabled" in st else "normal"
            try:
                return str(w.cget("state"))
            except Exception:
                return "normal"

        def set_state(w, s):
            if hasattr(w, "instate") and hasattr(w, "state"):
                if s == "disabled":
                    w.state(["disabled"])
                else:
                    w.state(["!disabled"])
                return
            try:
                w.configure(state=s)
            except Exception:
                pass

        def recurse(widget):
            for child in widget.winfo_children():
                if isinstance(child, INTERACTIVE_TYPES):
                    if busy:
                        if not hasattr(child, "_pre_busy_state"):
                            child._pre_busy_state = get_state(child)
                        set_state(child, "disabled")
                    else:
                        prev = getattr(child, "_pre_busy_state", "normal")
                        set_state(child, prev)
                        if hasattr(child, "_pre_busy_state"):
                            delattr(child, "_pre_busy_state")
                recurse(child)

        recurse(self.master)

        try:
            self.master.configure(cursor="watch" if busy else "")
        except tk.TclError:
            pass

    def set_ui_busy_threadsafe(self, busy: bool):
        self.master.after(0, lambda: self.set_ui_busy(busy))

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


    def _watch(self, entry_widget, tk_var, condition):
        def _check(*_):
            try:
                val = tk_var.get()
                valid = bool(condition(val))
            except (tk.TclError, ValueError):
                valid = False
            entry_widget.configure(style="Invalid.TEntry" if not valid else "TEntry")
        tk_var.trace_add("write", _check)
        _check()

    def add_tooltip(self, widget, text):
        ToolTip(widget, text)

    def add_detector_post_panel(self, parent_frame, mode="inline", row=99):
        lf = ttk.LabelFrame(parent_frame, text="Detector (post-processing, no rerun)", padding=(8, 6))
        lf.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))

        wg.create_label_entry(lf, "Pixel size detector (um) [0 = use tab value]:", 0, 0, textvariable=self.dp_pixel_det_um, padx=10)
        wg.create_label_entry(lf, "Detector FWHM (um) [0 = use tab value]:", 1, 0, textvariable=self.dp_fwhm_det_um, padx=10)
        wg.create_label_combobox(lf, "Noise type", ["none", "poisson", "gaussian", "poisson+gaussian"], 2, 0, textvariable=self.dp_noise_type)
        wg.create_label_entry(lf, "Gaussian sigma (only gaussian):", 3, 0, textvariable=self.dp_gauss_sigma, padx=10)
        wg.create_label_entry(lf, "Photons per pixel (only poisson):", 4, 0, textvariable=self.dp_poisson_N0, padx=10)
        wg.create_label_entry(lf, "Random seed (optional):", 5, 0, textvariable=self.dp_random_seed, padx=10)

        bt_frame = ttk.Frame(lf, style="TFrame")
        bt_frame.grid(row=6, column=0, sticky="ew", pady=(6, 0))
        bt_frame.columnconfigure(0, weight=1)
        bt_frame.columnconfigure(1, weight=1)

        ttk.Button(bt_frame, text="Apply", command=lambda: self.apply_detector_post(mode)).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(bt_frame, text="Reset (raw)", command=lambda: self.reset_detector_post(mode)).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        return lf

    def get_post_detector_params(self, mode="inline"):
        noise = self.dp_noise_type.get().strip().lower()
        if noise == "none":
            noise = None

        gauss_sigma = float(self.dp_gauss_sigma.get())
        N0_poisson = float(self.dp_poisson_N0.get())

        if mode == "inline":
            tab_pixel_det = float(self.i_detector_pixel_size.get())
            tab_fwhm = float(self.i_FWHM_detector.get())
            base_px = float(self.i_pixel_size.get())
        else:
            tab_pixel_det = float(self.TL_detector_pixel_size.get())
            tab_fwhm = float(self.TL_resolution.get())
            base_px = float(self.TL_pixel_size.get())

        px_det = float(self.dp_pixel_det_um.get())
        fwhm = float(self.dp_fwhm_det_um.get())

        if px_det <= 0:
            px_det = tab_pixel_det
        if fwhm <= 0:
            fwhm = tab_fwhm

        seed_text = self.dp_random_seed.get().strip()
        random_seed = None
        if seed_text:
            random_seed = int(seed_text)

        return px_det, fwhm, noise, gauss_sigma, base_px, N0_poisson, random_seed

    def apply_detector_post(self, mode="inline"):
        def worker():
            try:
                self.set_status_threadsafe("Applying detector model (post)...")

                px_det, fwhm, noise, gauss_sigma, base_px, N0_poisson, random_seed = self.get_post_detector_params(mode)
                det = detector.Detector(
                    Image_option="Realistic", pixel_size_detector=px_det, FWHM_detector=fwhm,
                    noise_type=noise, pixel_size=base_px, gaussian_sigma=gauss_sigma, N0=N0_poisson,
                    random_seed=random_seed,
                )

                if mode == "inline":
                    if not hasattr(self, "inline_raw_intensity"):
                        self.master.after(0, lambda: messagebox.showwarning("No data", "Run an Inline simulation first."))
                        return
                    cur_px = float(getattr(self, "inline_raw_px_um", self.i_pixel_size.get()))
                    out = det.applyDetector(self.inline_raw_intensity, current_pixel_size=cur_px)
                    out = np.asarray(out, dtype=np.float32)
                    self.inline_display_intensity = out

                    def ui():
                        if hasattr(self, "inline_post_frame") and self.inline_post_frame.winfo_exists():
                            self.Plot_Figure(self.inline_post_frame, self.inline_display_intensity, 0, 0, (3, 3), "Post-Processing")
                        else:
                            self.clear_frame(self.i_results_frame)
                            self.Plot_Figure(self.i_results_frame, self.inline_display_intensity, 0, 0, (3, 3), "Inline Simulation (Detector POST)")
                            wg.create_button(self.i_results_frame, "Save Image", 1, 0, command=lambda: self.save_image(self.inline_display_intensity))
                        self.set_status("Detector post-processing applied (Inline).")

                    self.master.after(0, ui)

                if mode == "tl":
                    if not hasattr(self, "TL_raw_i") or not hasattr(self, "TL_raw_ir"):
                        self.master.after(0, lambda: messagebox.showwarning("No data", "Run a TL simulation first."))
                        return
                    cur_px = float(getattr(self, "TL_raw_px_um", self.TL_detector_pixel_size.get()))
                    i_out = det.applyDetector(self.TL_raw_i, current_pixel_size=cur_px)
                    ir_out = det.applyDetector(self.TL_raw_ir, current_pixel_size=cur_px)
                    self.TL_i_display = np.asarray(i_out, dtype=np.float32)
                    self.TL_ir_display = np.asarray(ir_out, dtype=np.float32)

                    def ui():
                        if hasattr(self, "TL_canvas_post_obj") and hasattr(self, "TL_canvas_post_ref"):
                            self.stack_viewer_set_stack(self.TL_canvas_post_obj, self.TL_i_display)
                            self.stack_viewer_set_stack(self.TL_canvas_post_ref, self.TL_ir_display)
                        else:
                            self.refresh_TL_results_post()
                        self.set_status("Detector post-processing applied (TL).")

                    self.master.after(0, ui)

            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"Detector post-processing failed:\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def reset_detector_post(self, mode="inline"):
        if mode == "inline":
            if not hasattr(self, "inline_raw_intensity"):
                messagebox.showwarning("No data", "Run an Inline simulation first.")
                return
            self.inline_display_intensity = self.inline_raw_intensity.copy()
            self.Plot_Figure(self.inline_post_frame, self.inline_display_intensity, 0, 0, (3, 3), "Post-Processing")
            self.set_status("Reset to RAW (Inline).")
            return

        if mode == "tl":
            if not hasattr(self, "TL_raw_i") or not hasattr(self, "TL_raw_ir"):
                messagebox.showwarning("No data", "Run a TL simulation first.")
                return
            self.TL_i_display = self.TL_raw_i.copy()
            self.TL_ir_display = self.TL_raw_ir.copy()
            self.stack_viewer_set_stack(self.TL_canvas_post_obj, self.TL_i_display)
            self.stack_viewer_set_stack(self.TL_canvas_post_ref, self.TL_ir_display)
            self.set_status("Reset to RAW (TL).")

    def refresh_TL_results_post(self):
        self.clear_frame(self.TL_results_frame)
        self.Plot_Modulation_Curve(self.TL_results_frame, self.TL_i_display, self.TL_ir_display, 0, 0, (3, 3), "Phase Stepping Curve", columnspan=2)
        self.Plot_Figure(self.TL_results_frame, self.TL_i_display[0, :, :], 1, 0, (3, 3), "One Projection (POST)", columnspan=2)
        wg.create_button(self.TL_results_frame, "Save Stack Object Images", 2, 0, command=lambda: self.save_stack_image(self.TL_i_display))
        wg.create_button(self.TL_results_frame, "Save Stack Reference Images", 2, 1, command=lambda: self.save_stack_image(self.TL_ir_display))
        wg.create_button(self.TL_results_frame, "Send to TLRec", 3, 0, command=lambda: self.send_to_TLREC(self.TL_i_display, self.TL_ir_display))
        self.set_status("Detector post-processing applied (TL).")

    def update_canvas(self, canvas, image):
        width, height = canvas.winfo_width(), canvas.winfo_height()

        arr = np.asarray(image, dtype=float)
        finite = np.isfinite(arr)
        if not finite.any():
            arr = np.zeros_like(arr, dtype=float)
            vmin, vmax = 0.0, 1.0
        else:
            vals = arr[finite]
            p1, p99 = np.percentile(vals, [1, 99])
            if p1 == p99:
                vmin, vmax = vals.min(), vals.max()
                if vmin == vmax:
                    vmin, vmax = 0.0, 1.0
            else:
                vmin, vmax = p1, p99

        arr_clipped = np.clip(arr, vmin, vmax)
        norm = (arr_clipped - vmin) / (vmax - vmin + 1e-9)
        norm = (norm * 255.0).astype(np.uint8)

        image_pil = Image.fromarray(norm)
        h_img, w_img = norm.shape
        scale = min(width / w_img, height / h_img)
        new_w = int(w_img * scale)
        new_h = int(h_img * scale)
        resized_image = image_pil.resize((new_w, new_h), Image.BILINEAR)
        photo = ImageTk.PhotoImage(resized_image)

        canvas.image = photo
        canvas.delete("all")
        x0 = (width - new_w) // 2
        y0 = (height - new_h) // 2
        canvas.create_image(x0, y0, anchor=tk.NW, image=canvas.image)

    def make_stack_viewer(self, parent, title="Stack"):
        box = ttk.LabelFrame(parent, text=title, padding=(6, 6))
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(box, highlightthickness=0, bg="#333333")
        canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        ctrl = ttk.Frame(box)
        ctrl.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        ctrl.grid_columnconfigure(1, weight=1)

        lbl = ttk.Label(ctrl, text="Slice: 0")
        lbl.grid(row=0, column=0, sticky="w")

        slider = ttk.Scale(ctrl, from_=0, to=0, orient="horizontal")
        slider.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        canvas._stack = None
        canvas._idx = tk.IntVar(value=0)
        canvas._lbl = lbl
        canvas._slider = slider

        def _on_slide(v):
            i = int(float(v))
            canvas._idx.set(i)
            canvas._lbl.config(text=f"Slice: {i}")
            self.stack_viewer_redraw(canvas)

        slider.configure(command=_on_slide)

        if not getattr(canvas, "_cfg_bound", False):
            canvas.bind("<Configure>", lambda e: self.stack_viewer_redraw(canvas))
            canvas._cfg_bound = True

        return box, canvas

    def stack_viewer_set_stack(self, canvas, stack):
        arr = np.asarray(stack, dtype=np.float32)
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]
        canvas._stack = arr
        canvas._idx.set(0)
        n = arr.shape[0]
        canvas._slider.configure(from_=0, to=max(0, n - 1))
        canvas._lbl.config(text="Slice: 0")
        self.stack_viewer_redraw(canvas)

    def stack_viewer_redraw(self, canvas):
        if getattr(canvas, "_stack", None) is None:
            return
        arr = canvas._stack
        i = int(canvas._idx.get())
        i = max(0, min(i, arr.shape[0] - 1))
        self.update_canvas(canvas, arr[i, :, :])