from glob import glob
from posixpath import basename, splitext
from setuptools import setup
from setuptools import find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name="library",
    version="0.1.0",
    license="MIT",
    description="Common Library for ECoMan",
    author="Tomoyuki KOYAMA",
    url="https://github.com/cdsl-research/ecoman",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    install_requires=_requires_from_file('requirements.txt'),
)
