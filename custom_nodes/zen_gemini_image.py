from comfy_api.latest import io
import traceback
from io import BytesIO
from PIL import Image
import numpy as np
import torch

# preferred official package namespace
from google import genai
from google.genai.types import GenerateContentConfig, Modality, Part

from .zen_image_list import ZEN_IMAGE_LIST


import logging

logger = logging.getLogger(__name__)


class ZenGeminiImageNode(io.ComfyNode):

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ZenGeminiImageNode",
            display_name="Zen Gemini Image",
            category="debug",
            inputs=[
                io.String.Input("prompt", display_name="Prompt", multiline=True, placeholder="Describe the image generation/editing task."),
                io.String.Input("model_name", display_name="Model Name", default="gemini-3.1-flash-image-preview"),
                io.String.Input("api_key", display_name="API Key", placeholder="Enter your Gemini API key"),
                io.Custom(ZEN_IMAGE_LIST).Input("image_list", display_name="image_list", optional=True),
            ],
            outputs= [
                io.Image.Output(display_name="IMAGE"),
            ],
        )

    @classmethod
    def execute(cls, prompt: str, model_name: str, api_key: str, image_list: list | None = None):
        """
        所有图片平等参与生成
        """
        if genai is None:
            raise RuntimeError(
                "google-genai (or google.genai) library not found. Install with: pip install google-genai"
            )

        
        contents = [prompt]
        images = list(image_list) if image_list else []

        if images:
            logger.info(f"Received {len(images)} images for Gemini generation.")

            for idx, img in enumerate(images, start=1):
                try:
                    pil_img = cls._to_pil(img)
                    buf = BytesIO()
                    pil_img.save(buf, format="PNG")

                    contents.append(
                        Part.from_bytes(
                            data=buf.getvalue(),
                            mime_type="image/png"
                        )
                    )

                except Exception as e:
                    raise RuntimeError(f"Failed to process image {idx}: {e}")
        else:
            logger.info("No images provided, running text-only generation.")

        # 创建 Gemini client
        try:
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
        except Exception as e:
            raise RuntimeError(f"Failed to create genai.Client: {e}")

        # 调用模型
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=GenerateContentConfig(response_modalities=[Modality.IMAGE])
            )
        except Exception as e:
            tb = traceback.format_exc()
            raise RuntimeError(f"Model request failed: {e}\n{tb}")

        # 提取图像字节
        img_bytes = None
        try:
            if getattr(response, "candidates", None):
                for cand in response.candidates:
                    content = getattr(cand, "content", None)
                    if not content:
                        continue
                    for part in getattr(content, "parts", []) or []:
                        inline = getattr(part, "inline_data", None)
                        if inline is not None and getattr(inline, "data", None):
                            data_field = inline.data
                            img_bytes = bytes(data_field) if isinstance(data_field, (bytes, bytearray)) else bytes(list(data_field))
                            break
                    if img_bytes:
                        break
        except Exception:
            img_bytes = None

        # 如果没有返回图像，则提取文本信息
        if img_bytes is None:
            text_preview = None
            try:
                textual_parts = []
                if getattr(response, "candidates", None):
                    for cand in response.candidates:
                        content = getattr(cand, "content", None)
                        if not content:
                            continue
                        for part in getattr(content, "parts", []) or []:
                            t = getattr(part, "text", None)
                            if t:
                                textual_parts.append(t)
                if textual_parts:
                    text_preview = "\n".join(textual_parts[:3])
            except Exception:
                text_preview = None

            msg = "No image data found in model response."
            if text_preview:
                snippet = text_preview.strip()
                if len(snippet) > 800:
                    snippet = snippet[:800] + "..."
                msg += f" Model returned text instead:\n{snippet}"
            raise RuntimeError(msg)

        # 字节 -> PIL -> tensor
        try:
            out_pil = Image.open(BytesIO(img_bytes)).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to open returned image bytes: {e}")

        out_tensor = cls._pil_to_tensor_channel_last(out_pil)
        logger.info(f"Gemini generation successful, returning tensor shape: {out_tensor.shape}")

        return io.NodeOutput(out_tensor)
    

    # -----------------------
    # Utility converters
    # -----------------------  
    @classmethod
    def _to_pil(self, image):
        """将 ComfyUI 的 IMAGE（torch.Tensor / numpy.ndarray / PIL.Image）转换为 PIL.Image（RGB）。"""
        # Torch tensor
        if isinstance(image, torch.Tensor):
            img = image.detach().cpu()
            # 如果存在 batch 维 (1, C, H, W) 或 (1, H, W, C)
            if img.ndim == 4 and img.shape[0] == 1:
                img = img.squeeze(0)
            # 通道优先 (C,H,W) -> (H,W,C)
            if (
                img.ndim == 3
                and img.shape[0] in (1, 3, 4)
                and img.shape[0] < img.shape[1]
            ):
                img = img.permute(1, 2, 0)
            arr = img.numpy()
            # 浮点数如果在 [0..1] -> 缩放到 0..255
            if arr.dtype in (np.float32, np.float64):
                # 保守判断：如果最大值 <= 1.0 则认为范围是 [0..1]
                if np.nanmax(arr) <= 1.0:
                    arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    arr = np.clip(arr, 0, 255).astype(np.uint8)
            else:
                arr = arr.astype(np.uint8)
            # 灰度图 -> 3 通道
            if arr.ndim == 2:
                arr = np.stack([arr] * 3, axis=-1)
            if arr.ndim == 3 and arr.shape[2] == 1:
                arr = np.concatenate([arr, arr, arr], axis=2)
            return Image.fromarray(arr).convert("RGB")

        # Numpy 数组处理
        if isinstance(image, np.ndarray):
            arr = image
            # 通道优先的启发式处理
            if (
                arr.ndim == 3
                and arr.shape[0] in (1, 3, 4)
                and arr.shape[0] < arr.shape[1]
            ):
                arr = np.transpose(arr, (1, 2, 0))
            if arr.dtype in (np.float32, np.float64):
                if np.nanmax(arr) <= 1.0:
                    arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    arr = np.clip(arr, 0, 255).astype(np.uint8)
            else:
                arr = arr.astype(np.uint8)
            if arr.ndim == 2:
                arr = np.stack([arr] * 3, axis=-1)
            if arr.ndim == 3 and arr.shape[2] == 1:
                arr = np.concatenate([arr, arr, arr], axis=2)
            return Image.fromarray(arr).convert("RGB")

        # PIL.Image 处理
        if isinstance(image, Image.Image):
            return image.convert("RGB")

        raise TypeError(f"Unsupported image type: {type(image)}")
    
    @classmethod
    def _pil_to_tensor_channel_last(self, pil_img):
        """
        将 PIL.Image 转换为 torch.Tensor (1, H, W, 3)，float32，值域 [0,1]。
        """
        arr = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0  # H,W,3
        tensor = torch.from_numpy(arr).unsqueeze(0)  # 1,H,W,3
        return tensor

