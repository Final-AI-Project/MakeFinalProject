// 급수 예측 관련 타입 정의

export interface WateringPredictionRequest {
  plant_idx: number;
  current_humidity: number;
  temperature: number;
  hour_of_day: number;
}

export interface WateringPredictionResponse {
  success: boolean;
  plant_idx: number;
  current_humidity: number;
  predicted_hours: number;
  next_watering_date: string;
  message: string;
}

export interface WateringPredictionBoxProps {
  plantIdx: number;
  currentHumidity: number;
  temperature?: number;
  onPredictionUpdate?: (prediction: WateringPredictionResponse) => void;
}
