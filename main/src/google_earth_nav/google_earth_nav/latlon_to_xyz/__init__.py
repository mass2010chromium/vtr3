from numpy import radians, sin, cos, sqrt
import numpy as np

# Taken from blosm. Ellipsoid model of the earth as elevation zero.
_radii = _wgs84Radii = (
    6378137.0,
    6378137.0,
    6356752.3142451793
)
_radiiSquared = _wgs84RadiiSquared = (
    _radii[0] * _radii[0],
    _radii[1] * _radii[1],
    _radii[2] * _radii[2]
)

def latlon_to_ECEF(latitude_degrees: float | np.ndarray,
                    longitude_degrees: float | np.ndarray,
                    height: float | np.ndarray):
    """
    Convert coordinates in latlong to earth centered, earth fixed coordinate system.

    latitude/longitude are standard, in degrees.
    height is offset from "zero" surface (WGS 84) in meters.
    Inputs can be floats or numpy arrays.

    See: https://en.wikipedia.org/wiki/Geographic_coordinate_conversion#From_geodetic_to_ECEF_coordinates

    Return: if inputs are floats, np.array of X, Y, Z.
            if inputs are N-d arrays, 3xN array, where rows are X, Y, Z.
    """

    lat = radians(latitude_degrees)
    lon = radians(longitude_degrees)

    cos_lat = cos(lat)
    sin_lat = sin(lat)
    N = _radii[0]**2 / sqrt((_radii[0] * cos_lat)**2 + (_radii[2]*sin_lat)**2)
    return np.array([
        (N + height)*cos_lat*cos(lon),
        (N + height)*cos_lat*sin(lon),
        ((_radii[2]**2 / (_radii[0]**2)) * N + height) * sin_lat
    ])

class LatLonTangentConverter:

    def __init__(self, center_lat_degrees, center_lon_degrees, center_height=0):
        """
        Record a geodetic position in ECEF, and convert other geodetic
        positions to be relative to a coordinate frame whose origin is at
        this position, X ccw along lines of latitude, Z up and Y towards the north pole.

        Not actually "tangent" but more like "locally valid"

        Arguments expected in degrees. (center height in meters)
        """
        center_lat = radians(center_lat_degrees)
        center_lon = radians(center_lon_degrees)
        center_coord = latlon_to_ECEF(center_lat_degrees, center_lon_degrees, 0)
        

        # X along lines of latitude (CCW)
        # Y towards north pole
        # Z up
        local_basis = np.array([
            [-sin(center_lon), cos(center_lon), 0],
            [
                -sin(center_lat)*cos(center_lon),
                -sin(center_lat)*sin(center_lon),
                cos(center_lat),
            ],
            [
                cos(center_lat)*cos(center_lon),
                cos(center_lat)*sin(center_lon),
                sin(center_lat)
            ]
        ]).T    # Row definitions are easier on my brain, but we like column matrices
        self.local_frame = np.zeros((4, 4))
        self.local_frame[:3, :3] = local_basis
        # Z offset allowed
        self.local_frame[:3, 3] = center_coord + center_height * local_basis[:, 2]
        self.local_frame[3, 3] = 1
        self.local_frame_inv = np.linalg.inv(self.local_frame)

    def latlon_to_xyz_tangent(self,
                              latitude_degrees: float | np.ndarray,
                              longitude_degrees: float | np.ndarray,
                              height: float | np.ndarray):
        """
        Convert coordinates in latlong to ECEF but relative to this object's origin frame.

        latitude/longitude are standard, in degrees.
        height is offset from "zero" surface (WGS 84) in meters.
        Inputs can be floats or numpy arrays.

        Return: if inputs are floats, np.array of X, Y, Z.
                if inputs are N-d arrays, 3xN array, where rows are X, Y, Z.
        """
        coords_ECEF = latlon_to_ECEF(latitude_degrees, longitude_degrees, height)

        return self.local_frame_inv[:3, :3] @ coords_ECEF + self.local_frame_inv[:3, 3]




if __name__ == "__main__":
    cases = [
        (57, 34, 135),
        (61, 215, 9)
    ]
    print("Expect: [2886.761, 1947.145, 5326.013]")
    print(latlon_to_ECEF(*cases[0]) / 1000)
    print("Expect: [-2539.482, -1778.164, 5555.35]")
    print(latlon_to_ECEF(*cases[1]) / 1000)

    print("Expect: match above")
    print(latlon_to_ECEF(*np.array(cases).T).T / 1000)

    print()
    center_coord = (33.77499961853027, -84.39999771118164, 316)
    converter = LatLonTangentConverter(*center_coord)
    
    targets = np.array([
        (33.775324, -84.397959, 286.88),
        (33.776912, -84.401044, 295.94),
        (33.777196, -84.389882, 294.58)
    ])
    descs = [
        "due east",
        "northwest",
        "far east-north"
    ]

    print(converter.latlon_to_xyz_tangent(*center_coord))
    for desc, target in zip(descs, targets):
        print(desc)
        print(converter.latlon_to_xyz_tangent(*target))
    print(converter.latlon_to_xyz_tangent(*targets.T).T)
