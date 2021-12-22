__author__ = 'hhslepicka'
import setuptools
import versioneer
import os

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
    packages=setuptools.find_packages(),
    package_data={'conftrak': ['schemas/*.json']},
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
    ],
)
