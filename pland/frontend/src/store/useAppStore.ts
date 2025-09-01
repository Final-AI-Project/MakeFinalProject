import { create } from "zustand";
import { devtools } from "zustand/middleware";

// 타입 정의
export interface PredictionResult {
  species_topk: Array<{
    class: string;
    confidence: number;
    rank: number;
  }>;
  disease_topk: Array<{
    class: string;
    confidence: number;
    rank: number;
  }>;
  confidence: {
    species: number;
    disease: number;
  };
  talk: string;
  debug: {
    file_id: string;
    original_filename: string;
    processed_image_size: number[] | null;
    mask_path: string | null;
    crop_info: Record<string, any>;
    inference_time: string;
  };
}

export interface TrainingStatus {
  is_training: boolean;
  progress: number;
  current_epoch: number;
  total_epochs: number;
  current_loss: number;
  current_accuracy: number;
  start_time: string | null;
  end_time: string | null;
  error: string | null;
}

export interface ModelInfo {
  name: string;
  path: string;
  size_mb: number;
  created_at: string;
  model_type: string;
  is_active: boolean;
}

export interface AppState {
  // UI 상태
  isLoading: boolean;
  error: string | null;

  // 이미지 업로드
  selectedFile: File | null;
  previewUrl: string | null;

  // 추론 결과
  predictionResult: PredictionResult | null;
  predictionHistory: PredictionResult[];

  // 학습 상태
  trainingStatus: TrainingStatus | null;

  // 모델 관리
  models: ModelInfo[];
  activeModel: string | null;

  // 설정
  useOnnx: boolean;
  confidenceThreshold: number;
}

export interface AppActions {
  // UI 액션
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;

  // 파일 액션
  setSelectedFile: (file: File | null) => void;
  setPreviewUrl: (url: string | null) => void;
  clearFile: () => void;

  // 추론 액션
  setPredictionResult: (result: PredictionResult | null) => void;
  addToHistory: (result: PredictionResult) => void;
  clearHistory: () => void;

  // 학습 액션
  setTrainingStatus: (status: TrainingStatus | null) => void;

  // 모델 액션
  setModels: (models: ModelInfo[]) => void;
  setActiveModel: (modelName: string | null) => void;

  // 설정 액션
  setUseOnnx: (useOnnx: boolean) => void;
  setConfidenceThreshold: (threshold: number) => void;

  // 전체 초기화
  reset: () => void;
}

export type AppStore = AppState & AppActions;

// 초기 상태
const initialState: AppState = {
  isLoading: false,
  error: null,
  selectedFile: null,
  previewUrl: null,
  predictionResult: null,
  predictionHistory: [],
  trainingStatus: null,
  models: [],
  activeModel: null,
  useOnnx: false,
  confidenceThreshold: 0.5,
};

// 스토어 생성
export const useAppStore = create<AppStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // UI 액션
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),

      // 파일 액션
      setSelectedFile: (file) => set({ selectedFile: file }),
      setPreviewUrl: (url) => set({ previewUrl: url }),
      clearFile: () => set({ selectedFile: null, previewUrl: null }),

      // 추론 액션
      setPredictionResult: (result) => set({ predictionResult: result }),
      addToHistory: (result) => {
        const { predictionHistory } = get();
        const newHistory = [result, ...predictionHistory.slice(0, 9)]; // 최대 10개 유지
        set({ predictionHistory: newHistory });
      },
      clearHistory: () => set({ predictionHistory: [] }),

      // 학습 액션
      setTrainingStatus: (status) => set({ trainingStatus: status }),

      // 모델 액션
      setModels: (models) => set({ models }),
      setActiveModel: (modelName) => set({ activeModel: modelName }),

      // 설정 액션
      setUseOnnx: (useOnnx) => set({ useOnnx }),
      setConfidenceThreshold: (threshold) =>
        set({ confidenceThreshold: threshold }),

      // 전체 초기화
      reset: () => set(initialState),
    }),
    {
      name: "plant-whisperer-store",
    }
  )
);
