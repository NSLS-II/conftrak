__author__ = 'hhslepicka'
import setuptools
import versioneer
import os
import sys

# NOTE: This file must remain Python 2 compatible for the foreseeable future,
# to ensure that we error out properly for people with outdated setuptools
# and/or pip.
min_version = (3, 6)
if sys.version_info < min_version:
    error = """
mxtools does not support Python {0}.{1}.
Python {2}.{3} and above is required. Check your Python version like so:

python3 --version

This may be due to an out-of-date pip. Make sure you have pip >= 9.0.1.
Upgrade pip like so:

pip install --upgrade pip
""".format(
        *(sys.version_info[:2] + min_version)
    )
    sys.exit(error)

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open(os.path.join(here, "requirements.txt")) as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [line for line in requirements_file.read().splitlines() if not line.startswith("#")]

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name='conftrak',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Beamline and General Configurations Tracker and Storage",
    long_description=readme,
    install_requires=requirements,
    license="BSD 3-Clause",
    url="https://github.com/hhslepicka/conftrak.git",
    python_requires=">={}".format(".".join(str(n) for n in min_version)),
    packages=setuptools.find_packages(),
    package_data={'conftrak': ['schemas/*.json']},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
    ],
    entry_points={"console_scripts": ["conftrak_startup = startup:main"]},
)
