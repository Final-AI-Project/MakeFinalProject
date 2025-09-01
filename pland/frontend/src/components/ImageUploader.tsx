import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Image as ImageIcon, X } from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import { clsx } from "clsx";

export const ImageUploader: React.FC = () => {
  const {
    selectedFile,
    previewUrl,
    setSelectedFile,
    setPreviewUrl,
    clearFile,
    isLoading,
  } = useAppStore();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        setSelectedFile(file);

        // 미리보기 URL 생성
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      }
    },
    [setSelectedFile, setPreviewUrl]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpeg", ".jpg", ".png", ".webp"],
    },
    maxFiles: 1,
    disabled: isLoading,
  });

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    clearFile();
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={clsx(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            isDragActive
              ? "border-primary-400 bg-primary-50"
              : "border-gray-300 hover:border-primary-400 hover:bg-gray-50",
            isLoading && "opacity-50 cursor-not-allowed"
          )}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center space-y-4">
            <div
              className={clsx(
                "p-4 rounded-full",
                isDragActive ? "bg-primary-100" : "bg-gray-100"
              )}
            >
              {isDragActive ? (
                <Upload className="w-8 h-8 text-primary-600" />
              ) : (
                <ImageIcon className="w-8 h-8 text-gray-600" />
              )}
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? "여기에 놓으세요!" : "식물 사진을 업로드하세요"}
              </h3>
              <p className="text-sm text-gray-500">
                JPG, PNG, WebP 형식의 이미지를 드래그하거나 클릭하여 선택하세요
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative">
          <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-white shadow-sm">
            <img
              src={previewUrl!}
              alt="업로드된 이미지"
              className="w-full h-64 object-cover"
            />

            <button
              onClick={handleClear}
              disabled={isLoading}
              className="absolute top-2 right-2 p-2 bg-white rounded-full shadow-md hover:bg-gray-50 transition-colors disabled:opacity-50"
              title="이미지 제거"
            >
              <X className="w-4 h-4 text-gray-600" />
            </button>

            <div className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>

                {isLoading && (
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
                    <span>분석 중...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
