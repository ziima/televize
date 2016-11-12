# -*- coding: utf-8 -*-
from setuptools import setup


REQUIREMENTS = open('requirements.txt').read().split()
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: End Users/Desktop',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3 :: Only',
]


def main():
    setup(name='televize',
          version='0.1a1',
          author='Vlastimil Zíma',
          author_email='vlastimil.zima@gmail.com',
          description='Script to play Czech Television (Česká televize) streams in custom player.',
          py_modules=['televize'],
          python_requires='>=3.4',
          install_requires=REQUIREMENTS,
          classifiers=CLASSIFIERS,
          entry_points={'console_scripts': ['televize = televize:main']})


if __name__ == '__main__':
    main()
