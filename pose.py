import cv2
import mediapipe as mp
import shared

def track_body():
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        set_values = False
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            if shared.fully_visible(results):
                shared.measure_distance_between_hands(results)
                shared.measure_horizontal_distance_between_hands(results)
                shared.measure_hand_heights(results)
                shared.measure_right_hand_speed(results)
                set_values = True
                shared.tracking=True


        cv2.imshow("Pose", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if not set_values:
            shared.tracking=False

    cap.release()
    cv2.destroyAllWindows()
