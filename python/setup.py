from setuptools import setup, find_packages

setup(
    name='explain',
    version='0.2',
    author='Windhover Labs',
    author_email='evanderwerf@windhoverlabs.com',
    description='Generate structure mapping files for parsing Airliner logs.',
    url='windhoverlabs.com',
    license='3BSD-3-Clause',
    packages=find_packages(),
    install_requires=[
        'pyelftools'
    ],
    entry_points={
        'console_scripts': [
            'elf_reader = explain.elf_reader:main',
            'explain = explain.__main__:main'
        ]
    }
)
