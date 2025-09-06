import mediapipe as mp
import numpy as np
import time

#all values are normalized [0, 1] unless otherwise noted
distance_between_hands = 0
right_hand_height = 0
left_hand_height = 0

tracking = False

def convert_to_tuple(point):
    return (point.x, point.y, point.z)

def pythagorean_distance(point1:tuple, point2:tuple):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2) ** 0.5

def measure_total_distances(points:list[tuple]):
    total_distance = 0
    for i in range(len(points) - 1):
        total_distance += pythagorean_distance(points[i], points[i + 1])
    return total_distance

def center_of_two_points(point1:tuple, point2:tuple):
    return ((point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2, (point1[2] + point2[2]) / 2)

def angle_between_points(point1:tuple, point2:tuple, point3:tuple):
    import numpy as np
    a = np.array([point1[0], point1[1], point1[2]])
    b = np.array([point2[0], point2[1], point2[2]])
    c = np.array([point3[0], point3[1], point3[2]])

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)
    

def measure_hand_heights(results):
    global right_hand_height, left_hand_height
    right_hand_point = convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST])
    left_hand_point = convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_WRIST])

    avg_hip_location = center_of_two_points(
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP]))

    avg_shoulder_location = center_of_two_points(
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]))
    
    torso_length = pythagorean_distance(
        avg_hip_location,
        avg_shoulder_location)
    
    # direction from hip to shoulder (defines "up")
    up_dir = np.array(avg_shoulder_location) - np.array(avg_hip_location)
    up_dir = up_dir / np.linalg.norm(up_dir)  # normalize

    right_hand_vec = np.array(right_hand_point) - np.array(avg_shoulder_location)
    right_hand_height = np.dot(right_hand_vec, up_dir)
    right_hand_torso_height = (right_hand_height / torso_length)
    # adjust and clamp to [0, 1]. I found height above and below shoulders to be generally from -0.9 to 0.9
    right_hand_torso_height = max(-0.9, min(0.9, right_hand_torso_height))
    right_hand_height = (right_hand_torso_height + 0.9) / 1.8

    

    left_hand_vec = np.array(left_hand_point) - np.array(avg_shoulder_location)
    left_hand_height = np.dot(left_hand_vec, up_dir)
    left_hand_torso_height = (left_hand_height / torso_length)
    # adjust and clamp to [0, 1]. I found height above and below shoulders to be generally from -0.9 to 0.9
    left_hand_torso_height = max(-0.9, min(0.9, left_hand_torso_height))
    left_hand_height = (left_hand_torso_height + 0.9) / 1.8


def measure_distance_between_hands(results):
    global distance_between_hands

    #measure max distance between hands when arms are fully extended
    wingspan = measure_total_distances([
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_WRIST]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST])
    ])
    
    inter_hand_distance=pythagorean_distance(
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_WRIST]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST])
    )

    distance_between_hands = max(0, min(1, inter_hand_distance / wingspan))
    #print("#"*int(distance_between_hands*50))

