from tkinter import ttk

class Styles:

    @staticmethod
    def configure_style():

        font_type='Segoe Ui'
        font_size=10
        combobox_hover_background = "gray25"  
        combobox_hover_foreground = "black"  
        

        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TText", background="gray12", foreground="white", font=(font_type, font_size), borderwidth=1)
        style.configure("TLabel", background="gray20", foreground="white", font=(font_type, font_size))
        style.configure("Custom.TLabelframe", background="gray20", foreground="white", bordercolor="gray20")
        style.configure("TLabelframe.Label", background="gray20", foreground="white")
        style.configure("TEntry", background="gray35", foreground="black", font=(font_type, font_size))  
        style.configure("TLabelframe", background="gray20", foreground="white", font=(font_type, font_size))
        style.configure("TLabelframe.Label", background="gray20", foreground="white", font=(font_type, font_size))
        style.configure("TButton", background="gray35", foreground="white", font=(font_type, font_size))
       
        style.configure("TFrame", background="gray20")
        style.configure("TNotebook", background="gray20", borderwidth=0)
        style.configure("TNotebook.Tab", background="gray35", foreground="white", padding=[5, 2], ont=(font_type, font_size))
        
        style.configure("TNotebook", background="gray20", bordercolor="gray20")
        style.map("TNotebook.Tab", background=[("selected", "gray20")], expand=[("selected", [1, 1, 1, 0])])

        style.map("TButton",
                  background=[("active", combobox_hover_background)])

        style.map("TCombobox",
                  fieldbackground=[("active", combobox_hover_background), ("disabled", '#ffffff')],
                  foreground=[("active", combobox_hover_foreground)],
                  background=[("active", combobox_hover_background), ("disabled", '#737373')])
        style.configure("Dark.Horizontal.TScale", background="gray20", troughcolor="gray35")