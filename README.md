# televize #
Script to run stream of Czech Television (Česká televize) in mplayer.

## Usage ##
```sh
( ./televize.py | while read line; do curl $line; done; ) | mplayer -cache 2000 -
```

Based on Perl scripts `televize` and `ctstream` from Petr Písař (http://xpisar.wz.cz).
