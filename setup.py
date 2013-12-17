from setuptools import setup, find_packages

setup(
    name='dwarf',
    version='0.1.0',
    summary='OpenStack API on top of libvirt/kvm',
    author='Juerg Haefliger <juergh@gmail.com>',

    packages=find_packages(exclude=['tests']),
    package_data={
        '': ['*.template'],
    },
    scripts=['bin/dwarf', 'bin/dwarf-manage'],
)
