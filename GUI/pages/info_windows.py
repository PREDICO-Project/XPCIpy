import tkinter as tk
from tkinter import ttk
from GUI.utils import resource_path

class BaseTextWindow(tk.Toplevel):

    def __init__(self, master, title="Info", font=("Arial", 11)):
        super().__init__(master)
        self.title(title)
        self.geometry("800x600")

        self.text = tk.Text(self, wrap="word", font=font, bg="#222222", fg="white")
        scrollbar = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    def set_content(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.config(state="disabled")
        
class LicenseWindow(BaseTextWindow):

    def __init__(self, master):
        super().__init__(master, title="License", font=("Courier", 10))

        try:
            license_path = resource_path("LICENSE")
            with open(license_path, "r", encoding="utf-8") as f:
                license_text = f.read()
        except Exception as e:
            license_text = f"Error loading license file:\n{e}"

        self.set_content(license_text)


class CiteWindow(BaseTextWindow):

    def __init__(self, master):
        super().__init__(master, title="How to cite XPCIpy", font=("Arial", 11))

        plain_citation = (
            "V. Sanchez-Lara and D. Garcia-Pinto, \"XPCIpy: A Python toolkit for X-ray phase-contrast imaging,\" Opt. Express  33, 45949-45966 (2025).\n"
        )

        bibtex_entry = r"""
        @article{Sanchez-Lara:25,
        author = {Victor Sanchez-Lara and Diego Garcia-Pinto},
        journal = {Opt. Express},
        keywords = {Biomedical imaging; Diffraction gratings; Fourier transforms; 
        Phase contrast; Phase shift; X-ray imaging},
        number = {22},
        pages = {45949--45966},
        publisher = {Optica Publishing Group},
        title = {XPCIpy: A Python toolkit for X-ray phase-contrast imaging},
        volume = {33},
        month = {Nov},
        year = {2025},
        url = {https://opg.optica.org/oe/abstract.cfm?URI=oe-33-22-45949},
        doi = {10.1364/OE.573918},
        }
        """.strip("\n")

        content = (
            "How to cite XPCIpy\n"
            "------------------\n\n"
            + plain_citation
            + "\nBibTeX:\n\n"
            + bibtex_entry
        )

        self.set_content(content)