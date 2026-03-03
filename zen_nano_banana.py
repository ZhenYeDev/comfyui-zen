from nodes import IO  # (ComfyUI 运行时可能未使用)
import traceback
from io import BytesIO
from PIL import Image
import numpy as np
import torch

# preferred official package namespace
from google import genai
from google.genai.types import GenerateContentConfig, Modality, Part


class GeminiImageEditNode:
    """
    ComfyUI 节点：将输入图像（可选参考图像）和提示发送给
    Google Gemini 图像生成/编辑模型，并返回结果图像。

    - 必需输入：image, prompt
    - 可选输入：reference_image_1..4（最多 4 张参考图像）
    - 默认模型：'gemini-3.1-flash-image-preview'（支持图像响应）
    - 返回：torch.Tensor，形状 (1, H, W, 3)，float32，值域 [0,1]
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"default": "Edit the image as requested."}),
                "model_name": ("STRING", {"default": "gemini-3.1-flash-image-preview"}),
                "api_key": ("STRING", {"default": "AIzaSyBcC0MeDdf0BI32N1BsDZ9nUn0xuew6Dho"}),
            },
            "optional": {
                "reference_image_1": ("IMAGE", {"forceInput": False}),
                "reference_image_2": ("IMAGE", {"forceInput": False}),
                "reference_image_3": ("IMAGE", {"forceInput": False}),
                "reference_image_4": ("IMAGE", {"forceInput": False}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "generate"
    CATEGORY = "Google Gemini"

    def __init__(self):
        pass

    # -----------------------
    # Utility converters
    # -----------------------
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

    def _pil_to_tensor_channel_last(self, pil_img):
        """
        将 PIL.Image 转换为 torch.Tensor (1, H, W, 3)，float32，值域 [0,1]。
        """
        arr = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0  # H,W,3
        tensor = torch.from_numpy(arr).unsqueeze(0)  # 1,H,W,3
        return tensor

    # -----------------------
    # Core
    # -----------------------
    def generate(
        self,
        image,
        prompt,
        model_name="gemini-3.1-flash-image-preview",
        api_key="",
        reference_image_1=None,
        reference_image_2=None,
        reference_image_3=None,
        reference_image_4=None,
    ):
        """
        使用 Gemini 模型对主图与可选参考图进行编辑/生成请求，返回最终图像。
        """
        if genai is None:
            raise RuntimeError(
                "google-genai (or google.genai) library not found. Install with: pip install google-genai"
            )

        # 1) 必需输入图像 -> 转为 PIL
        try:
            pil_image = self._to_pil(image)
        except Exception as e:
            raise RuntimeError(f"Failed to convert input image to PIL: {e}")

        # 2) PIL -> PNG 字节
        try:
            buf = BytesIO()
            pil_image.save(buf, format="PNG")
            image_bytes = buf.getvalue()
        except Exception as e:
            raise RuntimeError(f"Failed to serialize PIL image to bytes: {e}")

        # 3) 创建客户端（当 api_key 为空时使用环境变量 GOOGLE_API_KEY）
        try:
            client = genai.Client(api_key=api_key) if api_key else genai.Client()
        except Exception as e:
            raise RuntimeError(f"Failed to create genai.Client: {e}")

        # 4) 主图像 Part
        try:
            base_part = Part.from_bytes(data=image_bytes, mime_type="image/png")
        except Exception as e:
            tb = traceback.format_exc()
            raise RuntimeError(
                f"Failed to create image Part for request. Ensure SDK exposes Part.from_bytes.\n{e}\n{tb}"
            )

        # 5) 可选参考图像 -> 转为 Part 列表
        ref_images = [
            reference_image_1,
            reference_image_2,
            reference_image_3,
            reference_image_4,
        ]
        ref_parts = []
        for idx, ref in enumerate(ref_images, start=1):
            if ref is None:
                continue
            try:
                pil_ref = self._to_pil(ref)
                rbuf = BytesIO()
                pil_ref.save(rbuf, format="PNG")
                ref_parts.append(
                    Part.from_bytes(data=rbuf.getvalue(), mime_type="image/png")
                )
            except Exception as e:
                raise RuntimeError(f"Failed to process reference_image_{idx}: {e}")

        # 6) 构建请求内容: [prompt, base image, reference1..4]
        contents = [prompt, base_part] + ref_parts

        # 7) 调用模型（请求图像响应）
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=GenerateContentConfig(response_modalities=[Modality.IMAGE]),
            )
        except Exception as e:
            tb = traceback.format_exc()
            raise RuntimeError(f"Model request failed: {e}\n{tb}")

        # 8) 从响应中提取图像字节（查找第一个 inline_data）
        img_bytes = None
        try:
            if getattr(response, "candidates", None):
                if response.candidates:
                    for cand in response.candidates:
                        content = getattr(cand, "content", None)
                        if not content:
                            continue
                        parts = getattr(content, "parts", None) or []
                        for part in parts:
                            inline = getattr(part, "inline_data", None)
                            if inline is not None and getattr(inline, "data", None):
                                data_field = inline.data
                                if isinstance(data_field, (bytes, bytearray)):
                                    img_bytes = bytes(data_field)
                                else:
                                    # 在某些运行时 data 可能是 memoryview 或可迭代对象
                                    img_bytes = bytes(list(data_field))
                                break
                        if img_bytes:
                            break
        except Exception:
            img_bytes = None

        # 9) 如果没有返回图像，则尝试提取文本片段并报错
        if img_bytes is None:
            text_preview = None
            try:
                textual_parts = []
                if getattr(response, "candidates", None):
                    if response.candidates:
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

        # 10) 字节 -> PIL -> 张量(1,H,W,3)
        try:
            out_pil = Image.open(BytesIO(img_bytes)).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to open returned image bytes: {e}")

        out_tensor = self._pil_to_tensor_channel_last(out_pil)
        return (out_tensor,)
