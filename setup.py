from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
)
