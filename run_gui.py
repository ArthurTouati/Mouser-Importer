import wx
from gui import FetcherDialog

app = wx.App()
dialog = FetcherDialog(None)
dialog.ShowModal()
dialog.Destroy()
app.MainLoop()
