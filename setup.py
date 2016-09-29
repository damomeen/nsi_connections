from setuptools import setup, find_packages

setup(name='nsi_connections',
      version='0.1',
      author='Damian Parniewicz',
      author_email='damian.parniewicz@gmail.com',
      package_dir = {'nsi_connections': 'src'},
      packages=find_packages(),
      description = ("Python daemon which exposes Geant BoD/NSI connection "
                                   "over HTTP/REST api."),
      keywords = 'Geant BoD NSI REST',
      install_requires=['Flask', 'Flask-Autodoc', 'isodate', 'pytk'],
      include_package_data = True,
)
