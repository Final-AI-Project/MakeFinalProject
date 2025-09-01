import React, { useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { ImageUploader } from "../components/ImageUploader";
import { ResultCard } from "../components/ResultCard";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";
import { Leaf, Settings, History, Brain, Heart } from "lucide-react";

export const Home: React.FC = () => {
  const {
    selectedFile,
    predictionResult,
    isLoading,
    error,
    setLoading,
    setError,
    setPredictionResult,
    addToHistory,
    useOnnx,
    confidenceThreshold,
    setUseOnnx,
    setConfidenceThreshold,
  } = useAppStore();

  // 추론 뮤테이션
  const predictMutation = useMutation({
    mutationFn: (file: File) =>
      api.predict.plant(file, useOnnx, confidenceThreshold),
    onMutate: () => {
      setLoading(true);
      setError(null);
    },
    onSuccess: (data) => {
      setPredictionResult(data);
      addToHistory(data);
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "분석 중 오류가 발생했습니다.";
      setError(errorMessage);
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  // 파일이 선택되면 자동으로 분석 시작
  useEffect(() => {
    if (selectedFile && !isLoading) {
      predictMutation.mutate(selectedFile);
    }
  }, [selectedFile]);

  const handleAnalyze = () => {
    if (selectedFile) {
      predictMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <Leaf className="w-8 h-8 text-green-600" />
              <h1 className="text-xl font-bold text-gray-900">
                Plant Whisperer
              </h1>
              <span className="text-sm text-gray-500">식물 스피킹 진단</span>
            </div>

            <div className="flex items-center space-x-4">
              <button
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="설정"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="히스토리"
              >
                <History className="w-5 h-5" />
              </button>
              <button
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="모델 정보"
              >
                <Brain className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* 제목 및 설명 */}
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold text-gray-900">
              식물과의 대화를 시작하세요
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              식물 사진을 업로드하면 품종을 추정하고 병충해를 분석하여
              <strong className="text-green-600">
                {" "}
                식물이 직접 말하는 것처럼
              </strong>{" "}
              결과를 전달합니다.
            </p>
          </div>

          {/* 설정 패널 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-w-2xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              분석 설정
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  추론 엔진
                </label>
                <select
                  value={useOnnx ? "onnx" : "pytorch"}
                  onChange={(e) => setUseOnnx(e.target.value === "onnx")}
                  className="input"
                >
                  <option value="pytorch">PyTorch (정확도 우선)</option>
                  <option value="onnx">ONNX Runtime (속도 우선)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  신뢰도 임계값
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.1"
                  value={confidenceThreshold}
                  onChange={(e) =>
                    setConfidenceThreshold(parseFloat(e.target.value))
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.1</span>
                  <span className="font-medium">{confidenceThreshold}</span>
                  <span>0.9</span>
                </div>
              </div>
            </div>
          </div>

          {/* 이미지 업로더 */}
          <ImageUploader />

          {/* 분석 버튼 */}
          {selectedFile && !isLoading && (
            <div className="text-center">
              <button
                onClick={handleAnalyze}
                disabled={!selectedFile || isLoading}
                className="btn btn-primary btn-lg"
              >
                <Brain className="w-5 h-5 mr-2" />
                분석 시작
              </button>
            </div>
          )}

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    분석 오류
                  </h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* 로딩 상태 */}
          {isLoading && (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
              </div>
              <p className="text-lg text-gray-600">
                식물을 분석하고 있습니다...
              </p>
              <p className="text-sm text-gray-500">잠시만 기다려주세요</p>
            </div>
          )}

          {/* 결과 */}
          {predictionResult && !isLoading && (
            <div className="animate-fade-in">
              <ResultCard result={predictionResult} />
            </div>
          )}

          {/* 하단 정보 */}
          <div className="text-center space-y-4 pt-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Leaf className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">품종 분류</h3>
                <p className="text-sm text-gray-600">
                  30가지 식물 품종 자동 분류
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Brain className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">질병 진단</h3>
                <p className="text-sm text-gray-600">
                  15가지 질병 유형 자동 진단
                </p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Heart className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  자연어 결과
                </h3>
                <p className="text-sm text-gray-600">
                  식물이 직접 말하는 듯한 결과
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-gray-500">
            <p>Plant Whisperer - 식물과의 대화를 시작하세요 🌱</p>
            <p className="mt-2">100% 무료 오픈소스 프로젝트</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
