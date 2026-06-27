import os
import csv
from pathlib import Path
from dotenv import load_dotenv
from ultralytics import YOLO
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "raw" / "images"
RESULTS_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

logger.add(
    LOGS_DIR / "yolo_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    level="INFO"
)

PERSON_CLASSES = {"person"}
PRODUCT_CLASSES = {"bottle", "cup", "bowl", "vase", "book", "box", "scissors"}


def classify_image(detected_classes):
    has_person = any(c in PERSON_CLASSES for c in detected_classes)
    has_product = any(c in PRODUCT_CLASSES for c in detected_classes)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"


def run_detection():
    logger.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")
    logger.info("Model loaded!")

    results_data = []
    image_files = list(IMAGES_DIR.glob("**/*.jpg"))
    logger.info(f"Found {len(image_files)} images to process")

    for i, image_path in enumerate(image_files):
        try:
            parts = image_path.parts
            channel_name = parts[-2]
            message_id = image_path.stem

            results = model(str(image_path), verbose=False)

            detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    detections.append({
                        "class_name": class_name,
                        "confidence": confidence
                    })

            detected_classes = [d["class_name"] for d in detections]
            image_category = classify_image(detected_classes)

            for detection in detections:
                results_data.append({
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "image_path": str(image_path),
                    "detected_class": detection["class_name"],
                    "confidence_score": round(detection["confidence"], 4),
                    "image_category": image_category,
                })

            if not detections:
                results_data.append({
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "image_path": str(image_path),
                    "detected_class": "none",
                    "confidence_score": 0.0,
                    "image_category": image_category,
                })

            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(image_files)} images")

        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
            continue

    output_file = RESULTS_DIR / "yolo_detections.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["message_id", "channel_name", "image_path",
                      "detected_class", "confidence_score", "image_category"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_data)

    logger.info(f"Detection complete! Results saved to {output_file}")
    logger.info(f"Total detections: {len(results_data)}")

    categories = {}
    for row in results_data:
        cat = row["image_category"]
        categories[cat] = categories.get(cat, 0) + 1
    logger.info(f"Category summary: {categories}")


if __name__ == "__main__":
    run_detection()