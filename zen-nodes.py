class ZenTextMerge:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_a": ("STRING", {"multiline": True, "default": "First text segment"}),
                "text_b": ("STRING", {"multiline": True, "default": "Second text segment"}),
                "delimiter": ("STRING", {"default": "\n"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("merged_text",)
    FUNCTION = "merge_texts"
    CATEGORY = "ZenNodes"

    def merge_texts(self, text_a, text_b, delimiter):
        # Join two strings with the specified delimiter
        combined_result = f"{text_a}{delimiter}{text_b}"
        
        # Log for debugging purposes
        print(f"[comfyui-zen] Merging texts. Length A: {len(text_a)}, Length B: {len(text_b)}")
        
        return (combined_result,)
