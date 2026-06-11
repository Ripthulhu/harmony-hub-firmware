# Harmony Hub Firmware

An index of official Logitech Harmony `.hfw2` firmware bundles found through
Logitech SUS and recovery tooling.

This repo does not contain modified firmware. The files listed below are
official Logitech update bundles.

## Firmware List

| Product / Skin ID | Firmware | File | Device | Codename | Role | Confidence |
| ---: | --- | --- | --- | --- | --- | --- |
| 97 | 4.15.600 | [4.15.600.2987731.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/106/4.15.600.2987731.hfw2) | Harmony Hub | Pimento | Hub | confirmed |
| 99 | 4.15.330 | [4.15.330.712524.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/99/4.15.330.712524.hfw2) | Harmony Touch | Juniper | Handheld remote | confirmed |
| 100 | 4.15.330 | [4.15.330.5773985.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/100/4.15.330.5773985.hfw2) | Harmony Ultimate | JuniperRF / Olive alias | Handheld remote | confirmed |
| 102 | 4.15.330 | [4.15.330.8596752.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/102/4.15.330.8596752.hfw2) | Harmony Ultimate One | Bulliet / Ultimate One | Handheld remote | confirmed |
| 105 | 4.15.330 | [4.15.330.7346716.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/105/4.15.330.7346716.hfw2) | Harmony Ultimate Home | NewCastle | Handheld remote | confirmed |
| 106 | 4.15.600 | [4.15.600.2987731.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/106/4.15.600.2987731.hfw2) | Harmony Home Hub | Creemore | Hub | confirmed |
| 108 | 4.15.330 | [4.15.330.1416643.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/108/4.15.330.1416643.hfw2) | Harmony Ultimate Home | NewCastleWhite | Handheld remote | confirmed |
| 109 | 4.15.600 | [4.15.600.2987731.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/106/4.15.600.2987731.hfw2) | Unresolved Harmony hub variant | unresolved | Hub | target skin confirmed, name unresolved |
| 111 | 4.15.330 | [4.15.330.6905402.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/111/4.15.330.6905402.hfw2) | Harmony Elite / Harmony Pro | Hops | Handheld remote | confirmed; depends on Pro SKU flag |
| 112 | 4.15.330 | [4.15.330.8196409.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/112/4.15.330.8196409.hfw2) | Harmony 950 | HopsLite | Handheld remote | confirmed |
| 115 | 10.0.230 | [10.0.230.1601641.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/115/10.0.230.1601641.hfw2) | Harmony Pro 2400 Hub | Crackerjack | Hub | confirmed codename and role |
| 116 | 10.0.215 | [10.0.215.6483963.hfw2](https://d3pk1wwd3l8fri.cloudfront.net/sus/images/116/10.0.215.6483963.hfw2) | Harmony Pro 2400 Remote | Orville | Handheld remote | confirmed |

## Notes

The `4.15.600.2987731.hfw2` hub bundle declares intended skins `97`, `106`,
and `109` in `Description.xml`.

The `4.15.330` handheld bundles have separate product URLs and filenames, but
the pulled files matched byte-for-byte across the listed handheld models.

Use these only for devices you own, and only when you know the bundle matches
the hardware you are working with.
