from comfy_api.latest import io
import random
import logging

logger = logging.getLogger(__name__)


ZEN_IMAGE_LIST = "ZEN_IMAGE_LIST"  # Custom type for voice selection


class ZenImageListNode(io.ComfyNode):

    @classmethod
    def define_schema(cls):
        autogrow_template = io.Autogrow.TemplatePrefix(
            io.Image.Input("image"),
            prefix="image_",
            min=1,
            max=50,
        )

        return io.Schema(
            node_id="ZenImageListNode",
            display_name="Zen Image List",
            category="image",
            inputs=[
                io.Autogrow.Input("images", template=autogrow_template),
            ],
            outputs=[
                io.Custom(ZEN_IMAGE_LIST).Output(display_name="IMAGE_LIST"),
            ],
        )

    @classmethod
    def execute(cls, images: dict):
        image_list = [img for img in images.values() if img is not None]
        return io.NodeOutput(image_list)
