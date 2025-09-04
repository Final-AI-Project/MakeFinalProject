# tone_llm.py
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class ToneRewriter:
    def __init__(self, model_id: str, device: Optional[str] = None, dtype: str = "auto"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=(torch.float16 if dtype=="fp16" else "auto"),
            device_map="auto" if device is None else None
        )
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=120,
            do_sample=True,
            temperature=0.5,
            top_p=0.9,
            repetition_penalty=1.1,
        )

    def rewrite(self, base_text: str, tone: str = "natural") -> str:
        system_rule = (
            "You are a rewriting assistant. Keep all facts, numbers, disease names, and care tips unchanged. "
            "Do not add new facts. Only adjust tone and phrasing. Output 2–4 sentences in Korean."
        )
        # 필요 시 <FACT_*> 마커로 보호한 뒤 재조립하는 로직을 여기에 추가 가능
        prompt = (
            f"{system_rule}\n"
            f"TONE: {tone}\n"
            f"TEXT:\n{base_text}\n"
            f"Rewrite the TEXT in the specified tone while preserving all factual content exactly."
        )
        out = self.pipe(prompt)[0]["generated_text"]
        # 모델에 따라 프롬프트가 재포함될 수 있으니, 간단한 후처리:
        # 마지막 줄 이후만 취하는 등의 정규화 로직을 필요에 맞게 보강
        return out.split("TEXT:")[-1].strip() if "TEXT:" in out else out.strip()