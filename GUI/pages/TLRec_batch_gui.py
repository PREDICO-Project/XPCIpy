import os
import json
import threading
from glob import glob
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import tifffile

from src.TLRec.Experimental_Retrieval import Modulation_Curve_Reconstruction
from src.TLRec.utils import Apply_Phase_Wiener_filter
from GUI.utils import resource_path
from GUI.ui.styles import Styles as stl
from GUI.ui.widgets import Widget as wg 


def log(msg, text_widget=None):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    print(line, end="")
    if text_widget is not None:
        text_widget.insert("end", line)
        text_widget.see("end")


def find_tiff_files(folder):
    exts = ("*.tif", "*.tiff")
    files = []
    for e in exts:
        files.extend(glob(os.path.join(folder, e)))
    files.sort()
    return files


def algo_name_to_rec_type(name):
    if name == 'Least Squares':
        return 'least_squares'
    if name == 'Fast Least Squares':
        return 'fast_lstsq'
    if name == 'Step Correction':
        return 'Step_correction'
    if name == 'FFT':
        return 'FFT'
    if name == 'Fast FFT':
        return 'Fast_FFT'
    raise ValueError(f"Algorithm not found: {name}")


def reconstruct_stack_pair(obj_stack_path, ref_stack_path, out_dir, cfg, rec_type: str, text_log=None):
    log(f"Reading Object Stack: {obj_stack_path}", text_log)
    log(f"Reading Reference Stack: {ref_stack_path}", text_log)

    images = tifffile.imread(obj_stack_path)
    images_ref = tifffile.imread(ref_stack_path)

    # G2Period: usamos directamente el valor del JSON (igual que en la GUI principal)
    G2Period = cfg["G2Period"]
    DSG1     = cfg["DSG1"]
    DG1G2    = cfg["DG1G2"]
    DOG1     = cfg["DOG1"]
    Energy   = cfg["Design_Energy"]
    px_size  = cfg["Detetor_pixel_size"]

    v0 = cfg["v0"]
    n  = cfg["m"]
    s  = cfg["s"]

    log(f"Reconstructing PC images (type={rec_type})...", text_log)
    Diff_Phase, transmission, Dark_Field, Phase, _, _ = Modulation_Curve_Reconstruction(
        images,
        images_ref,
        G2Period,
        DSG1,
        DG1G2,
        DOG1,
        Energy,
        px_size,
        type=rec_type,
        unwrap_phase=False
    )

    log("Applying Wiener filter...", text_log)
    Phase_filtered = Apply_Phase_Wiener_filter(Diff_Phase, px_size, px_size, v0, n, s)

    os.makedirs(out_dir, exist_ok=True)

    def save_tiff(arr, name):
        path = os.path.join(out_dir, f"{name}.tif")
        tifffile.imwrite(path, arr.astype(np.float32))
        log(f"Saved: {path}", text_log)

    save_tiff(Diff_Phase,     "DPC")
    save_tiff(Phase_filtered, "Phase")
    save_tiff(transmission,   "Transmission")
    save_tiff(Dark_Field,     "DarkField")

    log("Retrieval finished.\n", text_log)


def run_batch_TLRec(root_dir, cfg, algo_name, text_log=None):

    rec_type = algo_name_to_rec_type(algo_name)

    root_dir = os.path.abspath(root_dir)
    log(f"Root folder (Acquisitions): {root_dir}", text_log)
    log(f"Algorithm batch: {algo_name} -> type='{rec_type}'", text_log)

    ref_global_dir = os.path.join(root_dir, "Reference")
    has_global_ref = os.path.isdir(ref_global_dir)
    ref_global_stack = None

    if has_global_ref:
        ref_global_files = find_tiff_files(ref_global_dir)
        if not ref_global_files:
            log("[WARN] 'Reference' exists but there is no .tif/.tiff.", text_log)
            has_global_ref = False
        else:
            ref_global_stack = ref_global_files[0]
            log(f"Global reference is used: {ref_global_stack}", text_log)

    subdirs = [
        d for d in sorted(os.listdir(root_dir))
        if os.path.isdir(os.path.join(root_dir, d)) and d.lower() != "reference"
    ]

    log(f"Found {len(subdirs)} subfolders.", text_log)

    for acq_name in subdirs:
        acq_path = os.path.join(root_dir, acq_name)
        obj_dir  = os.path.join(acq_path, "Object")
        ref_dir_local = os.path.join(acq_path, "Reference")

        if not os.path.isdir(obj_dir):
            log(f"[SKIP] {acq_name}: no folder called 'Object'", text_log)
            continue

        obj_files = find_tiff_files(obj_dir)
        if not obj_files:
            log(f"[SKIP] {acq_name}: no .tif/.tiff in 'Object'", text_log)
            continue

        obj_stack = obj_files[0]

        mode = None
        ref_stack = None

        if os.path.isdir(ref_dir_local):
            ref_files = find_tiff_files(ref_dir_local)
            if ref_files:
                ref_stack = ref_files[0]
                mode = "Local Reference"
            else:
                log(f"[WARN] {acq_name}: 'Reference' empty.", text_log)

        if ref_stack is None and has_global_ref:
            ref_stack = ref_global_stack
            mode = "Global Reference"

        if ref_stack is None:
            log(f"[SKIP] {acq_name}: no valid reference stack.", text_log)
            continue

        out_dir = os.path.join(acq_path, "Retrieved")
        log(f"[INFO] {acq_name}: Object={os.path.basename(obj_stack)} | Ref={os.path.basename(ref_stack)} ({mode})", text_log)
        log(f"[INFO] Results -> {out_dir}", text_log)

        reconstruct_stack_pair(obj_stack, ref_stack, out_dir, cfg, rec_type, text_log=text_log)

    log("Batch TLRec completed.", text_log)

class TLRecBatchGUI:
    
    def __init__(self, master, status_var=None):

        self.master = master
        self.status_var = status_var

        stl.configure_style()

        config_path = resource_path(os.path.join("GUI", "config", "config_TLRec.json"))
        with open(config_path, "r") as f:
            self.cfg = json.load(f)

        self.root_dir_var = tk.StringVar(value="")
        self.algo_var = tk.StringVar(value="Fast FFT")

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.master, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        
        info_frame = ttk.LabelFrame(main, text="Batch Reconstruction", padding=(8, 6))
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        info_text = (
            "This tool automatically reconstructs multiple acquisitions without "
            "loading the stacks into the main GUI.\n\n"
            "Required folder structure inside the selected 'Acquisitions' folder:\n"
            "  - Acquisitions/AcquisitionX/Object/ -> object TIFF stack\n"
            "  - Acquisitions/AcquisitionX/Reference/ -> optional local reference stack (for each object TIFF stack)\n"
            "  - Acquisitions/Reference/ -> optional global reference stack\n\n"
            "For each AcquisitionX, the program uses the local Reference/ folder "
            "if available; otherwise it falls back to the global Acquisitions/Reference/.\n"
            "Results (DPC, Phase, Transmission, DarkField) are saved in:\n"
            "  Acquisitions/AcquisitionX/Retrieved/"
        )


        lbl_info = ttk.Label(info_frame, text=info_text, justify="left", anchor="w", wraplength=650)
        lbl_info.grid(row=0, column=0, sticky="w")
        
        ttk.Label(main, text="'Acquisitions' folder:").grid(row=1, column=0, sticky="w")
        entry = ttk.Entry(main, textvariable=self.root_dir_var, width=60)
        entry.grid(row=2, column=0, sticky="ew", padx=(0, 5))
        btn_browse = ttk.Button(main, text="Browse...", command=self.browse_root_dir)
        btn_browse.grid(row=2, column=1, sticky="e")

        ttk.Label(main, text="Reconstruction Algorithm:").grid(row=3, column=0, sticky="w", pady=(10, 0))

        OPTIONS = [
            "Fast FFT",
            "Least Squares",
            "Fast Least Squares",
            "Step Correction",
            "FFT",
        ]

        algo_cb = ttk.Combobox(main, textvariable=self.algo_var, values=OPTIONS, state="readonly", width=30)
        algo_cb.grid(row=4, column=0, sticky="w")
        algo_cb.current(0)

        btn_run = ttk.Button(main, text="Run batch", command=self.start_batch)
        btn_run.grid(row=4, column=1, sticky="e")

        self.text_log = tk.Text(main, height=15, bg="#1e1e1e", fg="white")
        self.text_log.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(10, 0))

        scroll = ttk.Scrollbar(main, command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=scroll.set)
        scroll.grid(row=5, column=2, sticky="ns", pady=(10, 0))

        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

    def browse_root_dir(self):
        folder = filedialog.askdirectory(title="Select 'Acquisitions' folder")
        if folder:
            self.root_dir_var.set(folder)

    def start_batch(self):
        root_dir = self.root_dir_var.get().strip()
        if not root_dir:
            messagebox.showwarning("Missing folder", "Please select the 'Acquisitions' folder.")
            return

        if not os.path.isdir(root_dir):
            messagebox.showerror("Invalid folder", "Selected path is not a folder.")
            return

        algo_name = self.algo_var.get()

        self.set_ui_busy(True)
        log("=== Starting batch reconstruction ===", self.text_log)

        def worker():
            try:
                run_batch_TLRec(root_dir, self.cfg, algo_name, text_log=self.text_log)
                # OJO: aquí usamos master.after, no self.after
                self.master.after(0, lambda: messagebox.showinfo("Batch finished", "Batch reconstruction completed."))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))
            finally:
                self.master.after(0, lambda: self.set_ui_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def set_ui_busy(self, busy: bool):
        state = "disabled" if busy else "normal"

        INTERACTIVE_TYPES = (
            tk.Button, ttk.Button,
            tk.Entry, ttk.Entry,
            ttk.Combobox,
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

if __name__ == "__main__":
    app = TLRecBatchGUI()
    app.mainloop()
