import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NanoController",
    version="0.0.1",
    author="Scorch / Tatarize",
    author_email="tatarize@gmail.com",
    description="Embroidery IO library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EmbroidePy/pyembroidery",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ),
)