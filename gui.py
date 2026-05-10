import wx
import json
import os
import threading
import io
import requests

from .mouser_api import MouserAPI
from .easyeda_fetcher import EasyedaFetcher

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

class FetcherDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Mouser Component Fetcher (EasyEDA Download)", size=(900, 600))
        
        self.config = self.load_config()
        self.mouser_parts = []
        
        self.init_ui()
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"mouser_api_key": "", "output_dir": "", "lib_name": "EasyEDA_Mouser"}
        
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)
            
    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # --- Config Section ---
        config_box = wx.StaticBox(self, label="Configuration")
        config_sizer = wx.StaticBoxSizer(config_box, wx.HORIZONTAL)
        
        config_sizer.Add(wx.StaticText(self, label="Output Dir:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.output_dir_input = wx.TextCtrl(self, value=self.config.get("output_dir", ""))
        config_sizer.Add(self.output_dir_input, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=5)
        
        dir_btn = wx.Button(self, label="Browse...")
        dir_btn.Bind(wx.EVT_BUTTON, self.on_browse_dir)
        config_sizer.Add(dir_btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=10)
        
        config_sizer.Add(wx.StaticText(self, label="Lib Name:"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.lib_name_input = wx.TextCtrl(self, value=self.config.get("lib_name", "EasyEDA_Mouser"))
        config_sizer.Add(self.lib_name_input, proportion=0, flag=wx.EXPAND)
        
        vbox.Add(config_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        
        # --- Search Section ---
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        search_sizer.Add(wx.StaticText(self, label="Search Keyword (e.g. NE555):"), flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        
        self.search_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search_input.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        search_sizer.Add(self.search_input, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)
        
        self.search_btn = wx.Button(self, label="Search Mouser")
        self.search_btn.Bind(wx.EVT_BUTTON, self.on_search)
        search_sizer.Add(self.search_btn)
        
        vbox.Add(search_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # --- Results Section ---
        results_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.list_ctrl.InsertColumn(0, "Manufacturer Part #", width=150)
        self.list_ctrl.InsertColumn(1, "Manufacturer", width=150)
        self.list_ctrl.InsertColumn(2, "Description", width=250)
        self.list_ctrl.InsertColumn(3, "In Stock", width=80)
        self.list_ctrl.InsertColumn(4, "Price", width=80)
        
        results_sizer.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)
        
        self.image_bitmap = wx.StaticBitmap(self, size=(150, 150))
        results_sizer.Add(self.image_bitmap, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        
        vbox.Add(results_sizer, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        # --- Action Section ---
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.download_btn = wx.Button(self, label="Download Footprint && Symbol")
        self.download_btn.Bind(wx.EVT_BUTTON, self.on_download)
        self.download_btn.Disable()
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        
        action_sizer.Add(self.download_btn, flag=wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(action_sizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)
        
        # --- Log Section ---
        self.log_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 100))
        vbox.Add(self.log_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        
        self.SetSizer(vbox)
        
    def log(self, message):
        wx.CallAfter(self.log_text.AppendText, message + "\n")
        
    def on_browse_dir(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.output_dir_input.SetValue(dlg.GetPath())
        dlg.Destroy()
        
    def on_item_selected(self, event):
        self.download_btn.Enable()
        sel = self.list_ctrl.GetFirstSelected()
        if sel >= 0:
            part = self.mouser_parts[sel]
            img_url = part.get("ImagePath", "")
            if img_url:
                threading.Thread(target=self.fetch_image, args=(img_url,), daemon=True).start()
            else:
                self.image_bitmap.SetBitmap(wx.NullBitmap)
                
    def fetch_image(self, url):
        try:
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = "https://www.mouser.com" + url
            url = url.replace("http://", "https://")
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                img_data = resp.content
                img_stream = io.BytesIO(img_data)
                img = wx.Image(img_stream)
                
                # Resize keeping aspect ratio
                w = img.GetWidth()
                h = img.GetHeight()
                if w > 150 or h > 150:
                    if w > h:
                        new_w = 150
                        new_h = int(h * (150.0 / w))
                    else:
                        new_h = 150
                        new_w = int(w * (150.0 / h))
                    img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
                    
                bmp = wx.Bitmap(img)
                wx.CallAfter(self.set_image, bmp)
            else:
                wx.CallAfter(self.log, f"Failed to fetch image: HTTP {resp.status_code}")
        except Exception as e:
            wx.CallAfter(self.log, f"Error fetching image: {e}")
            
    def set_image(self, bmp):
        self.image_bitmap.SetBitmap(bmp)
        self.Layout()
        
    def on_search(self, event):
        api_key = self.config.get("mouser_api_key", "").strip()
        keyword = self.search_input.GetValue().strip()
        
        if not api_key:
            wx.MessageBox("Mouser API Key not found! Please add your key to config.json.", "Error", wx.ICON_ERROR)
            return
            
        if not keyword:
            return
            
        self.save_config()
        
        self.search_btn.Disable()
        self.list_ctrl.DeleteAllItems()
        self.mouser_parts = []
        self.log(f"Searching Mouser for '{keyword}'...")
        
        threading.Thread(target=self.do_search, args=(api_key, keyword), daemon=True).start()
        
    def do_search(self, api_key, keyword):
        try:
            mouser = MouserAPI(api_key)
            parts = mouser.search_keyword(keyword)
            wx.CallAfter(self.update_results, parts)
        except Exception as e:
            self.log(f"Search Error: {e}")
            wx.CallAfter(self.search_btn.Enable)
            
    def update_results(self, parts):
        self.search_btn.Enable()
        self.mouser_parts = parts
        
        if not parts:
            self.log("No parts found.")
            return
            
        self.log(f"Found {len(parts)} parts.")
        
        for i, part in enumerate(parts):
            mpn = part.get("ManufacturerPartNumber", "")
            mfr = part.get("Manufacturer", "")
            desc = part.get("Description", "")
            stock = part.get("Availability", "")
            
            # Simple price extraction
            price = ""
            price_breaks = part.get("PriceBreaks", [])
            if price_breaks:
                price = price_breaks[0].get("Price", "")
                
            self.list_ctrl.InsertItem(i, mpn)
            self.list_ctrl.SetItem(i, 1, mfr)
            self.list_ctrl.SetItem(i, 2, desc)
            self.list_ctrl.SetItem(i, 3, stock)
            self.list_ctrl.SetItem(i, 4, price)

    def on_download(self, event):
        sel = self.list_ctrl.GetFirstSelected()
        if sel < 0:
            return
            
        part = self.mouser_parts[sel]
        mpn = part.get("ManufacturerPartNumber", "")
        output_dir = self.output_dir_input.GetValue().strip()
        lib_name = self.lib_name_input.GetValue().strip()
        
        if not output_dir or not lib_name:
            wx.MessageBox("Please select an output directory and a library name.", "Error", wx.ICON_ERROR)
            return
            
        self.config["output_dir"] = output_dir
        self.config["lib_name"] = lib_name
        self.save_config()
        
        self.download_btn.Disable()
        self.log(f"Starting download process for {mpn} into library '{lib_name}'...")
        
        threading.Thread(target=self.do_download, args=(mpn, output_dir, lib_name), daemon=True).start()
        
    def do_download(self, mpn, output_dir, lib_name):
        fetcher = EasyedaFetcher(output_dir)
        
        self.log(f"Searching EasyEDA for MPN: {mpn}")
        lcsc_ids = fetcher.search_mpn(mpn)
        
        if not lcsc_ids:
            self.log(f"Could not find an LCSC equivalent for {mpn} on EasyEDA.")
            wx.CallAfter(self.download_btn.Enable)
            return
            
        self.log(f"Found {len(lcsc_ids)} potential LCSC IDs. Trying to download CAD models...")
        
        success = False
        output = ""
        for lcsc_id in lcsc_ids:
            self.log(f"Trying LCSC ID: {lcsc_id}...")
            success, output = fetcher.download_component(lcsc_id, lib_name)
            if success:
                self.log(f"Successfully appended {lcsc_id} to library '{lib_name}'.")
                self.log(f"--> In KiCad, go to Preferences -> Manage Symbol/Footprint Libraries and add:")
                self.log(f"    {os.path.join(output_dir, lib_name + '.kicad_sym')}")
                self.log(f"    {os.path.join(output_dir, lib_name + '.pretty')}")
                wx.CallAfter(wx.MessageBox, f"Download complete!\nComponent added to library {lib_name}.\n\nIf not done yet, don't forget to add this library in KiCad's Preferences.", "Success", wx.ICON_INFORMATION)
                break
            else:
                self.log(f"Failed for {lcsc_id}. (Missing footprint or model).")
                
        if not success:
            self.log(f"All attempts failed. EasyEDA doesn't have CAD data for any matching parts.")
            self.log(f"Last error: {output}")
            
        wx.CallAfter(self.download_btn.Enable)
