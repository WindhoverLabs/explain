from setuptools import setup, find_packages

setup(
    name='explain',
    version='0.1',
    author='Windhover Labs',
    description='Generate structure mapping files for parsing Airliner logs.',
    url='windhoverlabs.com',
    license='3BSD-3-Clause',
    packages=find_packages(),
    install_requires=[
        'pyelftools'
    ]
)