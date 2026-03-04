from .zen_text_merge import ZenTextMergeNode
from .zen_image_list import ZenImageListNode
from .zen_gemini_image import ZenGeminiImageNode

NODE_CLASS_MAPPINGS = {
    "ZenTextMergeNode": ZenTextMergeNode,
    "ZenImageListNode": ZenImageListNode,
    "ZenGeminiImageNode": ZenGeminiImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZenTextMergeNode": "Zen Text Merge",
    "ZenImageListNode": "Zen Image List",
    "ZenGeminiImageNode": "Zen Gemini Image",
}
