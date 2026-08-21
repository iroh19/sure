import cv2
import os
import glob

# --- AYARLAR ---
# Videoların bulunduğu klasör
GIRIS_KLASORU = "/Users/batuhancitak/Desktop/sure-project/data/balık_videolar"
# Çıkarılan fotoğrafların kaydedileceği klasör
CIKTI_KLASORU = "/Users/batuhancitak/Desktop/sure-project/data/frames"
HEDEF_FPS = 1 # Saniyede 1 fotoğraf alınacak

def extract_frames_from_all_videos():
    # Çıktı klasörü yoksa oluştur
    if not os.path.exists(CIKTI_KLASORU):
        os.makedirs(CIKTI_KLASORU)
        print(f"📁 '{CIKTI_KLASORU}' klasörü oluşturuldu.")

    # Klasördeki mp4, MOV, avi gibi video formatlarını bul
    video_uzantilari = ('*.mp4', '*.MOV', '*.mov', '*.avi')
    video_dosyalari = []
    for uzanti in video_uzantilari:
        video_dosyalari.extend(glob.glob(os.path.join(GIRIS_KLASORU, uzanti)))

    if not video_dosyalari:
        print(f"❌ HATA: '{GIRIS_KLASORU}' içinde hiç video bulunamadı. Uzantıları kontrol et.")
        return

    print(f"📂 Toplam {len(video_dosyalari)} video bulundu. Toplu işlem başlıyor...\n")

    # Bulunan her bir video için döngüyü çalıştır
    for video_yolu in video_dosyalari:
        # Dosya yolundan sadece videonun adını al (örn: "video1")
        video_adi = os.path.basename(video_yolu).split('.')[0]
        print(f"🎥 İşleniyor: {video_adi}...")

        cap = cv2.VideoCapture(video_yolu)
        if not cap.isOpened():
            print(f"  ❌ HATA: Okunamadı -> {video_yolu}")
            continue

        fps_orijinal = int(cap.get(cv2.CAP_PROP_FPS))
        if fps_orijinal == 0:
             print(f"  ❌ HATA: FPS okunamadı -> {video_yolu}")
             continue

        frame_interval = int(fps_orijinal / HEDEF_FPS)
        count = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % frame_interval == 0:
                # Fotoğrafı videonun adıyla kaydet (Örn: video1_frame_0001.jpg)
                frame_name = os.path.join(CIKTI_KLASORU, f"{video_adi}_frame_{saved_count:04d}.jpg")
                cv2.imwrite(frame_name, frame)
                saved_count += 1

            count += 1

        cap.release()
        print(f"  ✅ {video_adi} tamamlandı. ({saved_count} kare çıkarıldı)")

    print(f"\n🎉 TÜM İŞLEMLER TAMAMLANDI! Bütün fotoğraflar '{CIKTI_KLASORU}' klasöründe seni bekliyor.")

if __name__ == "__main__":
    extract_frames_from_all_videos()