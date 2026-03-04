from comfy_api.latest import io
import random
import logging

logger = logging.getLogger(__name__)

class ZenTextMergeNode(io.ComfyNode):

    @classmethod
    def define_schema(cls):
        autogrow_template = io.Autogrow.TemplatePrefix(
            io.String.Input("STRING"),  # Input type
            prefix="string_",
            min=2,
            max=50,
        )

        return io.Schema(
            node_id="ZenTextMergeNode",
            display_name="Zen Text Merge",
            category="string",
            inputs=[
                io.Autogrow.Input("texts", template=autogrow_template),
                io.Int.Input("seed", display_name="Seed", default=random.randint(0, 0xFFFFFFFF), min=0, max=0xFFFFFFFF),
            ],
            outputs=[
                io.String.Output(display_name="MERGED_TEXT"),
            ],
        )

    @classmethod
    def execute(cls, texts: io.Autogrow.Type, seed: int):
        logger.info(f"Received texts: {texts}")
        random.seed(seed)
        # texts behaves like a dict
        keys = list(texts.keys()) 
        merged = "\n".join(texts[key] for key in keys)

        logger.info(f"Merged text: {merged}")

        # ✅ return plain Python str, NOT io.String.Output
        return io.NodeOutput(merged.strip())