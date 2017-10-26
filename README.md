# televize #
Script to play Czech Television (Česká televize) streams in custom player.

### Installation ###
Directly from pip (preferred)
```sh
pip install televize
```
or
```sh
pip install https://github.com/ziima/televize/archive/master.zip
```
or
```sh
python setup.py install
```

### Dependencies ###
 * python 3.4 or 3.5
 * Any player which supports internet playlists. mpv is used by default.
 * Other dependencies are listed in [requirements.txt](requirements.txt).

### Usage ###
```sh
televize live 24  # CT24
televize live D  # CT:D
televize live sport  # CT-sport
televize ivysilani http://www.ceskatelevize.cz/ivysilani/11276561613-kosmo/
```

#### macOS ####

To open stream in a native player on macOS (e.g. VLC), use `--player` command `open -a APP --args`.
For example:

```sh
televize --player "open -a VLC --args" live 24
```

Based on Perl scripts `televize` and `ctstream` from Petr Písař (http://xpisar.wz.cz).
