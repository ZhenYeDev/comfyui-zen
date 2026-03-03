import os
import sys

# 从你的节点文件导入核心的映射字典（注意文件名是zen-nodes.py，导入时要换成下划线）
from .zen_text_merge import ZenTextMerge
from .zen_nano_banana import GeminiImageEditNode


NODE_CLASS_MAPPINGS = {
    "ZenTextMerge": ZenTextMerge,
    "GeminiImageEditNode": GeminiImageEditNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZenTextMerge": "Zen Text Merge",
    "GeminiImageEditNode": "Gemini Image Edit Node",
}


# 可选：定义注册函数，兼容不同版本的ComfyUI
def register_nodes():
    return {
        "NODE_CLASS_MAPPINGS": NODE_CLASS_MAPPINGS,
        "NODE_DISPLAY_NAME_MAPPINGS": NODE_DISPLAY_NAME_MAPPINGS,
    }


# 必须导出这两个核心变量，ComfyUI会读取它们
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
