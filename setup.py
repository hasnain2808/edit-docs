# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in edit_docs/__init__.py
from edit_docs import __version__ as version

setup(
	name='edit_docs',
	version=version,
	description='Edit Documentation from your browser.',
	author='Frappe',
	author_email='developers@erpnext.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
