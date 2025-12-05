from tkinter import ttk
import tkinter as tk
import os
import platform
from tkinter import filedialog, messagebox

# For Drag and Drop functionality
try:
    from tkinterdnd2 import DND_FILES
    _HAS_DND = True
except Exception:
    DND_FILES = None
    _HAS_DND = False
    
    
class Widget:

    @staticmethod
    def create_frame(master, text, row, column, padx=10, pady=5, sticky="ew", font=("Arial", 12), background="#ffffff"):
        # Crear un estilo personalizado
        style_name = "Custom.TLabelframe"
        style = ttk.Style()
        style.configure(style_name, font=font, background=background)

     
        frame = ttk.LabelFrame(master, text=text, style=style_name)
        frame.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
        return frame

    @staticmethod
    def create_label_entry(master, label_text, row, column, padx=10, pady=5, textvariable=None, width_entry=10, state='normal'):
       
        label = ttk.Label(master, text=label_text)
        label.grid(row=row, column=column, padx=padx, pady=pady, sticky="w")

        entry = ttk.Entry(master, textvariable=textvariable, width=width_entry,state=state)
        entry.grid(row=row, column=column+1, padx=padx, pady=pady, sticky="w")

        return label, entry
    
    @staticmethod
    def create_entry(master, row, column, padx=10, pady=5,columnspan=1):
    
        entry = ttk.Entry(master, justify='center')
        entry.grid(row=row, column=column, columnspan=columnspan, padx=padx, pady=pady)

        return entry
    
    @staticmethod
    def create_button(master, button_text, row, column, padx=10, pady=5,columnspan=1, state = "normal", command=None):
       
        button = ttk.Button(master, text=button_text ,state = state, command=command)
        button.grid(row=row, column=column, columnspan=columnspan, padx=padx, pady=pady)

        return button
    
    @staticmethod
    def create_label(master, text, row, column, sticky="w", padx=10, pady=5, columnspan=1):
       
        label = ttk.Label(master, text=text)
        label.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky, columnspan=columnspan)
        return label

    @staticmethod
    def create_checkbox(master, text, row, column, variable=False, sticky="w", padx=10, pady=5, command=None):
     
        checkbox = ttk.Checkbutton(master, text=text, variable=variable, command = command)
        checkbox.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
        return checkbox

    
    @staticmethod
    def create_label_combobox(master, label_text, names, row, column, textvariable=None,state="readonly"):
        
        # Label
        label = ttk.Label(master, text=label_text)
        label.grid(row=row, column=column, padx=10, pady=5, sticky="w")

        # Combobox
        combobox = ttk.Combobox(master, values=names, textvariable=textvariable,state=state)
        combobox.grid(row=row, column=column+1, padx=10, pady=5, sticky="ew")

        return label, combobox

    @staticmethod
    def create_text_area(master, row, column, height=10, width=50, padx=20, pady=20, wrap=tk.WORD):
     
        
        text_area = tk.Text(master, height=height, width=width, wrap=wrap, padx=padx, pady=pady,
                            background="gray12", foreground="white", font=('Comic Sans', 10), borderwidth=1)
        text_area.grid(row=row, column=column, sticky="nsew")
        text_area.configure(state="disabled")
        
        return text_area

    @staticmethod
    def create_label_file_combobox(master, label_text, directory_path, row, column, combobox_textvariable=None, state="readonly", file_extension="all", distribution='horizontal'):
        """
        Create a combobox and its label. The values of the combobox will be the files inside directory_path.
        """
        label = ttk.Label(master, text=label_text)
        label.grid(row=row, column=column, padx=10, pady=5, sticky="w")

        if combobox_textvariable is None:
            combobox_textvariable = tk.StringVar(master)

      
        if file_extension == "all":
            file_names = sorted([f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))])
        else:
            file_names = sorted([f for f in os.listdir(directory_path) if f.endswith('.' + file_extension) and os.path.isfile(os.path.join(directory_path, f))])
        file_names.insert(0,'None')
    
        
        combobox = ttk.Combobox(master, textvariable=combobox_textvariable, values=file_names, state=state)
        combobox.grid(row=row, column=column+1, padx=10, pady=5, sticky="ew")

        return label, combobox
    
class VerticalScrolledFrame(ttk.Frame):

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)
        

        canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set, background="gray20")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vscrollbar.config(command=canvas.yview)

        self.interior = interior = ttk.Frame(canvas, style="TFrame")
        interior_id = canvas.create_window(0, 0, window=interior, anchor=tk.NW)
        
        system = platform.system()
        #print(system)

        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)

            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        #def _on_mousewheel(event):
            #canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel(event):
            if system == 'Windows':
                delta = int(-1 * (event.delta / 120))
            elif system == 'Darwin':
                delta = int(-1 * (event.delta))
            else:
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
                else:
                    delta = 0

            if delta != 0:
                canvas.yview_scroll(delta, "units")

        def _bind_mousewheel(event):
            if system in ('Windows', 'Darwin'):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            else:
                canvas.bind_all("<Button-4>", _on_mousewheel)
                canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            if system in ('Windows', 'Darwin'):
                canvas.unbind_all("<MouseWheel>")
            else:
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

class ToggleButton(ttk.Button):
    def __init__(self, master, text, variable, **kwargs):
        super().__init__(master, text=text, command=self.toggle, **kwargs)
        self.variable = variable
        self.update_color()

    def toggle(self):
        self.variable.set(not self.variable.get())
        self.update_color()

    def update_color(self):
        if self.variable.get():
            self.config(style="ToggleOn.TButton")
        else:
            self.config(style="ToggleOff.TButton")
            
class DropZone(tk.Frame):
    """
    Generic drag & drop + browse area.
    """
    
    def __init__(
        self,
        parent,
        title="Files",
        description="Drag & drop files here",
        button_text="Browse files",
        on_files_dropped=None,
        extensions=None,
        multiple=False,
        filetypes=None,
        enable_dnd=True,
        status_text="No file loaded",
        **kwargs
    ):
        super().__init__(parent, bg="#252525", bd=1, relief="solid", **kwargs)

        self.on_files_dropped = on_files_dropped
        self.extensions = [ext.lower() for ext in extensions] if extensions else None
        self.multiple = multiple
        self.filetypes = filetypes

        self.columnconfigure(0, weight=1)

        inner = tk.Frame(self, bg="#303030")
        inner.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        inner.columnconfigure(0, weight=1)

        #self.icon_lbl = tk.Label(inner, text=" ", bg="#303030", fg="#aaaaaa", font=("Segoe UI", 20, "bold"))
        #self.icon_lbl.grid(row=0, column=0, pady=(6, 0))


        self.title_lbl = tk.Label(inner, text=title, bg="#303030", fg="white", font=("Segoe UI", 10, "bold"))
        self.title_lbl.grid(row=0, column=0, pady=(2, 0))

        
        self.desc_lbl = tk.Label(inner, text=description, bg="#303030", fg="#cccccc", font=("Segoe UI", 9))
        self.desc_lbl.grid(row=1, column=0, pady=(2, 0))

        # "or"
        self.or_lbl = tk.Label(inner, text="or", bg="#303030", fg="#888888", font=("Segoe UI", 8, "italic"))
        self.or_lbl.grid(row=2, column=0, pady=(0, 0))

        # Browse button
        self.browse_btn = ttk.Button(inner, text=button_text, command=self._on_browse_clicked)
        self.browse_btn.grid(row=3, column=0, pady=(4, 8))
        
        # Filename loaded
        self.status_lbl = tk.Label(inner, text=status_text, bg="#303030", fg="#999999", font=("Segoe UI", 8), wraplength=260)
        self.status_lbl.grid(row=4, column=0, pady=(0, 4))

   
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        if enable_dnd and _HAS_DND:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_drop_event)
            except Exception:
                pass

    def _on_enter(self, event):
        self.configure(bg="#3a3a3a")

    def _on_leave(self, event):
        self.configure(bg="#252525")

    def _on_browse_clicked(self):
        """Open a file dialog and send selected paths to callback."""
        if self.multiple:
            paths = filedialog.askopenfilenames(filetypes=self.filetypes)
        else:
            path = filedialog.askopenfilename(filetypes=self.filetypes)
            paths = [path] if path else []

        if paths and self.on_files_dropped:
            self.on_files_dropped(list(paths))

    def _filter_by_extension(self, paths):
        """Filter list of paths by allowed extensions, if any."""
        if self.extensions is None:
            return list(paths)
        out = []
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in self.extensions:
                out.append(p)
        return out

    def _on_drop_event(self, event):
        """Handle <<Drop>> event from tkinterdnd2."""
        try:
            raw = event.data
            paths = self.tk.splitlist(raw)
            paths = self._filter_by_extension(paths)
            if not paths:
                messagebox.showwarning("Invalid files", "The dropped files do not match the expected extensions.")
                return
            if self.on_files_dropped:
                self.on_files_dropped(list(paths))
        except Exception as e:
            messagebox.showerror("Drop error", f"Could not process dropped files:\n{e}")
    
    def set_status_text(self, text):
        """Update the status label text."""
        if not text:
            text = "No file loaded"
        else:
            text = f"Loaded: {text}"
        self.status_lbl.config(text=text)
        
    