import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="compliance-io",
    version="0.0.1",
    author="Tom Wood",
    author_email="tom.wood@civicactions.com",
    description="Tools for read/writing Compliance as Code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/woodt/compliance-io",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pydantic",
        "click",
        "rtyaml",
        "python-slugify",
        "blinker",
        "pyyaml",
    ],
    python_requires=">=3.6",
)
