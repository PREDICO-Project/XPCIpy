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

from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import src.Simple_Numerical_Simulation.Objects as sns_obj
import src.Simple_Numerical_Simulation.simulation as sns_sim
from src.PCSim.material import make_material, list_available_materials

from GUI.ui.widgets import Widget as wg
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.ui.widgets import ToggleButton

# SNS = Simple Numerical Simulation
class SNSTab:

    def populate_sns_tab(self):
        scrollframe = vsf(self.sns_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior

        self.sns_tab.grid_rowconfigure(0, weight=1)
        self.sns_tab.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=0, minsize=560)
        container.grid_columnconfigure(1, weight=1)

        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.grid(row=0, column=0, sticky='nsew')

        self.sns_results_frame = ttk.Frame(container, style='TFrame')
        self.sns_results_frame.grid(row=0, column=1, sticky='nsew')
        self.sns_results_frame.grid_rowconfigure(0, weight=0)
        self.sns_results_frame.grid_rowconfigure(2, weight=1)
        self.sns_results_frame.grid_columnconfigure(0, weight=1)
        self.sns_results_frame.grid_columnconfigure(1, weight=0)

        self.initialize_Figure(self.sns_results_frame, (5, 5), 0, 0)

        nLabel, sns_n_e = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0, textvariable=self.sns_n, padx=20)
        pxLabel, sns_px_e = wg.create_label_entry(parameters_frame, 'Pixel size (micrometer)', 1, 0, textvariable=self.sns_pixel_size, padx=20)
        deltaLabel, sns_delta_e = wg.create_label_entry(parameters_frame, 'delta (2*pi/wavelength * delta)', 2, 0, textvariable=self.sns_delta, padx=20)
        betaLabel, sns_beta_e = wg.create_label_entry(parameters_frame, 'beta (2*pi/wavelength * beta)', 3, 0, textvariable=self.sns_beta, padx=20)
        energyLabel, sns_energy_e = wg.create_label_entry(parameters_frame, 'Energy (keV)', 4, 0, textvariable=self.sns_energy, padx=20)
        phaseStepLabel, sns_steps_e = wg.create_label_entry(parameters_frame, 'Phase steps', 5, 0, textvariable=self.sns_phase_steps, padx=20)
        noiseLabel, sns_noise_e = wg.create_label_entry(parameters_frame, 'Noise sigma', 6, 0, textvariable=self.sns_noise_mean, padx=20)
        stepErrLabel, sns_step_err_e = wg.create_label_entry(parameters_frame, 'Step error sigma (rad)', 7, 0, textvariable=self.sns_error_steps_mean, padx=20)
        doseErrLabel, sns_dose_err_e = wg.create_label_entry(parameters_frame, 'Dose error sigma', 8, 0, textvariable=self.sns_error_dose_mean, padx=20)

        axisLabel, _ = wg.create_label_combobox(parameters_frame, 'Gradient axis', ['0', '1'], 9, 0, textvariable=self.sns_axis)
        ToggleButton(parameters_frame, text='Enable Moire artifacts', variable=self.sns_moire).grid(row=10, column=0, pady=5)
        moireLabel, sns_moire_e = wg.create_label_entry(parameters_frame, 'Number of Moire fringes', 11, 0, textvariable=self.sns_moire_fringes, padx=20)
        moireProfileLabel, _ = wg.create_label_combobox(parameters_frame, 'Moire phase profile', ['linear', 'sinusoidal', 'triangular', 'square'], 12, 0, textvariable=self.sns_moire_profile)
        moireDirectionLabel, _ = wg.create_label_combobox(parameters_frame, 'Moire direction', ['x', 'y', 'diag'], 13, 0, textvariable=self.sns_moire_direction)
        moireScaleLabel, sns_moire_scale_e = wg.create_label_entry(parameters_frame, 'Moire phase scale', 14, 0, textvariable=self.sns_moire_phase_scale, padx=20)
        moireOffsetLabel, sns_moire_offset_e = wg.create_label_entry(parameters_frame, 'Moire phase offset (rad)', 15, 0, textvariable=self.sns_moire_phase_offset, padx=20)
        dfLabel, sns_df_e = wg.create_label_entry(parameters_frame, 'Dark-field strength', 16, 0, textvariable=self.sns_df_strength, padx=20)
        ToggleButton(parameters_frame, text='Create ZIP with simulation data', variable=self.sns_zip_var).grid(row=17, column=0, pady=5)

        self.sns_run_button = wg.create_button(parameters_frame, 'Run', 18, 0, command=self.RunSimpleNumerical)
        wg.create_button(parameters_frame, 'Save preset', 19, 0, command=self.save_preset_SNS)
        wg.create_button(parameters_frame, 'Load preset', 19, 1, command=self.load_preset_SNS)
        wg.create_button(parameters_frame, 'Exit', 20, 0, padx=60, command=self.close_app)

        layers_frame = ttk.LabelFrame(parameters_frame, text='Geometry Layer Manager', padding=(8, 6))
        layers_frame.grid(row=21, column=0, columnspan=3, sticky='ew', padx=10, pady=(10, 4))
        layers_frame.grid_columnconfigure(0, weight=1)
        layers_frame.grid_columnconfigure(1, weight=1)
        layers_frame.grid_columnconfigure(2, weight=1)

        self.sns_layers_listbox = tk.Listbox(
            layers_frame, height=7, exportselection=False,
            bg='#2a2a2a', fg='white', selectbackground='#555555', selectforeground='white',
        )
        self.sns_layers_listbox.grid(row=0, column=0, columnspan=3, sticky='ew', padx=4, pady=4)
        self.sns_layers_listbox.bind('<<ListboxSelect>>', self._sns_on_layer_select)

        wg.create_button(layers_frame, 'Add Layer', 1, 0, command=self._sns_add_layer)
        wg.create_button(layers_frame, 'Update Layer', 1, 1, command=self._sns_update_layer)
        wg.create_button(layers_frame, 'Remove Layer', 1, 2, command=self._sns_remove_layer)
        wg.create_button(layers_frame, 'Move Up', 2, 0, command=lambda: self._sns_move_layer(-1))
        wg.create_button(layers_frame, 'Move Down', 2, 1, command=lambda: self._sns_move_layer(1))
        wg.create_button(layers_frame, 'Load Layers From Scene JSON', 2, 2, command=self._sns_import_layers_from_scene_json)

        scenePathLabel, sns_scene_path_e = wg.create_label_entry(layers_frame, 'Scene JSON path', 3, 0, textvariable=self.sns_scene_json_path, padx=8)
        sns_scene_path_e.configure(width=40)
        wg.create_button(layers_frame, 'Browse scene JSON', 3, 2, command=self.browse_sns_scene_json)

        layer_geo_options = sns_obj.GeometryFactory.available_geometries()
        mode_options = ['add', 'subtract']
        l_type_label, _ = wg.create_label_combobox(layers_frame, 'Layer type', layer_geo_options, 4, 0, textvariable=self.sns_layer_type)
        self.sns_layer_type.trace_add('write', lambda *args: self._sns_update_params_tooltip())

        params_info_label = tk.Label(
            layers_frame, text='radius: float (micrometers)',
            wraplength=400, justify=tk.LEFT, fg='gray60', font=('Arial', 8),)
        
        params_info_label.grid(row=5, column=0, columnspan=3, sticky='ew', padx=4, pady=2)
        self.sns_params_info_label = params_info_label

        l_mode_label, _ = wg.create_label_combobox(layers_frame, 'Layer mode', mode_options, 6, 0, textvariable=self.sns_layer_mode)
        optics_modes = ['global', 'material', 'custom']
        l_optics_label, _ = wg.create_label_combobox(layers_frame, 'Optics source', optics_modes, 7, 0, textvariable=self.sns_layer_optics_mode)
        l_mat_label, _ = wg.create_label_combobox(layers_frame, 'Material', self.sns_material_options, 8, 0, textvariable=self.sns_layer_material)
        l_d_label, _ = wg.create_label_entry(layers_frame, 'Custom delta (scaled)', 9, 0, textvariable=self.sns_layer_delta)
        l_b_label, _ = wg.create_label_entry(layers_frame, 'Custom beta (scaled)', 10, 0, textvariable=self.sns_layer_beta)
        l_shiftx_label, _ = wg.create_label_entry(layers_frame, 'Shift X (um)', 11, 0, textvariable=self.sns_layer_shift_x)
        l_shifty_label, _ = wg.create_label_entry(layers_frame, 'Shift Y (um)', 12, 0, textvariable=self.sns_layer_shift_y)
        l_angle_label, _ = wg.create_label_entry(layers_frame, 'Angle (deg)', 13, 0, textvariable=self.sns_layer_angle)
        l_params_label, l_params_entry = wg.create_label_entry(layers_frame, 'Layer params (JSON)', 14, 0, textvariable=self.sns_layer_params)
        l_params_entry.configure(width=40)
        wg.create_button(layers_frame, 'Default Params For Type', 15, 0, command=self._sns_set_default_params_for_layer_type)
        wg.create_button(layers_frame, 'Reset Editor', 15, 1, command=self._sns_reset_layer_editor)

        self._sns_refresh_layers_listbox()
        self._sns_update_params_tooltip()

        self._watch(sns_n_e, self.sns_n, lambda v: v > 0)
        self._watch(sns_px_e, self.sns_pixel_size, lambda v: v > 0)
        self._watch(sns_delta_e, self.sns_delta, lambda v: v > 0)
        self._watch(sns_beta_e, self.sns_beta, lambda v: v >= 0)
        self._watch(sns_energy_e, self.sns_energy, lambda v: v > 0)
        self._watch(sns_steps_e, self.sns_phase_steps, lambda v: v > 2)
        self._watch(sns_noise_e, self.sns_noise_mean, lambda v: v >= 0)
        self._watch(sns_step_err_e, self.sns_error_steps_mean, lambda v: v >= 0)
        self._watch(sns_dose_err_e, self.sns_error_dose_mean, lambda v: v >= 0)
        self._watch(sns_moire_e, self.sns_moire_fringes, lambda v: v >= 0)
        self._watch(sns_moire_scale_e, self.sns_moire_phase_scale, lambda v: v >= 0)
        self._watch(sns_df_e, self.sns_df_strength, lambda v: v >= 0)

        self.add_tooltip(nLabel, 'Number of pixels of the simulated wavefront (n x n).')
        self.add_tooltip(pxLabel, 'Pixel size of the wavefront grid in micrometers.')
        self.add_tooltip(deltaLabel, 'Scaled refractive index decrement used to compute phase-based contrast maps.')
        self.add_tooltip(betaLabel, 'Scaled absorption index used to compute attenuation maps.')
        self.add_tooltip(energyLabel, 'Beam energy in keV used in near-field approximation.')
        self.add_tooltip(phaseStepLabel, 'Number of phase-stepping images per stack.')
        self.add_tooltip(scenePathLabel, 'Path to a scene JSON file. You can import its objects as editable layers.')
        self.add_tooltip(l_type_label, 'Geometry type used for the selected layer.')
        self.add_tooltip(l_mode_label, 'Composition mode for this layer over previous layers.')
        self.add_tooltip(l_optics_label, 'How this layer gets refractive properties: global tab values, material table, or custom delta/beta.')
        self.add_tooltip(l_mat_label, 'Material used with current energy when Optics source is material.')
        self.add_tooltip(l_d_label, 'Layer delta in scaled units (k*delta). Used when Optics source is custom.')
        self.add_tooltip(l_b_label, 'Layer beta in scaled units (k*beta). Used when Optics source is custom.')
        self.add_tooltip(l_shiftx_label, 'Layer translation in X (micrometers).')
        self.add_tooltip(l_shifty_label, 'Layer translation in Y (micrometers).')
        self.add_tooltip(l_angle_label, 'Layer rotation in degrees.')
        self.add_tooltip(l_params_label, 'JSON dictionary with geometry-specific parameters for this layer.')
        self.add_tooltip(axisLabel, 'Axis used for differential phase gradient (0 or 1).')
        self.add_tooltip(moireLabel, 'Approximate number of Moire fringes across the image width.')
        self.add_tooltip(moireProfileLabel, 'Shape of the phase perturbation used to synthesize Moire artifacts.')
        self.add_tooltip(moireDirectionLabel, 'Direction used for the Moire carrier: x, y, or diagonal.')
        self.add_tooltip(moireScaleLabel, 'Amplitude scaling for the Moire phase perturbation.')
        self.add_tooltip(moireOffsetLabel, 'Global phase offset for the Moire perturbation in radians.')
        self.add_tooltip(dfLabel, 'Strength parameter used to synthesize dark-field visibility reduction.')
        self.add_tooltip(self.sns_run_button, 'Run fast simulation of DPC, attenuation, dark-field and Moire stacks.')

    def RunSimpleNumerical(self):
        def _run():
            if not self.verify_physical_values_sns():
                self.set_status("Error in physical values for Simple Numerical simulation.")
                return

            sim_object = self._sns_build_object()
            axis = int(self.sns_axis.get())

            dpc = sim_object.Obtain_Phase_Gradient(axis=axis)
            attenuation = sim_object.a0_Distribution()
            dark_field = self._sns_dark_field_map(sim_object)
            pbi = sim_object.PBI_Theoretical_near_field(distance=10.0, energy=float(self.sns_energy.get()), M=1.0)

            images, images_reference = sns_sim.Simulation(
                sim_object,
                Phase_Steps=int(self.sns_phase_steps.get()),
                noise_mean=float(self.sns_noise_mean.get()),
                error_steps_mean=float(self.sns_error_steps_mean.get()),
                error_dose_mean=float(self.sns_error_dose_mean.get()),
                Moire=bool(self.sns_moire.get()),
                axis=axis,
                dark_field_map=dark_field,
                moire_fringes_count=int(self.sns_moire_fringes.get()),
                moire_profile=self.sns_moire_profile.get(),
                moire_direction=self.sns_moire_direction.get(),
                moire_phase_scale=float(self.sns_moire_phase_scale.get()),
                moire_phase_offset=float(self.sns_moire_phase_offset.get()),
            )

            self.sns_images = np.asarray(images, dtype=np.float32)
            self.sns_images_reference = np.asarray(images_reference, dtype=np.float32)
            self.sns_dpc = np.asarray(dpc, dtype=np.float32)
            self.sns_attenuation = np.asarray(attenuation, dtype=np.float32)
            self.sns_dark_field = np.asarray(dark_field, dtype=np.float32)
            self.sns_pbi = np.asarray(pbi, dtype=np.float32)
            self.sns_last_display = self.sns_images[0]

            def update_gui():
                self.clear_frame(self.sns_results_frame)
                self.Plot_SNS_Results(
                    frame=self.sns_results_frame,
                    dpc=self.sns_dpc,
                    attenuation=self.sns_attenuation,
                    dark_field=self.sns_dark_field,
                    pbi=self.sns_pbi,
                    images=self.sns_images,
                    images_reference=self.sns_images_reference,
                    row=0,
                    column=0,
                )
                save_actions = ttk.Frame(self.sns_results_frame, style='TFrame')
                save_actions.grid(row=0, column=1, sticky='nw', padx=(6, 4), pady=(4, 2))

                b_dpc = wg.create_button(save_actions, 'Save DPC image', 0, 0, command=lambda: self.save_image(self.sns_dpc))
                b_att = wg.create_button(save_actions, 'Save attenuation image', 1, 0, command=lambda: self.save_image(self.sns_attenuation))
                b_df = wg.create_button(save_actions, 'Save dark-field image', 2, 0, command=lambda: self.save_image(self.sns_dark_field))
                b_obj = wg.create_button(save_actions, 'Save object stack', 3, 0, command=lambda: self.save_stack_image(self.sns_images))
                b_ref = wg.create_button(save_actions, 'Save reference stack', 4, 0, command=lambda: self.save_stack_image(self.sns_images_reference))

                for btn in (b_dpc, b_att, b_df, b_obj, b_ref):
                    btn.configure(width=22)

                if self.sns_zip_var.get():
                    self.export_SNS_zip()

            self.master.after(0, update_gui)

        self.run_with_error_handling(_run, "Running Simple Numerical simulation...")

    def get_SNS_config(self):
        return {
            "n": self.sns_n.get(),
            "pixel_size": self.sns_pixel_size.get(),
            "delta": self.sns_delta.get(),
            "beta": self.sns_beta.get(),
            "energy": self.sns_energy.get(),
            "phase_steps": self.sns_phase_steps.get(),
            "noise_mean": self.sns_noise_mean.get(),
            "error_steps_mean": self.sns_error_steps_mean.get(),
            "error_dose_mean": self.sns_error_dose_mean.get(),
            "moire": bool(self.sns_moire.get()),
            "moire_fringes": self.sns_moire_fringes.get(),
            "moire_profile": self.sns_moire_profile.get(),
            "moire_direction": self.sns_moire_direction.get(),
            "moire_phase_scale": self.sns_moire_phase_scale.get(),
            "moire_phase_offset": self.sns_moire_phase_offset.get(),
            "axis": int(self.sns_axis.get()),
            "dark_field_strength": self.sns_df_strength.get(),
            "geometry_type": self.sns_geometry_type.get(),
            "geometry_params": self.sns_geometry_params.get(),
            "scene_json": self.sns_scene_json_path.get().strip(),
            "layers": self.sns_layers_data,
        }

    def save_preset_SNS(self):
        params = self.get_SNS_config()
        params["type"] = "SNS_SIM"
        filename = asksaveasfilename(defaultextension=".json")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(params, f, indent=4)
            self.set_status("SNS preset saved successfully.")

    def load_preset_SNS(self):
        filename = askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return

        with open(filename, "r", encoding="utf-8") as f:
            p = json.load(f)

        self.sns_n.set(p.get("n", self.sns_n.get()))
        self.sns_pixel_size.set(p.get("pixel_size", self.sns_pixel_size.get()))
        self.sns_delta.set(p.get("delta", self.sns_delta.get()))
        self.sns_beta.set(p.get("beta", self.sns_beta.get()))
        self.sns_energy.set(p.get("energy", self.sns_energy.get()))
        self.sns_phase_steps.set(p.get("phase_steps", self.sns_phase_steps.get()))
        self.sns_noise_mean.set(p.get("noise_mean", self.sns_noise_mean.get()))
        self.sns_error_steps_mean.set(p.get("error_steps_mean", self.sns_error_steps_mean.get()))
        self.sns_error_dose_mean.set(p.get("error_dose_mean", self.sns_error_dose_mean.get()))
        self.sns_moire.set(bool(p.get("moire", self.sns_moire.get())))
        self.sns_moire_fringes.set(p.get("moire_fringes", self.sns_moire_fringes.get()))
        self.sns_moire_profile.set(p.get("moire_profile", self.sns_moire_profile.get()))
        self.sns_moire_direction.set(p.get("moire_direction", self.sns_moire_direction.get()))
        self.sns_moire_phase_scale.set(p.get("moire_phase_scale", self.sns_moire_phase_scale.get()))
        self.sns_moire_phase_offset.set(p.get("moire_phase_offset", self.sns_moire_phase_offset.get()))
        self.sns_axis.set(p.get("axis", self.sns_axis.get()))
        self.sns_df_strength.set(p.get("dark_field_strength", self.sns_df_strength.get()))
        self.sns_geometry_type.set(p.get("geometry_type", self.sns_geometry_type.get()))
        self.sns_geometry_params.set(p.get("geometry_params", self.sns_geometry_params.get()))
        self.sns_scene_json_path.set(p.get("scene_json", self.sns_scene_json_path.get()))
        loaded_layers = p.get("layers", [])
        self.sns_layers_data = loaded_layers if isinstance(loaded_layers, list) else []
        self.sns_selected_layer_index = None
        self._sns_refresh_layers_listbox()
        self._sns_update_params_tooltip()
        self.set_status("SNS preset loaded successfully.")

    def browse_sns_scene_json(self):
        filename = askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.sns_scene_json_path.set(filename)

    def export_SNS_zip(self):
        zip_path = asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")],
        )
        if not zip_path:
            return

        config_json = json.dumps(self.get_SNS_config(), indent=2)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("sns_config.json", config_json)
            zf.writestr("README.txt", (
                "XPCIpy Simple Numerical Simulation\n"
                f"Timestamp: {timestamp}\n\n"
                "Files:\n"
                "  - sns_config.json\n"
                "  - dpc.tif\n"
                "  - attenuation.tif\n"
                "  - dark_field.tif\n"
                "  - object_stack.tif\n"
                "  - reference_stack.tif\n"
            ))
            for name, arr in (
                ("dpc.tif", self.sns_dpc),
                ("attenuation.tif", self.sns_attenuation),
                ("dark_field.tif", self.sns_dark_field),
            ):
                buf = io.BytesIO()
                tifffile.imwrite(buf, np.asarray(arr, dtype=np.float32))
                zf.writestr(name, buf.getvalue())

            buf_obj = io.BytesIO()
            tifffile.imwrite(buf_obj, np.asarray(self.sns_images, dtype=np.float32), photometric="minisblack")
            zf.writestr("object_stack.tif", buf_obj.getvalue())

            buf_ref = io.BytesIO()
            tifffile.imwrite(buf_ref, np.asarray(self.sns_images_reference, dtype=np.float32), photometric="minisblack")
            zf.writestr("reference_stack.tif", buf_ref.getvalue())

    def verify_physical_values_sns(self):
        if self.sns_n.get() <= 0:
            messagebox.showerror("Invalid Parameters", "SNS n must be > 0.")
            return False
        if self.sns_pixel_size.get() <= 0:
            messagebox.showerror("Invalid Parameters", "SNS pixel size must be > 0.")
            return False
        if self.sns_energy.get() <= 0:
            messagebox.showerror("Invalid Parameters", "SNS energy must be > 0.")
            return False
        if self.sns_phase_steps.get() <= 2:
            messagebox.showerror("Invalid Parameters", "SNS phase steps must be > 2.")
            return False
        if self.sns_delta.get() <= 0 or self.sns_beta.get() < 0:
            messagebox.showerror("Invalid Parameters", "SNS delta must be > 0 and beta must be >= 0.")
            return False
        return True

    def _sns_default_params_for_type(self, geometry_type):
        defaults = {
            'sphere': {'radius': 120.0},
            'cylinder': {'outer_radius': 90.0, 'inner_radius': 0.0, 'Orientation': 'Vertical'},
            'wedge': {'width': 140.0, 'thickness': 80.0},
            'ellipsoid': {'radius_x': 100.0, 'radius_y': 60.0, 'radius_z': 45.0},
            'rectangle': {'width': 180.0, 'height': 80.0, 'thickness': 20.0},
            'gaussian_lens': {'sigma_x': 20.0, 'sigma_y': 20.0, 'peak_thickness': 12.0},
            'sinusoidal_grating': {'period': 40.0, 'mean_thickness': 3.0, 'modulation': 0.5, 'axis': 'x', 'phase': 0.0},
        }
        return defaults.get(geometry_type, {})

    def _sns_get_params_description(self, geometry_type):
        descriptions = {
            'sphere': "radius: float (micrometers)",
            'cylinder': "outer_radius, inner_radius, Orientation",
            'wedge': "width, thickness",
            'ellipsoid': "radius_x, radius_y, radius_z",
            'rectangle': "width, height, thickness",
            'gaussian_lens': "sigma_x, sigma_y, peak_thickness",
            'sinusoidal_grating': "period, mean_thickness, modulation, axis, phase",
        }
        return descriptions.get(geometry_type.lower(), "Unknown geometry type.")

    def _sns_update_params_tooltip(self):
        gtype = self.sns_layer_type.get().strip().lower()
        desc = self._sns_get_params_description(gtype)
        if hasattr(self, 'sns_params_info_label'):
            self.sns_params_info_label.config(text=desc)

    def _sns_set_default_params_for_layer_type(self):
        gtype = self.sns_layer_type.get().strip().lower()
        self.sns_layer_params.set(json.dumps(self._sns_default_params_for_type(gtype)))
        self._sns_update_params_tooltip()

    def _sns_reset_layer_editor(self):
        self.sns_layer_type.set('sphere')
        self.sns_layer_mode.set('add')
        self.sns_layer_shift_x.set(0.0)
        self.sns_layer_shift_y.set(0.0)
        self.sns_layer_angle.set(0.0)
        self.sns_layer_params.set(json.dumps({'radius': 120.0}))
        self.sns_layer_optics_mode.set('global')
        if self.sns_material_options:
            self.sns_layer_material.set(self.sns_material_options[0])
        self.sns_layer_delta.set(self.sns_delta.get())
        self.sns_layer_beta.set(self.sns_beta.get())
        self.sns_selected_layer_index = None
        self._sns_refresh_layers_listbox()
        self._sns_update_params_tooltip()

    def _sns_layer_display_name(self, layer, idx):
        layer_type = layer.get('type', 'unknown')
        mode = layer.get('mode', 'add')
        optics = layer.get('optics', {})
        optics_mode = optics.get('mode', 'global')
        if optics_mode == 'material':
            optics_txt = f"mat:{optics.get('material', '?')}"
        elif optics_mode == 'custom':
            d = float(optics.get('delta', self.sns_delta.get()))
            b = float(optics.get('beta', self.sns_beta.get()))
            optics_txt = f"d={d:.2e}, b={b:.2e}"
        else:
            optics_txt = 'global d/b'
        transform = layer.get('transform', {})
        sx = float(transform.get('shift_x', 0.0))
        sy = float(transform.get('shift_y', 0.0))
        angle = float(transform.get('angle_deg', 0.0))
        return f"{idx+1:02d} | {layer_type} | {mode} | {optics_txt} | dx={sx:.1f}, dy={sy:.1f}, a={angle:.1f}"

    def _sns_refresh_layers_listbox(self):
        if not hasattr(self, 'sns_layers_listbox'):
            return
        self.sns_layers_listbox.delete(0, tk.END)
        for i, layer in enumerate(self.sns_layers_data):
            self.sns_layers_listbox.insert(tk.END, self._sns_layer_display_name(layer, i))
        if self.sns_selected_layer_index is not None and 0 <= self.sns_selected_layer_index < len(self.sns_layers_data):
            self.sns_layers_listbox.selection_clear(0, tk.END)
            self.sns_layers_listbox.selection_set(self.sns_selected_layer_index)

    def _sns_validate_params_json(self, params_txt):
        if not params_txt:
            return True, {}
        try:
            params = json.loads(params_txt)
        except Exception as exc:
            return False, f"Invalid JSON: {exc}"
        if not isinstance(params, dict):
            return False, "Layer params must be a JSON object."
        return True, params

    def _sns_validate_parameter_values(self, _layer_type, params):
        numeric_keys = [
            'radius', 'outer_radius', 'inner_radius', 'width', 'thickness',
            'radius_x', 'radius_y', 'radius_z', 'height', 'sigma_x', 'sigma_y',
            'peak_thickness', 'period', 'mean_thickness', 'modulation', 'phase',
        ]
        for key in numeric_keys:
            if key in params and key not in ('phase',):
                try:
                    if float(params[key]) < 0:
                        return False, f"Parameter '{key}' must be >= 0."
                except Exception:
                    return False, f"Parameter '{key}' must be numeric."
        return True, "ok"

    def _sns_editor_to_layer(self):
        layer_type = self.sns_layer_type.get().strip().lower()
        mode = self.sns_layer_mode.get().strip().lower()
        if mode not in ('add', 'subtract'):
            raise ValueError("Layer mode must be 'add' or 'subtract'.")

        params_txt = self.sns_layer_params.get().strip()
        success, result = self._sns_validate_params_json(params_txt)
        if not success:
            raise ValueError(result)
        params = result

        success, msg = self._sns_validate_parameter_values(layer_type, params)
        if not success:
            raise ValueError(msg)

        return {
            'type': layer_type,
            'params': params,
            'transform': {
                'shift_x': float(self.sns_layer_shift_x.get()),
                'shift_y': float(self.sns_layer_shift_y.get()),
                'angle_deg': float(self.sns_layer_angle.get()),
            },
            'mode': mode,
            'optics': {
                'mode': self.sns_layer_optics_mode.get().strip().lower(),
                'material': self.sns_layer_material.get().strip(),
                'delta': float(self.sns_layer_delta.get()),
                'beta': float(self.sns_layer_beta.get()),
            },
        }

    def _sns_layer_to_editor(self, layer):
        self.sns_layer_type.set(layer.get('type', 'sphere'))
        self.sns_layer_mode.set(layer.get('mode', 'add'))
        transform = layer.get('transform', {})
        self.sns_layer_shift_x.set(float(transform.get('shift_x', 0.0)))
        self.sns_layer_shift_y.set(float(transform.get('shift_y', 0.0)))
        self.sns_layer_angle.set(float(transform.get('angle_deg', 0.0)))
        self.sns_layer_params.set(json.dumps(layer.get('params', {})))
        optics = layer.get('optics', {})
        self.sns_layer_optics_mode.set(optics.get('mode', 'global'))
        self.sns_layer_material.set(optics.get('material', self.sns_layer_material.get()))
        self.sns_layer_delta.set(float(optics.get('delta', self.sns_delta.get())))
        self.sns_layer_beta.set(float(optics.get('beta', self.sns_beta.get())))
        self._sns_update_params_tooltip()

    def _sns_add_layer(self):
        try:
            layer = self._sns_editor_to_layer()
        except Exception as e:
            messagebox.showerror("Layer Error", str(e))
            return
        self.sns_layers_data.append(layer)
        self.sns_selected_layer_index = len(self.sns_layers_data) - 1
        self._sns_refresh_layers_listbox()
        self.sns_scene_json_path.set('')
        self.set_status("SNS layer added.")

    def _sns_update_layer(self):
        if self.sns_selected_layer_index is None:
            messagebox.showwarning("Layer manager", "Select a layer first.")
            return
        try:
            layer = self._sns_editor_to_layer()
        except Exception as e:
            messagebox.showerror("Layer Error", str(e))
            return
        if not (0 <= self.sns_selected_layer_index < len(self.sns_layers_data)):
            return
        self.sns_layers_data[self.sns_selected_layer_index] = layer
        self._sns_refresh_layers_listbox()
        self.sns_scene_json_path.set('')
        self.set_status("SNS layer updated.")

    def _sns_remove_layer(self):
        if self.sns_selected_layer_index is None:
            return
        if not (0 <= self.sns_selected_layer_index < len(self.sns_layers_data)):
            return
        del self.sns_layers_data[self.sns_selected_layer_index]
        if not self.sns_layers_data:
            self.sns_selected_layer_index = None
        else:
            self.sns_selected_layer_index = min(self.sns_selected_layer_index, len(self.sns_layers_data) - 1)
        self._sns_refresh_layers_listbox()
        self.set_status("SNS layer removed.")

    def _sns_move_layer(self, delta):
        if self.sns_selected_layer_index is None:
            return
        src = self.sns_selected_layer_index
        dst = src + int(delta)
        if src < 0 or src >= len(self.sns_layers_data):
            return
        if dst < 0 or dst >= len(self.sns_layers_data):
            return
        self.sns_layers_data[src], self.sns_layers_data[dst] = self.sns_layers_data[dst], self.sns_layers_data[src]
        self.sns_selected_layer_index = dst
        self._sns_refresh_layers_listbox()

    def _sns_on_layer_select(self, _event=None):
        if not hasattr(self, 'sns_layers_listbox'):
            return
        sel = self.sns_layers_listbox.curselection()
        if not sel:
            self.sns_selected_layer_index = None
            return
        idx = int(sel[0])
        self.sns_selected_layer_index = idx
        if 0 <= idx < len(self.sns_layers_data):
            self._sns_layer_to_editor(self.sns_layers_data[idx])

    def _sns_import_layers_from_scene_json(self):
        scene_path = self.sns_scene_json_path.get().strip()
        if not scene_path:
            messagebox.showwarning("Layer manager", "Set Scene JSON path first.")
            return
        if not os.path.isfile(scene_path):
            messagebox.showerror("Layer manager", "Scene JSON path does not exist.")
            return
        try:
            cfg = sns_obj.GeometryFactory.load_config_json(scene_path)
            objects = cfg.get('objects', [])
            if not isinstance(objects, list):
                raise ValueError("'objects' must be a list in scene JSON.")
            self.sns_layers_data = objects
            self.sns_selected_layer_index = 0 if self.sns_layers_data else None
            self._sns_refresh_layers_listbox()
            if self.sns_selected_layer_index is not None:
                self._sns_layer_to_editor(self.sns_layers_data[self.sns_selected_layer_index])
            self.set_status("SNS layers imported from scene JSON.")
        except Exception as e:
            messagebox.showerror("Layer manager", f"Could not import layers:\n{e}")

    def _sns_resolve_layer_delta_beta(self, layer):
        optics = layer.get('optics', {}) if isinstance(layer, dict) else {}
        mode = str(optics.get('mode', 'global')).strip().lower()

        if mode == 'custom':
            return float(optics.get('delta', self.sns_delta.get())), float(optics.get('beta', self.sns_beta.get()))

        if mode == 'material':
            material = str(optics.get('material', '')).strip()
            if not material:
                raise ValueError("Layer optics mode 'material' requires a material name.")
            energy = float(self.sns_energy.get())
            wavelength = 1.23984193 / (1000.0 * energy)
            k = 2.0 * np.pi / wavelength
            n_complex = np.asarray(make_material(material, energy), dtype=np.complex128)
            delta_physical = float(np.real(n_complex).reshape(-1)[0])
            beta_physical = float((-np.imag(n_complex)).reshape(-1)[0])
            return k * delta_physical, k * beta_physical

        return float(self.sns_delta.get()), float(self.sns_beta.get())

    def _sns_build_object(self):
        n = self.sns_n.get()
        pixel_size = self.sns_pixel_size.get()
        delta = self.sns_delta.get()
        beta = self.sns_beta.get()

        if self.sns_layers_data:
            thickness_map = np.zeros((n, n), dtype=float)
            phase_map = np.zeros((n, n), dtype=float)
            attenuation_map = np.zeros((n, n), dtype=float)

            transform_helper = sns_obj.GeometryManager(n=n, pixel_size=pixel_size, delta=1.0, beta=1.0)

            for layer in self.sns_layers_data:
                layer_type = layer.get('type', '').strip().lower()
                params = dict(layer.get('params', {}))
                transform = layer.get('transform', {})
                mode = str(layer.get('mode', 'add')).strip().lower()

                layer_delta, layer_beta = self._sns_resolve_layer_delta_beta(layer)

                geom_obj = sns_obj.GeometryFactory.create_object(
                    geometry_type=layer_type, n=n, pixel_size=pixel_size,
                    delta=1.0, beta=1.0, **params,
                )

                geom_proj = np.asarray(geom_obj.Obtain_projection(), dtype=float)
                transformed = transform_helper._transform_projection(
                    geom_proj,
                    shift_x=float(transform.get('shift_x', 0.0)),
                    shift_y=float(transform.get('shift_y', 0.0)),
                    angle_deg=float(transform.get('angle_deg', 0.0)),
                    order=1,
                )

                if mode == 'add':
                    thickness_map += transformed
                    phase_map += layer_delta * transformed
                    attenuation_map += layer_beta * transformed
                elif mode == 'subtract':
                    thickness_map -= transformed
                    phase_map -= layer_delta * transformed
                    attenuation_map -= layer_beta * transformed
                else:
                    raise ValueError("Layer mode must be add or subtract.")

                thickness_map[thickness_map < 0] = 0
                phase_map[phase_map < 0] = 0
                attenuation_map[attenuation_map < 0] = 0

            return sns_obj.MultiMaterialComposite(
                n=n, pixel_size=pixel_size,
                thickness_map=thickness_map,
                phase_map=phase_map,
                attenuation_map=attenuation_map,
            )

        scene_json = self.sns_scene_json_path.get().strip()
        if scene_json:
            return sns_obj.GeometryFactory.create_manager_from_json(
                json_path=scene_json, n=n, pixel_size=pixel_size, delta=delta, beta=beta,
            )

        geometry_type = self.sns_geometry_type.get().strip().lower()
        params_txt = self.sns_geometry_params.get().strip()
        params = {}
        if params_txt:
            params = json.loads(params_txt)
            if not isinstance(params, dict):
                raise ValueError("Geometry params JSON must be a dictionary.")

        return sns_obj.GeometryFactory.create_object(
            geometry_type=geometry_type, n=n, pixel_size=pixel_size, delta=delta, beta=beta, **params,
        )

    def _sns_dark_field_map(self, sim_object):
        strength = float(self.sns_df_strength.get())
        if strength <= 0:
            return np.ones_like(sim_object.Obtain_projection(), dtype=float)
        lap = sim_object.Obtain_Phase_Laplacian()
        norm = np.max(np.abs(lap))
        if norm <= 0:
            return np.ones_like(lap, dtype=float)
        return np.exp(-strength * np.abs(lap) / norm)

    def Plot_SNS_Results(self, frame, dpc, attenuation, dark_field, pbi, images, images_reference, row, column):
        params = {
            "text.color": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.grid": False,
            "axes.labelcolor": "white",
        }
        rcParams.update(params)

        fig = Figure(figsize=(9.2, 4.2))
        fig.set_facecolor("#333333")

        ax1 = fig.add_subplot(2, 3, 1)
        ax1.imshow(dpc, cmap='gray')
        ax1.set_title('DPC (theoretical)')
        ax1.set_xticks([])
        ax1.set_yticks([])

        ax2 = fig.add_subplot(2, 3, 2)
        ax2.imshow(attenuation, cmap='gray')
        ax2.set_title('Attenuation a0')
        ax2.set_xticks([])
        ax2.set_yticks([])

        ax3 = fig.add_subplot(2, 3, 3)
        ax3.imshow(dark_field, cmap='gray', vmin=0, vmax=1)
        ax3.set_title('Dark-field visibility')
        ax3.set_xticks([])
        ax3.set_yticks([])

        ax4 = fig.add_subplot(2, 3, 4)
        ax4.imshow(pbi, cmap='gray')
        ax4.set_title('PBI (near-field)')
        ax4.set_xticks([])
        ax4.set_yticks([])

        ax5 = fig.add_subplot(2, 3, 5)
        ax5.imshow(images[0], cmap='gray')
        ax5.set_title('Object stack (step 0)')
        ax5.set_xticks([])
        ax5.set_yticks([])

        ax6 = fig.add_subplot(2, 3, 6)
        cx = images.shape[1] // 2
        cy = images.shape[2] // 2
        ax6.plot(images[:, cx, cy], color='red', label='Object')
        ax6.plot(images_reference[:, cx, cy], color='deepskyblue', label='Reference')
        ax6.set_title('Modulation curve (center pixel)')
        ax6.set_xlabel('Phase step')
        legend = ax6.legend(facecolor='#333333', edgecolor='white', framealpha=0.85)
        for text in legend.get_texts():
            text.set_color('white')

        fig.tight_layout(pad=0.8, w_pad=0.8, h_pad=0.9)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=column, columnspan=1, padx=5, pady=4, sticky='nw')
