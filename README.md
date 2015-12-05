# televize #
Script to run stream of Czech Television (Česká televize) in mplayer.

### Dependencies ###
 * python 2.7
 * python-requests
 * curl
 * mplayer
 * bash

## Development dependencies ##
 * python-mock

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
