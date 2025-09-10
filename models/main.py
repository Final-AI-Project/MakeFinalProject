# ------ 모듈 임포트
from multiprocessing import process
from fastapi import FastAPI
import dotenv
import os

# ------ FastAPI 앱

app = FastAPI()

# ------ CORS
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 필요 시 ["*"] 로 전체 허용 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- 모델 경로
LLM_MODEL_PATH = process.env.LLM_MODEL_PATH
SPECIES_MODEL_PATH = process.env.SPECIES_MODEL_PATH
HEALTH_MODEL_PATH = process.env.HEALTH_MODEL_PATH
DISEASE_MODEL_PATH = process.env.DISEASE_MODEL_PATH

# -------------------- 디바이스/데이터타입 결정 --------------------
USE_CUDA = torch.cuda.is_available()
USE_MPS = getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()

if USE_CUDA:
    device = "cuda"
    dtype = torch.float16
elif USE_MPS:
    device = "mps"
    dtype = torch.float16
else:
    device = "cpu"
    dtype = torch.float32  # ✅ CPU는 반드시 fp32 (half 미지원 연산 있음)

print(f"🔧 Device: {device}, dtype: {dtype}")

# -------------------- 모델 로딩 --------------------
print("🔧 Loading ControlNet...")
health_model = yolov8n-cls.from_pretrained(
    HEALTH_MODEL_PATH,
    torch_dtype=dtype,
)

print("🔧 Loading Base SD Pipeline...")
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    BASE_MODEL_PATH,
    controlnet=controlnet,
    torch_dtype=dtype,
)

# LoRA 적용
print("🔧 Applying LoRA...")
pipe.load_lora_weights(
    os.path.dirname(LORA_PATH),
    weight_name=os.path.basename(LORA_PATH)
)

# 디바이스로 이동
pipe.to(device)

# (안정성) 텍스트 인코더는 fp32 권장
try:
    pipe.text_encoder.to(dtype=torch.float32, device=device)
except Exception:
    # 일부 버전에서 .to(dtype=...) 미지원일 수 있음 → 무시
    pass

# 메모리 최적화
try:
    if device == "cuda":
        pipe.enable_xformers_memory_efficient_attention()
    else:
        pipe.enable_attention_slicing()
except Exception:
    pipe.enable_attention_slicing()
    
    
    # -------------------------- 품종 분류기 로직 및 API
    @app.post("/species")
    async def species(
        image: UploadFile = File(None),
        ): 
        upload = image
        result = health_model(upload)
        return json.dumps(result)
    
    
    # -------------------------- 잎 상태 분류기 로직 및 API
    @app.post("/health")
    
    # -------------------------- 질병 분류기 로직 및 API
    @app.post("/disease")
    
    # -------------------------- LLM 처리 로직 및 API
    @app.post("/llm")
    