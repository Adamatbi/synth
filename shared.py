import mediapipe as mp
import time
location=(0,0)
distance = 0

def pythagorean_distance(point1, point2):
    return ((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2 + (point1.z - point2.z) ** 2) ** 0.5


def set_distance(results):
    global distance
    points = [0,17,13,9,5,0]
    distance_accum = 0
    points_list = []
    # for landmark in results.multi_hand_landmarks[0].landmark:
    #     points_list.append((landmark.x, landmark.y, landmark.z))
    # print(points_list)

    for point in points[:-1]:
        distance_accum+=pythagorean_distance(
            results.multi_hand_landmarks[0].landmark[point],
            results.multi_hand_landmarks[0].landmark[points[points.index(point)+1]]
        )
    #print(sum(distance_accum))
    #print(distance_accum)
    distance = min(distance_accum / 4,0.3)
    print(distance)



def set_location(x:float, y:float):
    global location
    location = (1-x, 1-y)