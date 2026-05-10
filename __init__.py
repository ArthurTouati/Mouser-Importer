try:
    from .plugin import MouserFetcherPlugin
    MouserFetcherPlugin().register()
except Exception as e:
    import wx
    import traceback
    
    class ErrorPlugin(pcbnew.ActionPlugin):
        def defaults(self):
            self.name = "Mouser Fetcher (ERROR)"
            self.category = "Component Download"
            self.description = "Failed to load. Click for details."
            
        def Run(self):
            wx.MessageBox(f"Error loading plugin:\n\n{traceback.format_exc()}", "Plugin Load Error", wx.ICON_ERROR)
            
    try:
        import pcbnew
        ErrorPlugin().register()
    except:
        pass

