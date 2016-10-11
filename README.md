# televize #
Script to run stream of Czech Television (Česká televize) in mplayer.

### Installation ###
```sh
pip install https://github.com/ziima/televize/archive/master.zip
```
or
```sh
python setup.py install
```

### Dependencies ###
 * python 2.7
 * requests
 * m3u8
 * mplayer

### Usage ###
```sh
./televize 1  # CT1
./televize 2  # CT2
./televize 24  # CT24
./televize sport  # CT-sport
./televize D  # CT-D
./televize art  # CT-art
```

Based on Perl scripts `televize` and `ctstream` from Petr Písař (http://xpisar.wz.cz).
