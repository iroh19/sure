"""
Otomatik etiketleme — öğretmen modeli ile kalan 545 kareye bounding box yazar.
Çalıştır: python auto_label.py
Çıktı:    data/frames/<görsel>.txt  (YOLO formatı, sınıf 0 = sturgeon)
"""
from pathlib import Path
from ultralytics import YOLO

FRAMES_DIR   = Path("/Users/batuhancitak/Desktop/sure-project/data/frames")
LABELED_DIR  = Path("/Users/batuhancitak/Desktop/sure-project/data/ogretmen_dataset/images")
MODEL_PATH   = Path("/Users/batuhancitak/Desktop/sure-project/sure_models/ogretmen/weights/best.pt")
CONF_THRESH  = 0.25   # düşük eşik — öğretmen gözden kaçırmasın; manuel incelemede temizlenir


def already_labeled() -> set:
    return {p.stem for p in LABELED_DIR.glob("*.jpg")}


def run():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model bulunamadı: {MODEL_PATH}\n"
            "Önce train_model.py'yi çalıştırarak öğretmen modelini eğit."
        )

    model = YOLO(str(MODEL_PATH))
    done  = already_labeled()

    frames = sorted(FRAMES_DIR.glob("*.jpg"))
    targets = [f for f in frames if f.stem not in done]

    print(f"Toplam kare       : {len(frames)}")
    print(f"Zaten etiketli    : {len(done)}")
    print(f"Etiketlenecek     : {len(targets)}\n")

    saved = 0
    skipped = 0

    for img_path in targets:
        results = model.predict(
            source=str(img_path),
            conf=CONF_THRESH,
            device="mps",
            verbose=False,
            save=False,
            save_txt=False,
        )

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            skipped += 1
            continue

        label_path = FRAMES_DIR / (img_path.stem + ".txt")
        with open(label_path, "w") as f:
            for box in boxes.xywhn:
                cx, cy, w, h = box.tolist()
                f.write(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

        saved += 1
        if saved % 50 == 0:
            print(f"  -> {saved}/{len(targets)} islendi...")

    print(f"\nTamamlandi.")
    print(f"  Etiket yazilan           : {saved}")
    print(f"  Balik bulunamayan (bos)  : {skipped}")
    print(f"  Etiket klasoru           : {FRAMES_DIR}")


if __name__ == "__main__":
    run()
