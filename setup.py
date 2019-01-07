import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="k40nano",
    version="0.1.0",
    install_requires=[
        "pyusb"
    ],
    author="Scorch / Tatarize",
    author_email="tatarize@gmail.com",
    description="Low Level K40 Control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/K40Nano/K40Nano",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ),
)