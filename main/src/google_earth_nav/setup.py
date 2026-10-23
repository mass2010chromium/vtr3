from glob import glob
import os
from setuptools import find_packages, setup

package_name = 'google_earth_nav'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (f'share/{package_name}/config',
            glob(os.path.join('config', '*.yaml'))),
        (f'share/{package_name}/maps',
            glob(os.path.join('maps', '*.kml'))),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hppeng',
    maintainer_email='hppeng@todo.todo',
    description='Navigation from google earth waypoints',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'print_location = google_earth_nav.print_location:main'
        ],
    },
)
