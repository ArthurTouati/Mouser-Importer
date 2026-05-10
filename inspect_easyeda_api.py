import inspect
from easyeda2kicad.easyeda import easyeda_api

for name, obj in inspect.getmembers(easyeda_api):
    if inspect.isclass(obj) or inspect.isfunction(obj):
        print(f"{name}: {obj}")
        if inspect.isclass(obj):
            for method_name, method_obj in inspect.getmembers(obj):
                if inspect.isfunction(method_obj) or str(type(method_obj)) == "<class 'method'>":
                    print(f"  - {method_name}")
