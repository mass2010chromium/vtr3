import os
import os.path as osp

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch import LaunchDescription
from launch.conditions import LaunchConfigurationEquals, LaunchConfigurationNotEquals
from launch_ros.actions import Node


def generate_launch_description():
    # config directory
    config_dir = osp.join(os.getenv('VTRSRC'), 'config')
    # temp directory
    temp_dir = os.getenv('VTRTEMP')

    commonNodeArgs = {
        "package": 'vtr_navigation',
        "namespace": 'vtr',
        "executable": 'vtr_navigation',
        "output": 'screen',
        #"prefix": 'xterm -e gdb -ex run --args',
        #"prefix": 'valgrind --tool=callgrind',
    }

    return LaunchDescription([
        #DeclareLaunchArgument('override_params', default_value='', description='scenario specific parameter overrides'),
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            output="screen",
            arguments=[
                "/world/larger_world/model/quadcopter/link/camera_link/sensor/camera_front/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
                "/world/larger_world/model/quadcopter/link/camera_link/sensor/camera_front/image@sensor_msgs/msg/Image[ignition.msgs.Image",
                #"/left_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
                #"/right_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU",
                "/model/quadcopter/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/model/quadcopter/pose_static@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/quadcopter/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist"
            ],
            remappings=[
                # (from (internal), to (external))
                ("/world/larger_world/model/quadcopter/link/camera_link/sensor/camera_front/points", "/temp/laser_points"),
                ("/world/larger_world/model/quadcopter/link/camera_link/sensor/camera_front/image", "/camera_image"),
                ("/model/quadcopter/pose", "/tf"),
                ("/model/quadcopter/pose_static", "/temp/tf_static"),
                #("/model/vehicle_blue/tf", "/tf"),
                #("/world/visualize_lidar_world/dynamic_pose/info", "/tf"),
                #("/world/visualize_lidar_world/pose/info", "/temp/tf_static"),
                ("/quadcopter/cmd_vel", "/cmd_vel")
            ]
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="screen",
            arguments=[
                *"0 0 0 0 0 0".split(),
                "/world",
                "/quadcopter/odom"
            ]
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="screen",
            arguments=[
                *"0 0 0 0 0 0".split(),
                "/quadcopter",
                "/robot"
            ]
        ),
        Node(
            package="vtr_simulation",
            executable="tf_qos_relay",
            output="screen",
            parameters=[
                {
                    'input_topic': "/temp/tf_static",
                    'output_topic': "/tf_static",
                }
            ]
        ),
        Node(
            package="topic_tools",
            executable="transform",
            output="screen",
            arguments=[
                "/temp/laser_points", "/laser_points",
                "sensor_msgs/msg/PointCloud2",
                #'sensor_msgs.msg.PointCloud2(header=std_msgs.msg.Header(stamp=m.header.stamp, frame_id="vehicle_blue/lidar_link"), height=m.height, width=m.width, fields=m.fields, is_bigendian=m.is_bigendian, point_step=m.point_step, row_step=m.row_step, data=m.data, is_dense=m.is_dense)',
                'sensor_msgs.msg.PointCloud2(header=std_msgs.msg.Header(stamp=m.header.stamp, frame_id="quadcopter/camera_link"), \
                    height=m.height, width=m.width, fields=m.fields+[ \
                        sensor_msgs.msg.PointField(name="t", offset=m.point_step, datatype=7, count=1), \
                        sensor_msgs.msg.PointField(name="intensity", offset=m.point_step, datatype=7, count=1), \
                    ], \
                    is_bigendian=m.is_bigendian, point_step=m.point_step+8, row_step=m.row_step+8*m.width, \
                    data=numpy.concatenate([ \
                        numpy.array(m.data).reshape((m.width*m.height, m.point_step)), \
                        numpy.array(list(numpy.zeros(m.width*m.height*2, dtype=numpy.float32).tobytes()), dtype=numpy.uint8).reshape((m.width*m.height, 8)) \
                    ], axis=1).flatten(), is_dense=m.is_dense)',
                "--import", "sensor_msgs", "std_msgs", "numpy"
            ]
        )
    ])
