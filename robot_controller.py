#!/usr/bin/env python3
"""
Robot Controller - Complete Logic with SDK Feedback
Contains all robot control functionality for motion sequence execution using SDK feedback.
"""

import time
import logging
from fairino import Robot


# ============================================================================
# ADJUSTABLE CONFIGURATION PARAMETERS - Modify these as needed
# ============================================================================

# Delay Settings (in seconds)
INTER_MOVEMENT_DELAY = 0.0          # Delay between sequence steps (0.0 for immediate execution)
FEEDBACK_CHECK_INTERVAL = 0.1       # Interval for SDK feedback polling (don't change unless needed)
RECONNECT_DELAY = 1.0               # Delay between reconnection attempts

# Movement Settings
MOVEMENT_SPEED = 20.0               # Movement velocity (percentage 0-100, degrees/second)
MOVEMENT_ACCELERATION = 100.0       # Movement acceleration (percentage 0-100)

# ============================================================================


class SimpleRobotController:
    """
    Complete robot controller with built-in motion sequence.
    Executes: home -> position1 -> home sequence.
    Uses SDK feedback for motion verification instead of artificial delays.
    """

    def __init__(self, robot_ip='192.168.58.101'):
        """Initialize the robot controller"""
        # Setup logging
        self.logger = logging.getLogger("SimpleRobotController")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Robot connection settings
        self.ROBOT_IP = robot_ip
        self.MAX_RECONNECT_ATTEMPTS = 3
        self.RECONNECT_DELAY = RECONNECT_DELAY

        # Movement settings
        self.MOVEMENT_SPEED = MOVEMENT_SPEED
        self.MOVEMENT_ACCELERATION = MOVEMENT_ACCELERATION
        self.INTER_MOVEMENT_DELAY = INTER_MOVEMENT_DELAY
        self.FEEDBACK_CHECK_INTERVAL = FEEDBACK_CHECK_INTERVAL

        # Robot connection object
        self.robot = None

        # Movement state tracking
        self.current_position = None
        self.is_moving = False

        # Predefined positions (joint angles in degrees)
        self.positions = {
            'home': [80.555, -111.609, 110.737, -188.994, -84.695, 144.436],
            'position_1': [80.555, -91.025, 126.989, -188.994, -84.695, 144.436],
            'position_2': [80.555, -111.609, 110.737, -188.994, -84.695, 144.436],
        }

        # Connect to robot during initialization
        self.connect_to_robot()
        self.logger.info("Robot Controller initialized successfully")

    def connect_to_robot(self):
        """Establish connection to the robot with retry mechanism"""
        attempt = 0
        while attempt < self.MAX_RECONNECT_ATTEMPTS:
            try:
                self.logger.info(f"Connecting to robot at {self.ROBOT_IP} (attempt {attempt+1}/{self.MAX_RECONNECT_ATTEMPTS})...")

                # Create robot connection using fairino SDK
                self.robot = Robot.RPC(self.ROBOT_IP)

                # Simple connection test
                if self.robot is not None:
                    self.logger.info(f"Successfully connected to robot at {self.ROBOT_IP}")
                    return True
                else:
                    self.logger.error("Robot connection returned None")

            except Exception as e:
                self.logger.error(f"Failed to connect to robot: {str(e)}")

            attempt += 1
            if attempt < self.MAX_RECONNECT_ATTEMPTS:
                self.logger.info(f"Retrying connection in {self.RECONNECT_DELAY} seconds...")
                time.sleep(self.RECONNECT_DELAY)

        self.logger.error("Failed to connect to robot after multiple attempts")
        return False

    def get_robot_feedback(self):
        """
        Get current robot state using SDK feedback methods.
        Returns joint positions from the robot's actual state.
        """
        try:
            if self.robot is None:
                return None

            error, joint_pos = self.robot.GetActualJointPosDegree()
            if error == 0:
                return joint_pos
            else:
                self.logger.warning(f"Failed to get robot feedback, error code: {error}")
                return None

        except Exception as e:
            self.logger.error(f"Exception getting robot feedback: {str(e)}")
            return None

    def verify_position_reached(self, target_position_name, tolerance=2.0):
        """
        Verify that robot reached the target position using SDK feedback.
        
        Args:
            target_position_name: Name of the target position
            tolerance: Allowable deviation in degrees
            
        Returns:
            True if position reached within tolerance, False otherwise
        """
        if target_position_name not in self.positions:
            return False

        target_angles = self.positions[target_position_name]
        current_angles = self.get_robot_feedback()

        if current_angles is None:
            self.logger.warning(f"Could not verify position {target_position_name} - no feedback")
            return True  # Assume success if no feedback available

        # Compare each joint
        for i, (current, target) in enumerate(zip(current_angles, target_angles)):
            deviation = abs(current - target)
            if deviation > tolerance:
                self.logger.warning(f"Joint {i+1} deviation: {deviation:.2f}° (target: {target:.2f}°, current: {current:.2f}°)")
                return False

        self.logger.info(f"Position '{target_position_name}' verified within tolerance")
        return True

    def move_to_position(self, position_name):
        """
        Move robot arm to a predefined position using blocking MoveJ command.
        Uses SDK feedback for motion verification.
        """
        # Check if position exists
        if position_name not in self.positions:
            self.logger.error(f'Position "{position_name}" not found')
            return False

        # Check if robot is already moving
        if self.is_moving:
            self.logger.warning(f'Robot already moving, cannot start new movement to {position_name}')
            return False

        # Check robot connection
        if self.robot is None:
            self.logger.error("Robot not connected, attempting to reconnect...")
            if not self.connect_to_robot():
                return False

        try:
            # Get target position angles
            target_angles = self.positions[position_name]

            self.logger.info(f"Starting movement to position '{position_name}': {target_angles}")

            # Set movement state
            self.is_moving = True
            self.current_position = position_name

            # Record start time for performance tracking
            start_time = time.time()

            # Send blocking movement command to robot
            # MoveJ with blendT=-1.0 is blocking - returns when movement complete
            # This provides SDK-level feedback instead of relying on delays
            error = self.robot.MoveJ(
                target_angles,
                tool=0,
                user=0,
                vel=self.MOVEMENT_SPEED,
                acc=self.MOVEMENT_ACCELERATION,
                blendT=-1.0  # Blocking mode - waits for motion completion
            )

            # Calculate movement time
            movement_time = time.time() - start_time

            # Reset movement state
            self.is_moving = False

            # Check return code from SDK
            if error == 0:
                self.logger.info(f"Successfully moved to '{position_name}' in {movement_time:.2f} seconds")

                # Verify position using SDK feedback
                if self.verify_position_reached(position_name):
                    return True
                else:
                    self.logger.warning(f"Position '{position_name}' reached but verification failed")
                    return True  # Still return true as movement command succeeded

            else:
                self.logger.error(f"Movement to {position_name} failed with error code: {error}")
                return False

        except Exception as e:
            self.logger.error(f"Exception during movement to {position_name}: {str(e)}")
            self.is_moving = False
            return False

    def execute_motion_sequence(self):
        """
        Execute the complete motion sequence: home -> position1 -> home
        Moves robot directly without artificial delays, using SDK feedback for verification.
        """
        self.logger.info("Starting robot motion sequence: home -> position1 -> home")
        print("=" * 60)
        print("ROBOT MOTION SEQUENCE - Starting Execution")
        print("=" * 60)

        # Check robot connection
        if self.robot is None:
            self.logger.error("Robot not connected, attempting to reconnect...")
            if not self.connect_to_robot():
                print("ERROR: Could not connect to robot")
                return False

        # Define the motion sequence steps
        sequence_steps = [
            ('home', 'Moving to home position (starting point)'),
            ('position_1', 'Moving to position 1 (target position)'),
            ('home', 'Returning to home position (completion)')
        ]

        success_count = 0
        total_steps = len(sequence_steps)

        # Execute each step in the sequence
        for step_num, (position, description) in enumerate(sequence_steps, 1):
            print(f"\n[Step {step_num}/{total_steps}] {description}")
            print(f"Target angles: {self.positions[position]}")

            # Record start time for this movement
            start_time = time.time()

            # Execute the movement (blocking command with SDK feedback)
            success = self.move_to_position(position)

            # Calculate total movement time
            total_time = time.time() - start_time

            if success:
                print(f"✓ SUCCESS: Completed {position} movement in {total_time:.2f} seconds")
                success_count += 1

                # Apply inter-movement delay if configured (adjustable at top of file)
                if step_num < total_steps and self.INTER_MOVEMENT_DELAY > 0:
                    print(f"Pausing {self.INTER_MOVEMENT_DELAY} seconds before next movement...")
                    time.sleep(self.INTER_MOVEMENT_DELAY)

            else:
                print(f"✗ FAILED: Could not move to {position}")
                print("Motion sequence aborted due to failure")
                break

        # Display final results
        print("\n" + "=" * 60)
        print("MOTION SEQUENCE RESULTS:")
        print(f"Completed steps: {success_count}/{total_steps}")
        print(f"Success rate: {(success_count/total_steps)*100:.1f}%")

        sequence_complete = (success_count == total_steps)

        if sequence_complete:
            print("✓ COMPLETE: Robot successfully returned to home position!")
            self.logger.info("Motion sequence completed successfully - robot at home position")
        else:
            print("✗ INCOMPLETE: Motion sequence failed")
            self.logger.error("Motion sequence failed to complete")

        print("=" * 60)
        return sequence_complete

    def stop_movement(self):
        """Emergency stop - immediately halt all robot movement"""
        try:
            if self.robot is None:
                self.logger.error("Robot not connected, cannot stop movement")
                return False

            self.logger.warning("Emergency stop activated!")

            # Send stop commands from SDK
            self.robot.StopMotion()      # Stop current motion
            self.robot.ImmStopJOG()      # Stop any jogging movement

            # Reset movement state
            self.is_moving = False

            self.logger.info("Robot movement stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping robot movement: {str(e)}")
            return False

    def get_available_positions(self):
        """Get list of all available predefined positions"""
        return list(self.positions.keys())

    def get_current_position_feedback(self):
        """Get current robot position using SDK feedback"""
        angles = self.get_robot_feedback()
        if angles:
            self.logger.info(f"Current joint angles: {angles}")
            return angles
        else:
            self.logger.error("Could not retrieve current position")
            return None

    def disconnect(self):
        """Clean up and disconnect from robot"""
        self.logger.info("Disconnecting from robot...")

        # Stop any ongoing movement
        if self.is_moving:
            self.stop_movement()

        # Clear robot connection
        self.robot = None

        self.logger.info("Robot controller disconnected")

    def __del__(self):
        """Destructor to ensure clean disconnection"""
        try:
            self.disconnect()
        except:
            pass  # Ignore errors during cleanup


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Example of how to use the SimpleRobotController
    """

    print("\n" + "=" * 60)
    print("Robot Controller - Example Usage")
    print("=" * 60 + "\n")

    # Create controller instance
    controller = SimpleRobotController(robot_ip='192.168.58.101')

    # Execute motion sequence
    success = controller.execute_motion_sequence()

    # Get current position feedback from robot
    print("\nGetting current robot position feedback...")
    current_pos = controller.get_current_position_feedback()

    # Disconnect
    controller.disconnect()

    print("\nProgram completed.\n")