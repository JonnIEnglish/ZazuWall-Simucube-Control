from setuptools import setup, find_packages

setup(
    name="zazuwall_control",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "smbus2>=0.4.2",
        "gpiod>=1.5.3",
    ],
    entry_points={
        'console_scripts': [
            'zazuwall=python.core.main:main',
            'zazuwall-torque=python.core.torque_speed:main',
        ],
    },
    python_requires=">=3.6",
    description="ZazuWall Simucube Control System",
    author="Jonno",
    author_email="",
    url="https://github.com/jonno/ZazuWall-Simucube-Control",
)