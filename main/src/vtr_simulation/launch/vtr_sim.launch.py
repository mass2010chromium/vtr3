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
                "/lidar2@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
                "/lidar2/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
                "/left_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/right_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
                "/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU",
                "/model/vehicle_blue/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/model/vehicle_blue/pose_static@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                #"/model/vehicle_blue/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                #"/world/visualize_lidar_world/dynamic_pose/info@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                #"/world/visualize_lidar_world/pose/info@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                "/model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist"
            ],
            remappings=[
                # (from (internal), to (external))
                ("/lidar2", "/temp/laserscan"),
	            ("/lidar2/points", "/temp/laser_points"),
                ("/model/vehicle_blue/pose", "/tf"),
                ("/model/vehicle_blue/pose_static", "/temp/tf_static"),
                #("/model/vehicle_blue/tf", "/tf"),
                #("/world/visualize_lidar_world/dynamic_pose/info", "/tf"),
                #("/world/visualize_lidar_world/pose/info", "/temp/tf_static"),
                ("/model/vehicle_blue/cmd_vel", "/cmd_vel")
            ]
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="screen",
            arguments=[
                *"0 0 0 0 0 0".split(),
                "/world",
                "/vehicle_blue/odom"
            ]
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="screen",
            arguments=[
                *"0 0 0 0 0 0".split(),
                "/vehicle_blue",
                "/robot"
            ]
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="screen",
            arguments=[
                *"0 0 0 0 0 0".split(),
                "/vehicle_blue/lidar_link",
                "/lidar"
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
                "/temp/laserscan", "/laserscan",
                "sensor_msgs/msg/LaserScan",
                'sensor_msgs.msg.LaserScan(header=std_msgs.msg.Header(stamp=m.header.stamp, frame_id="vehicle_blue/lidar_link"), angle_min=m.angle_min, angle_max=m.angle_max, angle_increment=m.angle_increment, time_increment=m.time_increment, scan_time=m.scan_time, range_min=m.range_min, range_max=m.range_max, ranges=m.ranges, intensities=m.intensities)',
                "--import", "sensor_msgs", "std_msgs"
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
                'sensor_msgs.msg.PointCloud2(header=std_msgs.msg.Header(stamp=m.header.stamp, frame_id="vehicle_blue/lidar_link"), \
                    height=m.height, width=m.width, fields=m.fields+[sensor_msgs.msg.PointField(name="t", offset=m.point_step, datatype=7, count=1)], \
                    is_bigendian=m.is_bigendian, point_step=m.point_step+4, row_step=m.row_step+4*m.width, \
                    data=numpy.concatenate([ \
                        numpy.array(m.data).reshape((m.width*m.height, m.point_step)), \
                        numpy.array(list(numpy.zeros(m.width*m.height, dtype=numpy.float32).tobytes()), dtype=numpy.uint8).reshape((m.width*m.height, 4)) \
                    ], axis=1).flatten(), is_dense=m.is_dense)',
                "--import", "sensor_msgs", "std_msgs", "numpy"
            ]
        )
    ])
