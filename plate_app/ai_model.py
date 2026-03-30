import cv2
import easyocr
import numpy as np
from ultralytics import YOLO
import re

# Load YOLO model
model = YOLO("yolov8n.pt")

# EasyOCR
reader = easyocr.Reader(['en'])

# 🔥 FULL STATE MAPPING
state_dict = {
    "KA": "Karnataka", "MH": "Maharashtra", "DL": "Delhi",
    "TN": "Tamil Nadu", "AP": "Andhra Pradesh", "TS": "Telangana",
    "GJ": "Gujarat", "RJ": "Rajasthan", "KL": "Kerala",
    "HR": "Haryana", "UP": "Uttar Pradesh", "MP": "Madhya Pradesh",
    "WB": "West Bengal", "OR": "Odisha", "PB": "Punjab",
    "CH": "Chandigarh", "UK": "Uttarakhand", "JH": "Jharkhand",
    "AS": "Assam", "HP": "Himachal Pradesh"
}


# 🔥 CLEAN TEXT (handles multi-line + noise)
def clean_text(text):
    text = text.upper()
    text = text.replace("\n", "")
    text = text.replace(" ", "")
    text = re.sub(r'[^A-Z0-9]', '', text)  # remove symbols
    return text


# 🔥 FIX COMMON OCR MISTAKES
def correct_text(text):
    replacements = {
        "O": "0", "I": "1", "Z": "2",
        "S": "5", "B": "8"
    }

    new_text = ""
    for char in text:
        new_text += replacements.get(char, char)

    return new_text


# 🔥 VALIDATE INDIAN NUMBER PLATE
def validate_plate(text):
    pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{3,4}$'
    return re.match(pattern, text)


# 🔥 FORMAT OUTPUT (KA 02 AB 1234)
def format_plate(text):
    try:
        return f"{text[0:2]} {text[2:4]} {text[4:-4]} {text[-4:]}"
    except:
        return text


def process_image(image_path):
    img = cv2.imread(image_path)

    results = model(img)

    best_plate = ""
    best_conf = 0

    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            plate = img[y1:y2, x1:x2]

            # 🔥 Preprocessing (strong)
            gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
            blur = cv2.bilateralFilter(gray, 11, 17, 17)
            thresh = cv2.adaptiveThreshold(
                blur, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # 🔥 OCR (get multiple results)
            ocr_results = reader.readtext(thresh)

            for (bbox, text, conf) in ocr_results:
                cleaned = clean_text(text)
                corrected = correct_text(cleaned)

                if len(corrected) >= 8 and conf > best_conf:
                    best_plate = corrected
                    best_conf = conf

    if best_plate:

        # 🔥 FINAL CLEAN
        best_plate = clean_text(best_plate)

        # 🔥 VALIDATE
        if not validate_plate(best_plate):
            # try partial fix (important for double line)
            best_plate = best_plate[:10]

        # 🔥 STATE DETECTION
        state_code = best_plate[:2]
        state_name = state_dict.get(state_code, "Unknown State")

        # 🔥 FORMAT
        formatted_plate = format_plate(best_plate)

        return {
            "status": True,
            "plate": formatted_plate,
            "state": state_name,
            "confidence": round(best_conf * 100, 2),
            "raw_plate": best_plate
        }

    return {
        "status": False,
        "message": "No number plate detected"
    }