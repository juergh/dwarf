import setuptools

setuptools.setup(
    name='python-dwarf',
    version='0.0.1',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    scripts=['bin/dwarf'],
)
