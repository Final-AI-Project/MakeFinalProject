import React from "react";
import { Leaf, Heart, AlertTriangle, CheckCircle } from "lucide-react";
import { PredictionResult } from "../store/useAppStore";

interface ResultCardProps {
  result: PredictionResult;
}

export const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
  const topSpecies = result.species_topk[0];
  const topDisease = result.disease_topk[0];
  const isHealthy = topDisease.class === "건강";

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.8) return "매우 높음";
    if (confidence >= 0.6) return "높음";
    if (confidence >= 0.4) return "보통";
    return "낮음";
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* 식물의 말 */}
      <div className="card p-6 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <Leaf className="w-6 h-6 text-green-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              🌱 식물의 말
            </h3>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                {result.talk}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 분석 결과 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 품종 분석 */}
        <div className="card p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Leaf className="w-5 h-5 text-green-600" />
            <h3 className="text-lg font-semibold text-gray-900">품종 분석</h3>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{topSpecies.class}</p>
                <p className="text-sm text-gray-500">1순위 예측</p>
              </div>
              <div className="text-right">
                <p
                  className={`font-semibold ${getConfidenceColor(
                    topSpecies.confidence
                  )}`}
                >
                  {(topSpecies.confidence * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">
                  {getConfidenceText(topSpecies.confidence)}
                </p>
              </div>
            </div>

            {result.species_topk.slice(1, 3).map((species, index) => (
              <div
                key={species.class}
                className="flex items-center justify-between p-2"
              >
                <div>
                  <p className="text-sm text-gray-700">{species.class}</p>
                  <p className="text-xs text-gray-500">{index + 2}순위</p>
                </div>
                <p className="text-sm text-gray-600">
                  {(species.confidence * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* 질병 분석 */}
        <div className="card p-6">
          <div className="flex items-center space-x-2 mb-4">
            {isHealthy ? (
              <Heart className="w-5 h-5 text-green-600" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-red-600" />
            )}
            <h3 className="text-lg font-semibold text-gray-900">건강 상태</h3>
          </div>

          <div className="space-y-3">
            <div
              className={`flex items-center justify-between p-3 rounded-lg ${
                isHealthy ? "bg-green-50" : "bg-red-50"
              }`}
            >
              <div className="flex items-center space-x-2">
                {isHealthy ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                )}
                <div>
                  <p className="font-medium text-gray-900">
                    {topDisease.class}
                  </p>
                  <p className="text-sm text-gray-500">주요 진단</p>
                </div>
              </div>
              <div className="text-right">
                <p
                  className={`font-semibold ${getConfidenceColor(
                    topDisease.confidence
                  )}`}
                >
                  {(topDisease.confidence * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">
                  {getConfidenceText(topDisease.confidence)}
                </p>
              </div>
            </div>

            {result.disease_topk.slice(1, 3).map((disease, index) => (
              <div
                key={disease.class}
                className="flex items-center justify-between p-2"
              >
                <div>
                  <p className="text-sm text-gray-700">{disease.class}</p>
                  <p className="text-xs text-gray-500">{index + 2}순위</p>
                </div>
                <p className="text-sm text-gray-600">
                  {(disease.confidence * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 신뢰도 요약 */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          분석 신뢰도
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">품종 분류</span>
              <span className="font-medium">
                {(result.confidence.species * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${result.confidence.species * 100}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">질병 진단</span>
              <span className="font-medium">
                {(result.confidence.disease * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  isHealthy ? "bg-green-600" : "bg-red-600"
                }`}
                style={{ width: `${result.confidence.disease * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 디버그 정보 (개발 모드에서만 표시) */}
      {process.env.NODE_ENV === "development" && (
        <details className="card p-4">
          <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-900">
            디버그 정보
          </summary>
          <div className="mt-3 text-xs text-gray-500 space-y-1">
            <p>파일 ID: {result.debug.file_id}</p>
            <p>원본 파일명: {result.debug.original_filename}</p>
            <p>
              처리된 이미지 크기:{" "}
              {result.debug.processed_image_size?.join("x") || "N/A"}
            </p>
            <p>마스크 경로: {result.debug.mask_path || "N/A"}</p>
            <p>추론 시간: {result.debug.inference_time}</p>
          </div>
        </details>
      )}
    </div>
  );
};
