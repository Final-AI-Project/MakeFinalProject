"""
ONNX Export Script
PyTorch 모델을 ONNX 형식으로 내보내기
"""

import os
import sys
import argparse
import torch
import torch.nn as nn
from torchvision import transforms
import onnx
import onnxruntime as ort
import numpy as np
from typing import Optional
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.classifier import PlantClassifier

logger = logging.getLogger(__name__)


def export_to_onnx(
    model_path: str,
    output_path: str,
    input_size: int = 224,
    batch_size: int = 1,
    device: str = "cpu"
) -> bool:
    """
    PyTorch 모델을 ONNX 형식으로 내보내기
    
    Args:
        model_path: PyTorch 모델 파일 경로
        output_path: ONNX 출력 파일 경로
        input_size: 입력 이미지 크기
        batch_size: 배치 크기
        device: 디바이스
        
    Returns:
        성공 여부
    """
    try:
        logger.info(f"ONNX 내보내기 시작: {model_path} -> {output_path}")
        
        # 모델 로드
        checkpoint = torch.load(model_path, map_location=device)
        
        # 모델 아키텍처 생성
        classifier = PlantClassifier()
        model = classifier._create_model_architecture()
        
        # 가중치 로드
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model.to(device)
        model.eval()
        
        # 더미 입력 생성
        dummy_input = torch.randn(batch_size, 3, input_size, input_size, device=device)
        
        # ONNX 내보내기
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        logger.info(f"ONNX 모델 내보내기 완료: {output_path}")
        
        # ONNX 모델 검증
        if validate_onnx_model(output_path, dummy_input, model):
            logger.info("ONNX 모델 검증 성공")
            return True
        else:
            logger.error("ONNX 모델 검증 실패")
            return False
            
    except Exception as e:
        logger.error(f"ONNX 내보내기 실패: {str(e)}")
        return False


def validate_onnx_model(
    onnx_path: str,
    dummy_input: torch.Tensor,
    pytorch_model: nn.Module
) -> bool:
    """
    ONNX 모델 검증
    
    Args:
        onnx_path: ONNX 모델 경로
        dummy_input: 테스트 입력
        pytorch_model: 원본 PyTorch 모델
        
    Returns:
        검증 성공 여부
    """
    try:
        # ONNX 모델 로드
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        
        # ONNX Runtime 세션 생성
        ort_session = ort.InferenceSession(onnx_path)
        
        # PyTorch 추론
        with torch.no_grad():
            pytorch_output = pytorch_model(dummy_input)
        
        # ONNX 추론
        ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.cpu().numpy()}
        ort_output = ort_session.run(None, ort_inputs)[0]
        
        # 출력 비교
        pytorch_output_np = pytorch_output.cpu().numpy()
        
        # 상대 오차 계산
        relative_error = np.abs(pytorch_output_np - ort_output) / (np.abs(pytorch_output_np) + 1e-8)
        max_relative_error = np.max(relative_error)
        
        logger.info(f"최대 상대 오차: {max_relative_error:.6f}")
        
        # 허용 오차 (1e-5)
        if max_relative_error < 1e-5:
            return True
        else:
            logger.warning(f"상대 오차가 너무 큽니다: {max_relative_error}")
            return False
            
    except Exception as e:
        logger.error(f"ONNX 모델 검증 실패: {str(e)}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="PyTorch 모델을 ONNX로 내보내기")
    parser.add_argument("--model_path", type=str, required=True, help="PyTorch 모델 파일 경로")
    parser.add_argument("--output_path", type=str, required=True, help="ONNX 출력 파일 경로")
    parser.add_argument("--input_size", type=int, default=224, help="입력 이미지 크기")
    parser.add_argument("--batch_size", type=int, default=1, help="배치 크기")
    parser.add_argument("--device", type=str, default="cpu", help="디바이스")
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    
    # ONNX 내보내기
    success = export_to_onnx(
        model_path=args.model_path,
        output_path=args.output_path,
        input_size=args.input_size,
        batch_size=args.batch_size,
        device=args.device
    )
    
    if success:
        print(f"✅ ONNX 내보내기 성공: {args.output_path}")
        sys.exit(0)
    else:
        print(f"❌ ONNX 내보내기 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
