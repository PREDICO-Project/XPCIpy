"""
Mixin class for the TLRec and TLRec-batch tabs.
"""

from GUI.ui.widgets import VerticalScrolledFrame as vsf
from GUI.pages.TLRec_gui import TLRec_GUI
from GUI.pages.TLRec_batch_gui import TLRecBatchGUI


class TLRecTab:

    def populate_TLRec_tab(self):
        scrollframe = vsf(self.TLRec_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior
        self.TLRec_tab.grid_rowconfigure(0, weight=1)
        self.TLRec_tab.grid_columnconfigure(0, weight=1)
        self.tlrec_gui = TLRec_GUI(container, status_var=self.status_var)

    def populate_TLRec_batch_tab(self):
        scrollframe = vsf(self.TL_batch_tab)
        scrollframe.grid(row=0, column=0, sticky="nsew")
        container = scrollframe.interior
        self.TL_batch_tab.grid_rowconfigure(0, weight=1)
        self.TL_batch_tab.grid_columnconfigure(0, weight=1)
        self.tlrec_batch_gui = TLRecBatchGUI(container)
