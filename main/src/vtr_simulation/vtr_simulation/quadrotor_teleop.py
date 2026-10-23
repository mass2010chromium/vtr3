#!/usr/bin/env python3

# Copyright (c) 2011, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Willow Garage, Inc. nor the names of its
#      contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, Vector3

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

import sys, select, termios, tty

msg = """
Control Your Turtlebot!
---------------------------
Moving around:
u    i    o
j    k    l
m    ,    .

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%
r/v : increase/decrease hover height by 0.1m
space key, k : force stop
anything else : stop smoothly

CTRL-C to quit
"""

moveBindings = {
    'i':(1,0),
    'o':(1,-1),
    'j':(0,1),
    'l':(0,-1),
    'u':(1,1),
    ',':(-1,0),
    '.':(-1,1),
    'm':(-1,-1),
}

speedBindings={
    'q':(1.1,1.1),
    'z':(.9,.9),
    'w':(1.1,1),
    'x':(.9,1),
    'e':(1,1.1),
    'c':(1,.9),
}

hoverBindings={
    'r':(0.1),
    'v':(-0.1)
}

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


if __name__=="__main__":

    speed = .2
    turn = 1
    target_height = 1.0

    def vels(speed,turn):
        return "currently:\tspeed %s\tturn %s " % (speed,turn)

    cmd_topic = '/cmd_vel'
    base_frame = 'larger_world'
    quadrotor_frame = 'quadcopter/base_link'
    tolerance = 1e-3
    if len(sys.argv) > 1:
        cmd_topic = sys.argv[1]

    class TeleopNode(Node):
        def __init__(self, command_topic='/cmd_vel',
                     base_frame='world', quadrotor_frame='quadcopter/base_link',
                     target_height=1.0, tolerance=1e-3
        ):
            super().__init__('base_teleop')
            self.cmd_pub = self.create_publisher(Twist, cmd_topic, 10)
            self.quadrotor_frame = quadrotor_frame
            self.base_frame = base_frame

            self.tf_buffer = Buffer()
            self.tf_listener = TransformListener(self.tf_buffer, self)
            self.cmd_pub = self.create_publisher(
                Twist, 
                command_topic, 
                1
            )
            self.target_height = target_height
            self.tolerance = tolerance
            self.get_logger().info(
                f"Moving quadrotor to {self.target_height} (on {command_topic})"
            )

        def control_loop(self, target_vx, target_vtheta):
            try:
                transform = self.tf_buffer.lookup_transform(self.base_frame, self.quadrotor_frame, rclpy.time.Time()).transform
            except TransformException:
                self.get_logger().info("tf lookup error")
                return
            dz = self.target_height - transform.translation.z
            #self.get_logger().info(f"Target: {self.target_height:.3f} | Current: {transform.translation.z:.3f} | Err: {dz:.3f}")
            if abs(dz) < self.tolerance:
                dz=0
            out_msg = Twist(
                linear=Vector3(x=float(target_vx), z=float(dz)),
                angular=Vector3(z=float(target_vtheta))
            )
            self.cmd_pub.publish(out_msg)

    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()

    teleop_node = TeleopNode(
        command_topic=cmd_topic,
        base_frame=base_frame,
        quadrotor_frame=quadrotor_frame,
        target_height=target_height,
        tolerance=tolerance
    )

    x = 0.0
    th = 0.0
    status = 0
    count = 0
    target_speed = 0.0
    target_turn = 0.0
    control_speed = 0.0
    control_turn = 0.0
    try:
        print(msg)
        print(vels(speed,turn))
        while(1):
            key = getKey()
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                th = moveBindings[key][1]
                count = 0
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]
                count = 0

                print(vels(speed,turn))
                if (status == 14):
                    print(msg)
                status = (status + 1) % 15
            elif key in hoverBindings.keys():
                teleop_node.target_height += hoverBindings[key]
                print(teleop_node.target_height)
                if (status == 14):
                    print(msg)
                status = (status + 1) % 15
            elif key == ' ' or key == 'k' :
                x = 0.0
                th = 0.0
                control_speed = 0.0
                control_turn = 0.0
            else:
                count = count + 1
                if count > 4:
                    x = 0.0
                    th = 0.0
                if (key == '\x03'):
                    break

            target_speed = speed * x
            target_turn = turn * th

            if target_speed > control_speed:
                control_speed = min( target_speed, control_speed + 0.02 )
            elif target_speed < control_speed:
                control_speed = max( target_speed, control_speed - 0.02 )
            else:
                control_speed = target_speed

            if target_turn > control_turn:
                control_turn = min( target_turn, control_turn + 0.1 )
            elif target_turn < control_turn:
                control_turn = max( target_turn, control_turn - 0.1 )
            else:
                control_turn = target_turn

            twist = Twist()
            teleop_node.control_loop(control_speed, control_turn)

            #print("loop: {0}".format(count))
            #print("target: vx: {0}, wz: {1}".format(target_speed, target_turn))
            #print("published: vx: {0}, wz: {1}".format(twist.linear.x, twist.angular.z))
            for i in range(50):
                rclpy.spin_once(teleop_node, timeout_sec=0.001)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)

    finally:
        twist = Twist()
        twist.linear.x = 0.0; twist.linear.y = 0.0; twist.linear.z = 0.0
        twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = 0.0
        teleop_node.cmd_pub.publish(twist)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

