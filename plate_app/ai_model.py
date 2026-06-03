import cv2
import easyocr
import numpy as np
from ultralytics import YOLO
import re

# ==========================
# LOAD MODELS
# ==========================

model = YOLO("yolov8n.pt")

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

# ==========================
# STATE CODES
# ==========================

state_dict = {
    "KA": "Karnataka",
    "MH": "Maharashtra",
    "DL": "Delhi",
    "TN": "Tamil Nadu",
    "AP": "Andhra Pradesh",
    "TS": "Telangana",
    "GJ": "Gujarat",
    "RJ": "Rajasthan",
    "KL": "Kerala",
    "HR": "Haryana",
    "UP": "Uttar Pradesh",
    "MP": "Madhya Pradesh",
    "WB": "West Bengal",
    "OR": "Odisha",
    "PB": "Punjab",
    "CH": "Chandigarh",
    "UK": "Uttarakhand",
    "JH": "Jharkhand",
    "AS": "Assam",
    "HP": "Himachal Pradesh"
}

# ==========================
# CLEAN OCR TEXT
# ==========================

def clean_text(text):
    text = text.upper()
    text = text.replace(" ", "")
    text = text.replace("\n", "")
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

# ==========================
# FIX OCR ERRORS
# ==========================

def correct_plate(text):

    chars = list(text)

    for i in range(len(chars)):

        if i >= 2:
            if chars[i] == 'O':
                chars[i] = '0'

        if chars[i] == 'I':
            chars[i] = '1'

        if chars[i] == 'Z':
            chars[i] = '2'

    return "".join(chars)

# ==========================
# VALIDATE INDIAN PLATE
# ==========================

def validate_plate(text):

    patterns = [
        r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$',
        r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{3}$'
    ]

    for pattern in patterns:
        if re.match(pattern, text):
            return True

    return False

# ==========================
# FORMAT PLATE
# ==========================

def format_plate(text):

    try:
        state = text[:2]
        district = text[2:4]
        number = text[-4:]
        series = text[4:-4]

        return f"{state} {district} {series} {number}"

    except:
        return text

# ==========================
# IMAGE PREPROCESSING
# ==========================

def preprocess_plate(plate):

    gray = cv2.cvtColor(
        plate,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.equalizeHist(gray)

    gray = cv2.bilateralFilter(
        gray,
        11,
        17,
        17
    )

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh

# ==========================
# OCR
# ==========================

def perform_ocr(image):

    texts = []

    results = reader.readtext(
        image,
        detail=1,
        paragraph=False
    )

    for (_, text, conf) in results:

        text = clean_text(text)
        text = correct_plate(text)

        texts.append((text, conf))

    return texts

# ==========================
# MAIN FUNCTION
# ==========================

def process_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "status": False,
            "message": "Image not found"
        }

    results = model(image)

    best_plate = ""
    best_conf = 0

    for result in results:

        boxes = result.boxes

        for box in boxes:

            detector_conf = float(box.conf)

            if detector_conf < 0.40:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            plate = image[y1:y2, x1:x2]

            if plate.size == 0:
                continue

            processed = preprocess_plate(plate)

            enlarged = cv2.resize(
                processed,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC
            )

            ocr_results = perform_ocr(enlarged)

            for text, conf in ocr_results:

                if len(text) < 8:
                    continue

                if conf > best_conf:

                    best_plate = text
                    best_conf = conf

    if best_plate:

        state_code = best_plate[:2]

        state_name = state_dict.get(
            state_code,
            "Unknown State"
        )

        return {
            "status": True,
            "plate": format_plate(best_plate),
            "raw_plate": best_plate,
            "state": state_name,
            "confidence": round(best_conf * 100, 2),
            "valid": validate_plate(best_plate)
        }

    return {
        "status": False,
        "message": "No number plate detected"
    }
def process_image_from_array(img):

    results = model(img)

    best_plate = ""
    best_conf = 0

    for r in results:

        for box in r.boxes:

            x1,y1,x2,y2 = map(int, box.xyxy[0])

            plate = img[y1:y2, x1:x2]

            text = reader.readtext(plate)

            for (_, t, conf) in text:

                if conf > best_conf:
                    best_plate = t
                    best_conf = conf

    return {
        "plate": best_plate,
        "confidence": round(best_conf*100,2)
    }
# ==========================
# TEST
# ==========================

if __name__ == "__main__":

    result = process_image("car.jpg")

    print(result)