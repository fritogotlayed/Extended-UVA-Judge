#!/usr/bin/env python

from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages

install_reqs = [str(ir.req) for ir in
                parse_requirements('requirements.txt', session=PipSession())]

setup(
    name='extended_uva_judge',
    author="Frito",
    description='Alternate UVa Judge',
    url='https://github.com/fritogotlayed/Extended-UVA-Judge',
    version='0.0.1',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    package_data={
        'extended_uva_judge': ['config.yml']
    },
    package_dir={'extended_uva_judge': 'extended_uva_judge'},
    install_requires=install_reqs,
    entry_points={
        'console_scripts': [
            'extended-uva-judge-server = extended_uva_judge.server:main'
        ]
    }
)
