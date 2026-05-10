import pcbnew
import wx
import os

from .gui import FetcherDialog

class MouserFetcherPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Mouser Component Fetcher"
        self.category = "Component Download"
        self.description = "Search Mouser for components and download footprints via EasyEDA"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

    def Run(self):
        # We need a wx.App if it doesn't exist, but inside KiCad it does.
        dialog = FetcherDialog(None)
        dialog.ShowModal()
        dialog.Destroy()
