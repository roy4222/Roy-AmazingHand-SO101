"""Data acquisition server.

Manages a recording session with a LeRobot robot.
Uses the provided LeRobot functions to record episodes and manage datasets.
Provides gRPC services for dataset management and session control.
"""

from concurrent import futures
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Optional

import grpc
from google.protobuf.empty_pb2 import Empty

from amazing_hand_api.amazing_hand_pb2 import (
    HandTeleoperationCommand,
    HandConfiguration,
    CalibrationData,
    FingerTipPosition,
)
from amazing_hand_api.amazing_hand_pb2_grpc import (
    add_AHTeleoperationServiceServicer_to_server,
)
from dora import Node
import pyarrow as pa
import time
import numpy as np


class AmazingHandServicer:
    """Servicer for data acquisition using LeRobot."""

    def __init__(self, low_filter) -> None:
        """Initialize the data acquisition servicer."""
        self._logger = getLogger(__name__)
        self.low_filter = low_filter
        self.node = Node()
        print("AmazingHandServicer initialized")

    def _register_to_server(self, server: Any) -> None:
        """Register the servicer to the gRPC server."""
        add_AHTeleoperationServiceServicer_to_server(self, server)

    def SendCalibrationData(
        self, request: CalibrationData, context: grpc.ServicerContext
    ) -> Empty:
        """Handle calibration data."""
        return Empty()

    def SendHandCommand(
        self, request: HandTeleoperationCommand, context: grpc.ServicerContext
    ) -> Empty:
        """Stop the current episode recording."""

        # r_res = [
        #     {
        #         "r_tip1": [
        #             request.right_hand.index.x * 0.87,
        #             request.right_hand.index.y * 0.87,
        #             request.right_hand.index.z * 0.87,
        #         ],
        #         "r_tip2": [
        #             request.right_hand.middle.x * 0.75,
        #             request.right_hand.middle.y * 0.75,
        #             request.right_hand.middle.z * 0.75,
        #         ],
        #         "r_tip3": [
        #             request.right_hand.ring.x * 0.77,
        #             request.right_hand.ring.y * 0.77,
        #             request.right_hand.ring.z * 0.77,
        #         ],
        #         "r_tip4": [
        #             request.right_hand.thumb.x * 0.75,
        #             request.right_hand.thumb.y * 0.75,
        #             request.right_hand.thumb.z * 0.75,
        #         ],
        #     }
        # ]

        def modulation_coeff(
            min_value: float,
            max_value: float,
            min_value_goal: float,
            max_value_goal: float,
            value: float,
        ) -> float:
            a = (max_value_goal - min_value_goal) / (max_value - min_value)
            b = (min_value_goal * max_value - max_value_goal * min_value) / (
                max_value - min_value
            )
            return a * value + b

        if request.right_hand.index_pinch.pinch_value < 0.5:
            request.right_hand.thumb.z *= modulation_coeff(
                0.5, 0, 1, 0.5, request.right_hand.index_pinch.pinch_value
            )
            request.right_hand.thumb.x += modulation_coeff(
                0.5, 0, 0, 0.05, request.right_hand.index_pinch.pinch_value
            )
            if request.right_hand.thumb.y < 0.0:
                request.right_hand.thumb.x += modulation_coeff(
                    0, -0.01, 0, -0.05, request.right_hand.thumb.y
                )

        # r_res = [
        #     {
        #         "r_tip1": [
        #             request.right_hand.index.x,
        #             request.right_hand.index.y,
        #             request.right_hand.index.z,
        #         ],
        #         "r_tip2": [
        #             request.right_hand.middle.x,
        #             request.right_hand.middle.y,
        #             request.right_hand.middle.z,
        #         ],
        #         "r_tip3": [
        #             request.right_hand.ring.x,
        #             request.right_hand.ring.y,
        #             request.right_hand.ring.z,
        #         ],
        #         "r_tip4": [
        #             request.right_hand.thumb.x,
        #             request.right_hand.thumb.y,
        #             request.right_hand.thumb.z,
        #         ],
        #     }
        # ]

        ## SEND LEFT HAND DATA TO RIGHT HAND FOR TESTING PURPOSES

        if request.left_hand.index_pinch.pinch_value < 0.6:
            request.left_hand.thumb.z *= modulation_coeff(
                0.6, 0, 1, 0.6, request.left_hand.index_pinch.pinch_value
            )
            # request.left_hand.thumb.x += modulation_coeff(
            #     0.7, 0, 0, 0.05, request.left_hand.index_pinch.pinch_value
            # )
            if request.left_hand.thumb.y > 0.0:
                request.left_hand.thumb.x += modulation_coeff(
                    0, 0.01, 0, -0.02, request.left_hand.thumb.y
                )

        r_res = [
            {
                "r_tip1": [
                    request.left_hand.index.x,
                    -request.left_hand.index.y,
                    request.left_hand.index.z,
                ],
                "r_tip2": [
                    request.left_hand.middle.x,
                    -request.left_hand.middle.y,
                    request.left_hand.middle.z,
                ],
                "r_tip3": [
                    request.left_hand.ring.x,
                    -request.left_hand.ring.y,
                    request.left_hand.ring.z,
                ],
                "r_tip4": [
                    request.left_hand.thumb.x,
                    -request.left_hand.thumb.y,
                    request.left_hand.thumb.z,
                ],
            }
        ]

        l_res = [
            {
                "l_tip1": [
                    request.left_hand.index.x,
                    request.left_hand.index.y,
                    request.left_hand.index.z,
                ],
                "l_tip2": [
                    request.left_hand.middle.x,
                    request.left_hand.middle.y,
                    request.left_hand.middle.z,
                ],
                "l_tip3": [
                    request.left_hand.ring.x,
                    request.left_hand.ring.y,
                    request.left_hand.ring.z,
                ],
                "l_tip4": [
                    request.left_hand.thumb.x,
                    request.left_hand.thumb.y,
                    request.left_hand.thumb.z,
                ],
            }
        ]

        # l_res[0]["l_tip1"][2] = l_res[0]["l_tip1"][2] + modulation(
        #     -0.03, request.left_hand.index_pinch.pinch_value
        # )
        # l_res[0]["l_tip4"][2] = l_res[0]["l_tip4"][2] + modulation(
        #     0.03, request.left_hand.index_pinch.pinch_value
        # )
        # l_res[0]["l_tip4"][0] = l_res[0]["l_tip4"][0] + modulation(
        #     -0.02, request.left_hand.index_pinch.pinch_value
        # )

        if r_res is not None:
            list_res = np.array(list(r_res[0].values())).flatten()
            self.low_filter.push(list_res)
            list_mod_res = self.low_filter.get_filtered_action()
            r_res = [
                {
                    "r_tip1": list(list_mod_res[0:3]),
                    "r_tip2": list(list_mod_res[3:6]),
                    "r_tip3": list(list_mod_res[6:9]),
                    "r_tip4": list(list_mod_res[9:12]),
                }
            ]
            self.node.send_output("r_hand_pos", pa.array(r_res))
            print("Sent right hand position:", r_res)
        if l_res is not None:
            self.node.send_output("l_hand_pos", pa.array(l_res))
        time.sleep(1 / 150)
        return Empty()


class LowPassActionFilter:
    def __init__(self, control_freq, cutoff_frequency=50.0):
        self.last_action = 0.0
        self.current_action = 0.0
        self.control_freq = float(control_freq)
        self.cutoff_frequency = float(cutoff_frequency)
        self.alpha = self.compute_alpha()

    def compute_alpha(self):
        return (1.0 / self.cutoff_frequency) / (
            1.0 / self.control_freq + 1.0 / self.cutoff_frequency
        )

    def push(self, action):
        self.current_action = action

    def get_filtered_action(self):
        self.last_action = (
            self.alpha * self.last_action + (1 - self.alpha) * self.current_action
        )
        return self.last_action


def main() -> None:
    """Main function to start the gRPC server."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    low_filter = LowPassActionFilter(control_freq=150.0)
    amazing_hand_servicer = AmazingHandServicer(low_filter)
    amazing_hand_servicer._register_to_server(server)
    server.add_insecure_port("[::]:50070")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
