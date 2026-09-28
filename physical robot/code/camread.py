import cv2

# Try camera indexes 0–9
cameras = []
cap = cv2.VideoCapture(2)
while not cap.isOpened():
    cap = cv2.VideoCapture(2)

    print("Available cameras: NOne")

cap.release()
cap = cv2.VideoCapture(2)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

while True:
    ok, frame = cap.read()

    if not ok:
        print("Failed to read frame")
        break

    cv2.imshow("Webcam", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()