import cv2
import supervision as sv
from inference import get_model

image = cv2.imread("Test_Img.jpg")
model = get_model(model_id="yolov8s-640", api_key="9DJU83gUHD4oGJmWP7uf")
result = model.infer(image)[0]
detections = sv.Detections.from_inference(result)

len(detections)