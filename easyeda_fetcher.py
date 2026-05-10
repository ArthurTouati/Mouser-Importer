import os
import subprocess
import sys
from easyeda2kicad.easyeda.easyeda_api import EasyedaApi

class EasyedaFetcher:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.api = EasyedaApi()
        
    def search_mpn(self, mpn):
        """Search EasyEDA for a Manufacturer Part Number and return the best LCSC ID."""
        try:
            data = self.api.search_jlcpcb_components(mpn)
            
            # search_jlcpcb_components returns a dict like {"total": 1, "results": [...]}
            # or sometimes just a list depending on the API changes. Let's handle both.
            if isinstance(data, dict):
                results = data.get("results", [])
            else:
                results = data
                
            if not results:
                return []
            
            lcsc_ids = []
            # First, add exact matches
            for res in results:
                if isinstance(res, dict) and res.get('model', '').upper() == mpn.upper():
                    lcsc = res.get('lcsc')
                    if lcsc and lcsc not in lcsc_ids:
                        lcsc_ids.append(lcsc)
            
            # Then, add other matches
            for res in results:
                if isinstance(res, dict):
                    lcsc = res.get('lcsc')
                    if lcsc and lcsc not in lcsc_ids:
                        lcsc_ids.append(lcsc)
                
            return lcsc_ids
        except Exception as e:
            print(f"Error searching EasyEDA: {e}")
            return []

    def download_component(self, lcsc_id, lib_name="EasyEDA_Mouser"):
        """Download KiCad symbol, footprint, and 3D model using easyeda2kicad CLI."""
        
        # In KiCad, sys.executable is usually kicad.exe, not python.exe
        # We need to find the actual python executable
        import os
        python_exe = os.path.join(os.path.dirname(sys.executable), "python.exe")
        if not os.path.exists(python_exe):
            # Fallback to just "python" if not found
            python_exe = "python"
            
        # ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        lib_file = f"{lib_name}.kicad_sym"
        cmd = [python_exe, "-m", "easyeda2kicad", "--full", "--lcsc_id", lcsc_id, "--output", lib_file]
        
        try:
            result = subprocess.run(cmd, cwd=self.output_dir, capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

