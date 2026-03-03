from comfy_api.latest import io


class ZenTextMerge:

    @classmethod
    def define_schema(cls):
        autogrow_template = io.Autogrow.TemplatePrefix(
            io.String.Input("text"),   # 👈 改成 String
            prefix="text",
            min=2,
            max=50
        )

        return io.Schema(
            node_id="ZenTextMergeNode",
            display_name="Zen Text Merge",
            category="text",
            inputs=[
                io.Autogrow.Input("texts", template=autogrow_template),
            ],
            outputs=[
                io.String.Output("merged_text"),  # 👈 输出 string
            ],
        )

    @classmethod
    def execute(cls, texts: io.Autogrow.Type):
        # texts 是 dict: {"text_1": "...", "text_2": "..."}
        merged = "\n".join(texts.values())

        return {
            "merged_text": merged
        }