if __name__ == '__main__':
    from ultralytics import YOLO

    #load model
    model = YOLO('yolov9c.pt') #yolo V8

    results = model.train(data='X:\AI\FineTunedYoloV8\paper-wad-1\data.yaml', epochs=5 , imgsz=640, batch=-1) #device=[0], save_period=10)
    
    