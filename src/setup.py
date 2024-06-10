# Copyright © 2024 the OAI-5G Core SDK Authors

# Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# Contact: netsoft@eurecom.fr
# coding: utf-8

from setuptools import setup, find_packages

NAME = "oai5gc"
VERSION = "0.0.1"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

requirements = [
    'Python3==3.10.12',
    'pip==22.0.2',	
    'attrs==21.4.0', 
    'Werkzeug==2.0.0', 
    'zipp==3.6.0',
    'PyYAML==6.0',
    'flask==2.0.3',
    'docker==7.0.0',
    'pymongo==4.6.1',
    'psutil==5.9.0'
]

# #Relative path issue in alpine
# with open("../requirements.txt") as requirement_file:
#     requirements = requirement_file.read().split()

setup(
    name=NAME,
    version=VERSION,
    description="OAI 5G Core SDK",
    author_email="netsoft@eurecom.fr",
    url="",
    keywords=["SDK", "5G"],
    install_requires=requirements,
    packages=find_packages(),
    #package_data={'': ['swagger/swagger.yaml']},
    #include_package_data=True,
    entry_points={
        'console_scripts': ['oai5gc-cli=main.oai5gc:main']},
    long_description="""\
    OAI 5G Core SDK bla bla
    """
)

