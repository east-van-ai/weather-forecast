from pathlib import Path

from transformers import AutoProcessor, AutoModelForImageTextToText
import torch


class WeatherVision:
    """
    Image-to-text describer optimized for M1/M2 Mac (MPS backend).

    The processor and the model load once per instantiation, onto MPS where
    Apple Silicon offers it and onto the CPU otherwise.
    """

    DEFAULT_MODEL_NAME = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.DEFAULT_MODEL_NAME

        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.processor = AutoProcessor.from_pretrained(self.model_name, use_fast=True)
        self.model = AutoModelForImageTextToText.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

    def generate_forecast(
        self, file_path: str | Path, prompt: str, max_tokens: int = 150
    ) -> str:
        """
        Describes a PNG in the model's own words.

        The model reads what is on the page. It does not analyze the chart,
        and any figure it volunteers is invented rather than measured, so the
        answer is a description and nothing more.

        The processor loads the image itself and decides how many image tokens
        the prompt needs, which depends on how it splits the image into crops.
        It rejects anything but a string, and the pipeline deals in Path, so
        the path is converted on the way in.

        The chat template puts the user turn inside the output sequence, so
        only the generated tail is decoded.

        Args:
            file_path (str | Path): Path to the PNG image file.
            prompt (str): Text prompt to guide the generation.
            max_tokens (int): Maximum number of tokens to generate.
        Returns:
            str: Generated description.
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "path": str(file_path)},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        prompt_length = inputs["input_ids"].shape[-1]

        for k in inputs:
            if isinstance(inputs[k], torch.Tensor):
                inputs[k] = inputs[k].to(self.device)

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                pad_token_id=self.processor.tokenizer.eos_token_id,
                max_new_tokens=max_tokens,
            )

        text = self.processor.decode(out[0][prompt_length:], skip_special_tokens=True)
        return text.strip()
