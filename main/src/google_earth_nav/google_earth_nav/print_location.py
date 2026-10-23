"""
Reading a google earth KML file, print out if we are within <tolerance> meters of any waypoint.
"""
from geometry_msgs.msg import Twist, Vector3

import rclpy
from rclpy.node import Node

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

from ament_index_python import get_package_share_directory

from google_earth_nav.latlon_to_xyz import LatLonTangentConverter

import os
import yaml
import xml.etree.ElementTree as ET

import numpy as np

# Thanks gemini
def parse_kml_waypoints(kml_string):
    root = ET.fromstring(kml_string)

    # KML files use a default namespace which must be mapped for ElementTree to find the tags
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    waypoints = []

    # Iterate through all Placemark elements in the document
    for placemark in root.findall('.//kml:Placemark', ns):
        name_elem = placemark.find('kml:name', ns)
        coords_elem = placemark.find('.//kml:Point/kml:coordinates', ns)

        if name_elem is not None and coords_elem is not None:
            waypoints.append({
                'id': placemark.attrib.get('id'),
                'name': name_elem.text,
                'geodetic_coordinate': np.array([
					float(x) for x in coords_elem.text.strip().split(',')
				])
            })
            
    return waypoints


class WhereAmI(Node):
    def __init__(self):
        super().__init__('google_earth_position')
        
        # Declare parameters for easy reusability
        self.declare_parameter('config', "config/gt_campus.yaml")

        root_dir = get_package_share_directory("google_earth_nav")
        config_file = self.get_parameter('config').get_parameter_value().string_value
        print(f"Config: {config_file}")
        with open(os.path.join(root_dir, config_file)) as _config:
            self.config = yaml.safe_load(_config)

        self.tolerance = self.config['tolerance']
        self.quadrotor_frame = self.config['robot']['frame']
        self.base_frame = self.config['map']['frame']
        self.origin = self.config['map']['origin']
        map_file = self.config['map']['file']
        with open(os.path.join(root_dir, map_file)) as _map:
            self.waypoints = parse_kml_waypoints(_map.read())

        coordinate_converter = LatLonTangentConverter(*self.origin)
        for waypoint in self.waypoints:
            # NOTE: they are saved (lon, lat, height)
            waypoint['xyz'] = coordinate_converter.latlon_to_xyz_tangent(
                waypoint['geodetic_coordinate'][1],
                waypoint['geodetic_coordinate'][0],
                waypoint['geodetic_coordinate'][2]
            )

        print(f"Loaded {len(self.waypoints)} waypoints.")

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def control_loop(self):
        try:
            transform = self.tf_buffer.lookup_transform(self.base_frame, self.quadrotor_frame, rclpy.time.Time()).transform
        except TransformException:
            self.get_logger().info("tf lookup error")
            return

        v = transform.translation
        pos = np.array([v.x, v.y, v.z])
        closest_dist = np.inf
        closest = None
        logged = False
        for waypoint in self.waypoints:
            distance = np.linalg.norm((waypoint['xyz'] - pos)[:2])
            if distance < self.tolerance:
                self.get_logger().info(f"Nearby: {waypoint['name']} ({pos} -> {waypoint['xyz']})")
                logged = True
            if distance < closest_dist:
                closest_dist = distance
                closest = waypoint
        if not logged:
            self.get_logger().info(f"closest: {closest['name']} ({pos} -> {closest['xyz']})")


def main(args=None):
    rclpy.init(args=args)
    node = WhereAmI()
    
    try:
        while True:
            for i in range(50):
                rclpy.spin_once(node, timeout_sec=0.02)
            node.control_loop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
