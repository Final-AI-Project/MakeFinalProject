# plants-dataset/train, val 에 실제 식물 이미지 넣은 뒤
python models/classifier/cascade/cascade.py --data_root models/plants-dataset --model mobilenet_v3_large --epochs 10 --weighted_sampler



# 추론
python models/classifier/infer_classifier.py --weights models/weight/mobilenet_v3_large_best.pth --model mobilenet_v3_large --image myplant.jpg



# 실행 디렉터리 위치
## 루트(MakeFinalProject)에서 실행하는 경우
python models/classifier/infer_classifier.py --weights models/weight/mobilenet_v3_large_best.pth --model mobilenet_v3_large --image myplant.jpg

## models/classifier 폴더 안에서 실행하는 경우
python infer_classifier.py --weights ../weight/mobilenet_v3_large_best.pth --model mobilenet_v3_large --image ../../myplant.jpg

## models/classifier/cascade 폴더 안에서 실행하는 경우
python ../infer_classifier.py --weights ../../weight/mobilenet_v3_large_best.pth --model mobilenet_v3_large --image ../../../myplant.jpg
