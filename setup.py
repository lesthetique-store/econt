from setuptools import setup, find_packages

setup(
    name="econt",
    version="1.0.0",
    author="Dmitry Kalinin",
    packages=["econt"],
    url="https://github.com/lesthetique-store/econt",
    install_requires=[
        "requests",
        "dicttoxml",
        "xmltodict",
        "nested_lookup"
    ],
)
