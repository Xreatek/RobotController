from ultralytics import YOLO

#load model
model = YOLO('M1V9.pt')

results = model.train(data='X:\AI\FineTunedYoloV8\paper-1\data.yaml', epochs=10, imgsz=640, batch=1, device="cuda")