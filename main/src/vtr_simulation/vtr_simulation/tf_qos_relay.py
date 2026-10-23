"""
Relay the tf_static topic with different QOS. Thanks ros

Written by gemini
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage

class TfQosRelay(Node):
    def __init__(self):
        super().__init__('tf_qos_relay')
        
        # Declare parameters for easy reusability
        self.declare_parameter('input_topic', '/tf_bridged')
        self.declare_parameter('output_topic', '/tf_static')
        
        input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        # 1. Define the incoming QoS (must be compatible with the Gazebo bridge output)
        # Volatile durability is typical for bridged topics without overrides
        incoming_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        # 2. Define the outgoing QoS (Standard for /tf_static is Transient Local)
        # If republishing standard /tf, change DurabilityPolicy to VOLATILE
        outgoing_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL 
        )

        # Create Publisher with the new QoS
        self.publisher_ = self.create_publisher(
            TFMessage, 
            output_topic, 
            outgoing_qos
        )

        # Create Subscriber to the bridged topic
        self.subscription = self.create_subscription(
            TFMessage,
            input_topic,
            self.listener_callback,
            incoming_qos
        )

        self.get_logger().info(
            f"Relaying TF messages from {input_topic} (Volatile) to {output_topic} (Transient Local)"
        )

    def listener_callback(self, msg):
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    tf_qos_relay = TfQosRelay()
    
    try:
        rclpy.spin(tf_qos_relay)
    except KeyboardInterrupt:
        pass
    finally:
        tf_qos_relay.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
