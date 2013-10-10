from setuptools import setup, find_packages

setup(
    name='dwarf',
    version='0.0.1',
    summary='OpenStack API on top of libvirt/kvm',
    author='Juerg Haefliger <juergh@gmail.com>',

    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        '': ['*.template'],
    },
    scripts=['bin/dwarf', 'bin/dwarf-manage'],
)
