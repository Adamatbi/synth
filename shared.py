import mediapipe as mp
import numpy as np
import time
from queue import Queue
import math

#all values are normalized [0, 1] unless otherwise noted
distance_between_hands = 0
horizontal_distance_between_hands = 0


right_hand_height = 0
left_hand_height = 0

right_hand_speed = 0




#reference variables
torso_length = 0
tracking = False

# variables to carry over state between frames
HAND_SPEED_HISTORY_SIZE = 5
right_hand_history = Queue(maxsize = HAND_SPEED_HISTORY_SIZE)

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

def scale_value_to_range(value, src_min, src_max):
    # Scale value from src range to [0, 1]
    scaled = (value - src_min) / (src_max - src_min)
    # Clamp to [0, 1]
    return max(0, min(1, scaled))

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

def fully_visible(results):
    for landmark in results.pose_landmarks.landmark:
        if landmark.x < 0 or landmark.x > 1 or landmark.y < 0 or landmark.y > 1:
            return False
    return True

def measure_right_hand_speed(results):
    global right_hand_history, right_hand_speed
    if not right_hand_history.full():
        right_hand_speed = 0
        right_hand_history.put(convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]))
        return
    
    # insert current position and remove oldest
    right_hand_history.get()
    right_hand_history.put(convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]))

    # calculate speed as average distance moved per frame
    positions = list(right_hand_history.queue)
    total_distance = 0

    for i in range(len(positions) - 1):
        total_distance += pythagorean_distance(positions[i], positions[i + 1])
        raw_right_hand_speed = total_distance / (len(positions) - 1)
    right_hand_speed = max(0, min(1, (raw_right_hand_speed/torso_length) * 4))  # scale factor to adjust sensitivity

    

def measure_hand_heights(results):
    global right_hand_height, left_hand_height, torso_length
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

def measure_horizontal_distance_between_hands(results):
    global horizontal_distance_between_hands

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

    #measure max horizontal distance between hands when arms are fully extended
    wingspan = measure_total_distances([
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_WRIST]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW]),
        convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST])
    ])
    
    left_hand = convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_WRIST])
    right_hand = convert_to_tuple(results.pose_world_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_WRIST])
    
    # project hand positions onto plane perpendicular to up_dir
    left_hand_vec = np.array(left_hand) - np.array(avg_shoulder_location)
    left_hand_proj = left_hand_vec - np.dot(left_hand_vec, up_dir) * up_dir
    left_hand_proj_point = left_hand_proj + np.array(avg_shoulder_location)

    right_hand_vec = np.array(right_hand) - np.array(avg_shoulder_location)
    right_hand_proj = right_hand_vec - np.dot(right_hand_vec, up_dir) * up_dir
    right_hand_proj_point = right_hand_proj + np.array(avg_shoulder_location)

    inter_hand_distance=pythagorean_distance(left_hand_proj_point, right_hand_proj_point)
    horizontal_distance_between_hands = max(0, min(1, inter_hand_distance / wingspan))
