import setuptools

setuptools.setup(
    name='dwarf',
    version='0.0.1',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    scripts=['bin/dwarf'],
)
