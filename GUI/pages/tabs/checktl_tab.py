import os
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import src.PCSim.source as source
import src.PCSim.check_Talbot as check_Talbot

from GUI.ui.widgets import Widget as wg
from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.text import check_TL_text


class CheckTLTab:

    def populate_checkTL_tab(self):

        scrollframe = vsf(self.check_TL_tab)
        scrollframe.grid(row=0, column=0, columnspan=3, sticky="nsew")
        container = scrollframe.interior

        self.check_TL_tab.grid_rowconfigure(0, weight=1)
        self.check_TL_tab.grid_columnconfigure(0, weight=0)
        self.check_TL_tab.grid_columnconfigure(1, weight=0)
        self.check_TL_tab.grid_columnconfigure(2, weight=1)
        Grating_OPTIONS = ["Custom", "Phase pi/2", "Phase pi"]

        parameters_frame = ttk.Frame(container, style='TFrame')
        parameters_frame.bind("<Button-1>", self.modify_TL_dist)
        parameters_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.c_results_frame = ttk.Frame(container, style='TFrame')
        self.c_results_frame.grid(row=0, column=2, rowspan=12, sticky='nsew')

        self.initialize_Figure(self.c_results_frame, (3, 3), 0, 0)

        nLabel, c_n_e = wg.create_label_entry(parameters_frame, 'n: size of the wavefront in pixels', 0, 0, textvariable=self.c_n, padx=20)
        pxLabel, c_px_e = wg.create_label_entry(parameters_frame, 'Pixel size (micrometer)', 1, 0, textvariable=self.c_pixel_size, padx=20)
        FWHMSouLabel, c_fwhm_src_e = wg.create_label_entry(parameters_frame, 'Source FWHM (micrometer)', 2, 0, textvariable=self.c_FWHM_source, padx=20)
        EnergyL, c_energy_e = wg.create_label_entry(parameters_frame, 'DEsign Energy (keV)', 3, 0, textvariable=self.c_energy, padx=20)
        PeriodL, c_period_e = wg.create_label_entry(parameters_frame, 'Grating Period (microns)', 4, 0, textvariable=self.c_period, padx=20)
        DCL, c_dc_e = wg.create_label_entry(parameters_frame, 'Duty Cycle', 5, 0, textvariable=self.c_DC, padx=20)
        materialL, _ = wg.create_label_entry(parameters_frame, 'Material (just used for custom grating)', 6, 0, textvariable=self.c_material, padx=20)
        barHeightL, c_barheight_e = wg.create_label_entry(parameters_frame, 'Bar height (micrometer, just for custom grating)', 7, 0, textvariable=self.c_bar_height, padx=20)
        gratigL, _ = wg.create_label_combobox(parameters_frame, label_text='Grating Type', row=8, column=0, textvariable=self.c_grating_def, names=Grating_OPTIONS)
        multiplesL, c_multiples_e = wg.create_label_entry(parameters_frame, 'Multiples of Talbot distance to be represented', row=9, column=0, textvariable=self.c_multiple, padx=20)
        iterationsL, c_iter_e = wg.create_label_entry(parameters_frame, 'Number of calculations performed', row=10, column=0, textvariable=self.c_iterations, padx=20)
        wg.create_label_entry(parameters_frame, 'Talbot Distance (cm)', 11, 0, textvariable=self.c_Talbot_distance, padx=20, state='disable')
        self.RunButton = wg.create_button(parameters_frame, 'Run', 12, 0, command=self.RunCheckTL)

        wg.create_button(parameters_frame, "Exit", 13, 0, padx=60, command=self.close_app)

        self._watch(c_n_e, self.c_n, lambda v: v > 0)
        self._watch(c_px_e, self.c_pixel_size, lambda v: v > 0)
        self._watch(c_fwhm_src_e, self.c_FWHM_source, lambda v: v > 0)
        self._watch(c_energy_e, self.c_energy, lambda v: v > 0)
        self._watch(c_period_e, self.c_period, lambda v: v > 0)
        self._watch(c_dc_e, self.c_DC, lambda v: 0 < v <= 1)
        self._watch(c_barheight_e, self.c_bar_height, lambda v: self.c_grating_def.get() != "Custom" or v > 0)
        self._watch(c_multiples_e, self.c_multiple, lambda v: v > 0)
        self._watch(c_iter_e, self.c_iterations, lambda v: v > 0)
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

        def _auto_update_checkTL(*_args):
            try:
                self.modify_TL_dist(None)
            except Exception:
                pass

        for _var in (self.c_energy, self.c_period, self.c_grating_def):
            try:
                _var.trace_add("write", _auto_update_checkTL)
            except Exception:
                pass

        self.modify_TL_dist(None)

        font = {
            'family': 'serif',
            'color': 'lightgray',
            'weight': 'normal',
            'size': 10,
        }
        fig_text = Figure(figsize=(5, 4))
        fig_text.set_facecolor("#333333")
        canvas = FigureCanvasTkAgg(fig_text, parameters_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=11, column=0, columnspan=3)
        fig_text.text(0.5, 0.5, check_TL_text, ha='center', va='center',
                      bbox=dict(facecolor='#333333', alpha=0.5), fontdict=font)
        canvas.figure = fig_text
        canvas.draw()


    def RunCheckTL(self):
        def _run():
            if not self.verify_physical_values_checkTL():
                self.set_status("Error in physical values for Talbot carpet simulation.")
                return
            n = self.c_n.get()
            pixel_size = self.c_pixel_size.get()
            FWHM_source = self.c_FWHM_source.get()
            Energy = self.c_energy.get()
            Period = self.c_period.get()
            DC = self.c_DC.get()
            Material = self.c_material.get()
            bar_height = self.c_bar_height.get()
            multiples = self.c_multiple.get()
            iterations = self.c_iterations.get()
            grating_option = self.c_grating_def.get()

            MySource = source.Source((FWHM_source, FWHM_source), 'Mono', Energy, 'Plane', pixel_size)

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

            Intensities = check_Talbot.Talbot_carpet(n, MySource, Period, DC, multiples, iterations, grating_type, pixel_size, Energy, material=Material, grating_height=bar_height)
            self.check_tl_intensities = np.asarray(Intensities, dtype=np.float32)

            def update_gui():
                self.clear_frame(self.c_results_frame)
                self.Plot_check_TL(self.c_results_frame, Intensities, 0, 0, (3, 3), title, multiples, n)
                wg.create_button(self.c_results_frame, 'Save Image', 1, 0, command=lambda: self.save_image(Intensities))

            self.master.after(0, update_gui)

        self.run_with_error_handling(_run, "Running Talbot carpet simulation...")

    def verify_physical_values_checkTL(self):
        n = self.c_n.get()
        pixel_size = self.c_pixel_size.get()
        FWHM_source = self.c_FWHM_source.get()
        Energy = self.c_energy.get()
        Period = self.c_period.get()
        DC = self.c_DC.get()
        bar_height = self.c_bar_height.get()
        multiples = self.c_multiple.get()
        iterations = self.c_iterations.get()
        grating_opt = self.c_grating_def.get()

        if n <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of Pixels is a positive value.")
            return False
        if pixel_size <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Pixel Size is a positive value.")
            return False
        if FWHM_source <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Source FWHM is a positive value.")
            return False
        if Energy <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Energy is a positive value.")
            return False
        if Period <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Grating Period is a positive value.")
            return False
        if DC <= 0 or DC > 1:
            messagebox.showerror("Invalid Parameters", "Please ensure that Duty Cycle is between 0 and 1.")
            return False
        if grating_opt == "Custom":
            if bar_height <= 0:
                messagebox.showerror("Invalid Parameter", "For a custom grating, bar height must be > 0 µm.")
                return False
        if multiples <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Talbot multiples is a positive value.")
            return False
        if iterations <= 0:
            messagebox.showerror("Invalid Parameters", "Please ensure that Number of calculations (iterations) is a positive value.")
            return False
        return True

    def Plot_Modulation_Curve(self, frame, image, image_reference, row, column, figsize, title, columnspan=1):
        params = {
            "text.color": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.labelcolor": "white",
            "axes.grid": True,
        }
        rcParams.update(params)

        fig = Figure(figsize=figsize)
        fig.set_facecolor("#333333")
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(image[:, image.shape[1] // 2, image.shape[2] // 2], color='red', label='Object')
        ax.plot(image_reference[:, image_reference.shape[1] // 2, image_reference.shape[2] // 2], color='blue', label='Reference')
        ax.legend()
        ax.set_title(title)
        ax.set_xlabel('Phase Stepping')

        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column, columnspan=columnspan, ipadx=90, ipady=20)

    def Plot_check_TL(self, frame, image, row, column, figsize, title, multiples, n):
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
        im = ax.imshow(image, "gray", interpolation='none', extent=[0, multiples, n, 0], aspect='auto')
        ax.set_title(title)
        ax.set_xlabel('Multiples of Talbot distance')
        fig.colorbar(im, ax=ax)
        fig.tight_layout()

        canvas1 = FigureCanvasTkAgg(fig, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().grid(row=row, column=column, ipadx=90, ipady=20)

    def modify_TL_dist(self, event=None):
        Period_G1 = self.c_period.get()
        energy = self.c_energy.get()
        grating = self.c_grating_def.get()
        mean_wavelength = 1.23984193 / (energy * 1000)

        if grating == 'Absorption':
            distance_Talbot = 2 * Period_G1 ** 2 / (mean_wavelength) * 10 ** (-4)
        elif grating == 'Phase pi':
            distance_Talbot = Period_G1 ** 2 / (8 * mean_wavelength) * 10 ** (-4)
        elif grating == 'Phase pi/2':
            distance_Talbot = Period_G1 ** 2 / (2 * mean_wavelength) * 10 ** (-4)
        else:
            return

        self.c_Talbot_distance.set(distance_Talbot)
