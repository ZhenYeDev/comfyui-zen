from .zen_nodes import ZenTextMerge

NODE_CLASS_MAPPINGS = {
    "ZenTextMerge": ZenTextMerge
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZenTextMerge": "Zen Text Merge Node"
}

# Web UI startup message
print("--- [comfyui-zen] Zen Nodes loaded successfully ---")

