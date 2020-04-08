import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="koebepy-pkg-johncbowers", # Replace with your own username
    version="0.0.1",
    author="John C. Bowers",
    author_email="bowersjc@jmu.edu",
    description="A package for explorations in discrete geometry. ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johncbowers/koebepy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
