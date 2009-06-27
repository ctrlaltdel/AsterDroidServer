from setuptools import setup, find_packages
setup(
    name = "AsterDroidServer",
    version = "0.1",
    packages = find_packages(),
    install_requires = ['twisted'],
    test_suite = 'tests',
)
