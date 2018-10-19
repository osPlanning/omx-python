from setuptools import setup, find_packages

# To push to PyPi/pip, use
# python setup.py sdist bdist_wheel upload

setup(
    name='OpenMatrix',
    keywords='openmatrix omx',
    version='0.3.4.1',
    author='Billy Charlton, Ben Stabler',
    author_email='billy@okbecause.com, benstabler@yahoo.com',
    packages=find_packages(),
    url='https://github.com/osPlanning/omx',
    license='Apache',
    description='OMX, the open matrix data format',
    long_description=open('README.txt').read(),
    install_requires=[
        "tables >= 3.1.0",
        "numpy >= 1.5.0",
    ],
    classifiers=[
        'License :: OSI Approved :: Apache Software License'
    ]
)
