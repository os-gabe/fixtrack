import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.read()

setuptools.setup(
    name="fixtrack",
    version="0.3",
    author="Gabriel Hein",
    author_email="heingab@gmail.com",
    description="A python package for working with fish tracks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/os-gabe/fixtrack",
    packages=setuptools.find_packages(),
    scripts=["scripts/fixtrack_app.py"],
    package_data={
        'fixtrack': ['frontend/icons/*.svg'],
    },
    install_requires=install_requires,
    python_requires='>=3.6',
)
