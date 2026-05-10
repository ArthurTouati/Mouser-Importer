from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
import json

api = EasyedaApi()
try:
    results = api.search_jlcpcb_components("NE555P")
    print(json.dumps(results, indent=2))
except Exception as e:
    print("Error:", e)
