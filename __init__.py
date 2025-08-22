import os
import importlib

# Tell ComfyUI server our Web directory
WEB_DIRECTORY = "./js"

# ComfyUI node mapping dictionaries
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Dynamically load all nodes
# ======================================================================================================================
# Get current file directory
current_dir = os.path.dirname(os.path.abspath(__file__))
nodes_dir = os.path.join(current_dir, "nodes")

# Traverse all python files in nodes directory
for filename in os.listdir(nodes_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = f".nodes.{filename[:-3]}"
        try:
            # Dynamically import module
            module = importlib.import_module(module_name, package=__name__)
            
            # Get node mappings from module
            if hasattr(module, "NODE_CLASS_MAPPINGS") and hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
                print(f"  - Successfully loaded module: {module_name}")
            else:
                print(f"  - Warning: Module {module_name} missing required mapping variables")

        except Exception as e:
            print(f"  - Error: Failed to load module {module_name} - {e}")
# ======================================================================================================================

# Export variables required by ComfyUI
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

print("🎨 ComfyUI-Only custom nodes loaded")
print(f"   - Frontend extension directory: {WEB_DIRECTORY}")
print(f"   📦 Registered {len(NODE_CLASS_MAPPINGS)} nodes:")
for name in NODE_CLASS_MAPPINGS.keys():
    display_name = NODE_DISPLAY_NAME_MAPPINGS.get(name, name)
    print(f"   - {name} ({display_name})")