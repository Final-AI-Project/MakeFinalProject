import axios from "axios";
import { z } from "zod";

// API 응답 스키마
export const PredictionResponseSchema = z.object({
  species_topk: z.array(
    z.object({
      class: z.string(),
      confidence: z.number(),
      rank: z.number(),
    })
  ),
  disease_topk: z.array(
    z.object({
      class: z.string(),
      confidence: z.number(),
      rank: z.number(),
    })
  ),
  confidence: z.object({
    species: z.number(),
    disease: z.number(),
  }),
  talk: z.string(),
  debug: z.object({
    file_id: z.string(),
    original_filename: z.string(),
    processed_image_size: z.array(z.number()).nullable(),
    mask_path: z.string().nullable(),
    crop_info: z.record(z.any()),
    inference_time: z.string(),
  }),
});

export const TrainingStatusSchema = z.object({
  is_training: z.boolean(),
  progress: z.number(),
  current_epoch: z.number(),
  total_epochs: z.number(),
  current_loss: z.number(),
  current_accuracy: z.number(),
  start_time: z.string().nullable(),
  end_time: z.string().nullable(),
  error: z.string().nullable(),
});

export const ModelInfoSchema = z.object({
  name: z.string(),
  path: z.string(),
  size_mb: z.number(),
  created_at: z.string(),
  model_type: z.string(),
  is_active: z.boolean(),
});

export const ModelsResponseSchema = z.object({
  models: z.array(ModelInfoSchema),
  active_model: z.string().nullable(),
  total_count: z.number(),
});

// API 클라이언트 생성
const apiClient = axios.create({
  baseURL: "/api",
  timeout: 120000, // 2분으로 증가
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API 요청: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("API 요청 오류:", error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API 응답: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error("API 응답 오류:", error);
    return Promise.reject(error);
  }
);

// API 함수들
export const api = {
  // 헬스체크
  health: {
    check: () => apiClient.get("/health"),
    detailed: () => apiClient.get("/health/detailed"),
  },

  // 추론
  predict: {
    plant: async (file: File, useOnnx = false, confidenceThreshold = 0.5) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("use_onnx", useOnnx.toString());
      formData.append("confidence_threshold", confidenceThreshold.toString());

      const response = await apiClient.post("/predict", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return PredictionResponseSchema.parse(response.data);
    },
  },

  // 학습
  train: {
    start: async (config: {
      dataset_source: string;
      epochs: number;
      batch_size: number;
      learning_rate: number;
      freeze_backbone: boolean;
      output_name: string;
      validation_split: number;
      random_seed: number;
    }) => {
      const response = await apiClient.post("/train", config);
      return response.data;
    },

    status: async () => {
      const response = await apiClient.get("/train/status");
      return TrainingStatusSchema.parse(response.data);
    },
  },

  // 모델 관리
  models: {
    list: async () => {
      const response = await apiClient.get("/models");
      return ModelsResponseSchema.parse(response.data);
    },

    select: async (modelName: string) => {
      const response = await apiClient.post("/models/select", {
        model_name: modelName,
      });
      return response.data;
    },

    delete: async (modelName: string) => {
      const response = await apiClient.delete(`/models/${modelName}`);
      return response.data;
    },

    info: async (modelName: string) => {
      const response = await apiClient.get(`/models/info/${modelName}`);
      return response.data;
    },
  },
};

export default apiClient;
