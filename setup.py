# -*- coding: utf-8 -*-

import setuptools

import tmate

with open('README.md', 'rb') as fp:
    README = fp.read().decode()


with open('requirements.txt') as fp:
    text = fp.read()
    REQUIREMENTS = text.split('\n')


def find_packages():
    packages = []
    for pkg in setuptools.find_packages():
        if not pkg.startswith('test'):
            print(pkg)
            packages.append(pkg)
    return packages


setuptools.setup(
    author="drunkdream",
    author_email="drunkdream@qq.com",
    name='tmate',
    license="MIT",
    description='tmate implemented by python.',
    version=tmate.VERSION,
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/drunkdream/pytmate',
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    classifiers=[
        # Trove classifiers
        # (https://pypi.python.org/pypi?%3Aaction=list_classifiers)
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'tmate = tmate.__main__:main',
        ],
    }
)
