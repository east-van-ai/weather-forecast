# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import os

from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch


class WeatherVision:
    """
    Image-to-text forecaster optimized for M1/M2 Mac (MPS backend).
    """

    DEFAULT_MODEL_NAME = "llava-hf/llava-interleave-qwen-0.5b-hf"

    def __init__(self, model_name: str = None):
        # Resolve model: explicit arg > env var > default
        self.model_name = (
            model_name or os.getenv("WF_VISION_MODEL") or self.DEFAULT_MODEL_NAME
        )

        # Detect MPS
        if torch.backends.mps.is_available():
            # Using MPS backend (Apple Silicon).
            self.device = torch.device("mps")
        else:
            # MPS not available — using CPU.
            self.device = torch.device("cpu")

        # Load model + processor
        self.processor = AutoProcessor.from_pretrained(self.model_name, use_fast=True)
        self.model = AutoModelForImageTextToText.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

    def generate_forecast(
        self, file_path: str, prompt: str, max_tokens: int = 150
    ) -> str:
        """
        Generates weather analysis or description from a PNG.

        Args:
            file_path (str): Path to the PNG image file.
            prompt (str): Text prompt to guide the generation.
            max_tokens (int): Maximum number of tokens to generate.
        Returns:
            str: Generated text forecast.
        """

        # Load image
        img = Image.open(file_path).convert("RGB")

        # Prepare inputs
        inputs = self.processor(text=prompt, images=img, return_tensors="pt")

        # Move tensors to MPS/CPU
        for k in inputs:
            if isinstance(inputs[k], torch.Tensor):
                inputs[k] = inputs[k].to(self.device)

        # Generate
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                pad_token_id=self.processor.tokenizer.eos_token_id,
                max_new_tokens=max_tokens,
            )

        # Decode result
        text = self.processor.decode(out[0], skip_special_tokens=True)
        return text
