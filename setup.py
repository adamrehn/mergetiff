from setuptools import setup

setup(
	name='mergetiff',
	version='0.0.15',
	description='Library and command-line tool to merge GeoTiff files using GDAL',
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Environment :: Console'
	],
	keywords='gdal geotiff',
	url='http://github.com/adamrehn/mergetiff',
	author='Adam Rehn',
	author_email='adam@adamrehn.com',
	license='MIT',
	packages=['mergetiff'],
	zip_safe=True,
	install_requires = [
		'GDAL>=2',
		'numpy'
	],
	entry_points = {
		'console_scripts': ['mergetiff=mergetiff.cli:main']
	}
)
