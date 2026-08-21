"""
Öğretmen modeli eğitimi.
Önce labels/ klasörüne .txt dosyalarını taşır, ardından YOLOv11n eğitir.
Çalıştır: python train_model.py
"""
import shutil
from pathlib import Path
from ultralytics import YOLO

IMAGES_DIR = Path("/Users/batuhancitak/Desktop/sure-project/data/ogretmen_dataset/images")
LABELS_DIR = Path("/Users/batuhancitak/Desktop/sure-project/data/ogretmen_dataset/labels")
YAML_PATH  = Path("/Users/batuhancitak/Desktop/sure-project/data/ogretmen.yaml")
OUTPUT_DIR = Path("/Users/batuhancitak/Desktop/sure-project/sure_models")


def fix_labels():
    """images/ içindeki .txt etiketleri labels/ altına taşı."""
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for txt in IMAGES_DIR.glob("*.txt"):
        dest = LABELS_DIR / txt.name
        if not dest.exists():
            shutil.move(str(txt), str(dest))
            moved += 1
    print(f"[fix_labels] {moved} etiket labels/ klasörüne taşındı.")


def train():
    fix_labels()

    model = YOLO("yolo11n.pt")  # nano — 20 karelik küçük set için ideal

    results = model.train(
        data=str(YAML_PATH),
        epochs=100,
        imgsz=640,
        batch=8,            # MPS için güvenli; VRAM baskısı yaratmaz
        device="mps",       # M4 Pro Metal backend
        workers=0,          # macOS'ta MPS ile workers=0 zorunlu
        patience=20,        # early stopping
        lr0=0.01,
        lrf=0.01,
        mosaic=0.5,         # küçük sette aşırı augmentation önlemi
        mixup=0.0,
        degrees=10.0,
        flipud=0.3,
        fliplr=0.5,
        project=str(OUTPUT_DIR),
        name="ogretmen",
        exist_ok=True,
        verbose=True,
    )

    best_pt = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\n✅ Eğitim tamamlandı. Model: {best_pt}")
    return best_pt


if __name__ == "__main__":
    train()
