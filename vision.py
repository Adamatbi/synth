import cv2
import mediapipe as mp
import shared
import time


def track_hand():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        set_values = False
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label
                if label == "Left":
                    # Draw landmarks and connections
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    # Optional: print wrist coordinates
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    shared.set_location(wrist.x, wrist.y)
                    shared.set_distance(results)
                    set_values = True
        cv2.imshow("Left Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if not set_values:
            shared.location = (0, 0)

    cap.release()
    cv2.destroyAllWindows()