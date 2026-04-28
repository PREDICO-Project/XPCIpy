import os
import sys
import json
import io
import zipfile
import datetime
import numpy as np
import tifffile
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename

import src.PCSim.Objects as obj
import src.PCSim.Geometry as geom
import src.PCSim.experiments as exp
import src.PCSim.source as source
import src.PCSim.detector as detector
from src.PCSim.TL_conf import TL_CONFIG
import src.PCSim.utils as pcsim_utils

from GUI.ui.widgets import Widget as wg
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.ui.widgets import ToggleButton
from GUI.utils import resource_path

class TLTab:

    def populate_TL_tab(self):

        Grating_OPTIONS = ["Phase pi/2", "Phase pi"]
        Movable_OPTIONS = ["G1", "G2"]

        scrollframe = vsf(self.TL_tab)
        scrollframe.grid(row=0, column=0, columnspan=3, sticky="nsew")

        container = scrollframe.interior
        container.grid_columnconfigure(2, weight=1)

        self.TL_tab.grid_rowconfigure(0, weight=1)
        self.TL_tab.grid_columnconfigure(0, weight=0)
        self.TL_tab.grid_columnconfigure(1, weight=0)
        self.TL_tab.grid_columnconfigure(2, weight=1)

        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.TL_results_frame = ttk.Frame(container, style='TFrame')
        self.TL_results_frame.grid(row=0, column=2, rowspan=12, sticky='nsew')
        self.TL_results_frame.grid_rowconfigure(0, weight=1)
        self.TL_results_frame.grid_columnconfigure(0, weight=1)

        self.initialize_Figure(self.TL_results_frame, (5, 5), 0, 0)

        nLabel, tl_n_e = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0, textvariable=self.TL_n, padx=20)
        pxLabel, tl_px_e = wg.create_label_entry(parameters_frame, 'Pixel size (microns)', 1, 0, textvariable=self.TL_pixel_size, padx=20)
        sourceLabel, tl_fwhm_src_e = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 2, 0, textvariable=self.TL_FWHM_source, padx=20)
        beamShapeLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Beam Shape', row=3, column=0, textvariable=self.TL_BeamShape, names=self.Beam_Shape_OPTIONS)
        spectrumLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Spectrum', row=4, column=0, textvariable=self.TL_Beam_Spectrum, names=self.Beam_Spectrum_OPTIONS)
        energyLabel, tl_energy_e = wg.create_label_entry(parameters_frame, 'Design Energy (keV)', row=5, column=0, textvariable=self.TL_beam_energy, padx=20)
        DSG1Label, tl_dsg1_e = wg.create_label_entry(parameters_frame, 'Distance Source-G1 (cm)', 6, 0, textvariable=self.TL_DSO, padx=20)
        DOG1Label, tl_dog1_e = wg.create_label_entry(parameters_frame, 'Distance Object-G1 (cm)', 7, 0, textvariable=self.TL_DOG1, padx=20)
        multiplesLabel, tl_multiples_e = wg.create_label_entry(parameters_frame, 'Multiple of Talbot distance', 8, 0, textvariable=self.TL_TLmultiple, padx=20)
        TalbotDistanceLabel, _ = wg.create_label_entry(parameters_frame, 'Talbot Distance (cm)', 9, 0, textvariable=self.TL_Talbot_distance, padx=20, state='disable')
        Magnification, _ = wg.create_label_entry(parameters_frame, 'Magnification', 10, 0, textvariable=self.TL_M, padx=20, state='disable')
        DG1G1Label, _ = wg.create_label_entry(parameters_frame, 'Distance G1-G2 (cm)', 11, 0, textvariable=self.TL_DOD, padx=20, state='disable')
        G1PeriodLabel, tl_g1period_e = wg.create_label_entry(parameters_frame, 'G1 Period (microns)', 12, 0, textvariable=self.TL_Period_G1, padx=20)
        G2PeriodLabel, _ = wg.create_label_entry(parameters_frame, 'G2 Period (microns)', 13, 0, textvariable=self.TL_Period_G2, padx=20, state='disable')
        G1PhaseLabel, _ = wg.create_label_combobox(parameters_frame, label_text='G1 Phase', row=14, column=0, textvariable=self.TL_G1_Phase, names=Grating_OPTIONS)
        MovableLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Movable Grating', row=15, column=0, textvariable=self.TL_MovableGrating, names=Movable_OPTIONS)
        NumberStepsLabel, tl_steps_e = wg.create_label_entry(parameters_frame, 'Number of steps (int)', 16, 0, textvariable=self.TL_steps, padx=20)
        StepLenghtLabel, tl_steplength_e = wg.create_label_entry(parameters_frame, 'Step Length (microns)', 17, 0, textvariable=self.TL_step_length, padx=20)
        ObjectLabel = ttk.Label(parameters_frame, text='Objects')
        ObjectLabel.grid(row=18, column=0, padx=10, pady=5, sticky='w')
        self.TLObjectSummary = ttk.Label(parameters_frame, textvariable=self.tl_objects_summary_var, wraplength=260, justify='left')
        self.TLObjectSummary.grid(row=18, column=1, padx=10, pady=5, sticky='ew')
        wg.create_button(parameters_frame, 'Manage Objects', 19, 0, command=self.open_params_TL)
        ImageOptionLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Image', row=20, column=0, textvariable=self.TL_image_option, names=self.Image_OPTIONS)
        DetectorPXLabel, tl_pxdet_e = wg.create_label_entry(parameters_frame, 'Detector Pixel Size (microns)', 21, 0, textvariable=self.TL_detector_pixel_size, padx=20)
        DetectorResolutionLabel, tl_res_e = wg.create_label_entry(parameters_frame, 'Detector Resolution (pixel Size in microns)', 22, 0, textvariable=self.TL_resolution, padx=20)
        ToggleButton(parameters_frame, text="Create ZIP with simulation data", variable=self.TL_zip_var).grid(row=23, column=0, pady=5)

        RunBtton = wg.create_button(parameters_frame, 'Run', 24, 0, command=self.RunTL)
        wg.create_button(parameters_frame, "Save preset", 25, 0, command=self.save_preset_TL)
        wg.create_button(parameters_frame, "Load preset", 25, 1, command=self.load_preset_TL)
        wg.create_button(parameters_frame, "Exit", 26, 0, padx=60, command=self.close_app)

        self.add_detector_post_panel(parameters_frame, mode="tl", row=27)

        self._watch(tl_n_e, self.TL_n, lambda v: v > 0)
        self._watch(tl_px_e, self.TL_pixel_size, lambda v: v > 0)
        self._watch(tl_fwhm_src_e, self.TL_FWHM_source, lambda v: v > 0)
        self._watch(tl_energy_e, self.TL_beam_energy, lambda v: v > 0)
        self._watch(tl_dsg1_e, self.TL_DSO, lambda v: v > 0)
        self._watch(tl_dog1_e, self.TL_DOG1, lambda v: v > 0)
        self._watch(tl_multiples_e, self.TL_TLmultiple, lambda v: v > 0)
        self._watch(tl_g1period_e, self.TL_Period_G1, lambda v: v > 0)
        self._watch(tl_steps_e, self.TL_steps, lambda v: v > 0)
        self._watch(tl_steplength_e, self.TL_step_length, lambda v: v > 0)
        self._watch(tl_pxdet_e, self.TL_detector_pixel_size, lambda v: v > 0)
        self._watch(tl_res_e, self.TL_resolution, lambda v: v > 0)
        self.add_tooltip(nLabel, "Number of pixels of the simulated wavefront (n x n).")
        self.add_tooltip(pxLabel, "Pixel size of the wavefront grid in micrometers.")
        self.add_tooltip(sourceLabel, "Full Width at Half Maximum (FWHM) of the X-ray source in micrometers.")
        self.add_tooltip(beamShapeLabel, "Beam geometry: 'Plane' = parallel beam, 'Conical' = diverging cone.")
        self.add_tooltip(spectrumLabel, "Select a spectrum file or 'Monoenergetic' for a single energy.")
        self.add_tooltip(energyLabel, "Design energy of the setup in keV. Used for Talbot distance calculation.")
        self.add_tooltip(DSG1Label, "Distance from the source to the first grating (G1) in centimeters.")
        self.add_tooltip(DOG1Label, "Distance from the object to the first grating (G1) in centimeters.")
        self.add_tooltip(multiplesLabel, "Multiple of Talbot distance (maximum distance).")
        self.add_tooltip(TalbotDistanceLabel, "Talbot distance (auto-calculated from energy and G1 period). Read-only.")
        self.add_tooltip(Magnification, "Geometric magnification factor (auto-calculated from source-to-G1 distance). Read-only.")
        self.add_tooltip(DG1G1Label, "Distance between G1 and G2 gratings in centimeters (auto-calculated). Read-only.")
        self.add_tooltip(G1PeriodLabel, "Period of the first grating (G1) in micrometers.")
        self.add_tooltip(G2PeriodLabel, "Period of the second grating (G2) in micrometers (auto-calculated). Read-only.")
        self.add_tooltip(G1PhaseLabel, "Phase shift introduced by the first grating (G1).")
        self.add_tooltip(MovableLabel, "Select which grating (G1 or G2) will be moved during the phase stepping simulation.")
        self.add_tooltip(NumberStepsLabel, "Number of discrete steps in the phase stepping process.")
        self.add_tooltip(StepLenghtLabel, "Length of each step in micrometers.")
        self.add_tooltip(ObjectLabel, "Open the object manager to define one or more objects, each with its own geometry, material and Object-G1 distance.")
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

    def RunTL(self):
        def _run():
            if not self.verify_physical_values_TL():
                self.set_status("Error in physical values for Talbot-Lau simulation.")
                return

            n = self.TL_n.get()
            pixel_size = self.TL_pixel_size.get()
            FWHM_source = self.TL_FWHM_source.get()
            Beam_Shape = self.TL_BeamShape.get()
            Beam_Spectrum = os.path.splitext(self.TL_Beam_Spectrum.get())[0]
            design_energy = self.TL_beam_energy.get()

            DSG1 = self.TL_DSO.get()
            Period_G1 = self.TL_Period_G1.get()
            G1_Phase = self.TL_G1_Phase.get()
            FWHM_detector = self.TL_resolution.get()
            detector_pixel_size = self.TL_detector_pixel_size.get()
            image_option = self.TL_image_option.get()
            Objects = self._build_tl_objects(n, pixel_size, DSG1)
            earliest_object_dso = min(float(current_object.DSO) for current_object in Objects)

            if Beam_Spectrum == 'Monoenergetic':
                Beam_Spectrum = 'Mono'
            if G1_Phase == 'Phase pi/2':
                G1_type = 'phase_pi_2'
            elif G1_Phase == 'Phase pi':
                G1_type = 'phase_pi'

            MySource = source.Source((FWHM_source, FWHM_source), Beam_Spectrum, design_energy, Beam_Shape, pixel_size)
            MyDetector = detector.Detector(image_option, detector_pixel_size, FWHM_detector, 'gaussian', pixel_size)

            configuration = TL_CONFIG(
                Design_energy=design_energy, G1_Period=Period_G1, DSG1=DSG1,
                Movable_Grating=self.TL_MovableGrating.get(), G1_type=G1_type,
                TL_multiple=self.TL_TLmultiple.get(), Number_steps=self.TL_steps.get(),
                Step_length=self.TL_step_length.get(), pixel_size=pixel_size, angle=0,
                resolution=FWHM_detector, pixel_detector=detector_pixel_size,
            )

            pixel_size = configuration.pixel_size
            geometry = geom.Geometry()
            distance, G2Period = geometry.calculate_Talbot_distance_and_G2period(MySource, configuration)
            geometry.DSD = DSG1 + distance
            configuration.G2_Period = G2Period

            if earliest_object_dso - distance <= 0:
                self.TL_Talbot_distance.set(0.0)
                self.TL_DOD.set(0.0)
                self.TL_M.set(0.0)
                self.TL_Period_G2.set(0.0)
                self.set_status("Talbot configuration not physically valid for these parameters.")
                return

            G1 = obj.Grating(n, Period_G1, 0.5, pixel_size, 'Si', DSG1, grating_type=G1_type, design_energy=design_energy)
            G2 = obj.Grating(n, G2Period, 0.5, pixel_size, 'Au', DSG1 + distance, 40, grating_type='custom', design_energy=design_energy)
            self.gui_check_grating_sampling(Period_G1 / pixel_size)
            self.gui_check_grating_sampling(G2Period / pixel_size)
            self.gui_check_phase_stepping(self.TL_steps.get(), G2Period / pixel_size, self.TL_step_length.get() / pixel_size)

            progress_cb = self.make_progress_callback("TL simulation")
            i, ir, i_raw, ir_raw = exp.Experiment_Phase_Stepping(
                n, MyDetector, MySource, geometry, Objects, G1, G2, configuration,
                padding=0, progress_cb=progress_cb, return_raw=True, apply_detector=True,
            )

            self.TL_raw_i = np.asarray(i_raw, dtype=np.float32)
            self.TL_raw_ir = np.asarray(ir_raw, dtype=np.float32)
            self.TL_i_display = np.asarray(i, dtype=np.float32)
            self.TL_ir_display = np.asarray(ir, dtype=np.float32)
            self.TL_raw_px_um = float(self.TL_detector_pixel_size.get())

            def update_gui():
                curve_f = ttk.Frame(self.TL_results_frame, style="TFrame")
                curve_f.grid(row=0, column=0, columnspan=2, sticky="nsew")
                self.Plot_Modulation_Curve(curve_f, self.TL_i_display, self.TL_ir_display, 0, 0, (3, 3), "Phase Stepping Curve")

                dual = ttk.Frame(self.TL_results_frame, style="TFrame")
                dual.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
                dual.grid_rowconfigure(0, weight=1)
                dual.grid_columnconfigure(0, weight=1, uniform="dual")
                dual.grid_columnconfigure(1, weight=1, uniform="dual")

                raw_f = ttk.Frame(dual, style="TFrame")
                post_f = ttk.Frame(dual, style="TFrame")
                raw_f.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
                post_f.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

                raw_f.grid_rowconfigure((0, 1), weight=1)
                raw_f.grid_columnconfigure(0, weight=1)
                post_f.grid_rowconfigure((0, 1), weight=1)
                post_f.grid_columnconfigure(0, weight=1)

                b, self.TL_canvas_raw_obj = self.make_stack_viewer(raw_f, "RAW Object")
                b.grid(row=0, column=0, sticky="nsew")
                b, self.TL_canvas_raw_ref = self.make_stack_viewer(raw_f, "RAW Reference")
                b.grid(row=1, column=0, sticky="nsew")
                b, self.TL_canvas_post_obj = self.make_stack_viewer(post_f, "POST Object")
                b.grid(row=0, column=0, sticky="nsew")
                b, self.TL_canvas_post_ref = self.make_stack_viewer(post_f, "POST Reference")
                b.grid(row=1, column=0, sticky="nsew")

                self.stack_viewer_set_stack(self.TL_canvas_raw_obj, self.TL_raw_i)
                self.stack_viewer_set_stack(self.TL_canvas_raw_ref, self.TL_raw_ir)
                self.stack_viewer_set_stack(self.TL_canvas_post_obj, self.TL_i_display)
                self.stack_viewer_set_stack(self.TL_canvas_post_ref, self.TL_ir_display)

                wg.create_button(raw_f, 'Save Raw Object Stack', 2, 0, command=lambda: self.save_stack_image(self.TL_raw_i))
                wg.create_button(raw_f, 'Save Raw Reference Stack', 3, 0, command=lambda: self.save_stack_image(self.TL_raw_ir))
                wg.create_button(post_f, 'Save Display Object Stack', 3, 0, command=lambda: self.save_stack_image(self.TL_i_display))
                wg.create_button(post_f, 'Save Display Reference Stack', 2, 0, command=lambda: self.save_stack_image(self.TL_ir_display))
                wg.create_button(self.TL_results_frame, 'Send to TLRec', 4, 0, command=lambda: self.send_to_TLREC(self.TL_i_display, self.TL_ir_display))

                if self.TL_zip_var.get():
                    self.export_TL_zip(self.TL_i_display, self.TL_ir_display)

            self.master.after(0, update_gui)

        self.run_with_error_handling(_run, "Running Talbot-Lau simulation...")

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
            "objects": self.tl_objects_data,
            "image_option": self.TL_image_option.get(),
            "detector_pixel_size": self.TL_detector_pixel_size.get(),
            "resolution": self.TL_resolution.get(),
        }

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
            "material": self.TL_material.get(),
            "objects": self.tl_objects_data,
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
            p = json.load(f)

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

        if "objects" in p:
            self.tl_objects_data = self._normalize_object_specs(p["objects"], mode="tl")
        else:
            self.tl_objects_data = self._normalize_object_specs([self._legacy_tl_object_spec()], mode="tl")
        self._sync_tl_legacy_from_objects()

        self.set_status("Preset loaded successfully.")

    def export_TL_zip(self, i_stack, ir_stack):
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

    def verify_physical_values_TL(self):
        Period_G1 = self.TL_Period_G1.get()
        Talbot_multiple = self.TL_TLmultiple.get()
        FWHM_source = self.TL_FWHM_source.get()
        energy = self.TL_beam_energy.get()
        n = self.TL_n.get()
        pixel_size = self.TL_pixel_size.get()
        DSG1 = self.TL_DSO.get()
        FWHM_detector = self.TL_resolution.get()
        detector_pixel_size = self.TL_detector_pixel_size.get()

        if Period_G1 <= 0 or energy <= 0 or Talbot_multiple <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Period G1, Energy and Talbot Multiple are positive values.")
            return False
        if FWHM_source <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        if n <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        if detector_pixel_size <= 0 or FWHM_detector <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Detector Pixel Size and Detector FWHM are positive values.")
            return False
        if pixel_size <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        try:
            self._validate_object_collection(self.tl_objects_data, mode="tl")
        except Exception as exc:
            messagebox.showerror("Invalid Object", str(exc))
            return False
        return True

    def modify_DOD(self, event=None):
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
            return

        if Spectrum == 'Monoenergetic':
            Spectrum = 'Mono'

        Source = source.Source((FWHM_source, FWHM_source), Spectrum, energy, Beam_Shape, pixel_size)
        mean_energy = Source.mean_energy
        mean_wavelength = 1.23984193 / (mean_energy * 1000)

        if Beam_Shape == 'Conical':
            if G1_Phase == 'Phase pi':
                distance_Talbot = Period_G1 ** 2 / (8 * mean_wavelength) * 10 ** (-4)
                distance = DSO * Talbot_multiple * distance_Talbot / (DSO - Talbot_multiple * distance_Talbot)
                M = (DSO + distance) / DSO
                G2Period = Period_G1 * M / 2
            elif G1_Phase == 'Phase pi/2':
                distance_Talbot = Period_G1 ** 2 / (2 * mean_wavelength) * 10 ** (-4)
                distance = DSO * Talbot_multiple * distance_Talbot / (DSO - Talbot_multiple * distance_Talbot)
                M = (DSO + distance) / DSO
                G2Period = Period_G1 * M
            else:
                return

        if Beam_Shape == 'Plane':
            M = 1
            if G1_Phase == 'Phase pi':
                G2Period = Period_G1 / 2
                distance = Period_G1 ** 2 / (8 * mean_wavelength) * 10 ** (-4)
                distance_Talbot = distance
            elif G1_Phase == 'Phase pi/2':
                G2Period = Period_G1
                distance = Period_G1 ** 2 / (2 * mean_wavelength) * 10 ** (-4)
                distance_Talbot = distance
            else:
                return
        else:
            return

        self.TL_Talbot_distance.set(distance_Talbot)
        self.TL_Period_G2.set(G2Period)
        self.TL_DOD.set(distance)
        self.TL_M.set(M)

    def open_params_TL(self):
        self._open_object_manager(mode="tl")


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


    def send_to_TLREC(self, i_stack, ir_stack):
        if not hasattr(self, "tlrec_gui"):
            self.set_status("TLRec GUI is not available.")
            return
        self.tab_container.select(self.TLRec_tab)
        self.tlrec_gui.load_from_arrays(i_stack, ir_stack, label="Simulation")


    def refresh_TL_results_post(self):
        self.clear_frame(self.TL_results_frame)
        self.Plot_Modulation_Curve(self.TL_results_frame, self.TL_i_display, self.TL_ir_display, 0, 0, (3, 3), "Phase Stepping Curve", columnspan=2)
        self.Plot_Figure(self.TL_results_frame, self.TL_i_display[0, :, :], 1, 0, (3, 3), "One Projection (POST)", columnspan=2)
        wg.create_button(self.TL_results_frame, "Save Stack Object Images", 2, 0, command=lambda: self.save_stack_image(self.TL_i_display))
        wg.create_button(self.TL_results_frame, "Save Stack Reference Images", 2, 1, command=lambda: self.save_stack_image(self.TL_ir_display))
        wg.create_button(self.TL_results_frame, "Send to TLRec", 3, 0, command=lambda: self.send_to_TLREC(self.TL_i_display, self.TL_ir_display))
        self.set_status("Detector post-processing applied (TL).")
