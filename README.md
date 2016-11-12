# televize #
Script to play Czech Television (Česká televize) streams in custom player.

### Installation ###
```sh
pip install https://github.com/ziima/televize/archive/master.zip
```
or
```sh
python setup.py install
```

### Dependencies ###
 * python 3.4 or 3.5
 * Any player which can play stream from stdin. mpv is used by default.

### Usage ###
```sh
televize live 24  # CT24
televize live D  # CT:D
televize live sport  # CT-sport
televize ivysilani http://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/
```

Based on Perl scripts `televize` and `ctstream` from Petr Písař (http://xpisar.wz.cz).
