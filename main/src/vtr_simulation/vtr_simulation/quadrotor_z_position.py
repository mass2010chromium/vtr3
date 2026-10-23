"""
Control quadrotor to specified height
"""
from geometry_msgs.msg import Twist, Vector3

import rclpy
from rclpy.node import Node

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

class PositionControl(Node):
    def __init__(self):
        super().__init__('quadrotor_z_setter')
        
        # Declare parameters for easy reusability
        self.declare_parameter('target_height', 1.0)
        self.declare_parameter('tolerance', 1e-3)
        self.declare_parameter('command_topic', '/cmd_vel')
        self.declare_parameter('quadrotor_frame', 'quadcopter/base_link')
        self.declare_parameter('base_frame', 'quadcopter_world')
        
        self.target_height = self.get_parameter('target_height').get_parameter_value().double_value
        self.tolerance = self.get_parameter('tolerance').get_parameter_value().double_value
        command_topic = self.get_parameter('command_topic').get_parameter_value().string_value
        self.quadrotor_frame = self.get_parameter('quadrotor_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.cmd_pub = self.create_publisher(
            Twist, 
            command_topic, 
            1
        )
        self.get_logger().info(
            f"Moving quadrotor to {self.target_height} (on {command_topic})"
        )
        self.done = False

    def control_loop(self):
        try:
            transform = self.tf_buffer.lookup_transform(self.base_frame, self.quadrotor_frame, rclpy.time.Time()).transform
        except TransformException:
            self.get_logger().info("tf lookup error")
            return
        dz = self.target_height - transform.translation.z
        self.get_logger().info(f"Target: {self.target_height:.3f} | Current: {transform.translation.z:.3f} | Err: {dz:.3f}")
        if abs(dz) < self.tolerance:
            self.cmd_pub.publish(Twist())
            self.done = True
        else:
            out_msg = Twist(
                linear=Vector3(z=dz)
            )
            self.cmd_pub.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    position_controller = PositionControl()
    
    try:
        while not position_controller.done:
            for i in range(50):
                rclpy.spin_once(position_controller, timeout_sec=0.001)
            position_controller.control_loop()
    except KeyboardInterrupt:
        pass
    finally:
        position_controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
