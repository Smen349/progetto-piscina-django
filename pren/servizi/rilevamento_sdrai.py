from dataclasses import dataclass
from ultralytics import YOLO


@dataclass
class SdraioRilevato:
    x_percentuale: float
    y_percentuale: float
    confidenza: float
    classe: str

def rileva_sdrai_da_immagine(percorso_immagine: str, conf_min: float = 0.20):

    CLASSI_OK = {"chair", "bench"}

    model = YOLO("yolov8n.pt")
    results = model(percorso_immagine)
    #print("YOLO detections:", len(results[0].boxes))

    scartate_conf = 0
    scartate_classe = 0
    accettate = 0

    import cv2

    img = cv2.imread(percorso_immagine)
    height, width = img.shape[:2]

    #print("Dimensione immagine reale:", width, height)
    rilevati = []

    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf[0])
        if conf < conf_min:
            scartate_conf += 1
            continue
        cls_id = int(box.cls[0])
        nome_classe = results[0].names[cls_id]
        if nome_classe not in CLASSI_OK:
            scartate_classe += 1
            continue

        #print("BBox:", x1, y1, x2, y2, "conf:", conf, "classe", nome_classe)

        x_center = float(x1 + x2) / 2
        y_center = float(y1 + y2) / 2

        #print("Centro bbox:", x_center, y_center)

        x_percentuale = (x_center / width) * 100
        y_percentuale = (y_center / height) * 100

        #print("Percentuali:", x_percentuale, y_percentuale)

        rilevati.append(
            SdraioRilevato(
                x_percentuale=float(x_percentuale),
                y_percentuale=float(y_percentuale),
                confidenza=conf,
                classe=nome_classe,
            )
        )

        accettate += 1

    print("Riepilogo YOLO:",
          "totali=", len(results[0].boxes),
          "scartate_conf=", scartate_conf,
          "scartate_classe=", scartate_classe,
          "accettate=", accettate)


    return rilevati