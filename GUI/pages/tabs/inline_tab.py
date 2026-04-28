import os
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

from GUI.ui.widgets import Widget as wg
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.ui.widgets import ToggleButton
from GUI.utils import resource_path


class InlineTab:

    def populate_inline_tab(self):

        scrollframe = vsf(self.inline_tab)
        scrollframe.grid(row=0, column=0, columnspan=3, sticky="nsew")
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
        parameters_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.i_results_frame = ttk.Frame(container, style='TFrame')
        self.i_results_frame.grid(row=0, column=2, rowspan=12, sticky='nsew')
        self.i_results_frame.grid_rowconfigure(0, weight=1)
        self.i_results_frame.grid_columnconfigure(0, weight=1)

        self.initialize_Figure(self.i_results_frame, (3, 3), 0, 0)

        nLabel, i_n_e = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0, textvariable=self.i_n, padx=20)
        pxLabel, i_px_e = wg.create_label_entry(parameters_frame, 'Pixel size (micrometer)', 1, 0, textvariable=self.i_pixel_size, padx=20)
        DODLabel, i_dod_e = wg.create_label_entry(parameters_frame, 'Distance Object Detector (cm)', 2, 0, textvariable=self.i_DOD, padx=20)
        self.DSOLabel, i_dso_e = wg.create_label_entry(parameters_frame, 'Distance Source-Object (cm)', 3, 0, textvariable=self.i_DSO, padx=20)
        self.FWHMSouLabel, i_fwhm_src_e = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 4, 0, textvariable=self.i_FWHM_source, padx=20)
        self.BeamShapeLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Beam Shape', row=5, column=0, textvariable=self.i_Beam_Shape, names=self.Beam_Shape_OPTIONS)
        self.BeamSpectrumLabel, _ = wg.create_label_combobox(parameters_frame, label_text='Spectrum', row=6, column=0, textvariable=self.i_Beam_Spectrum, names=self.Beam_Spectrum_OPTIONS)
        self.BeamEnergyL, i_energy_e = wg.create_label_entry(parameters_frame, 'Energy (keV, necessary to initialize the variable)', row=7, column=0, textvariable=self.i_beam_energy, padx=20)
        self.ObjectLabel = ttk.Label(parameters_frame, text='Objects')
        self.ObjectLabel.grid(row=8, column=0, padx=10, pady=5, sticky='w')
        self.ObjectSummary = ttk.Label(parameters_frame, textvariable=self.inline_objects_summary_var, wraplength=260, justify='left')
        self.ObjectSummary.grid(row=8, column=1, padx=10, pady=5, sticky='ew')
        wg.create_button(parameters_frame, 'Manage Objects', 9, 0, command=self.open_params)
        self.DetectorL, _ = wg.create_label_combobox(parameters_frame, label_text='Image', row=10, column=0, textvariable=self.i_image_option, names=self.Image_OPTIONS)
        self.PixelDetectorL, i_pxdet_e = wg.create_label_entry(parameters_frame, 'Detector Pixel Size (microns)', 11, 0, textvariable=self.i_detector_pixel_size, padx=20)
        self.ResolutionL, i_fwhm_det_e = wg.create_label_entry(parameters_frame, 'Detector Resolution (FWHM microns)', 12, 0, textvariable=self.i_FWHM_detector, padx=20)
        ToggleButton(parameters_frame, text="Create ZIP with simulation data", variable=self.i_zip_var).grid(row=13, column=0, pady=5)
        self.RunButton = wg.create_button(parameters_frame, 'Run', 14, 0, command=self.RunInline)

        wg.create_button(parameters_frame, "Save preset", 15, 0, command=self.save_preset_Inline)
        wg.create_button(parameters_frame, "Load preset", 15, 1, command=self.load_preset_Inline)

        self.add_detector_post_panel(parameters_frame, mode="inline", row=17)

        wg.create_button(parameters_frame, "Exit", 16, 0, padx=60, command=self.close_app)

        self._watch(i_n_e, self.i_n, lambda v: v > 0)
        self._watch(i_px_e, self.i_pixel_size, lambda v: v > 0)
        self._watch(i_dod_e, self.i_DOD, lambda v: v > 0)
        self._watch(i_dso_e, self.i_DSO, lambda v: v > 0)
        self._watch(i_fwhm_src_e, self.i_FWHM_source, lambda v: v > 0)
        self._watch(i_energy_e, self.i_beam_energy, lambda v: v > 0)
        self._watch(i_pxdet_e, self.i_detector_pixel_size, lambda v: v > 0)
        self._watch(i_fwhm_det_e, self.i_FWHM_detector, lambda v: v > 0)
        self.add_tooltip(nLabel, "Number of pixels of the simulated wavefront (n x n).")
        self.add_tooltip(pxLabel, "Pixel size of the wavefront grid in micrometers.")
        self.add_tooltip(DODLabel, "Distance from the object to the detector in centimeters.")
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
            image_option = self.i_image_option.get()
            FWHM_detector = self.i_FWHM_detector.get()
            detector_pixel_size = self.i_detector_pixel_size.get()
            Sample = self._build_inline_objects(n, pixel_size)

            if Beam_Spectrum == 'Monoenergetic':
                Beam_Spectrum = 'Mono'

            MySource = source.Source((FWHM_source, FWHM_source), Beam_Spectrum, beam_energy, Beam_Shape, pixel_size)
            MyDetector = detector.Detector(image_option, detector_pixel_size, FWHM_detector, 'gaussian', pixel_size)
            MyGeometry = geom.Geometry(DSO + DOD)
            progress_cb = self.make_progress_callback("Inline simulation")
            Intensity, Intensity_raw = exp.Experiment_Inline(n, MyGeometry, MySource, MyDetector, Sample, progress_cb=progress_cb, return_raw=True, apply_detector=True)

            self.inline_raw_intensity = np.asarray(Intensity_raw, dtype=np.float32)
            self.inline_display_intensity = np.asarray(Intensity, dtype=np.float32)
            self.inline_raw_px_um = float(self.i_pixel_size.get())

            def update_gui():
                dual = ttk.Frame(self.i_results_frame, style="TFrame")
                dual.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

                self.i_results_frame.grid_rowconfigure(0, weight=1)
                self.i_results_frame.grid_columnconfigure(0, weight=1)

                dual.grid_rowconfigure(0, weight=1)
                dual.grid_columnconfigure(0, weight=1, uniform="dual")
                dual.grid_columnconfigure(1, weight=1, uniform="dual")

                raw_f = ttk.Frame(dual, style="TFrame")
                post_f = ttk.Frame(dual, style="TFrame")
                raw_f.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
                post_f.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

                self.inline_raw_frame = raw_f
                self.inline_post_frame = post_f

                self.Plot_Figure(raw_f, self.inline_raw_intensity, 0, 0, (3, 3), "RAW (Pre-detector)")
                self.Plot_Figure(post_f, self.inline_display_intensity, 0, 0, (3, 3), "Post-Processing")

                wg.create_button(raw_f, 'Save Raw Image', 1, 0,
                                 command=lambda: self.save_image(self.inline_raw_intensity))
                wg.create_button(post_f, 'Save Post-Processed Image', 1, 0,
                                 command=lambda: self.save_image(self.inline_display_intensity))

                if self.i_zip_var.get():
                    self.export_inline_zip(self.inline_display_intensity)

            self.master.after(0, update_gui)

        self.run_with_error_handling(_run, "Running Inline simulation...")

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
            "outer_radius": self.i_radius.get(),
            "inner_radius": self.i_inner_radius.get(),
            "xshift": self.i_xshift.get(),
            "yshift": self.i_yshift.get(),
            "material": self.i_material.get(),
            "objects": self.inline_objects_data,
            "image_option": self.i_image_option.get(),
            "detector_pixel_size": self.i_detector_pixel_size.get(),
            "FWHM_detector": self.i_FWHM_detector.get(),
            "resolution": self.i_resolution.get(),
        }

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
            "Object": self.i_Object.get(),
            "outer_radius": self.i_radius.get(),
            "material": self.i_material.get(),
            "objects": self.inline_objects_data,
            "image_option": self.i_image_option.get(),
            "resolution": self.i_resolution.get(),
            "inner_radius": self.i_inner_radius.get(),
            "xshift": self.i_xshift.get(),
            "yshift": self.i_yshift.get(),
            "orientation": self.i_orientation.get(),
            "FWHM_detector": self.i_FWHM_detector.get(),
            "detector_pixel_size": self.i_detector_pixel_size.get(),
        }
        filename = asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, "w") as f:
                json.dump(params, f, indent=4)
            self.set_status("Preset saved successfully.")

    def load_preset_Inline(self):
        filename = askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return

        with open(filename, "r") as f:
            p = json.load(f)

        self.i_n.set(p["n"])
        self.i_pixel_size.set(p["pixel_size"])
        self.i_FWHM_source.set(p["FWHM_source"])
        self.i_Beam_Shape.set(p["Beam_Shape"])
        self.i_Beam_Spectrum.set(p["Beam_Spectrum"])
        self.i_beam_energy.set(p["energy"])
        self.i_DSO.set(p["DSO"])
        self.i_DOD.set(p["DOD"])
        self.i_Object.set(p["Object"])
        self.i_radius.set(p["outer_radius"])
        self.i_material.set(p["material"])
        self.i_image_option.set(p["image_option"])
        self.i_resolution.set(p["resolution"])
        self.i_inner_radius.set(p["inner_radius"])
        self.i_xshift.set(p["xshift"])
        self.i_yshift.set(p["yshift"])
        self.i_orientation.set(p["orientation"])
        self.i_FWHM_detector.set(p["FWHM_detector"])
        self.i_detector_pixel_size.set(p["detector_pixel_size"])

        if "objects" in p:
            self.inline_objects_data = self._normalize_object_specs(p["objects"], mode="inline")
        else:
            self.inline_objects_data = self._normalize_object_specs([self._legacy_inline_object_spec()], mode="inline")
        self._sync_inline_legacy_from_objects()

        self.set_status("Preset loaded successfully.")

    def export_inline_zip(self, intensity_array):
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
            "- intensity.tif -> output intensity image\n"
        )

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("inline_config.json", config_json)
            zf.writestr("README.txt", readme)
            zf.writestr("intensity.tif", tiff_buffer.getvalue())

    def verify_physical_values_inline(self):
        n = self.i_n.get()
        DSO = self.i_DSO.get()
        DOD = self.i_DOD.get()
        pixel_size = self.i_pixel_size.get()
        FWHM_source = self.i_FWHM_source.get()
        FWHM_detector = self.i_FWHM_detector.get()
        detector_pixel_size = self.i_detector_pixel_size.get()

        if n <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        if DSO <= 0 or DOD <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that DSO and DOD are positive values.")
            return False
        if pixel_size <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        if FWHM_source <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        if detector_pixel_size <= 0 or FWHM_detector <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Detector Pixel Size and Detector FWHM are positive values.")
            return False
        try:
            self._validate_object_collection(self.inline_objects_data, mode="inline")
        except Exception as exc:
            messagebox.showerror("Invalid Object", str(exc))
            return False
        return True

    def open_params(self):
        self._open_object_manager(mode="inline")
