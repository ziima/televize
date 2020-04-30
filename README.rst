========
televize
========

Script to play `Czech Television (Česká televize) <http://www.ceskatelevize.cz/>`_ streams in custom video player.

------------
Installation
------------

Directly using pip::

    pip install televize

------------
Dependencies
------------

* python >=3.4
* Any player which supports internet playlists. ``mpv`` is used by default.
* Other dependencies are listed in `requirements.txt <requirements.txt>`_.

-----
Usage
-----

::

    televize live 24  # CT24
    televize live D  # CT:D
    televize live sport  # CT-sport
    televize ivysilani http://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/
    televize ivysilani http://www.ceskatelevize.cz/porady/11276561613-kosmo/215512121020005-triumf

Complete usage is printed using `--help` argument::

    televize --help

macOS
=====

To open stream in a native player on macOS (e.g. VLC), use `--player` command `open -a APP --args`.
For example::

    televize --player "open -a VLC --args" live 24

---------------
Recommendations
---------------
A reload script https://github.com/4e6/mpv-reload is highly recommended for `mpv`.

---------------
Acknowledgement
---------------

Based on Perl scripts ``televize`` and ``ctstream`` from Petr Písař (http://xpisar.wz.cz).
