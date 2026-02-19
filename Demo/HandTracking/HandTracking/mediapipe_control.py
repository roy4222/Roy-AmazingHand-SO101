import argparse
import os
import time

import cv2
import numpy as np
import pyarrow as pa
from dora import Node
import mediapipe as mp
from scipy.spatial.transform import Rotation

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# https://mediapipe.readthedocs.io/en/latest/solutions/hands.html


def process_img(hand_proc, image):
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hand_proc.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    r_res = None
    l_res = None
    if results.multi_hand_landmarks:

        for index, handedness_classif in enumerate(results.multi_handedness):
            if (
                handedness_classif.classification[0].score > 0.8
            ):  # let's considere only one right hand

                hand_landmarks = results.multi_hand_world_landmarks[index]  # metric
                hand_landmarks_norm = results.multi_hand_landmarks[index]  # normalized

                # Wrist as origin
                origin = np.array(
                    [
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x,
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y,
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].z,
                    ]
                )

                # Creating coordinate system
                mid_mcp = np.array(
                    [
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_MCP
                        ].x,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_MCP
                        ].y,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_MCP
                        ].z,
                    ]
                )  # base of the middle finger
                index_mcp = np.array(
                    [
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_MCP
                        ].x,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_MCP
                        ].y,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_MCP
                        ].z,
                    ]
                )  # base of the index finger

                unit_z = (
                    mid_mcp - origin
                )  # z is unit vector from base of wrist toward base of middle finger
                unit_z = unit_z / np.linalg.norm(unit_z)

                if handedness_classif.classification[0].label == "Right":
                    vec_towards_y = (
                        origin - index_mcp
                    )  # vector from wrist base towards index base
                if handedness_classif.classification[0].label == "Left":
                    vec_towards_y = (
                        index_mcp - origin
                    )  # vector from wrist base towards index base

                unit_x = np.cross(
                    vec_towards_y, unit_z
                )  # we say unit x is the cross product of z and the vector towards pinky

                unit_x = unit_x / np.linalg.norm(unit_x)

                unit_y = np.cross(unit_z, unit_x)

                if handedness_classif.classification[0].label == "Right":
                    # A=np.array([unit_x,unit_y,unit_z]).reshape((3,3))
                    R = np.array([unit_x, -unit_y, unit_z]).reshape(
                        (3, 3)
                    )  # -y because of mirror?
                if handedness_classif.classification[0].label == "Left":
                    R = np.array([unit_x, -unit_y, unit_z]).reshape(
                        (3, 3)
                    )  # -y because of mirror?

                # Get tip position in world coordinates

                tip1_world = np.array(
                    [
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_TIP
                        ].x,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_TIP
                        ].y,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.INDEX_FINGER_TIP
                        ].z,
                    ]
                )

                tip2_world = np.array(
                    [
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_TIP
                        ].x,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_TIP
                        ].y,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.MIDDLE_FINGER_TIP
                        ].z
                        + 0.04,
                    ]
                )

                tip3_world = np.array(
                    [
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.RING_FINGER_TIP
                        ].x,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.RING_FINGER_TIP
                        ].y,
                        hand_landmarks.landmark[
                            mp_hands.HandLandmark.RING_FINGER_TIP
                        ].z,
                    ]
                )

                tip4_world = np.array(
                    [
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x,
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y,
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].z,
                    ]
                )

                # print(f'TIP: {tip_x} {tip_y} {tip_z} ({hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x} {hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y} {hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].z})')
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks_norm,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )

                tip1 = R @ (tip1_world - origin)
                tip2 = R @ (tip2_world - origin)
                tip3 = R @ (tip3_world - origin)
                tip4 = R @ (tip4_world - origin)

                middle_finger_mcp = R @ (mid_mcp - origin)
                print(f"MIDDLE_FINGER_MCP - TIP2: {mid_mcp - tip2_world}")
                # print(
                #     f"MIDDLE_FINGER_MCP: {middle_finger_mcp[0]:.3f} {middle_finger_mcp[1]:.3f} {middle_finger_mcp[2]:.3f}"
                # )
                # print(f"TIP2: {tip2[0]:.3f} {tip2[1]:.3f} {tip2[2]:.3f}")

                # scale=0.01
                # image = cv2.drawFrameAxes(image, K, disto, rotV, origin, scale)

                # res=[{'r_tip1': [tip1_x,tip1_y,tip1_z],'r_tip2': [tip2_x,tip2_y,tip2_z],'r_tip3': [tip3_x,tip3_y,tip3_z],'r_tip4': [tip4_x,tip4_y,tip4_z]}]
                if handedness_classif.classification[0].label == "Right":
                    r_res = [
                        {"r_tip1": tip1, "r_tip2": tip2, "r_tip3": tip3, "r_tip4": tip4}
                    ]
                    # print(f"RIGHT: {tip1_x:.3f} {tip1_y:.3f} {tip1_z:.3f} => {tip1}. {unit_x} {unit_y} {unit_z}")
                elif handedness_classif.classification[0].label == "Left":
                    l_res = [
                        {"l_tip1": tip1, "l_tip2": tip2, "l_tip3": tip3, "l_tip4": tip4}
                    ]
                    # print(f"LEFT: {tip1_x:.3f} {tip1_y:.3f} {tip1_z:.3f} => {tip1}. {unit_x} {unit_y} {unit_z}")
    # Flip the image horizontally for a selfie-view display.
    return image, r_res, l_res


# cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))


def main():

    node = Node()

    pa.array([])  # initialize pyarrow array
    cap = cv2.VideoCapture(2, cv2.CAP_V4L2)

    # --- Low-latency settings ---
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # may not be supported on all drivers, but try
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    with mp_hands.Hands(
        model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5
    ) as hands:

        for event in node:

            event_type = event["type"]

            if event_type == "INPUT":
                event_id = event["id"]

                if event_id == "tick":
                    ret, frame = cap.read()

                    if not ret:
                        continue

                    frame = cv2.flip(frame, 1)
                    # process
                    frame, r_res, l_res = process_img(hands, frame)

                    if r_res is not None:
                        node.send_output("r_hand_pos", pa.array(r_res))
                    if l_res is not None:
                        node.send_output("l_hand_pos", pa.array(l_res))

                    cv2.imshow("MediaPipe Hands", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

            elif event_type == "ERROR":
                raise RuntimeError(event["error"])


if __name__ == "__main__":
    main()
