# P9 tables: CFFDRS ignition R0 on lightning starts (E-44)

Run: `runs\20261104-0330_ignition_r0`. Reconstructed (ours).

Design check (weather-only matched-set AUC = 0.5): passed.

| score | matched-set AUC [95 % CI] | sets | pooled AUC | unscored points |
|---|---|---|---|---|
| FFMC class (weather only: design check) | 0.500 [0.500, 0.500] | 1,298 | 0.497 | 0 |
| P(sustained flaming), CWFIS fuel before the start | 0.523 [0.506, 0.539] | 1,213 | 0.515 | 473 |
| P(sustained flaming), SCANFI fuel before the start | 0.530 [0.513, 0.546] | 1,298 | 0.521 | 0 |

Fuel categories (scanfi):

| category | starts | controls | mean P |
|---|---|---|---|
| FC8 black spruce, moss | 731 | 2,844 | 0.497 |
| FC10 aspen, leaf | 281 | 1,807 | 0.135 |
| FC6 mixedwood, moss | 169 | 795 | 0.328 |
| FC4 jack pine, moss | 83 | 340 | 0.493 |
| FC3 jack pine, lichen | 24 | 74 | 0.704 |
| FC5 pine, needles | 10 | 36 | 0.414 |

Fuel categories (cwfis):

| category | starts | controls | mean P |
|---|---|---|---|
| FC8 black spruce, moss | 438 | 1,693 | 0.454 |
| FC6 mixedwood, moss | 235 | 1,163 | 0.298 |
| FC10 aspen, leaf | 125 | 862 | 0.115 |
| FC4 jack pine, moss | 178 | 671 | 0.559 |
| FC5 pine, needles | 144 | 613 | 0.494 |
| none  | 80 | 393 |  |
| FC3 jack pine, lichen | 56 | 268 | 0.679 |
| FC2 grass, summer | 37 | 195 | 0.788 |
| FC1 grass, spring | 5 | 38 | 0.742 |
