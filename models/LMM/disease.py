from typing import Dict, List

# === 공통 병해충/장해: 여러 실내식물에 빈발 ===
COMMON_DISEASE_TIPS_KO: Dict[str, Dict[str, List[str]]] = {
    "spider_mite": {  # 두점박이응애 등
        "desc": [
            "고온·저습 및 통풍 불량 환경에서 개체 수가 급증",
            "잎 뒷면의 연조직을 흡즙하여 피해 확대",
        ],
        "care": [
            "감염 개체 격리 후 잎 뒷면 중심으로 미지근한 물 샤워로 물리적 제거",
            "살충비누/유상제(라벨 준수) 7일 간격 2~3회, 재발 시 반복",
            "실내 습도·통풍 개선, 과밀 배치를 피함",
        ],
    },
    "scale_insect": {  # 깍지벌레
        "desc": [
            "저광·통풍불량에서 고착성 흡즙, 꿀액 분비로 2차 그을음병 유발",
        ],
        "care": [
            "면봉+알코올로 문질러 제거, 심하면 잎·가지 절단 폐기",
            "유상 살충제 도포/살포(표기 작물·용법 준수)",
            "꿀액 제거를 위한 잎 세척 → 그을음병 2차 발생 차단",
        ],
    },
    "mealybug": {  # 밀깍지벌레
        "desc": [
            "잎 겨드랑이·새순 부위에 정착, 당분 분비로 그을음 유발",
        ],
        "care": [
            "알코올 적신 면봉·분무로 군체 분리 후 제거",
            "살충비누/유상제 반복 처리, 새로 유입된 개체 모니터링",
        ],
    },
    "aphid": {  # 진딧물
        "desc": [
            "연한 새순·꽃대에서 급속 증식, 꿀액 분비로 그을음 유발",
        ],
        "care": [
            "물리적 세척으로 대량 탈락 유도",
            "살충비누/유상제 적용, 외부 반입 식물 검역",
        ],
    },
    "thrips": {  # 총채벌레
        "desc": [
            "건조·고온·저광 환경에서 개체 수 증가, 꽃·새순 변색·은백화",
        ],
        "care": [
            "노랑 끈끈이트랩 배치, 개화부 제거로 산란처 감소",
            "스피노사드 등 등록 약제(실내·관엽 라벨 준수) 교호 살포",
        ],
    },
    "fungus_gnat": {  # 버섯파리/뿌리파리
        "desc": [
            "과습한 배지·유기물 축적에서 유충이 뿌리 표면을 가해",
        ],
        "care": [
            "관수 간 건조 기간 확보, 상층 배지 마름 유지",
            "끈끈이트랩·BTi 제제(라벨 준수)로 유충/성충 동시 관리",
        ],
    },
    "sooty_mold": {  # 그을음병(2차)
        "desc": [
            "진딧물·깍지·밀깍지 등의 꿀액 위에 그을음균이 착생",
        ],
        "care": [
            "원인 흡즙 해충 선제 방제",
            "미온수+약한 세제 용액으로 잎 표면 세척, 통풍·채광 개선",
        ],
    },
    "powdery_mildew": {  # 흰가루병
        "desc": [
            "통풍 불량·과밀 식재·일교차 큰 환경에서 분생포자 증식",
            "잎 표면이 건조하나 주변 상대습도가 높은 조건에서 발병 유리",
        ],
        "care": [
            "감염 잎 즉시 제거·폐기, 상부 관수 지양",
            "황 제제/중탄산염 등 등록 약제 사용(실내 라벨 확인)",
            "식재 간격·환기·채광 개선",
        ],
    },
    "leaf_spot": {  # 잎반점(균/세균성 혼합 개념)
        "desc": [
            "물 튐·장시간 엽면 습윤·통풍 불량 시 병원체 감염 확률 증가",
        ],
        "care": [
            "반점 잎 제거·폐기, 도구 소독",
            "하부 관수/국소 관수로 엽면 습윤 최소화",
            "등록 살균제(구리제 등) 라벨 준수 적용",
        ],
    },
    "blight": {  # 잎마름/전반적 도장부 시들음
        "desc": [
            "고온다습·통풍불량에서 병원균 급확산 또는 뿌리 기능 저하",
        ],
        "care": [
            "감염 부위 제거, 환기·온습도 교정",
            "토양 포화 상태 해소, 필요 시 살균제 검토",
        ],
    },
    "root_rot": {  # 뿌리썩음(피시움/파이토프토라 등)
        "desc": [
            "배수 불량·과습·저온 과습에서 토양 병원균 활성·뿌리 산소 결핍",
        ],
        "care": [
            "즉시 분갈이(배수성 높은 배지), 썩은 조직 절제 후 건조·칼러스 형성",
            "관수 간 충분한 건조 간격, 과습 유발 받침물 물빼기",
            "필요 시 인산계/금속계 살균제 라벨 준수 관주",
        ],
    },
    "sunscald_leaf_scorch": {  # 일소/엽소
        "desc": [
            "갑작스런 강광·직사광 노출 또는 수분 스트레스",
        ],
        "care": [
            "점진적 순광(적응) 과정 부여, 밝은 간접광으로 전환",
            "관수 리듬 안정화, 고온 시간대 직사광 차단",
        ],
    },
    "edema": {  # 부종/수침斑(생리장해)
        "desc": [
            "야간 저온·과습·급격한 수분 흡수로 세포 파열",
        ],
        "care": [
            "급수 간격 늘리고 배수 개선, 야간 저온 관수 지양",
            "광량·통풍 개선으로 증산 균형 회복",
        ],
    },
    "bacterial_soft_rot": {  # 세균성 연부병(일반)
        "desc": [
            "상처·과습·고온에서 세균(Erwinia/Pectobacterium 등) 침입·조직 괴사",
        ],
        "care": [
            "감염부 즉시 절단·폐기, 도구·분 소독",
            "건조·통풍 강화, 상처부 건조 후 재식",
        ],
    },
    "botrytis_gray_mold": {  # 회색곰팡이
        "desc": [
            "저온·고습·통풍불량에서 꽃·연조직에 포자 형성",
        ],
        "care": [
            "감염 조직 제거, 개화부 과습·결로 방지",
            "보트리티스 등록 약제(라벨 준수) 교호 살포",
        ],
    },
}

# === 식물별(상대적으로 특정) 문제: 종·속 특이 성향 반영 ===
PLANT_SPECIFIC_DISEASE_TIPS_KO: Dict[str, Dict[str, List[str]]] = {
    # 몬스테라
    "monstera_bacterial_leaf_spot": {
        "desc": [
            "상처+물튐 환경에서 세균성 잎마름·반점(예: Xanthomonas) 감염",
        ],
        "care": [
            "반점 잎 절단·폐기, 상부 관수 지양, 도구 소독",
            "구리계 등 등록 세균성 방제제 라벨 준수 사용",
        ],
    },
    "monstera_edema": {
        "desc": [
            "대형엽에서 급격한 수분 흡수·저온 과습으로 엽저면 수침斑",
        ],
        "care": [
            "관수 주기 길게, 배지 통기성 상향(펄라이트·마사 혼합)",
            "광량·통풍 개선으로 증산 균형 회복",
        ],
    },

    # 스투키(산세베리아)
    "sansevieria_soft_rot": {
        "desc": [
            "저온 과습·상처를 통해 세균성 연부병이 잎저에서 상향 진행",
        ],
        "care": [
            "감염 잎 기부까지 과감히 절단, 절단면 건조·칼러스 후 재식",
            "저온기 급수 최소화, 배수성 높은 무기질 배지 사용",
        ],
    },
    "sansevieria_leaf_spot": {
        "desc": [
            "엽면 장시간 습윤 시 곰팡이성 반점 발생",
        ],
        "care": [
            "엽면 건조 유지, 감염 잎 제거·폐기",
            "필요 시 등록 살균제 국소 적용",
        ],
    },

    # 금전수(ZZ)
    "zamioculcas_tuber_rot": {
        "desc": [
            "괴경(뿌리줄기)이 과습·배수불량에서 세균/곰팡이성 부패",
        ],
        "care": [
            "분해체 밖으로 분리해 썩은 부위 절제, 황/계피 등 건조 후 재식",
            "물빠짐 우수 배지·깊은 받침물 물빼기·저빈도 관수",
        ],
    },

    # 선인장
    "cactus_stem_rot": {
        "desc": [
            "상처·과습·고온에서 줄기 수침성 부패가 급속 진행",
        ],
        "care": [
            "건강 조직 위에서 과감 절단, 절단면 건조·칼러스 후 삽목",
            "관수 대폭 축소, 통풍·광량 상향",
        ],
    },
    "cactus_sunburn": {
        "desc": [
            "음지 재배 개체를 갑작스레 강한 직사광·고온에 노출",
        ],
        "care": [
            "1~2주 단계적 순광, 차광막으로 광도 완만히 상승",
        ],
    },

    # 호접란(팔레놉시스)
    "orchid_crown_rot": {
        "desc": [
            "로제트 중심부(크라운)에 물 고임 → 세균·곰팡이성 부패",
        ],
        "care": [
            "즉시 수분 제거·흡수, 감염 조직 절단·소독",
            "상부 관수·분무 시 크라운 고임 방지, 통풍·저녁 관수 지양",
        ],
    },
    "orchid_bud_blast": {
        "desc": [
            "온도 급변·건조·이동 스트레스 → 꽃망울 낙과",
        ],
        "care": [
            "온·습도 안정(주간 23~27°C/야간 18~20°C, RH 50~70%)",
            "개화 중 위치·환경 유지, 냉풍·건조 바람 차단",
        ],
    },

    # 야자류 공통 특이(테이블야자·관음죽에 주로 보고)
    "palm_pink_rot": {
        "desc": [
            "고습·통풍불량에서 줄기·잎 기부의 분홍색 곰팡이성 부패(핑크롯)",
        ],
        "care": [
            "감염 조직 제거·폐기, 환기·채광 개선",
            "등록 살균제 교호 살포(라벨 준수), 상처·과습 방지",
        ],
    },

    # 홍콩야자(쉐플레라 계통으로 간주)
    "schefflera_anthracnose": {
        "desc": [
            "Colletotrichum 계열 탄저병이 저광·다습·물튐 환경에서 발생",
        ],
        "care": [
            "반점 잎 절단·폐기, 상부 관수 지양·통풍 개선",
            "구리계 등 등록 살균제 라벨 준수 살포",
        ],
    },

    # 스파티필럼
    "peace_lily_fungal_leaf_spot": {
        "desc": [
            "엽면 장시간 습윤·과밀 재배에서 곰팡이성 반점",
        ],
        "care": [
            "감염 잎 제거, 분주·정리로 과밀 완화",
            "국소 살균제 처리 및 하부 관수 전환",
        ],
    },

    # 벵갈고무나무(Ficus)
    "ficus_bacterial_leaf_spot": {
        "desc": [
            "물튐·상처 부위로 세균성 반점이 도입·확산",
        ],
        "care": [
            "감염 잎 제거, 상처 관리·도구 소독",
            "구리계 등 등록 세균성 방제제 적용",
        ],
    },

    # 올리브나무
    "olive_peacock_spot": {
        "desc": [
            "Spilocaea oleagina(공작병)가 저온다습·저광에서 발병(실내·베란다에서도 가능)",
        ],
        "care": [
            "채광·통풍 증대, 잎 젖음 시간 단축",
            "구리계 등록 약제 시즌성 예방 살포(라벨 준수)",
        ],
    },

    # 디펜바키아
    "dieffenbachia_bacterial_soft_rot": {
        "desc": [
            "고온 과습·상처에서 연부병(Erwinia/Pectobacterium) 급속 진행",
        ],
        "care": [
            "감염부 절단·폐기, 분·도구 소독, 관수·습도 낮추기",
            "심한 경우 폐기 후 재도입 권장",
        ],
    },

    # 보스턴고사리
    "fern_rhizoctonia_blight": {
        "desc": [
            "고온다습·환기부족에서 Rhizoctonia 잎마름성 병해",
        ],
        "care": [
            "관수·분무 조절로 엽면 건조 확보, 감염엽 제거",
            "등록 살균제 교호 살포 및 포트 밀집 완화",
        ],
    },
}

# 최종 조회용(공통 + 식물별 특정) 통합
DISEASE_TIPS_KO: Dict[str, Dict[str, List[str]]] = {
    **COMMON_DISEASE_TIPS_KO,
    **PLANT_SPECIFIC_DISEASE_TIPS_KO,
}

# === 식물 → {common, specific} 추천 키 인덱스 ===
PLANT_DISEASE_INDEX_KO: Dict[str, Dict[str, List[str]]] = {
    "몬스테라": {
        "common": ["spider_mite", "thrips", "scale_insect", "mealybug", "leaf_spot", "root_rot", "fungus_gnat", "sooty_mold"],
        "specific": ["monstera_bacterial_leaf_spot", "monstera_edema"],
    },
    "스투키": {
        "common": ["spider_mite", "scale_insect", "mealybug", "root_rot", "leaf_spot"],
        "specific": ["sansevieria_soft_rot", "sansevieria_leaf_spot"],
    },
    "금전수": {
        "common": ["scale_insect", "mealybug", "root_rot", "fungus_gnat", "sooty_mold"],
        "specific": ["zamioculcas_tuber_rot"],
    },
    "선인장": {
        "common": ["spider_mite", "mealybug", "scale_insect", "sunscald_leaf_scorch"],
        "specific": ["cactus_stem_rot", "cactus_sunburn"],
    },
    "호접란": {
        "common": ["scale_insect", "mealybug", "spider_mite", "botrytis_gray_mold", "bacterial_soft_rot"],
        "specific": ["orchid_crown_rot", "orchid_bud_blast"],
    },
    "테이블야자": {
        "common": ["spider_mite", "scale_insect", "thrips", "leaf_spot", "root_rot", "sooty_mold"],
        "specific": ["palm_pink_rot"],
    },
    "홍콩야자": {
        "common": ["scale_insect", "mealybug", "aphid", "leaf_spot", "sooty_mold", "spider_mite", "thrips"],
        "specific": ["schefflera_anthracnose"],
    },
    "스파티필럼": {
        "common": ["fungus_gnat", "root_rot", "leaf_spot", "scale_insect"],
        "specific": ["peace_lily_fungal_leaf_spot"],
    },
    "관음죽": {
        "common": ["scale_insect", "spider_mite", "leaf_spot", "root_rot", "sooty_mold", "thrips"],
        "specific": ["palm_pink_rot"],
    },
    "벵갈고무나무": {
        "common": ["scale_insect", "mealybug", "thrips", "leaf_spot", "sooty_mold", "edema"],
        "specific": ["ficus_bacterial_leaf_spot"],
    },
    "올리브나무": {
        "common": ["scale_insect", "aphid", "leaf_spot", "sooty_mold"],
        "specific": ["olive_peacock_spot"],
    },
    "디펜바키아": {
        "common": ["mealybug", "scale_insect", "root_rot", "leaf_spot"],
        "specific": ["dieffenbachia_bacterial_soft_rot"],
    },
    "보스턴고사리": {
        "common": ["spider_mite", "fungus_gnat", "leaf_spot"],
        "specific": ["fern_rhizoctonia_blight"],
    },
}

# 사용 예시:
# for key in (PLANT_DISEASE_INDEX_KO["몬스테라"]["common"] + PLANT_DISEASE_INDEX_KO["몬스테라"]["specific"]):
#     tips = DISEASE_TIPS_KO[key]
#     print(key, tips["desc"], tips["care"], sep="\n")
