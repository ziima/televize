# -*- coding: utf-8 -*-
from setuptools import setup


REQUIREMENTS = open('requirements.txt').read().split()


def main():
    setup(name='televize',
          version='0.1a',
          author='Vlastimil Zíma',
          author_email='vlastimil.zima@gmail.com',
          description='Script to play Czech Television (Česká televize) streams in custom player.',
          py_modules=['televize'],
          install_requires=REQUIREMENTS,
          entry_points={'console_scripts': ['televize = televize:main']})


if __name__ == '__main__':
    main()
