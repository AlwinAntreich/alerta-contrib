
from setuptools import setup, find_packages

version = '5.0.0'

setup(
    name="alerta-discord",
    version=version,
    description='Alerta plugin for Discord',
    url='https://github.com/alerta/alerta-contrib',
    license='MIT',
    author='Alwin Antreich',
    author_email='alwin.antreich@croit.io',
    packages=find_packages(),
    py_modules=['alerta_discord'],
    install_requires=[
        'requests'
    ],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'alerta.plugins': [
            'discord = alerta_discord:PostMessage'
        ]
    }
)
