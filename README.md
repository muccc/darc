# Data Radio Channel (DARC)
Implementation for python and gnuradio, following ETSI EN 300 751 v1.2.1

## Contents

`./docs/`

Documentation about the MVG Layer 6 Protocol, gained from reverse engineering

`./src/gr-darc/`

Gnuradio implementation of Layer 1 and Layer 2

`./src/py/`

Python implementation of Layer 2-5

## Operation

There are several possibilities to use the DARC implementation:

### Offline

Receive and demodulate the DARC signal and dump the bitstream to a file, then open it using 

`python darc_prototype.py <filename>`

### Online

Receive and demodulate the DARC signal and process it using the DARC Layer2 block. Use the UDP sink to provide the data on the network. Process the other layers using

`python darc_udp.py`

## Installation of the gr-darc out of tree module

Info Used GnuRadio-Version: 3.7.5.1

In the gr-darc folder:

```
  mkdir build
  cd build
  cmake ..
  sudo make install
  sudo ldconfig
```

## Station IDs in Munich

| ID   | ID (Hex) | Stop  | Direction/Destination |
| ---- |:--------:| :-----|:----------------------|
| 1509 | 0x05E5   | Schluesselbergstr | Tram 19 -> Pasing |
| 1510 | 0x05E6   | Schluesselbergstr | Tram 19 -> StVeitstr |
| 1549 | 0x060D   | Grillparzer | Bus 187 -> Ruemelinstr | Bus 190 -> Messe Ost |
| 1625 | 0x0659   | Adunistr | Bus 53 -> Aidenbachstr |
| 1626 | 0x065A   | Adunistr | Bus 53 -> Muenchner Freiheit |
| 1642 | 0x066A   | Lehel | Tram 18 -> Gondrellplatz |
| 1701 | 0x06A5   | Einsteinstr | Bus 144 -> Ackermannbogen |
| 1761 | 0x06E1   | Sendlinger Tor | Bus 62 -> Ostbahnhof |
| 1775 | 0x06EF   | Waltherstr | Bus 62 -> Rotkreuzplatz |
| 1800 | 0x0708   | Mariannenplatz | Gondrellplatz |
| 1814 | 0x0716   | Maxmonument | Tram 19 -> StVeitstr |
| 1818 | 0x071A   | Maxmonument | Tram 19 -> Pasing |
| 1840 | 0x0730   | Mariannenplatz | Effnerplatz |
| 1923 | 0x0783   | Waltherstr | Bus 62 -> Ostbahnhof | 
| 1927 | 0x0787   | Isator/Zweibrueckenstr | Bus 132 -> Forstenrieder Park |

## Ressources

### Official

* http://www.axentia.se/pt/ibus_display.html

* http://www.axentia.se/db/DARC%20Technology.pdf

* http://www.etsi.org/deliver/etsi_en/300700_300799/300751/01.02.01_60/en_300751v010201p.pdf

### Projects

* http://www.windytan.com/2013/11/broadcast-messages-on-darc-side.html

* https://apollo.open-resource.org/mission:log:2014:08:08:darc-side-of-munich-hunting-fm-broadcasts-for-bus-and-tram-display-information-on-90-mhz

* http://www.tramgeschichten.de/2009/09/19/auf-der-spur-des-geheimen-dfi-datensignals/
