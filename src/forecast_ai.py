from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch


class WeatherVision:
    """
    Image-to-text forecaster optimized for M1/M2 Mac (MPS backend).
    """

    MODEL_NAME = "llava-hf/llava-interleave-qwen-0.5b-hf"

    def __init__(self):
        print("Loading WeatherVision model...")

        # Detect MPS
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            print("Using MPS backend (Apple Silicon).")
        else:
            self.device = torch.device("cpu")
            print("⚠️ MPS not available — using CPU.")

        # Load model + processor
        self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME, use_fast=True)
        self.model = AutoModelForImageTextToText.from_pretrained(self.MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()

    def generate_forecast(
        self, file_path: str, prompt: str, max_tokens: int = 150
    ) -> str:
        """
        Generates weather analysis or description from a PNG.
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
            out = self.model.generate(**inputs, max_new_tokens=max_tokens)

        # Decode result
        text = self.processor.decode(out[0], skip_special_tokens=True)
        return text
