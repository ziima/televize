# -*- coding: utf-8 -*-
from setuptools import setup

VERSION = '0.2'
REQUIREMENTS = open('requirements.txt').read().split()
LONG_DESCRIPTION = open('README.md').read()
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Internet',
    'Topic :: Multimedia :: Video',
    'Topic :: Utilities',
]


def main():
    setup(name='televize',
          version=VERSION,
          author='Vlastimil Zíma',
          author_email='vlastimil.zima@gmail.com',
          description='Script to play Czech Television (Česká televize) streams in custom player.',
          long_description=LONG_DESCRIPTION,
          url='https://github.com/ziima/televize',
          license='GPLv2+',
          py_modules=['televize'],
          python_requires='>=3.4',
          install_requires=REQUIREMENTS,
          classifiers=CLASSIFIERS,
          entry_points={'console_scripts': ['televize = televize:main']})


if __name__ == '__main__':
    main()
