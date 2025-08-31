"""
Plant Speech Generator Service
식물의 말 생성 (자연어 생성)
"""

import random
from typing import List, Dict, Any, Optional
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


class PlantSpeechGenerator:
    """식물의 말 생성기"""
    
    def __init__(self, language: str = "ko"):
        """
        초기화
        
        Args:
            language: 언어 (ko: 한국어, en: 영어)
        """
        self.language = language
        self.templates = self._load_templates()
        self.care_guides = self._load_care_guides()
    
    def _load_templates(self) -> Dict[str, str]:
        """템플릿 로드"""
        if self.language == "ko":
            return {
                "healthy": """
안녕하세요 주인님! 저는 {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}이에요.

{% if confidence >= 0.8 %}
저는 현재 건강한 상태예요! 잎도 선명하고 줄기도 튼튼해 보이죠?
{% elif confidence >= 0.6 %}
전반적으로 건강한 편이에요. 조금 더 관심을 주시면 더 좋아질 것 같아요.
{% else %}
음... 조금 불안한 상태일 수도 있어요. 주인님이 더 자세히 봐주시면 좋겠어요.
{% endif %}

{{ care_guide }}
""",
                "diseased": """
안녕하세요 주인님... 저는 {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}인데요.

{% if disease_confidence >= 0.8 %}
아파요... {{ disease_name }}에 걸린 것 같아요. {% if severity == "high" %}상태가 심각해요.{% elif severity == "medium" %}중간 정도의 상태예요.{% else %}초기 단계인 것 같아요.{% endif %}
{% elif disease_confidence >= 0.6 %}
{{ disease_name }} 증상이 보여요. 빨리 치료해주시면 좋겠어요.
{% else %}
{{ disease_name }}일 가능성이 있어요. 주의해서 지켜봐주세요.
{% endif %}

{{ care_guide }}
""",
                "uncertain": """
안녕하세요 주인님! 저는 {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}이에요.

사진이 조금 흐리거나 제가 잘 보이지 않아서 정확한 상태를 알기 어려워요.
더 선명한 사진을 찍어주시거나, 다른 각도에서도 찍어주시면 더 정확하게 진단할 수 있을 것 같아요.

{{ care_guide }}
"""
            }
        else:
            # 영어 템플릿
            return {
                "healthy": """
Hello! I'm {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}.

{% if confidence >= 0.8 %}
I'm in great health! My leaves are vibrant and my stem is strong.
{% elif confidence >= 0.6 %}
I'm generally healthy, but a little more care would make me even better.
{% else %}
I might be a bit under the weather. Could you take a closer look?
{% endif %}

{{ care_guide }}
""",
                "diseased": """
Hello... I'm {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}.

{% if disease_confidence >= 0.8 %}
I'm not feeling well... I think I have {{ disease_name }}. {% if severity == "high" %}It's quite serious.{% elif severity == "medium" %}It's moderate.{% else %}It seems to be in early stages.{% endif %}
{% elif disease_confidence >= 0.6 %}
I'm showing symptoms of {{ disease_name }}. Please treat me soon.
{% else %}
I might have {{ disease_name }}. Please keep an eye on me.
{% endif %}

{{ care_guide }}
""",
                "uncertain": """
Hello! I'm {{ species_name }}{% if scientific_name %} ({{ scientific_name }}){% endif %}.

The photo is a bit blurry or I'm not clearly visible, so it's hard to tell my exact condition.
If you could take a clearer photo or shoot from different angles, I could give you a more accurate diagnosis.

{{ care_guide }}
"""
            }
    
    def _load_care_guides(self) -> Dict[str, str]:
        """케어 가이드 로드"""
        if self.language == "ko":
            return {
                "토마토": "저는 햇빛을 좋아해요. 하루에 6-8시간 정도 햇빛을 받고, 물은 흙이 마를 때마다 충분히 주세요. 온도는 20-25도가 좋아요.",
                "고추": "저는 따뜻한 곳을 좋아해요. 햇빛이 충분하고, 물은 적당히 주세요. 너무 많이 주면 뿌리가 썩을 수 있어요.",
                "상추": "저는 시원한 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 잎이 시들면 물이 부족한 거예요.",
                "양파": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "마늘": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "당근": "저는 햇빛을 좋아하고 흙이 부드러워야 해요. 물은 적당히 주세요. 뿌리가 자라니까 흙이 단단하면 안 돼요.",
                "감자": "저는 햇빛을 좋아하고 흙이 부드러워야 해요. 물은 적당히 주세요. 뿌리가 자라니까 흙이 단단하면 안 돼요.",
                "고구마": "저는 햇빛을 좋아하고 흙이 부드러워야 해요. 물은 적당히 주세요. 뿌리가 자라니까 흙이 단단하면 안 돼요.",
                "배추": "저는 시원한 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 잎이 시들면 물이 부족한 거예요.",
                "무": "저는 햇빛을 좋아하고 흙이 부드러워야 해요. 물은 적당히 주세요. 뿌리가 자라니까 흙이 단단하면 안 돼요.",
                "오이": "저는 따뜻한 곳을 좋아해요. 햇빛이 충분하고, 물은 많이 주세요. 잎이 시들면 물이 부족한 거예요.",
                "호박": "저는 따뜻한 곳을 좋아해요. 햇빛이 충분하고, 물은 적당히 주세요. 너무 많이 주면 뿌리가 썩을 수 있어요.",
                "가지": "저는 따뜻한 곳을 좋아해요. 햇빛이 충분하고, 물은 적당히 주세요. 너무 많이 주면 뿌리가 썩을 수 있어요.",
                "피망": "저는 따뜻한 곳을 좋아해요. 햇빛이 충분하고, 물은 적당히 주세요. 너무 많이 주면 뿌리가 썩을 수 있어요.",
                "브로콜리": "저는 시원한 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 잎이 시들면 물이 부족한 거예요.",
                "양배추": "저는 시원한 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 잎이 시들면 물이 부족한 거예요.",
                "시금치": "저는 시원한 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 잎이 시들면 물이 부족한 거예요.",
                "부추": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "파": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "생강": "저는 그늘진 곳을 좋아해요. 햇빛은 적당히, 물은 자주 조금씩 주세요. 흙이 너무 젖으면 안 돼요.",
                "우엉": "저는 햇빛을 좋아하고 흙이 부드러워야 해요. 물은 적당히 주세요. 뿌리가 자라니까 흙이 단단하면 안 돼요.",
                "연근": "저는 물을 좋아해요. 흙이 항상 젖어있어야 해요. 햇빛은 적당히 주세요.",
                "미나리": "저는 물을 좋아해요. 흙이 항상 젖어있어야 해요. 햇빛은 적당히 주세요.",
                "깻잎": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "바질": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 따뜻한 곳에서 잘 자라요.",
                "로즈마리": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 따뜻한 곳에서 잘 자라요.",
                "라벤더": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 따뜻한 곳에서 잘 자라요.",
                "민트": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 서늘한 곳에서 잘 자라요.",
                "레몬그라스": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 따뜻한 곳에서 잘 자라요.",
                "타임": "저는 햇빛을 좋아하고 물은 적당히 주세요. 흙이 너무 젖으면 안 돼요. 따뜻한 곳에서 잘 자라요.",
                "default": "저는 햇빛과 물이 적당히 필요해요. 너무 많이 주거나 적게 주면 안 돼요. 주인님이 잘 챙겨주시면 건강하게 자랄 거예요!"
            }
        else:
            # 영어 케어 가이드
            return {
                "default": "I need moderate sunlight and water. Don't give me too much or too little. With your care, I'll grow healthy!"
            }
    
    def _get_scientific_name(self, species_name: str) -> Optional[str]:
        """학명 반환"""
        scientific_names = {
            "토마토": "Solanum lycopersicum",
            "고추": "Capsicum annuum",
            "상추": "Lactuca sativa",
            "양파": "Allium cepa",
            "마늘": "Allium sativum",
            "당근": "Daucus carota",
            "감자": "Solanum tuberosum",
            "고구마": "Ipomoea batatas",
            "배추": "Brassica rapa subsp. pekinensis",
            "무": "Raphanus sativus",
            "오이": "Cucumis sativus",
            "호박": "Cucurbita pepo",
            "가지": "Solanum melongena",
            "피망": "Capsicum annuum",
            "브로콜리": "Brassica oleracea var. italica",
            "양배추": "Brassica oleracea var. capitata",
            "시금치": "Spinacia oleracea",
            "부추": "Allium tuberosum",
            "파": "Allium fistulosum",
            "생강": "Zingiber officinale",
            "우엉": "Arctium lappa",
            "연근": "Nelumbo nucifera",
            "미나리": "Oenanthe javanica",
            "깻잎": "Perilla frutescens",
            "바질": "Ocimum basilicum",
            "로즈마리": "Rosmarinus officinalis",
            "라벤더": "Lavandula",
            "민트": "Mentha",
            "레몬그라스": "Cymbopogon citratus",
            "타임": "Thymus vulgaris"
        }
        return scientific_names.get(species_name)
    
    def _get_disease_severity(self, disease_name: str, confidence: float) -> str:
        """질병 심각도 판단"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def generate_speech(
        self,
        species_results: List[Dict[str, Any]],
        disease_results: List[Dict[str, Any]],
        confidence_threshold: float = 0.5
    ) -> str:
        """
        식물의 말 생성
        
        Args:
            species_results: 품종 분류 결과
            disease_results: 질병 분류 결과
            confidence_threshold: 신뢰도 임계값
            
        Returns:
            생성된 식물의 말
        """
        try:
            # 기본값 설정
            species_name = "알 수 없는 식물"
            species_confidence = 0.0
            disease_name = "건강"
            disease_confidence = 0.0
            
            # 품종 정보 추출
            if species_results:
                top_species = species_results[0]
                species_name = top_species.get("class", "알 수 없는 식물")
                species_confidence = top_species.get("confidence", 0.0)
            
            # 질병 정보 추출
            if disease_results:
                top_disease = disease_results[0]
                disease_name = top_disease.get("class", "건강")
                disease_confidence = top_disease.get("confidence", 0.0)
            
            # 템플릿 선택
            if disease_name == "건강" or disease_confidence < confidence_threshold:
                template_key = "healthy"
                confidence = species_confidence
            elif species_confidence < confidence_threshold:
                template_key = "uncertain"
                confidence = 0.0
            else:
                template_key = "diseased"
                confidence = species_confidence
            
            # 템플릿 렌더링
            template = Template(self.templates[template_key])
            
            # 케어 가이드 선택
            care_guide = self.care_guides.get(species_name, self.care_guides["default"])
            
            # 학명 가져오기
            scientific_name = self._get_scientific_name(species_name)
            
            # 질병 심각도
            severity = self._get_disease_severity(disease_name, disease_confidence)
            
            # 템플릿 렌더링
            speech = template.render(
                species_name=species_name,
                scientific_name=scientific_name,
                disease_name=disease_name,
                confidence=confidence,
                disease_confidence=disease_confidence,
                severity=severity,
                care_guide=care_guide
            )
            
            return speech.strip()
            
        except Exception as e:
            logger.error(f"식물의 말 생성 실패: {str(e)}")
            return "안녕하세요! 사진을 분석하는 중에 문제가 생겼어요. 다시 시도해주세요."
    
    def get_speech_info(self) -> Dict[str, Any]:
        """생성기 정보 반환"""
        return {
            "language": self.language,
            "available_species": list(self.care_guides.keys()),
            "template_types": list(self.templates.keys()),
            "generation_method": "Jinja2 template-based"
        }
