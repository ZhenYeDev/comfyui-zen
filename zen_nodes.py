import random

import logging

logger = logging.getLogger(__name__)


# 你的原有 ZenTextMerge 类代码（不变）
class ZenTextMerge:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_a": (
                    "STRING",
                    {"multiline": True, "default": "First text segment"},
                ),
                "text_b": (
                    "STRING",
                    {"multiline": True, "default": "Second text segment"},
                ),
                "delimiter": ("STRING", {"default": "\n"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("merged_text",)
    FUNCTION = "merge_texts"
    CATEGORY = "ZenNodes"

    def merge_texts(self, text_a, text_b, delimiter, seed):
        parsed_delimiter = bytes(delimiter, "utf-8").decode("unicode_escape")
        # Join two strings with the specified delimiter
        combined_result = f"{text_a}{parsed_delimiter}{text_b}"
        random.seed(seed)

        # Log for debugging purposes
        logger.info(f"Merging texts. Length A: {len(text_a)}, Length B: {len(text_b)}")

        return (combined_result,)


NODE_CLASS_MAPPINGS = {"ZenTextMerge": ZenTextMerge}

NODE_DISPLAY_NAME_MAPPINGS = {"ZenTextMerge": "Zen Text Merge"}
