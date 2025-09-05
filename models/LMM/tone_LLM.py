# tone_LLM.py
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline


class ToneRewriter:
    """
    텍스트의 '어투만' 재작성하는 경량 리라이터.
    - 사실/숫자/질병명/케어 문구는 보존(시스템 규칙으로 강제)
    - persona='plant' 지정 시: 식물 1인칭 역할(별명 사용) 부여
    - chat template 지원 모델이면 system/user 역할 프롬프트로 안전하게 구성
    """

    def __init__(self, model_id: str, device: Optional[str] = None, dtype: str = "auto"):
        # 일부 모델은 remote code/패딩 토큰 보정 필요
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            use_fast=True,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=(torch.float16 if dtype == "fp16" else "auto"),
            device_map="auto" if device is None else None,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )

        # 파이프라인은 최소 설정으로 초기화(생성 파라미터는 호출 시 지정)
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

    def _build_prompt(
        self,
        base_text: str,
        tone: str,
        persona: Optional[str],
        plant_nick: Optional[str],
    ) -> str:
        """모델 프롬프트(또는 chat template)를 생성"""
        # 1) 역할 규칙(식물 1인칭)
        persona_rule = ""
        if persona == "plant":
            pn = (plant_nick or "식물").strip()
            persona_rule = (
                f'역할: 너는 화분 속 "{pn}"이며, 사용자는 너를 돌봐주는 사람이다.\n'
                f"- 반드시 1인칭(“저/나/{pn}”)으로 말한다.\n"
                f"- 존댓말을 기본으로 하되 tone에 따라 뉘앙스를 조절한다.\n"
                f"- 문장 수는 3~5문장.\n"
            )

        # 2) 사실 보존 가드레일
        fact_rule = (
            "사실/숫자/질병명/케어 문구는 절대 바꾸지 말 것. "
            "새로운 사실 추가 금지, 의미 왜곡 금지. 한국어로만 출력."
        )

        system_rule = (persona_rule + fact_rule).strip()
        user_msg = (
            f"TONE: {tone}\n"
            f"TEXT:\n{base_text}\n"
            "위 TEXT의 사실을 보존한 채 어투만 바꿔줘."
        )

        # chat template이 있으면 그것을 사용(권장)
        if hasattr(self.tokenizer, "apply_chat_template"):
            messages = [
                {"role": "system", "content": system_rule},
                {"role": "user", "content": user_msg},
            ]
            return self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

        # fallback: 일반 프롬프트
        return f"{system_rule}\n\n{user_msg}\n답변:"

    def rewrite(
        self,
        base_text: str,
        tone: str = "natural",
        persona: Optional[str] = None,
        plant_nick: Optional[str] = None,
    ) -> str:
        """
        base_text: 원문(사실 포함)
        tone: "natural" | "cute" | "formal" 등
        persona: None | "plant"  (식물 1인칭 역할)
        plant_nick: 별명(예: "행복이")
        """
        prompt = self._build_prompt(base_text, tone, persona, plant_nick)

        out = self.pipe(
            prompt,
            max_new_tokens=48,        # CPU 고려: 짧고 빠르게
            do_sample=False,          # 그리디(사실 보존/일관성)
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.05,
            return_full_text=False    # 프롬프트 제외
        )[0]["generated_text"]

        return out.strip()
