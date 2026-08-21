"""
S.U.R.E. — Güçlü Model Eğitimi
================================
510 karelik tam dataset (412 train / 98 val) üzerinde YOLOv11s eğitir.
Öğretmen modelinden (nano) büyük model (small) → daha iyi tespit.

Çalıştır: python3 train_sure.py
Çıktı   : sure_models/sure_v1/weights/best.pt
"""
from pathlib import Path
from ultralytics import YOLO

YAML_PATH  = Path("/Users/batuhancitak/Desktop/sure-project/data/sure_dataset.yaml")
OUTPUT_DIR = Path("/Users/batuhancitak/Desktop/sure-project/sure_models")


def train():
    model = YOLO("yolo11s.pt")   # small: nano'dan %~15 daha iyi mAP, Jetson'da hâlâ hızlı

    results = model.train(
        data=str(YAML_PATH),
        epochs=100,          # 20 → 100: eğitim 5 epoch'ta kesilince underfit kalmıştı
        imgsz=640,
        batch=8,             # MPS için güvenli
        device="mps",
        workers=0,           # macOS MPS zorunluluğu
        amp=False,           # MPS'te AMP index OOB bug'ını engeller
        patience=40,         # 30 → 40: daha geniş erken durma marjı
        close_mosaic=10,     # son 10 epoch mosaic kapat → temiz yakınsama

        # Optimizasyon
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,

        # Augmentation — 510 kare için dengeli
        mosaic=1.0,
        mixup=0.1,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.3,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,

        # Çıktı
        project=str(OUTPUT_DIR),
        name="sure_v1",
        exist_ok=True,
        verbose=True,
        plots=True,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\n✅ Eğitim tamamlandı.")
    print(f"   Model : {best}")
    print(f"   mAP50 : {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"\n🔁 yolo_runner.py --model parametresini güncelle:")
    print(f"   --model {best}")
    return best


if __name__ == "__main__":
    train()
