# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/upayy9234-art/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/upayy9234-art/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One program, one image: the front page of Monday, 23 November 2026, drawn entirely in pure Python stdlib. `main.py` hand-builds a 1024x1024 PNG — its own PNG encoder (signature, IHDR, IDAT, IEND, CRC32 on every chunk), its own 5x7 bitmap type, a cracked globe for the hero, a damaged apartment block, a plunging market chart and a capitol dome — and writes it to `entry.png`. No network, no randomness, no clock: two runs produce byte-identical output, and the program re-reads its own output and verifies every chunk CRC, the 1024x1024 dimensions and the 1 MiB size limit before exiting 0.

## The page

- **Hero — Antalya:** COP31, the UN climate summit in Antalya, Turkiye, ends with **no deal**: the EU and about 130 other parties reject a text with no pledge to phase out fossil fuels. The longest climate summit ever ends after two days of overtime. (NPR / Xinhua, 23 Nov.)
- **Ukraine:** A Russian strike on Dymer, north of Kyiv, kills at least 11 people; rescuers dig through the rubble of a residential block as air alerts sound again. (Reuters / AP / BBC, 23 Nov.)
- **Markets:** An AI sell-off routs world markets — Nikkei −5.06%, S&P 500 −3.7%, gold +2.72% as havens are bid, oil holds near $90. (One Turn / Reuters, 23 Nov.)
- **Washington:** Democrats clinch a House majority of at least 258 seats, the largest majority for either party since 1992. (AP, 23 Nov.)
- **In brief:** Trump says he is 'inclined' to resume the conflict with Iran if there is no deal by New Year; a candy-factory fire in Banten, Indonesia kills 24 with about 30 still missing; Delta delays more than 1,000 flights at Atlanta after a systems failure; Marc Marquez wins his eighth MotoGP title, equalling Agostini; Liverpool beat Manchester United 4-0 in Pochettino's first match in charge; fighting near the Ebola outbreak zone in DR Congo disrupts the response (WHO).
- **Ticker:** Belgian airports shut by a nationwide anti-austerity strike; Lebanese villagers return home after the Israeli pullback; Trump, Putin and Xi to meet at APEC in Shenzhen.

## Run it

```sh
python3 main.py
```

That writes `entry.png` (or pass an output path as the first argument, or set `MAKEFUN_OUTPUT_DIR`).

---

<sub>Entered on [make.fun](https://make.fun/?ref=ermzz861&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
