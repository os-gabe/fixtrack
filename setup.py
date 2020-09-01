import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.read()

# # Legal keyword arguments for the setup() function
# setup_keywords = ('distclass', 'script_name', 'script_args', 'options',
#                   'name', 'version', 'author', 'author_email',
#                   'maintainer', 'maintainer_email', 'url', 'license',
#                   'description', 'long_description', 'keywords',
#                   'platforms', 'classifiers', 'download_url',
#                   'requires', 'provides', 'obsoletes',
#                   )

# # Legal keyword arguments for the Extension constructor
# extension_keywords = ('name', 'sources', 'include_dirs',
#                       'define_macros', 'undef_macros',
#                       'library_dirs', 'libraries', 'runtime_library_dirs',
#                       'extra_objects', 'extra_compile_args', 'extra_link_args',
#                       'swig_opts', 'export_symbols', 'depends', 'language')

setuptools.setup(
    name="fixtrack",  # Replace with your own username
    version="0.1",
    author="Gabriel Hein",
    author_email="heingab@gmail.com",
    description="A python package for working with fish tracks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/os-gabe/fixtrack",
    # packages=["fixtrack"],  # setuptools.find_packages(),
    # package_dir={"": "fixtrack"},
    packages=setuptools.find_packages(),
    scripts=["scripts/fixtrack_app.py"],
    # classifiers=[
    #     "Programming Language :: Python :: 3",
    #     "License :: OSI Approved :: MIT License",
    #     "Operating System :: OS Independent",
    # ],
    package_data={
        'fixtrack': ['frontend/icons/*.svg'],
    },
    install_requires=install_requires,
    python_requires='>=3.6',
)
