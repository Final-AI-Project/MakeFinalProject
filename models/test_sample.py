import requests
import base64
import json
from PIL import Image, ImageDraw
import io
import os

def create_sample_plant_image():
    """테스트용 식물 이미지 생성"""
    # 400x400 크기의 흰색 배경 이미지 생성
    img = Image.new('RGB', (400, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # 잎 모양 그리기 (여러 개)
    # 잎 1
    draw.ellipse([50, 100, 150, 200], fill='green', outline='darkgreen', width=2)
    draw.line([100, 200, 100, 250], fill='darkgreen', width=3)  # 줄기
    
    # 잎 2
    draw.ellipse([200, 80, 300, 180], fill='lightgreen', outline='darkgreen', width=2)
    draw.line([250, 180, 250, 230], fill='darkgreen', width=3)  # 줄기
    
    # 잎 3
    draw.ellipse([120, 200, 220, 300], fill='green', outline='darkgreen', width=2)
    draw.line([170, 300, 170, 350], fill='darkgreen', width=3)  # 줄기
    
    # 잎 4 (작은 잎)
    draw.ellipse([280, 220, 350, 290], fill='lightgreen', outline='darkgreen', width=2)
    draw.line([315, 290, 315, 320], fill='darkgreen', width=2)  # 줄기
    
    # 저장
    img.save('sample_plant.jpg', 'JPEG', quality=95)
    print("✅ 샘플 식물 이미지 생성 완료: sample_plant.jpg")
    return 'sample_plant.jpg'

def test_detector_api(image_path, api_url="http://localhost:8000/detector"):
    """detector API 테스트"""
    try:
        # 이미지 파일을 multipart/form-data로 전송
        with open(image_path, 'rb') as f:
            files = {'image': (image_path, f, 'image/jpeg')}
            response = requests.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 호출 성공!")
            print(f"📊 탐지된 잎 개수: {result['detected_leaves_count']}")
            print(f"💬 메시지: {result['message']}")
            
            # 크롭된 잎 이미지들 저장
            if result['cropped_leaves']:
                os.makedirs('output_leaves', exist_ok=True)
                for i, leaf_data in enumerate(result['cropped_leaves']):
                    # base64 디코딩하여 이미지 저장
                    img_data = base64.b64decode(leaf_data['image'])
                    with open(f'output_leaves/leaf_{i+1}.jpg', 'wb') as f:
                        f.write(img_data)
                    print(f"💾 잎 {i+1} 저장 완료: output_leaves/leaf_{i+1}.jpg")
            
            # 세그멘테이션된 이미지 저장
            if 'segmented_image' in result:
                seg_img_data = base64.b64decode(result['segmented_image']['image'])
                with open('output_segmented.jpg', 'wb') as f:
                    f.write(seg_img_data)
                print("💾 세그멘테이션 이미지 저장 완료: output_segmented.jpg")
            
            return result
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.")
        print("💡 서버 실행 명령: cd models && uvicorn main:app --reload")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def test_health_check(api_url="http://localhost:8000/health"):
    """헬스 체크 API 테스트"""
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            result = response.json()
            print("✅ 헬스 체크 성공!")
            print(f"📊 모델 상태: {result['models']}")
            return result
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
        return None

if __name__ == "__main__":
    print("🌱 Plant AI API 테스트 시작")
    print("=" * 50)
    
    # 1. 헬스 체크
    print("\n1️⃣ 헬스 체크 테스트")
    test_health_check()
    
    # 2. 샘플 이미지 로드
    print("\n2️⃣ 샘플 이미지 로드")
    sample_image = "sample1.jpg"  # 사용자 제공 이미지 사용
    if not os.path.exists(sample_image):
        print(f"❌ 오류: {sample_image} 파일을 찾을 수 없습니다. 파일을 현재 디렉토리에 넣어주세요.")
        exit(1)
    print(f"✅ 사용자 제공 이미지 사용: {sample_image}")
    
    # 3. Detector API 테스트
    print("\n3️⃣ Detector API 테스트")
    result = test_detector_api(sample_image)
    
    if result:
        print("\n🎉 테스트 완료!")
        print("📁 생성된 파일들:")
        print("  - sample_plant.jpg (입력 이미지)")
        print("  - output_segmented.jpg (세그멘테이션 결과)")
        print("  - output_leaves/ (크롭된 잎들)")
    else:
        print("\n❌ 테스트 실패")
        print("💡 해결 방법:")
        print("  1. FastAPI 서버가 실행 중인지 확인")
        print("  2. 필요한 패키지가 설치되어 있는지 확인")
        print("  3. seg_best.pt 모델 파일이 올바른 위치에 있는지 확인")
