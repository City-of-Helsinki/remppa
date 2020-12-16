import pathlib
import pkg_resources
from setuptools import setup, find_packages


with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name="yolov5",
    install_requires=install_requires,
    packages=find_packages(include=["models", "utils", "utils.*"]),
)
