# Qwen：全部方法的 root_level 画像

三个主数据集、各阶段自身共同病例；不能跨阶段排名。完整五数据集与其他范围见 method_profiles.csv。


## RQ1.1 / rq1_cf

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| V_FACTUAL | node | 51 | 0.1961 | 0.1765 | 0.2157 | 0.2157 |
| V_FACTUAL | pod | 38 | 0.1952 | 0.1316 | 0.2632 | 0.2895 |
| V_FACTUAL | pod+service | 35 | 0.0619 | 0.0000 | 0.1429 | 0.1429 |
| V_FACTUAL | service | 176 | 0.3513 | 0.2443 | 0.4830 | 0.4943 |
| V_NEUTRAL | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| V_NEUTRAL | pod | 38 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| V_NEUTRAL | pod+service | 35 | 0.1286 | 0.0857 | 0.1714 | 0.1714 |
| V_NEUTRAL | service | 176 | 0.0748 | 0.0511 | 0.1080 | 0.1080 |
| V_PLACEBO | node | 51 | 0.2190 | 0.1765 | 0.2745 | 0.2745 |
| V_PLACEBO | pod | 38 | 0.1654 | 0.1053 | 0.2105 | 0.2632 |
| V_PLACEBO | pod+service | 35 | 0.0524 | 0.0000 | 0.1143 | 0.1143 |
| V_PLACEBO | service | 176 | 0.3452 | 0.2386 | 0.4659 | 0.4830 |
| V_TARGETED | node | 51 | 0.2663 | 0.2157 | 0.3137 | 0.3333 |
| V_TARGETED | pod | 38 | 0.1425 | 0.0789 | 0.2105 | 0.2368 |
| V_TARGETED | pod+service | 35 | 0.1000 | 0.0571 | 0.1714 | 0.1714 |
| V_TARGETED | service | 176 | 0.2623 | 0.1591 | 0.4148 | 0.4148 |

## RQ1.1 / rq1_rca

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| C | node | 51 | 0.2582 | 0.2157 | 0.3137 | 0.3137 |
| C | pod | 38 | 0.1491 | 0.1316 | 0.1842 | 0.1842 |
| C | pod+service | 35 | 0.2010 | 0.0857 | 0.3429 | 0.3714 |
| C | service | 176 | 0.3989 | 0.2841 | 0.5455 | 0.5625 |
| H | node | 51 | 0.3186 | 0.2549 | 0.3922 | 0.4118 |
| H | pod | 38 | 0.1206 | 0.0789 | 0.1579 | 0.1842 |
| H | pod+service | 35 | 0.2024 | 0.1143 | 0.3143 | 0.3429 |
| H | service | 176 | 0.3466 | 0.2273 | 0.4943 | 0.5170 |
| LV | node | 51 | 0.3382 | 0.2745 | 0.4118 | 0.4314 |
| LV | pod | 38 | 0.0877 | 0.0526 | 0.1053 | 0.1579 |
| LV | pod+service | 35 | 0.1643 | 0.0857 | 0.2571 | 0.2857 |
| LV | service | 176 | 0.3414 | 0.2273 | 0.4716 | 0.5114 |
| MV | node | 51 | 0.3144 | 0.2549 | 0.3725 | 0.3922 |
| MV | pod | 38 | 0.0724 | 0.0263 | 0.1053 | 0.1316 |
| MV | pod+service | 35 | 0.1771 | 0.0857 | 0.2857 | 0.3143 |
| MV | service | 176 | 0.3371 | 0.2102 | 0.4830 | 0.5170 |
| S | node | 51 | 0.1144 | 0.0980 | 0.1373 | 0.1373 |
| S | pod | 38 | 0.0526 | 0.0263 | 0.0789 | 0.0789 |
| S | pod+service | 35 | 0.1333 | 0.0857 | 0.2000 | 0.2000 |
| S | service | 176 | 0.3087 | 0.2216 | 0.4432 | 0.4432 |
| T | node | 51 | 0.2719 | 0.2157 | 0.3333 | 0.3529 |
| T | pod | 38 | 0.0877 | 0.0789 | 0.1053 | 0.1053 |
| T | pod+service | 35 | 0.1690 | 0.0571 | 0.3143 | 0.3429 |
| T | service | 176 | 0.3958 | 0.2670 | 0.5511 | 0.5739 |
| TCV | node | 51 | 0.3366 | 0.2941 | 0.3922 | 0.3922 |
| TCV | pod | 38 | 0.1228 | 0.1053 | 0.1579 | 0.1579 |
| TCV | pod+service | 35 | 0.1690 | 0.0857 | 0.2571 | 0.2857 |
| TCV | service | 176 | 0.3160 | 0.2159 | 0.4205 | 0.4659 |
| TPV | node | 51 | 0.2353 | 0.2157 | 0.2549 | 0.2549 |
| TPV | pod | 38 | 0.2171 | 0.1579 | 0.2895 | 0.3158 |
| TPV | pod+service | 35 | 0.2143 | 0.1429 | 0.3143 | 0.3143 |
| TPV | service | 176 | 0.4934 | 0.3864 | 0.6136 | 0.6250 |
| V | node | 51 | 0.1892 | 0.1569 | 0.1961 | 0.2549 |
| V | pod | 38 | 0.1864 | 0.1316 | 0.2368 | 0.2632 |
| V | pod+service | 35 | 0.0619 | 0.0000 | 0.1429 | 0.1429 |
| V | service | 176 | 0.3456 | 0.2386 | 0.4773 | 0.4886 |
| V_LG | node | 51 | 0.1961 | 0.1765 | 0.2157 | 0.2157 |
| V_LG | pod | 38 | 0.2346 | 0.1842 | 0.2895 | 0.3158 |
| V_LG | pod+service | 35 | 0.2343 | 0.1714 | 0.3143 | 0.3429 |
| V_LG | service | 176 | 0.5045 | 0.4034 | 0.6136 | 0.6364 |
| V_MG | node | 51 | 0.2108 | 0.1765 | 0.2353 | 0.2549 |
| V_MG | pod | 38 | 0.0811 | 0.0526 | 0.1053 | 0.1316 |
| V_MG | pod+service | 35 | 0.1714 | 0.1143 | 0.2286 | 0.2286 |
| V_MG | service | 176 | 0.4337 | 0.3182 | 0.5682 | 0.5795 |
| V_ML | node | 51 | 0.3121 | 0.2549 | 0.3725 | 0.3922 |
| V_ML | pod | 38 | 0.0680 | 0.0526 | 0.0789 | 0.1053 |
| V_ML | pod+service | 35 | 0.1667 | 0.0857 | 0.2857 | 0.2857 |
| V_ML | service | 176 | 0.3321 | 0.2102 | 0.4773 | 0.5114 |
| V_MLG | node | 51 | 0.1814 | 0.1373 | 0.2157 | 0.2353 |
| V_MLG | pod | 38 | 0.0592 | 0.0000 | 0.1053 | 0.1842 |
| V_MLG | pod+service | 35 | 0.1667 | 0.1143 | 0.2286 | 0.2286 |
| V_MLG | service | 176 | 0.3902 | 0.2841 | 0.5227 | 0.5341 |
| V_MR | node | 51 | 0.3007 | 0.2549 | 0.3529 | 0.3529 |
| V_MR | pod | 38 | 0.1118 | 0.0789 | 0.1316 | 0.1579 |
| V_MR | pod+service | 35 | 0.1500 | 0.0571 | 0.2857 | 0.3143 |
| V_MR | service | 176 | 0.3018 | 0.1989 | 0.4148 | 0.4489 |
| V_MRG | node | 51 | 0.2000 | 0.1765 | 0.2157 | 0.2353 |
| V_MRG | pod | 38 | 0.2390 | 0.1579 | 0.3421 | 0.3684 |
| V_MRG | pod+service | 35 | 0.1048 | 0.0571 | 0.1714 | 0.1714 |
| V_MRG | service | 176 | 0.3646 | 0.2500 | 0.5170 | 0.5170 |
| V_MRL | node | 51 | 0.3056 | 0.2353 | 0.3725 | 0.3922 |
| V_MRL | pod | 38 | 0.0285 | 0.0000 | 0.0526 | 0.0789 |
| V_MRL | pod+service | 35 | 0.1224 | 0.0286 | 0.2286 | 0.2857 |
| V_MRL | service | 176 | 0.2533 | 0.1648 | 0.3580 | 0.3864 |
| V_RG | node | 51 | 0.2222 | 0.1961 | 0.2549 | 0.2549 |
| V_RG | pod | 38 | 0.3377 | 0.2632 | 0.4211 | 0.4211 |
| V_RG | pod+service | 35 | 0.1857 | 0.1143 | 0.2857 | 0.2857 |
| V_RG | service | 176 | 0.4143 | 0.2841 | 0.5625 | 0.5795 |
| V_RL | node | 51 | 0.3137 | 0.2549 | 0.3922 | 0.3922 |
| V_RL | pod | 38 | 0.1053 | 0.0789 | 0.1579 | 0.1579 |
| V_RL | pod+service | 35 | 0.1643 | 0.0857 | 0.2571 | 0.2857 |
| V_RL | service | 176 | 0.3049 | 0.2045 | 0.4261 | 0.4489 |
| V_RLG | node | 51 | 0.2271 | 0.1961 | 0.2549 | 0.2745 |
| V_RLG | pod | 38 | 0.3728 | 0.2895 | 0.4737 | 0.4737 |
| V_RLG | pod+service | 35 | 0.1248 | 0.0571 | 0.2000 | 0.2286 |
| V_RLG | service | 176 | 0.4209 | 0.3182 | 0.5341 | 0.5511 |

## RQ2.1 / composition

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| D0 | node | 51 | 0.2114 | 0.1765 | 0.2353 | 0.2745 |
| D0 | pod | 38 | 0.1425 | 0.1053 | 0.1842 | 0.2105 |
| D0 | pod+service | 35 | 0.0952 | 0.0571 | 0.1429 | 0.1429 |
| D0 | service | 176 | 0.3423 | 0.2386 | 0.4773 | 0.4830 |
| D_AIRY | node | 51 | 0.2288 | 0.1961 | 0.2745 | 0.2745 |
| D_AIRY | pod | 38 | 0.1513 | 0.0789 | 0.2368 | 0.2632 |
| D_AIRY | pod+service | 35 | 0.1295 | 0.0571 | 0.2000 | 0.2286 |
| D_AIRY | service | 176 | 0.3622 | 0.2727 | 0.4716 | 0.4773 |
| D_COMPACT | node | 51 | 0.1536 | 0.1176 | 0.1961 | 0.1961 |
| D_COMPACT | pod | 38 | 0.1425 | 0.1053 | 0.1842 | 0.2105 |
| D_COMPACT | pod+service | 35 | 0.1405 | 0.0857 | 0.2000 | 0.2286 |
| D_COMPACT | service | 176 | 0.3561 | 0.2443 | 0.4886 | 0.5000 |
| D_ENTITY | node | 51 | 0.2190 | 0.1765 | 0.2745 | 0.2745 |
| D_ENTITY | pod | 38 | 0.2083 | 0.1579 | 0.2632 | 0.2895 |
| D_ENTITY | pod+service | 35 | 0.1095 | 0.0571 | 0.1714 | 0.1714 |
| D_ENTITY | service | 176 | 0.3513 | 0.2500 | 0.4773 | 0.4773 |
| D_LANDSCAPE | node | 51 | 0.2124 | 0.1765 | 0.2549 | 0.2549 |
| D_LANDSCAPE | pod | 38 | 0.1930 | 0.1053 | 0.3158 | 0.3158 |
| D_LANDSCAPE | pod+service | 35 | 0.1048 | 0.0286 | 0.2000 | 0.2000 |
| D_LANDSCAPE | service | 176 | 0.3774 | 0.2727 | 0.5000 | 0.5170 |
| D_ONSET_ORDER | node | 51 | 0.1585 | 0.1176 | 0.1961 | 0.2157 |
| D_ONSET_ORDER | pod | 38 | 0.1732 | 0.1316 | 0.2105 | 0.2368 |
| D_ONSET_ORDER | pod+service | 35 | 0.1190 | 0.0571 | 0.2000 | 0.2000 |
| D_ONSET_ORDER | service | 176 | 0.3733 | 0.2841 | 0.4716 | 0.4886 |
| D_PORTRAIT | node | 51 | 0.1438 | 0.0980 | 0.1961 | 0.1961 |
| D_PORTRAIT | pod | 38 | 0.1031 | 0.0526 | 0.1579 | 0.1842 |
| D_PORTRAIT | pod+service | 35 | 0.1429 | 0.0857 | 0.2000 | 0.2000 |
| D_PORTRAIT | service | 176 | 0.3134 | 0.2102 | 0.4375 | 0.4489 |
| D_SCALE_075 | node | 51 | 0.1601 | 0.1176 | 0.2157 | 0.2157 |
| D_SCALE_075 | pod | 38 | 0.1557 | 0.1053 | 0.2105 | 0.2368 |
| D_SCALE_075 | pod+service | 35 | 0.0857 | 0.0286 | 0.1429 | 0.1429 |
| D_SCALE_075 | service | 176 | 0.3182 | 0.2102 | 0.4659 | 0.4773 |
| D_SCALE_125 | node | 51 | 0.2533 | 0.1961 | 0.3137 | 0.3333 |
| D_SCALE_125 | pod | 38 | 0.1425 | 0.1053 | 0.1842 | 0.2105 |
| D_SCALE_125 | pod+service | 35 | 0.1095 | 0.0571 | 0.1714 | 0.1714 |
| D_SCALE_125 | service | 176 | 0.3750 | 0.2841 | 0.4773 | 0.4886 |
| D_SCALE_150 | node | 51 | 0.1830 | 0.1569 | 0.2157 | 0.2157 |
| D_SCALE_150 | pod | 38 | 0.1557 | 0.0789 | 0.2632 | 0.2895 |
| D_SCALE_150 | pod+service | 35 | 0.1429 | 0.0286 | 0.2857 | 0.2857 |
| D_SCALE_150 | service | 176 | 0.3816 | 0.2841 | 0.5114 | 0.5114 |
| D_TOPOLOGY_CENTER | node | 51 | 0.1477 | 0.0980 | 0.1961 | 0.2157 |
| D_TOPOLOGY_CENTER | pod | 38 | 0.1469 | 0.1053 | 0.1842 | 0.2105 |
| D_TOPOLOGY_CENTER | pod+service | 35 | 0.0952 | 0.0286 | 0.1714 | 0.1714 |
| D_TOPOLOGY_CENTER | service | 176 | 0.3059 | 0.2216 | 0.4148 | 0.4148 |

## RQ2.1 / selection

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0__T | node | 51 | 0.2784 | 0.2157 | 0.3529 | 0.3725 |
| P0__T | pod | 38 | 0.0965 | 0.0789 | 0.1316 | 0.1316 |
| P0__T | pod+service | 35 | 0.1905 | 0.0571 | 0.4000 | 0.4000 |
| P0__T | service | 176 | 0.3908 | 0.2614 | 0.5398 | 0.5739 |
| P0__V | node | 51 | 0.2114 | 0.1765 | 0.2353 | 0.2745 |
| P0__V | pod | 38 | 0.1425 | 0.1053 | 0.1842 | 0.2105 |
| P0__V | pod+service | 35 | 0.0952 | 0.0571 | 0.1429 | 0.1429 |
| P0__V | service | 176 | 0.3423 | 0.2386 | 0.4773 | 0.4830 |
| P_BARO_RS__T | node | 51 | 0.2843 | 0.2353 | 0.3529 | 0.3529 |
| P_BARO_RS__T | pod | 38 | 0.1579 | 0.1053 | 0.2368 | 0.2368 |
| P_BARO_RS__T | pod+service | 35 | 0.1500 | 0.0571 | 0.2857 | 0.3143 |
| P_BARO_RS__T | service | 176 | 0.3468 | 0.2216 | 0.5000 | 0.5284 |
| P_BARO_RS__V | node | 51 | 0.1078 | 0.0784 | 0.1373 | 0.1373 |
| P_BARO_RS__V | pod | 38 | 0.2588 | 0.2105 | 0.3158 | 0.3158 |
| P_BARO_RS__V | pod+service | 35 | 0.0714 | 0.0286 | 0.1143 | 0.1143 |
| P_BARO_RS__V | service | 176 | 0.3035 | 0.1875 | 0.4432 | 0.4602 |
| P_COVERAGE__T | node | 51 | 0.0523 | 0.0196 | 0.0980 | 0.0980 |
| P_COVERAGE__T | pod | 38 | 0.0702 | 0.0263 | 0.1316 | 0.1316 |
| P_COVERAGE__T | pod+service | 35 | 0.1724 | 0.0857 | 0.2857 | 0.3143 |
| P_COVERAGE__T | service | 176 | 0.4210 | 0.3011 | 0.5682 | 0.5966 |
| P_COVERAGE__V | node | 51 | 0.0261 | 0.0196 | 0.0392 | 0.0392 |
| P_COVERAGE__V | pod | 38 | 0.0680 | 0.0263 | 0.1053 | 0.1316 |
| P_COVERAGE__V | pod+service | 35 | 0.0286 | 0.0000 | 0.0571 | 0.0571 |
| P_COVERAGE__V | service | 176 | 0.2614 | 0.1591 | 0.3977 | 0.3977 |
| P_DIVERSITY__T | node | 51 | 0.1536 | 0.1176 | 0.1961 | 0.1961 |
| P_DIVERSITY__T | pod | 38 | 0.1623 | 0.0789 | 0.2632 | 0.2632 |
| P_DIVERSITY__T | pod+service | 35 | 0.2143 | 0.1429 | 0.3143 | 0.3143 |
| P_DIVERSITY__T | service | 176 | 0.4216 | 0.3125 | 0.5625 | 0.5682 |
| P_DIVERSITY__V | node | 51 | 0.1438 | 0.0980 | 0.1961 | 0.1961 |
| P_DIVERSITY__V | pod | 38 | 0.1776 | 0.1053 | 0.2632 | 0.2895 |
| P_DIVERSITY__V | pod+service | 35 | 0.1000 | 0.0571 | 0.1429 | 0.1429 |
| P_DIVERSITY__V | service | 176 | 0.2865 | 0.1875 | 0.4034 | 0.4091 |
| P_LOG_FREQ__T | node | 51 | 0.2974 | 0.2549 | 0.3529 | 0.3529 |
| P_LOG_FREQ__T | pod | 38 | 0.0877 | 0.0789 | 0.1053 | 0.1053 |
| P_LOG_FREQ__T | pod+service | 35 | 0.1952 | 0.0857 | 0.3714 | 0.3714 |
| P_LOG_FREQ__T | service | 176 | 0.3792 | 0.2557 | 0.5284 | 0.5625 |
| P_LOG_FREQ__V | node | 51 | 0.2075 | 0.1765 | 0.2353 | 0.2549 |
| P_LOG_FREQ__V | pod | 38 | 0.1689 | 0.1053 | 0.2368 | 0.2632 |
| P_LOG_FREQ__V | pod+service | 35 | 0.1000 | 0.0571 | 0.1714 | 0.1714 |
| P_LOG_FREQ__V | service | 176 | 0.3264 | 0.2386 | 0.4375 | 0.4489 |
| P_RANDOM__T | node | 51 | 0.0882 | 0.0588 | 0.1176 | 0.1176 |
| P_RANDOM__T | pod | 38 | 0.0088 | 0.0000 | 0.0263 | 0.0263 |
| P_RANDOM__T | pod+service | 35 | 0.1762 | 0.0857 | 0.2857 | 0.2857 |
| P_RANDOM__T | service | 176 | 0.2713 | 0.1989 | 0.3750 | 0.3807 |
| P_RANDOM__V | node | 51 | 0.0588 | 0.0588 | 0.0588 | 0.0588 |
| P_RANDOM__V | pod | 38 | 0.0395 | 0.0263 | 0.0526 | 0.0526 |
| P_RANDOM__V | pod+service | 35 | 0.0143 | 0.0000 | 0.0286 | 0.0286 |
| P_RANDOM__V | service | 176 | 0.1203 | 0.0795 | 0.1761 | 0.1761 |
| P_SIGMA__T | node | 51 | 0.1895 | 0.1373 | 0.2549 | 0.2549 |
| P_SIGMA__T | pod | 38 | 0.0351 | 0.0263 | 0.0526 | 0.0526 |
| P_SIGMA__T | pod+service | 35 | 0.1476 | 0.0857 | 0.2286 | 0.2286 |
| P_SIGMA__T | service | 176 | 0.3291 | 0.2330 | 0.4602 | 0.4659 |
| P_SIGMA__V | node | 51 | 0.0686 | 0.0588 | 0.0784 | 0.0784 |
| P_SIGMA__V | pod | 38 | 0.0548 | 0.0263 | 0.0789 | 0.1053 |
| P_SIGMA__V | pod+service | 35 | 0.0762 | 0.0286 | 0.1429 | 0.1429 |
| P_SIGMA__V | service | 176 | 0.2296 | 0.1364 | 0.3580 | 0.3636 |
| P_TRACE_SC__T | node | 51 | 0.2784 | 0.2353 | 0.3333 | 0.3529 |
| P_TRACE_SC__T | pod | 38 | 0.1228 | 0.0789 | 0.2105 | 0.2105 |
| P_TRACE_SC__T | pod+service | 35 | 0.2143 | 0.0857 | 0.4000 | 0.4000 |
| P_TRACE_SC__T | service | 176 | 0.4064 | 0.2841 | 0.5625 | 0.5795 |
| P_TRACE_SC__V | node | 51 | 0.2141 | 0.1569 | 0.2745 | 0.2941 |
| P_TRACE_SC__V | pod | 38 | 0.1579 | 0.0789 | 0.2895 | 0.2895 |
| P_TRACE_SC__V | pod+service | 35 | 0.1143 | 0.0571 | 0.2000 | 0.2000 |
| P_TRACE_SC__V | service | 176 | 0.3509 | 0.2614 | 0.4716 | 0.4773 |

## RQ2.1 / silhouette

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| S0 | node | 51 | 0.2114 | 0.1765 | 0.2353 | 0.2745 |
| S0 | pod | 38 | 0.1425 | 0.1053 | 0.1842 | 0.2105 |
| S0 | pod+service | 35 | 0.0952 | 0.0571 | 0.1429 | 0.1429 |
| S0 | service | 176 | 0.3423 | 0.2386 | 0.4773 | 0.4830 |
| S_COMPACT_MIX | node | 51 | 0.1732 | 0.1373 | 0.2353 | 0.2353 |
| S_COMPACT_MIX | pod | 38 | 0.2039 | 0.1316 | 0.2895 | 0.3158 |
| S_COMPACT_MIX | pod+service | 35 | 0.0571 | 0.0286 | 0.0857 | 0.0857 |
| S_COMPACT_MIX | service | 176 | 0.3324 | 0.2330 | 0.4659 | 0.4659 |
| S_DENSITY_COMPACT | node | 51 | 0.1902 | 0.1569 | 0.1961 | 0.2549 |
| S_DENSITY_COMPACT | pod | 38 | 0.2368 | 0.1579 | 0.3158 | 0.3684 |
| S_DENSITY_COMPACT | pod+service | 35 | 0.1048 | 0.0571 | 0.1714 | 0.1714 |
| S_DENSITY_COMPACT | service | 176 | 0.3546 | 0.2557 | 0.4830 | 0.4886 |
| S_G_LAYERED | node | 51 | 0.1748 | 0.1373 | 0.2157 | 0.2353 |
| S_G_LAYERED | pod | 38 | 0.1908 | 0.1316 | 0.2632 | 0.2895 |
| S_G_LAYERED | pod+service | 35 | 0.1667 | 0.1143 | 0.2286 | 0.2286 |
| S_G_LAYERED | service | 176 | 0.3828 | 0.2557 | 0.5341 | 0.5398 |
| S_G_MATRIX | node | 51 | 0.1895 | 0.1569 | 0.2353 | 0.2353 |
| S_G_MATRIX | pod | 38 | 0.1864 | 0.1053 | 0.2895 | 0.3158 |
| S_G_MATRIX | pod+service | 35 | 0.0952 | 0.0571 | 0.1429 | 0.1429 |
| S_G_MATRIX | service | 176 | 0.3466 | 0.2330 | 0.4886 | 0.4886 |
| S_L_MATRIX | node | 51 | 0.2124 | 0.1765 | 0.2549 | 0.2549 |
| S_L_MATRIX | pod | 38 | 0.2083 | 0.1579 | 0.2632 | 0.2895 |
| S_L_MATRIX | pod+service | 35 | 0.0952 | 0.0286 | 0.1714 | 0.1714 |
| S_L_MATRIX | service | 176 | 0.3584 | 0.2500 | 0.5057 | 0.5114 |
| S_M_HEATMAP | node | 51 | 0.0997 | 0.0588 | 0.1569 | 0.1765 |
| S_M_HEATMAP | pod | 38 | 0.1513 | 0.1316 | 0.1579 | 0.1842 |
| S_M_HEATMAP | pod+service | 35 | 0.1095 | 0.0571 | 0.1714 | 0.1714 |
| S_M_HEATMAP | service | 176 | 0.3182 | 0.2273 | 0.4318 | 0.4318 |
| S_M_OVERLAY | node | 51 | 0.1732 | 0.1176 | 0.2157 | 0.2549 |
| S_M_OVERLAY | pod | 38 | 0.2127 | 0.1579 | 0.2632 | 0.2895 |
| S_M_OVERLAY | pod+service | 35 | 0.1000 | 0.0571 | 0.1429 | 0.1429 |
| S_M_OVERLAY | service | 176 | 0.3723 | 0.2841 | 0.4830 | 0.4886 |
| S_M_TIME_BARS | node | 51 | 0.1699 | 0.1373 | 0.1961 | 0.2353 |
| S_M_TIME_BARS | pod | 38 | 0.2259 | 0.1842 | 0.2632 | 0.2895 |
| S_M_TIME_BARS | pod+service | 35 | 0.0952 | 0.0571 | 0.1429 | 0.1429 |
| S_M_TIME_BARS | service | 176 | 0.3553 | 0.2443 | 0.4830 | 0.4886 |
| S_R_DUMBBELL | node | 51 | 0.2075 | 0.1765 | 0.2353 | 0.2549 |
| S_R_DUMBBELL | pod | 38 | 0.1272 | 0.0789 | 0.2105 | 0.2105 |
| S_R_DUMBBELL | pod+service | 35 | 0.0714 | 0.0286 | 0.1143 | 0.1143 |
| S_R_DUMBBELL | service | 176 | 0.3641 | 0.2670 | 0.4886 | 0.4943 |
| S_R_PAIRED_BARS | node | 51 | 0.2598 | 0.2157 | 0.3137 | 0.3333 |
| S_R_PAIRED_BARS | pod | 38 | 0.1842 | 0.1316 | 0.2632 | 0.2632 |
| S_R_PAIRED_BARS | pod+service | 35 | 0.1143 | 0.0571 | 0.2000 | 0.2000 |
| S_R_PAIRED_BARS | service | 176 | 0.3608 | 0.2557 | 0.4943 | 0.4943 |
| S_TABLE | node | 51 | 0.1078 | 0.0784 | 0.1569 | 0.1569 |
| S_TABLE | pod | 38 | 0.1325 | 0.0789 | 0.1842 | 0.2105 |
| S_TABLE | pod+service | 35 | 0.1143 | 0.0857 | 0.1429 | 0.1429 |
| S_TABLE | service | 176 | 0.3400 | 0.2443 | 0.4659 | 0.4659 |

## RQ3.1 / exp_budget_curve

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| budget=0.5__representation=X_C | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.5__representation=X_C | pod | 9 | 0.2593 | 0.2222 | 0.3333 | 0.3333 |
| budget=0.5__representation=X_C | pod+service | 3 | 0.1111 | 0.0000 | 0.3333 | 0.3333 |
| budget=0.5__representation=X_C | service | 36 | 0.3542 | 0.3333 | 0.3611 | 0.3889 |
| budget=0.5__representation=X_C_TABLE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.5__representation=X_C_TABLE | pod | 9 | 0.2222 | 0.2222 | 0.2222 | 0.2222 |
| budget=0.5__representation=X_C_TABLE | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.5__representation=X_C_TABLE | service | 36 | 0.3042 | 0.2778 | 0.3056 | 0.3611 |
| budget=0.5__representation=X_V_CONTRAST | node | 12 | 0.0833 | 0.0833 | 0.0833 | 0.0833 |
| budget=0.5__representation=X_V_CONTRAST | pod | 9 | 0.1481 | 0.1111 | 0.2222 | 0.2222 |
| budget=0.5__representation=X_V_CONTRAST | pod+service | 3 | 0.0833 | 0.0000 | 0.0000 | 0.3333 |
| budget=0.5__representation=X_V_CONTRAST | service | 36 | 0.3759 | 0.3333 | 0.4167 | 0.4444 |
| budget=0.75__representation=X_C | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C | service | 36 | 0.4421 | 0.3333 | 0.5556 | 0.5833 |
| budget=0.75__representation=X_C_TABLE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C_TABLE | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C_TABLE | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_C_TABLE | service | 36 | 0.4269 | 0.3056 | 0.5278 | 0.6111 |
| budget=0.75__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_V_CONTRAST | pod | 9 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| budget=0.75__representation=X_V_CONTRAST | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| budget=0.75__representation=X_V_CONTRAST | service | 36 | 0.3495 | 0.3056 | 0.3889 | 0.4167 |

## RQ3.1 / exp_contrastive_rca_effectiveness

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_T_CAL | node | 51 | 0.3660 | 0.3137 | 0.4118 | 0.4510 |
| P0_T_CAL | pod | 38 | 0.0711 | 0.0263 | 0.1053 | 0.1316 |
| P0_T_CAL | pod+service | 35 | 0.2081 | 0.0857 | 0.3143 | 0.4286 |
| P0_T_CAL | service | 176 | 0.3734 | 0.2386 | 0.4716 | 0.6136 |
| P0_V_CONTRAST | node | 51 | 0.2033 | 0.1373 | 0.2549 | 0.3137 |
| P0_V_CONTRAST | pod | 38 | 0.1342 | 0.0789 | 0.1579 | 0.2368 |
| P0_V_CONTRAST | pod+service | 35 | 0.0976 | 0.0286 | 0.1714 | 0.2000 |
| P0_V_CONTRAST | service | 176 | 0.3720 | 0.2330 | 0.5114 | 0.5909 |
| P0_V_STANDARD | node | 51 | 0.2176 | 0.1765 | 0.2353 | 0.3333 |
| P0_V_STANDARD | pod | 38 | 0.1009 | 0.0789 | 0.1316 | 0.1316 |
| P0_V_STANDARD | pod+service | 35 | 0.1557 | 0.0857 | 0.2000 | 0.3143 |
| P0_V_STANDARD | service | 176 | 0.3401 | 0.2159 | 0.4545 | 0.5341 |
| SIRCL_TEXT | node | 51 | 0.2843 | 0.2549 | 0.3333 | 0.3333 |
| SIRCL_TEXT | pod | 38 | 0.2684 | 0.1842 | 0.3947 | 0.4211 |
| SIRCL_TEXT | pod+service | 35 | 0.2119 | 0.1714 | 0.2571 | 0.2857 |
| SIRCL_TEXT | service | 176 | 0.3728 | 0.2784 | 0.4830 | 0.5057 |
| T | node | 51 | 0.2817 | 0.2353 | 0.3333 | 0.3529 |
| T | pod | 38 | 0.0965 | 0.0789 | 0.1316 | 0.1316 |
| T | pod+service | 35 | 0.1690 | 0.0571 | 0.3143 | 0.3429 |
| T | service | 176 | 0.3837 | 0.2557 | 0.5341 | 0.5625 |
| TPV | node | 51 | 0.2392 | 0.2157 | 0.2549 | 0.2745 |
| TPV | pod | 38 | 0.2171 | 0.1579 | 0.2895 | 0.3158 |
| TPV | pod+service | 35 | 0.2429 | 0.1714 | 0.3429 | 0.3429 |
| TPV | service | 176 | 0.5019 | 0.3977 | 0.6193 | 0.6307 |
| T_COMPACT | node | 51 | 0.2484 | 0.1961 | 0.3137 | 0.3137 |
| T_COMPACT | pod | 38 | 0.1404 | 0.1316 | 0.1579 | 0.1579 |
| T_COMPACT | pod+service | 35 | 0.1771 | 0.0857 | 0.2857 | 0.3143 |
| T_COMPACT | service | 176 | 0.3968 | 0.2898 | 0.5341 | 0.5455 |
| V | node | 51 | 0.2245 | 0.1961 | 0.2353 | 0.2745 |
| V | pod | 38 | 0.1864 | 0.1316 | 0.2368 | 0.2632 |
| V | pod+service | 35 | 0.0619 | 0.0000 | 0.1429 | 0.1429 |
| V | service | 176 | 0.3381 | 0.2273 | 0.4716 | 0.4830 |
| X_C | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C | pod | 38 | 0.1842 | 0.1579 | 0.2105 | 0.2105 |
| X_C | pod+service | 35 | 0.2571 | 0.1714 | 0.3429 | 0.3429 |
| X_C | service | 176 | 0.4372 | 0.3466 | 0.5284 | 0.5398 |
| X_C_TABLE | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C_TABLE | pod | 38 | 0.1535 | 0.1053 | 0.2105 | 0.2105 |
| X_C_TABLE | pod+service | 35 | 0.1476 | 0.0857 | 0.2286 | 0.2286 |
| X_C_TABLE | service | 176 | 0.3991 | 0.3125 | 0.4716 | 0.5227 |
| X_MTEXT | node | 51 | 0.0196 | 0.0196 | 0.0196 | 0.0196 |
| X_MTEXT | pod | 38 | 0.1798 | 0.1579 | 0.2105 | 0.2105 |
| X_MTEXT | pod+service | 35 | 0.1286 | 0.0857 | 0.1714 | 0.1714 |
| X_MTEXT | service | 176 | 0.3709 | 0.2955 | 0.4489 | 0.4716 |
| X_S | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_S | pod | 38 | 0.1118 | 0.0789 | 0.1316 | 0.1579 |
| X_S | pod+service | 35 | 0.1057 | 0.0571 | 0.1143 | 0.2000 |
| X_S | service | 176 | 0.3169 | 0.2443 | 0.3864 | 0.4261 |
| X_T | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_T | pod | 38 | 0.1842 | 0.1842 | 0.1842 | 0.1842 |
| X_T | pod+service | 35 | 0.2190 | 0.1429 | 0.2857 | 0.3429 |
| X_T | service | 176 | 0.4299 | 0.3352 | 0.5227 | 0.5568 |
| X_V_CONTRAST | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_V_CONTRAST | pod | 38 | 0.0785 | 0.0263 | 0.1053 | 0.1842 |
| X_V_CONTRAST | pod+service | 35 | 0.1738 | 0.0857 | 0.2571 | 0.2857 |
| X_V_CONTRAST | service | 176 | 0.3773 | 0.2898 | 0.4659 | 0.5000 |
| X_V_STANDARD | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_V_STANDARD | pod | 38 | 0.1785 | 0.1579 | 0.1842 | 0.2368 |
| X_V_STANDARD | pod+service | 35 | 0.1310 | 0.0857 | 0.1714 | 0.2000 |
| X_V_STANDARD | service | 176 | 0.3503 | 0.2557 | 0.4545 | 0.4830 |

## RQ3.1 / exp_final_test

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| SIRCL_TEXT | node | 51 | 0.2196 | 0.1961 | 0.2353 | 0.2549 |
| SIRCL_TEXT | pod | 44 | 0.1750 | 0.1136 | 0.2500 | 0.2727 |
| SIRCL_TEXT | pod+service | 37 | 0.2185 | 0.1351 | 0.2973 | 0.3243 |
| SIRCL_TEXT | service | 228 | 0.4720 | 0.3509 | 0.6140 | 0.6316 |
| T | node | 51 | 0.3464 | 0.2549 | 0.4510 | 0.4510 |
| T | pod | 44 | 0.0758 | 0.0227 | 0.1591 | 0.1591 |
| T | pod+service | 37 | 0.1667 | 0.0811 | 0.2703 | 0.2703 |
| T | service | 228 | 0.3816 | 0.2500 | 0.5307 | 0.5570 |
| TPV | node | 51 | 0.3105 | 0.2941 | 0.3333 | 0.3333 |
| TPV | pod | 44 | 0.1477 | 0.0909 | 0.2045 | 0.2045 |
| TPV | pod+service | 37 | 0.2568 | 0.2162 | 0.2973 | 0.2973 |
| TPV | service | 228 | 0.4671 | 0.3421 | 0.5965 | 0.6316 |
| T_COMPACT | node | 51 | 0.3137 | 0.2353 | 0.4118 | 0.4118 |
| T_COMPACT | pod | 44 | 0.0795 | 0.0227 | 0.1591 | 0.1591 |
| T_COMPACT | pod+service | 37 | 0.1622 | 0.0811 | 0.2703 | 0.2703 |
| T_COMPACT | service | 228 | 0.4064 | 0.2851 | 0.5614 | 0.5789 |
| X_C | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C | pod | 44 | 0.1932 | 0.1818 | 0.2045 | 0.2045 |
| X_C | pod+service | 37 | 0.0991 | 0.0541 | 0.1622 | 0.1622 |
| X_C | service | 228 | 0.3694 | 0.2982 | 0.4386 | 0.4825 |
| X_C_TABLE | node | 51 | 0.0196 | 0.0196 | 0.0196 | 0.0196 |
| X_C_TABLE | pod | 44 | 0.1837 | 0.1591 | 0.2045 | 0.2273 |
| X_C_TABLE | pod+service | 37 | 0.1216 | 0.0811 | 0.1622 | 0.1622 |
| X_C_TABLE | service | 228 | 0.4292 | 0.3553 | 0.5132 | 0.5482 |
| X_MTEXT | node | 51 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_MTEXT | pod | 44 | 0.1364 | 0.1364 | 0.1364 | 0.1364 |
| X_MTEXT | pod+service | 37 | 0.1081 | 0.0541 | 0.1622 | 0.1622 |
| X_MTEXT | service | 228 | 0.3792 | 0.3114 | 0.4561 | 0.4737 |
| X_V_CONTRAST | node | 51 | 0.0039 | 0.0000 | 0.0000 | 0.0196 |
| X_V_CONTRAST | pod | 44 | 0.1780 | 0.1364 | 0.2273 | 0.2273 |
| X_V_CONTRAST | pod+service | 37 | 0.1270 | 0.0541 | 0.1892 | 0.2162 |
| X_V_CONTRAST | service | 228 | 0.3800 | 0.3202 | 0.4430 | 0.4737 |

## RQ3.1 / exp_redundant_load

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| load=0.25__representation=X_C | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C | service | 35 | 0.4214 | 0.3429 | 0.4571 | 0.5429 |
| load=0.25__representation=X_C_TABLE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C_TABLE | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C_TABLE | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_C_TABLE | service | 35 | 0.4167 | 0.3714 | 0.4571 | 0.4857 |
| load=0.25__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_V_CONTRAST | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_V_CONTRAST | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.25__representation=X_V_CONTRAST | service | 35 | 0.3857 | 0.3429 | 0.4571 | 0.4571 |
| load=0.5__representation=X_C | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C | service | 35 | 0.3857 | 0.3143 | 0.4286 | 0.4857 |
| load=0.5__representation=X_C_TABLE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C_TABLE | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C_TABLE | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_C_TABLE | service | 35 | 0.4190 | 0.3714 | 0.4857 | 0.4857 |
| load=0.5__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_V_CONTRAST | pod | 9 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| load=0.5__representation=X_V_CONTRAST | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| load=0.5__representation=X_V_CONTRAST | service | 35 | 0.3333 | 0.2857 | 0.3714 | 0.4286 |

## RQ3.1 / exp_replicate_stability

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| condition=X_C__replicate=1 | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=1 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=1 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=1 | service | 36 | 0.3889 | 0.3056 | 0.4722 | 0.4722 |
| condition=X_C__replicate=2 | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=2 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=2 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_C__replicate=2 | service | 36 | 0.3889 | 0.3056 | 0.4722 | 0.4722 |
| condition=X_V_CONTRAST__replicate=1 | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=1 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=1 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=1 | service | 36 | 0.3644 | 0.2778 | 0.4167 | 0.5278 |
| condition=X_V_CONTRAST__replicate=2 | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=2 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=2 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_CONTRAST__replicate=2 | service | 36 | 0.3681 | 0.2778 | 0.4444 | 0.5278 |
| condition=X_V_STANDARD__replicate=1 | node | 12 | 0.0208 | 0.0000 | 0.0000 | 0.0833 |
| condition=X_V_STANDARD__replicate=1 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_STANDARD__replicate=1 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_STANDARD__replicate=1 | service | 36 | 0.2741 | 0.1944 | 0.3611 | 0.3889 |
| condition=X_V_STANDARD__replicate=2 | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_STANDARD__replicate=2 | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_STANDARD__replicate=2 | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=X_V_STANDARD__replicate=2 | service | 36 | 0.2741 | 0.1944 | 0.3611 | 0.3889 |

## RQ3.1 / exp_table_screenshot

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| X_C_TABLE_S | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C_TABLE_S | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C_TABLE_S | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_C_TABLE_S | service | 36 | 0.3056 | 0.2500 | 0.3889 | 0.3889 |

## RQ3.1 / exp_transfer_and_diagnostic_robustness

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| representation=X_C__transform=CANDIDATE_REORDER | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=CANDIDATE_REORDER | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=CANDIDATE_REORDER | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=CANDIDATE_REORDER | service | 36 | 0.4931 | 0.4167 | 0.5556 | 0.5833 |
| representation=X_C__transform=REANONYMIZE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=REANONYMIZE | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=REANONYMIZE | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_C__transform=REANONYMIZE | service | 36 | 0.4537 | 0.4167 | 0.5000 | 0.5000 |
| representation=X_V_CONTRAST__transform=CANDIDATE_REORDER | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=CANDIDATE_REORDER | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=CANDIDATE_REORDER | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=CANDIDATE_REORDER | service | 36 | 0.3704 | 0.2778 | 0.4722 | 0.5278 |
| representation=X_V_CONTRAST__transform=REANONYMIZE | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=REANONYMIZE | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=REANONYMIZE | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| representation=X_V_CONTRAST__transform=REANONYMIZE | service | 36 | 0.3056 | 0.2500 | 0.3611 | 0.3611 |

## RQ3.1 / exp_visual_diagnostic_mechanisms

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| condition=NO_CONTRAST_SELECTION__representation=X_C | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_C | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_C | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_C | service | 36 | 0.4306 | 0.3611 | 0.5278 | 0.5278 |
| condition=NO_CONTRAST_SELECTION__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_V_CONTRAST | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_V_CONTRAST | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_CONTRAST_SELECTION__representation=X_V_CONTRAST | service | 36 | 0.3727 | 0.3056 | 0.4444 | 0.4722 |
| condition=NO_GROUPING__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_GROUPING__representation=X_V_CONTRAST | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_GROUPING__representation=X_V_CONTRAST | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_GROUPING__representation=X_V_CONTRAST | service | 36 | 0.2741 | 0.1944 | 0.3611 | 0.3889 |
| condition=NO_SHARED_TIME__representation=X_V_CONTRAST | node | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_SHARED_TIME__representation=X_V_CONTRAST | pod | 9 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_SHARED_TIME__representation=X_V_CONTRAST | pod+service | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=NO_SHARED_TIME__representation=X_V_CONTRAST | service | 36 | 0.3991 | 0.3333 | 0.4444 | 0.5278 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_C | pod | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_C | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_C | service | 25 | 0.4600 | 0.4000 | 0.5200 | 0.5200 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_V_CONTRAST | pod | 4 | 0.0625 | 0.0000 | 0.0000 | 0.2500 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_V_CONTRAST | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_NON_TARGET_BUNDLE__representation=X_V_CONTRAST | service | 25 | 0.4433 | 0.3600 | 0.5200 | 0.5600 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_C | pod | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_C | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_C | service | 25 | 0.3000 | 0.2400 | 0.3600 | 0.3600 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_V_CONTRAST | pod | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_V_CONTRAST | pod+service | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| condition=REMOVE_TARGET_BUNDLE__representation=X_V_CONTRAST | service | 25 | 0.4413 | 0.3600 | 0.5200 | 0.5600 |

## RQ3.2 / mechanisms

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| NO_GROUPING__C_CONTRAST | node | 11 | 0.2727 | 0.2727 | 0.2727 | 0.2727 |
| NO_GROUPING__C_CONTRAST | pod | 8 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| NO_GROUPING__C_CONTRAST | pod+service | 7 | 0.4095 | 0.1429 | 0.7143 | 0.8571 |
| NO_GROUPING__C_CONTRAST | service | 34 | 0.2897 | 0.1471 | 0.4118 | 0.5294 |
| NO_GROUPING__M_TEXT | node | 11 | 0.2727 | 0.2727 | 0.2727 | 0.2727 |
| NO_GROUPING__M_TEXT | pod | 8 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| NO_GROUPING__M_TEXT | pod+service | 7 | 0.1429 | 0.0000 | 0.1429 | 0.4286 |
| NO_GROUPING__M_TEXT | service | 34 | 0.3333 | 0.2059 | 0.4412 | 0.5000 |
| REANONYMIZE__C_CONTRAST | node | 11 | 0.3182 | 0.1818 | 0.4545 | 0.4545 |
| REANONYMIZE__C_CONTRAST | pod | 8 | 0.0625 | 0.0000 | 0.1250 | 0.1250 |
| REANONYMIZE__C_CONTRAST | pod+service | 7 | 0.3333 | 0.1429 | 0.4286 | 0.7143 |
| REANONYMIZE__C_CONTRAST | service | 33 | 0.2727 | 0.0909 | 0.4242 | 0.5455 |
| REANONYMIZE__M_TEXT | node | 11 | 0.3485 | 0.2727 | 0.4545 | 0.4545 |
| REANONYMIZE__M_TEXT | pod | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| REANONYMIZE__M_TEXT | pod+service | 7 | 0.2857 | 0.1429 | 0.4286 | 0.4286 |
| REANONYMIZE__M_TEXT | service | 34 | 0.2647 | 0.1765 | 0.3235 | 0.3824 |
| REDUNDANT_NOISE__C_CONTRAST | node | 11 | 0.2576 | 0.1818 | 0.2727 | 0.4545 |
| REDUNDANT_NOISE__C_CONTRAST | pod | 8 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| REDUNDANT_NOISE__C_CONTRAST | pod+service | 7 | 0.3262 | 0.1429 | 0.4286 | 0.7143 |
| REDUNDANT_NOISE__C_CONTRAST | service | 34 | 0.3162 | 0.1471 | 0.5000 | 0.5294 |
| REDUNDANT_NOISE__M_TEXT | node | 11 | 0.2455 | 0.1818 | 0.2727 | 0.3636 |
| REDUNDANT_NOISE__M_TEXT | pod | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| REDUNDANT_NOISE__M_TEXT | pod+service | 7 | 0.1905 | 0.0000 | 0.4286 | 0.4286 |
| REDUNDANT_NOISE__M_TEXT | service | 34 | 0.3245 | 0.2059 | 0.3824 | 0.5294 |
| REMOVE_MATCHED_NONTARGET__C_CONTRAST | node | 7 | 0.4286 | 0.4286 | 0.4286 | 0.4286 |
| REMOVE_MATCHED_NONTARGET__C_CONTRAST | pod | 5 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| REMOVE_MATCHED_NONTARGET__C_CONTRAST | pod+service | 6 | 0.2639 | 0.0000 | 0.5000 | 0.6667 |
| REMOVE_MATCHED_NONTARGET__C_CONTRAST | service | 22 | 0.2667 | 0.0909 | 0.4091 | 0.5455 |
| REMOVE_MATCHED_NONTARGET__M_TEXT | node | 6 | 0.2833 | 0.1667 | 0.3333 | 0.5000 |
| REMOVE_MATCHED_NONTARGET__M_TEXT | pod | 5 | 0.2400 | 0.2000 | 0.2000 | 0.4000 |
| REMOVE_MATCHED_NONTARGET__M_TEXT | pod+service | 6 | 0.3472 | 0.1667 | 0.5000 | 0.6667 |
| REMOVE_MATCHED_NONTARGET__M_TEXT | service | 22 | 0.3614 | 0.1364 | 0.4545 | 0.7273 |
| REMOVE_TARGET__C_CONTRAST | node | 7 | 0.4286 | 0.4286 | 0.4286 | 0.4286 |
| REMOVE_TARGET__C_CONTRAST | pod | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| REMOVE_TARGET__C_CONTRAST | pod+service | 6 | 0.3056 | 0.1667 | 0.5000 | 0.5000 |
| REMOVE_TARGET__C_CONTRAST | service | 23 | 0.2971 | 0.1304 | 0.4348 | 0.5217 |
| REMOVE_TARGET__M_TEXT | node | 7 | 0.4286 | 0.4286 | 0.4286 | 0.4286 |
| REMOVE_TARGET__M_TEXT | pod | 5 | 0.0400 | 0.0000 | 0.0000 | 0.2000 |
| REMOVE_TARGET__M_TEXT | pod+service | 6 | 0.0417 | 0.0000 | 0.0000 | 0.1667 |
| REMOVE_TARGET__M_TEXT | service | 23 | 0.2428 | 0.1739 | 0.2609 | 0.3913 |
| REPLICATE_1__C_CONTRAST | node | 11 | 0.2727 | 0.2727 | 0.2727 | 0.2727 |
| REPLICATE_1__C_CONTRAST | pod | 8 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| REPLICATE_1__C_CONTRAST | pod+service | 7 | 0.4095 | 0.1429 | 0.7143 | 0.8571 |
| REPLICATE_1__C_CONTRAST | service | 33 | 0.2833 | 0.1212 | 0.4242 | 0.5455 |
| REPLICATE_1__M_TEXT | node | 11 | 0.2121 | 0.1818 | 0.2727 | 0.2727 |
| REPLICATE_1__M_TEXT | pod | 8 | 0.1500 | 0.1250 | 0.1250 | 0.2500 |
| REPLICATE_1__M_TEXT | pod+service | 6 | 0.3472 | 0.1667 | 0.5000 | 0.6667 |
| REPLICATE_1__M_TEXT | service | 34 | 0.3284 | 0.2059 | 0.4412 | 0.5000 |
| REPLICATE_2__C_CONTRAST | node | 11 | 0.2727 | 0.2727 | 0.2727 | 0.2727 |
| REPLICATE_2__C_CONTRAST | pod | 8 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| REPLICATE_2__C_CONTRAST | pod+service | 6 | 0.4444 | 0.1667 | 0.8333 | 0.8333 |
| REPLICATE_2__C_CONTRAST | service | 34 | 0.2750 | 0.1176 | 0.4118 | 0.5294 |
| REPLICATE_2__M_TEXT | node | 11 | 0.2000 | 0.1818 | 0.1818 | 0.2727 |
| REPLICATE_2__M_TEXT | pod | 8 | 0.1500 | 0.1250 | 0.1250 | 0.2500 |
| REPLICATE_2__M_TEXT | pod+service | 7 | 0.2262 | 0.1429 | 0.2857 | 0.4286 |
| REPLICATE_2__M_TEXT | service | 34 | 0.3309 | 0.2059 | 0.4412 | 0.5294 |

## RQ3.2 / representation

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_C_CONTRAST | node | 47 | 0.3262 | 0.2766 | 0.3830 | 0.3830 |
| P0_C_CONTRAST | pod | 34 | 0.0809 | 0.0294 | 0.1176 | 0.1471 |
| P0_C_CONTRAST | pod+service | 34 | 0.2127 | 0.0882 | 0.3235 | 0.4412 |
| P0_C_CONTRAST | service | 153 | 0.3553 | 0.2026 | 0.4967 | 0.6013 |
| P0_M_TEXT | node | 47 | 0.3280 | 0.2766 | 0.3830 | 0.4043 |
| P0_M_TEXT | pod | 34 | 0.1529 | 0.1176 | 0.1471 | 0.2353 |
| P0_M_TEXT | pod+service | 34 | 0.1740 | 0.0588 | 0.2941 | 0.3235 |
| P0_M_TEXT | service | 153 | 0.3851 | 0.2549 | 0.5163 | 0.5621 |
| P0_V_CONTRAST | node | 47 | 0.2064 | 0.1489 | 0.2340 | 0.2979 |
| P0_V_CONTRAST | pod | 34 | 0.1186 | 0.0588 | 0.1765 | 0.2059 |
| P0_V_CONTRAST | pod+service | 34 | 0.1544 | 0.1176 | 0.1765 | 0.2059 |
| P0_V_CONTRAST | service | 153 | 0.3928 | 0.2549 | 0.5425 | 0.5882 |
| P0_V_STANDARD | node | 47 | 0.2401 | 0.1915 | 0.2766 | 0.3191 |
| P0_V_STANDARD | pod | 34 | 0.0882 | 0.0588 | 0.1176 | 0.1176 |
| P0_V_STANDARD | pod+service | 34 | 0.1373 | 0.0588 | 0.2059 | 0.2647 |
| P0_V_STANDARD | service | 153 | 0.3357 | 0.2288 | 0.4183 | 0.5033 |
| SC_C_CONTRAST | node | 47 | 0.3394 | 0.2979 | 0.3617 | 0.4043 |
| SC_C_CONTRAST | pod | 34 | 0.1250 | 0.1176 | 0.1176 | 0.1471 |
| SC_C_CONTRAST | pod+service | 34 | 0.2485 | 0.1471 | 0.3235 | 0.4412 |
| SC_C_CONTRAST | service | 153 | 0.3382 | 0.1895 | 0.4706 | 0.5752 |
| SC_M_TEXT | node | 47 | 0.2496 | 0.1915 | 0.2979 | 0.3404 |
| SC_M_TEXT | pod | 34 | 0.2289 | 0.2059 | 0.2353 | 0.2941 |
| SC_M_TEXT | pod+service | 34 | 0.2961 | 0.2353 | 0.3235 | 0.4412 |
| SC_M_TEXT | service | 153 | 0.3841 | 0.2614 | 0.4902 | 0.5882 |
| SC_V_CONTRAST | node | 47 | 0.1532 | 0.1064 | 0.1702 | 0.2340 |
| SC_V_CONTRAST | pod | 34 | 0.0794 | 0.0588 | 0.0882 | 0.1176 |
| SC_V_CONTRAST | pod+service | 34 | 0.1480 | 0.0882 | 0.2059 | 0.2353 |
| SC_V_CONTRAST | service | 153 | 0.3178 | 0.2026 | 0.4248 | 0.4902 |
| SC_V_STANDARD | node | 47 | 0.1574 | 0.1064 | 0.1702 | 0.2553 |
| SC_V_STANDARD | pod | 34 | 0.0882 | 0.0882 | 0.0882 | 0.0882 |
| SC_V_STANDARD | pod+service | 34 | 0.0975 | 0.0294 | 0.1471 | 0.2353 |
| SC_V_STANDARD | service | 153 | 0.3211 | 0.2026 | 0.4248 | 0.5033 |
| SIRCL_TEXT | node | 47 | 0.3376 | 0.2979 | 0.3830 | 0.4043 |
| SIRCL_TEXT | pod | 34 | 0.3235 | 0.2059 | 0.5000 | 0.5000 |
| SIRCL_TEXT | pod+service | 34 | 0.1887 | 0.1471 | 0.2353 | 0.2647 |
| SIRCL_TEXT | service | 153 | 0.3809 | 0.2941 | 0.4771 | 0.5033 |
| T | node | 47 | 0.2844 | 0.2340 | 0.3404 | 0.3617 |
| T | pod | 34 | 0.0980 | 0.0882 | 0.1176 | 0.1176 |
| T | pod+service | 34 | 0.1740 | 0.0588 | 0.3235 | 0.3529 |
| T | service | 153 | 0.3867 | 0.2418 | 0.5621 | 0.5882 |
| TPV | node | 47 | 0.2383 | 0.2128 | 0.2553 | 0.2766 |
| TPV | pod | 34 | 0.2574 | 0.2059 | 0.3235 | 0.3529 |
| TPV | pod+service | 34 | 0.2206 | 0.1471 | 0.3235 | 0.3235 |
| TPV | service | 153 | 0.5147 | 0.4052 | 0.6405 | 0.6471 |

## RQ3.2 / selection

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_CAL | node | 47 | 0.3252 | 0.2766 | 0.3617 | 0.4043 |
| P0_CAL | pod | 34 | 0.1275 | 0.0882 | 0.1765 | 0.1765 |
| P0_CAL | pod+service | 31 | 0.1882 | 0.0645 | 0.3226 | 0.3871 |
| P0_CAL | service | 161 | 0.3459 | 0.2236 | 0.4596 | 0.5342 |
| P0_MORE | node | 47 | 0.3142 | 0.2340 | 0.3830 | 0.4468 |
| P0_MORE | pod | 34 | 0.0245 | 0.0000 | 0.0588 | 0.0588 |
| P0_MORE | pod+service | 31 | 0.1828 | 0.1290 | 0.2581 | 0.2581 |
| P0_MORE | service | 161 | 0.3318 | 0.2112 | 0.4224 | 0.5342 |
| SC_COVER | node | 47 | 0.2773 | 0.2340 | 0.3191 | 0.3404 |
| SC_COVER | pod | 34 | 0.1176 | 0.0882 | 0.1176 | 0.1765 |
| SC_COVER | pod+service | 31 | 0.1570 | 0.0645 | 0.2581 | 0.3548 |
| SC_COVER | service | 161 | 0.3404 | 0.2236 | 0.4161 | 0.5528 |
| SC_FULL | node | 47 | 0.2986 | 0.2766 | 0.3191 | 0.3404 |
| SC_FULL | pod | 34 | 0.1618 | 0.1471 | 0.1765 | 0.1765 |
| SC_FULL | pod+service | 31 | 0.2710 | 0.1613 | 0.3548 | 0.4839 |
| SC_FULL | service | 161 | 0.3777 | 0.2484 | 0.4969 | 0.5901 |
| SC_MORE | node | 47 | 0.2780 | 0.1915 | 0.3404 | 0.4255 |
| SC_MORE | pod | 34 | 0.1676 | 0.1471 | 0.1765 | 0.2059 |
| SC_MORE | pod+service | 31 | 0.2323 | 0.1290 | 0.3226 | 0.4194 |
| SC_MORE | service | 161 | 0.3727 | 0.2174 | 0.5155 | 0.6087 |
| SC_NO_BACKBONE | node | 47 | 0.2383 | 0.1915 | 0.2553 | 0.3191 |
| SC_NO_BACKBONE | pod | 34 | 0.0294 | 0.0000 | 0.0588 | 0.0588 |
| SC_NO_BACKBONE | pod+service | 31 | 0.1478 | 0.0968 | 0.1935 | 0.2258 |
| SC_NO_BACKBONE | service | 161 | 0.3125 | 0.1677 | 0.4410 | 0.5466 |
| SC_NO_STRATA | node | 47 | 0.2986 | 0.2553 | 0.3404 | 0.3617 |
| SC_NO_STRATA | pod | 34 | 0.1397 | 0.1176 | 0.1471 | 0.1765 |
| SC_NO_STRATA | pod+service | 31 | 0.2065 | 0.0968 | 0.2903 | 0.4194 |
| SC_NO_STRATA | service | 161 | 0.3517 | 0.1988 | 0.4783 | 0.6087 |
| SC_STRICT_PAIR | node | 47 | 0.3050 | 0.2766 | 0.3404 | 0.3404 |
| SC_STRICT_PAIR | pod | 34 | 0.1324 | 0.1176 | 0.1471 | 0.1471 |
| SC_STRICT_PAIR | pod+service | 31 | 0.2366 | 0.0968 | 0.3871 | 0.4516 |
| SC_STRICT_PAIR | service | 161 | 0.3640 | 0.2236 | 0.4658 | 0.5963 |
| X_ALIGNED | node | 47 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_ALIGNED | pod | 34 | 0.1275 | 0.1176 | 0.1471 | 0.1471 |
| X_ALIGNED | pod+service | 31 | 0.1290 | 0.0645 | 0.2258 | 0.2258 |
| X_ALIGNED | service | 161 | 0.3601 | 0.3043 | 0.4161 | 0.4472 |
| X_NATIVE_CAL | node | 47 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| X_NATIVE_CAL | pod | 34 | 0.1471 | 0.1471 | 0.1471 | 0.1471 |
| X_NATIVE_CAL | pod+service | 31 | 0.2204 | 0.1290 | 0.2903 | 0.3548 |
| X_NATIVE_CAL | service | 161 | 0.4042 | 0.3168 | 0.4845 | 0.5155 |

## RQ3.2 / test

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| SC_C_CONTRAST | node | 48 | 0.3160 | 0.2500 | 0.3958 | 0.3958 |
| SC_C_CONTRAST | pod | 40 | 0.0563 | 0.0500 | 0.0500 | 0.0750 |
| SC_C_CONTRAST | pod+service | 34 | 0.1833 | 0.0882 | 0.2353 | 0.3529 |
| SC_C_CONTRAST | service | 219 | 0.3967 | 0.2968 | 0.4840 | 0.5845 |
| SC_M_TEXT | node | 48 | 0.3583 | 0.3125 | 0.4167 | 0.4375 |
| SC_M_TEXT | pod | 40 | 0.0708 | 0.0500 | 0.1000 | 0.1000 |
| SC_M_TEXT | pod+service | 34 | 0.1431 | 0.0588 | 0.2059 | 0.2941 |
| SC_M_TEXT | service | 219 | 0.3983 | 0.2968 | 0.4977 | 0.5616 |
| SC_V_CONTRAST | node | 48 | 0.2271 | 0.1667 | 0.2917 | 0.3333 |
| SC_V_CONTRAST | pod | 40 | 0.0833 | 0.0750 | 0.1000 | 0.1000 |
| SC_V_CONTRAST | pod+service | 34 | 0.2093 | 0.0882 | 0.3235 | 0.3824 |
| SC_V_CONTRAST | service | 219 | 0.2756 | 0.1781 | 0.3744 | 0.4338 |
| SIRCL_TEXT | node | 48 | 0.2125 | 0.1875 | 0.2292 | 0.2500 |
| SIRCL_TEXT | pod | 40 | 0.1675 | 0.1000 | 0.2500 | 0.2750 |
| SIRCL_TEXT | pod+service | 34 | 0.2377 | 0.1471 | 0.3235 | 0.3529 |
| SIRCL_TEXT | service | 219 | 0.4800 | 0.3562 | 0.6256 | 0.6438 |
| T | node | 48 | 0.3090 | 0.2083 | 0.4167 | 0.4167 |
| T | pod | 40 | 0.0771 | 0.0250 | 0.1500 | 0.1750 |
| T | pod+service | 34 | 0.1667 | 0.0882 | 0.2647 | 0.2647 |
| T | service | 219 | 0.3969 | 0.2648 | 0.5525 | 0.5753 |
| TPV | node | 48 | 0.3299 | 0.3125 | 0.3542 | 0.3542 |
| TPV | pod | 40 | 0.1250 | 0.0750 | 0.1750 | 0.1750 |
| TPV | pod+service | 34 | 0.2157 | 0.1765 | 0.2647 | 0.2647 |
| TPV | service | 219 | 0.4574 | 0.3333 | 0.5845 | 0.6210 |

## RQ3.3 / budget

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_MORE_TRUE_B1024 | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0_MORE_TRUE_B1024 | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| P0_MORE_TRUE_B1024 | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| P0_MORE_TRUE_B1024 | service | 36 | 0.3935 | 0.3056 | 0.5278 | 0.5278 |
| P0_MORE_TRUE_B2048 | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0_MORE_TRUE_B2048 | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0_MORE_TRUE_B2048 | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| P0_MORE_TRUE_B2048 | service | 36 | 0.3981 | 0.3333 | 0.5000 | 0.5000 |
| P0_MORE_TRUE_B4096 | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0_MORE_TRUE_B4096 | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| P0_MORE_TRUE_B4096 | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| P0_MORE_TRUE_B4096 | service | 36 | 0.3634 | 0.2778 | 0.4722 | 0.5000 |
| TPV | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| TPV | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| TPV | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| TPV | service | 36 | 0.4074 | 0.3056 | 0.5556 | 0.5556 |
| W_G_B1024 | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| W_G_B1024 | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_G_B1024 | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_G_B1024 | service | 36 | 0.3889 | 0.3056 | 0.5278 | 0.5278 |
| W_G_B2048 | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_G_B2048 | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_G_B2048 | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_G_B2048 | service | 36 | 0.4120 | 0.3333 | 0.5278 | 0.5278 |
| W_G_B4096 | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_G_B4096 | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| W_G_B4096 | pod+service | 9 | 0.2407 | 0.1111 | 0.4444 | 0.4444 |
| W_G_B4096 | service | 36 | 0.3843 | 0.2778 | 0.5556 | 0.5556 |

## RQ3.3 / calibration

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| SC_TEXT_AS_RUN | node | 8 | 0.5417 | 0.5000 | 0.6250 | 0.6250 |
| SC_TEXT_AS_RUN | pod | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| SC_TEXT_AS_RUN | pod+service | 9 | 0.2963 | 0.2222 | 0.4444 | 0.4444 |
| SC_TEXT_AS_RUN | service | 35 | 0.2476 | 0.1429 | 0.3429 | 0.4000 |
| SC_TEXT_GUIDE_FIXED | node | 8 | 0.4167 | 0.3750 | 0.5000 | 0.5000 |
| SC_TEXT_GUIDE_FIXED | pod | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| SC_TEXT_GUIDE_FIXED | pod+service | 9 | 0.2222 | 0.1111 | 0.3333 | 0.3333 |
| SC_TEXT_GUIDE_FIXED | service | 35 | 0.3057 | 0.1714 | 0.4000 | 0.5429 |
| SC_TEXT_SOURCE_FIXED | node | 8 | 0.4167 | 0.3750 | 0.5000 | 0.5000 |
| SC_TEXT_SOURCE_FIXED | pod | 6 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| SC_TEXT_SOURCE_FIXED | pod+service | 9 | 0.2222 | 0.1111 | 0.3333 | 0.3333 |
| SC_TEXT_SOURCE_FIXED | service | 35 | 0.3057 | 0.1714 | 0.4000 | 0.5429 |
| TPV_BRIDGE | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| TPV_BRIDGE | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| TPV_BRIDGE | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| TPV_BRIDGE | service | 35 | 0.3905 | 0.2857 | 0.5429 | 0.5429 |

## RQ3.3 / check

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_MORE_TRUE | node | 17 | 0.2059 | 0.1765 | 0.2353 | 0.2353 |
| P0_MORE_TRUE | pod | 17 | 0.2353 | 0.1765 | 0.2941 | 0.2941 |
| P0_MORE_TRUE | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| P0_MORE_TRUE | service | 71 | 0.5575 | 0.4648 | 0.6620 | 0.6761 |
| SIRCL_TEXT | node | 17 | 0.3725 | 0.3529 | 0.4118 | 0.4118 |
| SIRCL_TEXT | pod | 17 | 0.2961 | 0.2353 | 0.3529 | 0.4118 |
| SIRCL_TEXT | pod+service | 13 | 0.2179 | 0.1538 | 0.3077 | 0.3077 |
| SIRCL_TEXT | service | 71 | 0.3533 | 0.2535 | 0.4789 | 0.4930 |
| TPV | node | 17 | 0.1765 | 0.1176 | 0.2353 | 0.2353 |
| TPV | pod | 17 | 0.1912 | 0.1176 | 0.2353 | 0.2941 |
| TPV | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| TPV | service | 71 | 0.5246 | 0.4507 | 0.5915 | 0.6056 |
| W_G | node | 17 | 0.3059 | 0.2353 | 0.3529 | 0.4118 |
| W_G | pod | 17 | 0.1618 | 0.0588 | 0.2353 | 0.2941 |
| W_G | pod+service | 13 | 0.3077 | 0.2308 | 0.3846 | 0.3846 |
| W_G | service | 71 | 0.5599 | 0.5070 | 0.6056 | 0.6197 |
| W_T | node | 17 | 0.3333 | 0.2353 | 0.4706 | 0.4706 |
| W_T | pod | 17 | 0.2941 | 0.2353 | 0.3529 | 0.3529 |
| W_T | pod+service | 13 | 0.2692 | 0.1538 | 0.4615 | 0.4615 |
| W_T | service | 71 | 0.4312 | 0.3099 | 0.5775 | 0.6056 |

## RQ3.3 / diagnostic

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| FIRST_TPV | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| FIRST_TPV | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| FIRST_TPV | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| FIRST_TPV | service | 37 | 0.4234 | 0.3243 | 0.5676 | 0.5676 |
| REPEAT | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| REPEAT | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| REPEAT | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| REPEAT | service | 37 | 0.4099 | 0.2973 | 0.5676 | 0.5676 |
| VERIFY_SAME | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| VERIFY_SAME | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| VERIFY_SAME | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| VERIFY_SAME | service | 37 | 0.4099 | 0.2973 | 0.5676 | 0.5676 |
| VERIFY_WITNESS | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| VERIFY_WITNESS | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| VERIFY_WITNESS | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| VERIFY_WITNESS | service | 37 | 0.4279 | 0.3243 | 0.5676 | 0.5676 |

## RQ3.3 / screen

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_MORE_TRUE | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0_MORE_TRUE | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0_MORE_TRUE | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| P0_MORE_TRUE | service | 35 | 0.4095 | 0.3429 | 0.5143 | 0.5143 |
| TPV | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| TPV | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| TPV | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| TPV | service | 35 | 0.4190 | 0.3143 | 0.5714 | 0.5714 |
| W_COHORT | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_COHORT | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_COHORT | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_COHORT | service | 35 | 0.4238 | 0.3429 | 0.5429 | 0.5429 |
| W_COHORT_MARGINAL | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_COHORT_MARGINAL | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_COHORT_MARGINAL | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_COHORT_MARGINAL | service | 35 | 0.4238 | 0.3429 | 0.5429 | 0.5429 |
| W_EXEC | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_EXEC | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_EXEC | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_EXEC | service | 35 | 0.4333 | 0.3429 | 0.5714 | 0.5714 |
| W_FRONT | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| W_FRONT | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_FRONT | pod+service | 9 | 0.0741 | 0.0000 | 0.2222 | 0.2222 |
| W_FRONT | service | 35 | 0.3881 | 0.2857 | 0.5143 | 0.5429 |
| W_RAW | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_RAW | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_RAW | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_RAW | service | 35 | 0.4238 | 0.3429 | 0.5429 | 0.5429 |
| W_SEM | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_SEM | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_SEM | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_SEM | service | 35 | 0.4333 | 0.3429 | 0.5714 | 0.5714 |
| W_SEM_EXEC | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| W_SEM_EXEC | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| W_SEM_EXEC | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| W_SEM_EXEC | service | 35 | 0.4333 | 0.3429 | 0.5714 | 0.5714 |

## RQ3.4 / exp_contract_alignment

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| SIRCL_IDS | node | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| SIRCL_IDS | pod | 5 | 0.3667 | 0.2000 | 0.6000 | 0.6000 |
| SIRCL_IDS | pod+service | 9 | 0.1389 | 0.1111 | 0.1111 | 0.2222 |
| SIRCL_IDS | service | 36 | 0.4523 | 0.3333 | 0.5556 | 0.6111 |
| SIRCL_IDS_ALT | node | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| SIRCL_IDS_ALT | pod | 5 | 0.3667 | 0.2000 | 0.6000 | 0.6000 |
| SIRCL_IDS_ALT | pod+service | 9 | 0.1667 | 0.1111 | 0.1111 | 0.3333 |
| SIRCL_IDS_ALT | service | 36 | 0.4662 | 0.3611 | 0.5556 | 0.6111 |
| SIRCL_NATIVE | node | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| SIRCL_NATIVE | pod | 5 | 0.3000 | 0.0000 | 0.8000 | 0.8000 |
| SIRCL_NATIVE | pod+service | 9 | 0.1389 | 0.1111 | 0.1111 | 0.2222 |
| SIRCL_NATIVE | service | 36 | 0.3773 | 0.3056 | 0.4444 | 0.4722 |

## RQ3.4 / exp_evidence_reasoning_factorial

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0H0K0_G | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0H0K0_G | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0H0K0_G | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| P0H0K0_G | service | 36 | 0.4352 | 0.3611 | 0.5556 | 0.5556 |
| P0H0K1_G | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| P0H0K1_G | pod | 6 | 0.1667 | 0.1667 | 0.1667 | 0.1667 |
| P0H0K1_G | pod+service | 9 | 0.1481 | 0.1111 | 0.2222 | 0.2222 |
| P0H0K1_G | service | 36 | 0.4074 | 0.3333 | 0.5000 | 0.5000 |
| P0H1K0_G | node | 8 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| P0H1K0_G | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0H1K0_G | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| P0H1K0_G | service | 36 | 0.4051 | 0.3056 | 0.5278 | 0.5556 |
| P0H1K1_G | node | 8 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| P0H1K1_G | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0H1K1_G | pod+service | 9 | 0.1481 | 0.1111 | 0.2222 | 0.2222 |
| P0H1K1_G | service | 36 | 0.4259 | 0.3333 | 0.5278 | 0.5278 |
| P0_MORE_TRUE | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| P0_MORE_TRUE | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P0_MORE_TRUE | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| P0_MORE_TRUE | service | 36 | 0.4259 | 0.3611 | 0.5278 | 0.5278 |
| P1H0K0_G | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| P1H0K0_G | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| P1H0K0_G | pod+service | 9 | 0.2037 | 0.1111 | 0.3333 | 0.3333 |
| P1H0K0_G | service | 36 | 0.4398 | 0.3611 | 0.5278 | 0.5278 |
| P1H0K1_G | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| P1H0K1_G | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| P1H0K1_G | pod+service | 9 | 0.2407 | 0.1111 | 0.4444 | 0.4444 |
| P1H0K1_G | service | 36 | 0.4537 | 0.3333 | 0.5833 | 0.5833 |
| P1H1K0_G | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| P1H1K0_G | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P1H1K0_G | pod+service | 9 | 0.2593 | 0.1111 | 0.4444 | 0.4444 |
| P1H1K0_G | service | 36 | 0.4491 | 0.3611 | 0.5556 | 0.5556 |
| P1H1K1_G | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| P1H1K1_G | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| P1H1K1_G | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| P1H1K1_G | service | 36 | 0.4306 | 0.3056 | 0.5833 | 0.5833 |
| TPV | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| TPV | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| TPV | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| TPV | service | 36 | 0.4213 | 0.3056 | 0.5833 | 0.5833 |

## RQ3.4 / exp_integrated_locked_check

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| P0_MORE_TRUE | node | 17 | 0.2059 | 0.1765 | 0.2353 | 0.2353 |
| P0_MORE_TRUE | pod | 15 | 0.2667 | 0.2000 | 0.3333 | 0.3333 |
| P0_MORE_TRUE | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| P0_MORE_TRUE | service | 68 | 0.5674 | 0.4853 | 0.6618 | 0.6765 |
| P1H1K0_G | node | 17 | 0.2059 | 0.1765 | 0.2353 | 0.2353 |
| P1H1K0_G | pod | 15 | 0.2500 | 0.1333 | 0.3333 | 0.4000 |
| P1H1K0_G | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| P1H1K0_G | service | 68 | 0.5797 | 0.5294 | 0.6324 | 0.6471 |
| P1H1K1_G | node | 17 | 0.2059 | 0.1765 | 0.2353 | 0.2353 |
| P1H1K1_G | pod | 15 | 0.2500 | 0.1333 | 0.3333 | 0.4000 |
| P1H1K1_G | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| P1H1K1_G | service | 68 | 0.5392 | 0.5000 | 0.5882 | 0.5882 |
| P1H1K1_T | node | 17 | 0.2745 | 0.1765 | 0.4118 | 0.4118 |
| P1H1K1_T | pod | 15 | 0.3389 | 0.2667 | 0.4000 | 0.4667 |
| P1H1K1_T | pod+service | 13 | 0.2051 | 0.0769 | 0.3846 | 0.3846 |
| P1H1K1_T | service | 68 | 0.3946 | 0.2647 | 0.5588 | 0.5588 |
| SIRCL_IDS | node | 17 | 0.4510 | 0.3529 | 0.5882 | 0.5882 |
| SIRCL_IDS | pod | 15 | 0.5333 | 0.5333 | 0.5333 | 0.5333 |
| SIRCL_IDS | pod+service | 13 | 0.1795 | 0.0769 | 0.3077 | 0.3077 |
| SIRCL_IDS | service | 68 | 0.3199 | 0.2206 | 0.4412 | 0.4559 |
| TPV | node | 17 | 0.1882 | 0.1176 | 0.2353 | 0.2941 |
| TPV | pod | 15 | 0.2167 | 0.1333 | 0.2667 | 0.3333 |
| TPV | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| TPV | service | 68 | 0.5404 | 0.4706 | 0.6029 | 0.6176 |

## RQ3.4 / exp_verified_visual_binding

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| G_NONE | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| G_NONE | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| G_NONE | pod+service | 9 | 0.2593 | 0.1111 | 0.4444 | 0.4444 |
| G_NONE | service | 35 | 0.4190 | 0.3429 | 0.5143 | 0.5143 |
| G_REPEAT | node | 8 | 0.6250 | 0.6250 | 0.6250 | 0.6250 |
| G_REPEAT | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| G_REPEAT | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| G_REPEAT | service | 35 | 0.4286 | 0.3429 | 0.5429 | 0.5429 |
| G_VERIFIED | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| G_VERIFIED | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| G_VERIFIED | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| G_VERIFIED | service | 35 | 0.4000 | 0.2857 | 0.5429 | 0.5429 |
| T_NONE | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| T_NONE | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| T_NONE | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| T_NONE | service | 35 | 0.3952 | 0.2857 | 0.5429 | 0.5429 |
| T_REPEAT | node | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| T_REPEAT | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| T_REPEAT | pod+service | 9 | 0.2407 | 0.1111 | 0.4444 | 0.4444 |
| T_REPEAT | service | 35 | 0.2857 | 0.2000 | 0.4000 | 0.4000 |
| T_VERIFIED | node | 8 | 0.4167 | 0.3750 | 0.5000 | 0.5000 |
| T_VERIFIED | pod | 6 | 0.2500 | 0.1667 | 0.3333 | 0.3333 |
| T_VERIFIED | pod+service | 9 | 0.1111 | 0.0000 | 0.3333 | 0.3333 |
| T_VERIFIED | service | 35 | 0.3571 | 0.2571 | 0.5143 | 0.5143 |

## RQ3.5 / A

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| E_P_D_P | node | 8 | 0.1250 | 0.1250 | 0.1250 | 0.1250 |
| E_P_D_P | pod | 6 | 0.2000 | 0.1667 | 0.1667 | 0.3333 |
| E_P_D_P | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| E_P_D_P | service | 35 | 0.4095 | 0.2857 | 0.5143 | 0.6286 |
| E_P_D_S | node | 8 | 0.2812 | 0.2500 | 0.2500 | 0.3750 |
| E_P_D_S | pod | 6 | 0.2222 | 0.1667 | 0.3333 | 0.3333 |
| E_P_D_S | pod+service | 9 | 0.2444 | 0.1111 | 0.4444 | 0.5556 |
| E_P_D_S | service | 35 | 0.3762 | 0.2286 | 0.5429 | 0.6000 |
| E_S_D_P | node | 8 | 0.2188 | 0.1250 | 0.2500 | 0.3750 |
| E_S_D_P | pod | 6 | 0.5056 | 0.3333 | 0.6667 | 0.8333 |
| E_S_D_P | pod+service | 9 | 0.3556 | 0.2222 | 0.4444 | 0.5556 |
| E_S_D_P | service | 35 | 0.4381 | 0.3143 | 0.6000 | 0.6000 |
| E_S_D_S | node | 8 | 0.2604 | 0.1250 | 0.3750 | 0.5000 |
| E_S_D_S | pod | 6 | 0.3056 | 0.1667 | 0.5000 | 0.5000 |
| E_S_D_S | pod+service | 9 | 0.1111 | 0.0000 | 0.2222 | 0.2222 |
| E_S_D_S | service | 35 | 0.4357 | 0.2857 | 0.6000 | 0.6286 |
| SIRCL_IDS_NATIVE | node | 8 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| SIRCL_IDS_NATIVE | pod | 6 | 0.3889 | 0.1667 | 0.6667 | 0.6667 |
| SIRCL_IDS_NATIVE | pod+service | 9 | 0.1389 | 0.1111 | 0.1111 | 0.2222 |
| SIRCL_IDS_NATIVE | service | 35 | 0.4652 | 0.3714 | 0.5429 | 0.6000 |
| T_NATIVE | node | 8 | 0.3750 | 0.3750 | 0.3750 | 0.3750 |
| T_NATIVE | pod | 6 | 0.0556 | 0.0000 | 0.1667 | 0.1667 |
| T_NATIVE | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| T_NATIVE | service | 35 | 0.3333 | 0.2000 | 0.5143 | 0.5143 |

## RQ3.5 / B

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| J_COND | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| J_COND | pod | 5 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| J_COND | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| J_COND | service | 37 | 0.4144 | 0.2973 | 0.5405 | 0.5946 |
| J_JOINT | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| J_JOINT | pod | 5 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| J_JOINT | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| J_JOINT | service | 37 | 0.4279 | 0.3243 | 0.5405 | 0.5946 |
| J_MARG | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| J_MARG | pod | 5 | 0.2667 | 0.2000 | 0.4000 | 0.4000 |
| J_MARG | pod+service | 9 | 0.1852 | 0.1111 | 0.3333 | 0.3333 |
| J_MARG | service | 37 | 0.3964 | 0.2703 | 0.5405 | 0.5946 |
| MORE | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| MORE | pod | 5 | 0.2667 | 0.2000 | 0.4000 | 0.4000 |
| MORE | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| MORE | service | 37 | 0.4144 | 0.3514 | 0.5135 | 0.5135 |
| TPV | node | 8 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| TPV | pod | 5 | 0.2667 | 0.2000 | 0.4000 | 0.4000 |
| TPV | pod+service | 9 | 0.2222 | 0.1111 | 0.4444 | 0.4444 |
| TPV | service | 37 | 0.4009 | 0.2973 | 0.5405 | 0.5405 |
| W_NO_K | node | 8 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |
| W_NO_K | pod | 5 | 0.2667 | 0.2000 | 0.4000 | 0.4000 |
| W_NO_K | pod+service | 9 | 0.2593 | 0.1111 | 0.4444 | 0.4444 |
| W_NO_K | service | 37 | 0.4369 | 0.3514 | 0.5405 | 0.5405 |

## RQ3.6 / A_check120

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| E_P_D_P | node | 9 | 0.3889 | 0.3333 | 0.4444 | 0.4444 |
| E_P_D_P | pod | 16 | 0.3229 | 0.1875 | 0.5625 | 0.5625 |
| E_P_D_P | pod+service | 13 | 0.2436 | 0.1538 | 0.3846 | 0.3846 |
| E_P_D_P | service | 59 | 0.5492 | 0.4237 | 0.6780 | 0.7458 |
| E_P_D_S | node | 9 | 0.4444 | 0.3333 | 0.5556 | 0.5556 |
| E_P_D_S | pod | 16 | 0.2604 | 0.1875 | 0.3750 | 0.3750 |
| E_P_D_S | pod+service | 13 | 0.2013 | 0.0769 | 0.3077 | 0.4615 |
| E_P_D_S | service | 59 | 0.5246 | 0.4237 | 0.6610 | 0.6949 |
| E_S_D_P | node | 9 | 0.2222 | 0.1111 | 0.3333 | 0.3333 |
| E_S_D_P | pod | 16 | 0.5208 | 0.4375 | 0.6250 | 0.6250 |
| E_S_D_P | pod+service | 13 | 0.2051 | 0.1538 | 0.3077 | 0.3077 |
| E_S_D_P | service | 59 | 0.4816 | 0.4068 | 0.5763 | 0.5932 |
| E_S_D_S | node | 9 | 0.4815 | 0.3333 | 0.6667 | 0.6667 |
| E_S_D_S | pod | 16 | 0.4583 | 0.3750 | 0.5625 | 0.5625 |
| E_S_D_S | pod+service | 13 | 0.1218 | 0.0769 | 0.1538 | 0.2308 |
| E_S_D_S | service | 59 | 0.4237 | 0.3559 | 0.4915 | 0.5254 |
| E_S_G_P_V_S | node | 9 | 0.3333 | 0.2222 | 0.4444 | 0.4444 |
| E_S_G_P_V_S | pod | 16 | 0.5312 | 0.5000 | 0.5625 | 0.5625 |
| E_S_G_P_V_S | pod+service | 13 | 0.2051 | 0.1538 | 0.3077 | 0.3077 |
| E_S_G_P_V_S | service | 59 | 0.4949 | 0.4068 | 0.6102 | 0.6271 |
| E_S_G_S_V_P | node | 9 | 0.4444 | 0.3333 | 0.5556 | 0.5556 |
| E_S_G_S_V_P | pod | 16 | 0.4583 | 0.3750 | 0.5625 | 0.5625 |
| E_S_G_S_V_P | pod+service | 13 | 0.1026 | 0.0769 | 0.1538 | 0.1538 |
| E_S_G_S_V_P | service | 59 | 0.4257 | 0.3559 | 0.4915 | 0.5254 |
| MORE | node | 9 | 0.2222 | 0.1111 | 0.3333 | 0.3333 |
| MORE | pod | 16 | 0.3125 | 0.2500 | 0.3750 | 0.3750 |
| MORE | pod+service | 13 | 0.2308 | 0.1538 | 0.3077 | 0.3077 |
| MORE | service | 59 | 0.5932 | 0.4915 | 0.6949 | 0.7288 |
| SIRCL_IDS_NATIVE | node | 9 | 0.6111 | 0.5556 | 0.6667 | 0.6667 |
| SIRCL_IDS_NATIVE | pod | 16 | 0.5312 | 0.5000 | 0.5625 | 0.5625 |
| SIRCL_IDS_NATIVE | pod+service | 13 | 0.1667 | 0.0769 | 0.3077 | 0.3077 |
| SIRCL_IDS_NATIVE | service | 59 | 0.3347 | 0.2373 | 0.4576 | 0.4746 |
| TPV | node | 9 | 0.2222 | 0.1111 | 0.3333 | 0.3333 |
| TPV | pod | 16 | 0.2344 | 0.1875 | 0.2500 | 0.3125 |
| TPV | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| TPV | service | 59 | 0.5734 | 0.4915 | 0.6441 | 0.6780 |
| T_NATIVE | node | 9 | 0.3333 | 0.2222 | 0.4444 | 0.4444 |
| T_NATIVE | pod | 16 | 0.1458 | 0.1250 | 0.1875 | 0.1875 |
| T_NATIVE | pod+service | 13 | 0.2179 | 0.0769 | 0.4615 | 0.4615 |
| T_NATIVE | service | 59 | 0.4441 | 0.3051 | 0.6271 | 0.6441 |
| W_NO_K | node | 9 | 0.2778 | 0.2222 | 0.3333 | 0.3333 |
| W_NO_K | pod | 16 | 0.3125 | 0.1875 | 0.4375 | 0.4375 |
| W_NO_K | pod+service | 13 | 0.2692 | 0.1538 | 0.3846 | 0.3846 |
| W_NO_K | service | 59 | 0.6073 | 0.5593 | 0.6610 | 0.6610 |

## Tournament / R01

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R01 | node | 51 | 0.1722 | 0.0980 | 0.2549 | 0.2941 |
| R01 | pod | 38 | 0.3456 | 0.2368 | 0.3947 | 0.5526 |
| R01 | pod+service | 35 | 0.2295 | 0.1429 | 0.2857 | 0.3714 |
| R01 | service | 176 | 0.4526 | 0.3125 | 0.5455 | 0.7102 |

## Tournament / R02

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R02 | node | 46 | 0.1141 | 0.0435 | 0.1522 | 0.2174 |
| R02 | pod | 29 | 0.2546 | 0.1034 | 0.3448 | 0.5172 |
| R02 | pod+service | 30 | 0.0806 | 0.0000 | 0.1333 | 0.2333 |
| R02 | service | 121 | 0.2393 | 0.0744 | 0.3719 | 0.5372 |

## Tournament / R03

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R03 | node | 44 | 0.1277 | 0.0455 | 0.2045 | 0.2500 |
| R03 | pod | 26 | 0.2192 | 0.0769 | 0.3462 | 0.4615 |
| R03 | pod+service | 30 | 0.1033 | 0.0000 | 0.1000 | 0.3333 |
| R03 | service | 112 | 0.3246 | 0.1339 | 0.4643 | 0.6696 |

## Tournament / R04

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R04 | node | 42 | 0.1238 | 0.0238 | 0.2143 | 0.2857 |
| R04 | pod | 24 | 0.2340 | 0.0417 | 0.4167 | 0.5000 |
| R04 | pod+service | 30 | 0.1178 | 0.0000 | 0.1667 | 0.3333 |
| R04 | service | 97 | 0.2625 | 0.0722 | 0.4021 | 0.5979 |

## Tournament / R05

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R05 | node | 41 | 0.0630 | 0.0000 | 0.1220 | 0.1463 |
| R05 | pod | 23 | 0.1703 | 0.0000 | 0.3043 | 0.4348 |
| R05 | pod+service | 30 | 0.2122 | 0.1333 | 0.2000 | 0.4667 |
| R05 | service | 90 | 0.2246 | 0.0889 | 0.2889 | 0.5111 |

## Tournament / R06

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R06 | node | 41 | 0.0850 | 0.0000 | 0.1707 | 0.2439 |
| R06 | pod | 23 | 0.1348 | 0.0000 | 0.1739 | 0.3913 |
| R06 | pod+service | 26 | 0.0878 | 0.0000 | 0.1154 | 0.2692 |
| R06 | service | 82 | 0.2022 | 0.0000 | 0.3537 | 0.5732 |

## Tournament / R07

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R07 | node | 41 | 0.0638 | 0.0244 | 0.0976 | 0.1463 |
| R07 | pod | 23 | 0.0754 | 0.0000 | 0.1304 | 0.2174 |
| R07 | pod+service | 26 | 0.1000 | 0.0000 | 0.1154 | 0.3077 |
| R07 | service | 82 | 0.2065 | 0.0610 | 0.3171 | 0.4512 |

## Tournament / R08

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R08 | node | 40 | 0.1113 | 0.0750 | 0.1250 | 0.1750 |
| R08 | pod | 23 | 0.1717 | 0.0435 | 0.2174 | 0.3913 |
| R08 | pod+service | 26 | 0.1603 | 0.1154 | 0.1923 | 0.2692 |
| R08 | service | 77 | 0.2853 | 0.1299 | 0.3766 | 0.5325 |

## Tournament / R09

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R09 | node | 37 | 0.0901 | 0.0541 | 0.1351 | 0.1351 |
| R09 | pod | 22 | 0.2265 | 0.0909 | 0.3182 | 0.4545 |
| R09 | pod+service | 23 | 0.0775 | 0.0435 | 0.0870 | 0.1739 |
| R09 | service | 67 | 0.2741 | 0.0896 | 0.4179 | 0.6269 |

## Tournament / R10

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R10 | node | 35 | 0.0152 | 0.0000 | 0.0286 | 0.0571 |
| R10 | pod | 20 | 0.0958 | 0.0000 | 0.2000 | 0.2500 |
| R10 | pod+service | 22 | 0.1606 | 0.0909 | 0.2273 | 0.2727 |
| R10 | service | 61 | 0.1817 | 0.0492 | 0.2951 | 0.4262 |

## Tournament / R11

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R11 | node | 35 | 0.1786 | 0.1429 | 0.2000 | 0.2286 |
| R11 | pod | 20 | 0.3767 | 0.3500 | 0.4000 | 0.4500 |
| R11 | pod+service | 20 | 0.1500 | 0.1000 | 0.2000 | 0.2000 |
| R11 | service | 58 | 0.2351 | 0.1207 | 0.2759 | 0.4828 |

## Tournament / R12

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R12 | node | 30 | 0.0344 | 0.0000 | 0.0667 | 0.1000 |
| R12 | pod | 13 | 0.1372 | 0.0769 | 0.1538 | 0.3077 |
| R12 | pod+service | 18 | 0.0926 | 0.0000 | 0.2222 | 0.2222 |
| R12 | service | 51 | 0.2052 | 0.0588 | 0.3137 | 0.4314 |

## Tournament / R13

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R13 | node | 30 | 0.0428 | 0.0000 | 0.0667 | 0.1333 |
| R13 | pod | 12 | 0.0903 | 0.0000 | 0.1667 | 0.2500 |
| R13 | pod+service | 18 | 0.1481 | 0.0556 | 0.2778 | 0.2778 |
| R13 | service | 48 | 0.1146 | 0.0208 | 0.1458 | 0.3333 |

## Tournament / R14

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R14 | node | 30 | 0.0333 | 0.0000 | 0.0333 | 0.1000 |
| R14 | pod | 12 | 0.0833 | 0.0000 | 0.1667 | 0.1667 |
| R14 | pod+service | 17 | 0.0951 | 0.0000 | 0.1765 | 0.2941 |
| R14 | service | 47 | 0.1160 | 0.0000 | 0.2340 | 0.3191 |

## Tournament / R15

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R15 | node | 30 | 0.0667 | 0.0000 | 0.1000 | 0.1667 |
| R15 | pod | 12 | 0.0694 | 0.0000 | 0.1667 | 0.1667 |
| R15 | pod+service | 17 | 0.1176 | 0.0588 | 0.1176 | 0.2353 |
| R15 | service | 47 | 0.1631 | 0.0426 | 0.2128 | 0.4468 |

## Tournament / R16

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R16 | node | 30 | 0.0956 | 0.0000 | 0.1333 | 0.3000 |
| R16 | pod | 12 | 0.0556 | 0.0000 | 0.1667 | 0.1667 |
| R16 | pod+service | 16 | 0.0521 | 0.0000 | 0.1250 | 0.1250 |
| R16 | service | 45 | 0.1400 | 0.0444 | 0.2000 | 0.3333 |

## Tournament / R17

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R17 | node | 30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R17 | pod | 12 | 0.0278 | 0.0000 | 0.0833 | 0.0833 |
| R17 | pod+service | 16 | 0.1302 | 0.0625 | 0.1250 | 0.3125 |
| R17 | service | 43 | 0.1477 | 0.0465 | 0.2326 | 0.3256 |

## Tournament / R18

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R18 | node | 30 | 0.0678 | 0.0000 | 0.1000 | 0.2000 |
| R18 | pod | 12 | 0.0278 | 0.0000 | 0.0833 | 0.0833 |
| R18 | pod+service | 15 | 0.0722 | 0.0000 | 0.1333 | 0.2000 |
| R18 | service | 41 | 0.1163 | 0.0000 | 0.1951 | 0.3171 |

## Tournament / R19

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R19 | node | 30 | 0.1161 | 0.0333 | 0.1333 | 0.3000 |
| R19 | pod | 12 | 0.0556 | 0.0000 | 0.1667 | 0.1667 |
| R19 | pod+service | 15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R19 | service | 41 | 0.1134 | 0.0000 | 0.2195 | 0.3415 |

## Tournament / R20

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R20 | node | 29 | 0.0569 | 0.0345 | 0.0345 | 0.1379 |
| R20 | pod | 12 | 0.0694 | 0.0000 | 0.1667 | 0.1667 |
| R20 | pod+service | 15 | 0.0667 | 0.0000 | 0.0667 | 0.2000 |
| R20 | service | 41 | 0.1720 | 0.0488 | 0.2683 | 0.3902 |

## Tournament / R21

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R21 | node | 28 | 0.0476 | 0.0357 | 0.0714 | 0.0714 |
| R21 | pod | 12 | 0.1111 | 0.0833 | 0.1667 | 0.1667 |
| R21 | pod+service | 15 | 0.1911 | 0.1333 | 0.2667 | 0.3333 |
| R21 | service | 39 | 0.1265 | 0.0256 | 0.1795 | 0.3590 |

## Tournament / R22

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R22 | node | 27 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R22 | pod | 11 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R22 | pod+service | 13 | 0.0962 | 0.0769 | 0.0769 | 0.1538 |
| R22 | service | 38 | 0.2145 | 0.0789 | 0.3684 | 0.4474 |

## Tournament / R23

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R23 | node | 27 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R23 | pod | 11 | 0.0455 | 0.0000 | 0.0909 | 0.0909 |
| R23 | pod+service | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R23 | service | 35 | 0.2819 | 0.0857 | 0.4286 | 0.6286 |

## Tournament / R24

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R24 | node | 27 | 0.0093 | 0.0000 | 0.0000 | 0.0370 |
| R24 | pod | 11 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R24 | pod+service | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R24 | service | 32 | 0.1099 | 0.0000 | 0.1875 | 0.3125 |

## Tournament / R25

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R25 | node | 27 | 0.0093 | 0.0000 | 0.0000 | 0.0370 |
| R25 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R25 | pod+service | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R25 | service | 32 | 0.0745 | 0.0000 | 0.0938 | 0.2500 |

## Tournament / R26

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R26 | node | 27 | 0.0185 | 0.0000 | 0.0370 | 0.0370 |
| R26 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R26 | pod+service | 12 | 0.0278 | 0.0000 | 0.0833 | 0.0833 |
| R26 | service | 32 | 0.1245 | 0.0000 | 0.1875 | 0.3438 |

## Tournament / R27

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R27 | node | 27 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R27 | pod | 11 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R27 | pod+service | 12 | 0.0208 | 0.0000 | 0.0000 | 0.0833 |
| R27 | service | 32 | 0.1714 | 0.0625 | 0.2500 | 0.3438 |

## Tournament / R28

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R28 | node | 27 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R28 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R28 | pod+service | 12 | 0.0375 | 0.0000 | 0.0000 | 0.1667 |
| R28 | service | 30 | 0.0950 | 0.0000 | 0.1667 | 0.3000 |

## Tournament / R29

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R29 | node | 27 | 0.0123 | 0.0000 | 0.0370 | 0.0370 |
| R29 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R29 | pod+service | 12 | 0.0625 | 0.0000 | 0.0833 | 0.1667 |
| R29 | service | 30 | 0.0733 | 0.0000 | 0.1333 | 0.1667 |

## Tournament / R30

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R30 | node | 27 | 0.0463 | 0.0370 | 0.0370 | 0.0741 |
| R30 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R30 | pod+service | 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R30 | service | 30 | 0.1111 | 0.0000 | 0.2000 | 0.2667 |

## Tournament / R31

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R31 | node | 26 | 0.0910 | 0.0000 | 0.1154 | 0.3077 |
| R31 | pod | 11 | 0.0606 | 0.0000 | 0.1818 | 0.1818 |
| R31 | pod+service | 12 | 0.0417 | 0.0000 | 0.0833 | 0.0833 |
| R31 | service | 30 | 0.0822 | 0.0000 | 0.1333 | 0.2667 |

## Tournament / R32

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R32 | node | 26 | 0.0590 | 0.0000 | 0.0769 | 0.1923 |
| R32 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R32 | pod+service | 12 | 0.0583 | 0.0000 | 0.0833 | 0.1667 |
| R32 | service | 30 | 0.1078 | 0.0000 | 0.1667 | 0.3000 |

## Tournament / R33

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R33 | node | 26 | 0.0192 | 0.0000 | 0.0000 | 0.0769 |
| R33 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R33 | pod+service | 12 | 0.0417 | 0.0000 | 0.0833 | 0.0833 |
| R33 | service | 30 | 0.0483 | 0.0000 | 0.0667 | 0.1333 |

## Tournament / R34

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R34 | node | 26 | 0.0679 | 0.0000 | 0.1154 | 0.2308 |
| R34 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R34 | pod+service | 12 | 0.0417 | 0.0000 | 0.0833 | 0.0833 |
| R34 | service | 30 | 0.0900 | 0.0000 | 0.2000 | 0.2333 |

## Tournament / R35

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R35 | node | 26 | 0.0590 | 0.0000 | 0.0769 | 0.1923 |
| R35 | pod | 11 | 0.0455 | 0.0000 | 0.0909 | 0.0909 |
| R35 | pod+service | 12 | 0.0417 | 0.0000 | 0.0833 | 0.0833 |
| R35 | service | 30 | 0.1594 | 0.0667 | 0.2333 | 0.3000 |

## Tournament / R36

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R36 | node | 26 | 0.0474 | 0.0000 | 0.0385 | 0.1923 |
| R36 | pod | 11 | 0.0303 | 0.0000 | 0.0909 | 0.0909 |
| R36 | pod+service | 12 | 0.0833 | 0.0000 | 0.1667 | 0.1667 |
| R36 | service | 28 | 0.0988 | 0.0000 | 0.1429 | 0.3214 |

## Tournament / R37

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R37 | node | 26 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R37 | pod | 11 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| R37 | pod+service | 12 | 0.0583 | 0.0000 | 0.0000 | 0.2500 |
| R37 | service | 28 | 0.0685 | 0.0000 | 0.1429 | 0.1786 |

## Tournament / R38

| arm | stratum | n | mrr | ac@1 | ac@3 | ac@5 |
|---|---|---|---|---|---|---|
| R38 | node | 26 | 0.0192 | 0.0000 | 0.0385 | 0.0385 |
| R38 | pod | 11 | 0.0606 | 0.0000 | 0.1818 | 0.1818 |
| R38 | pod+service | 12 | 0.0625 | 0.0000 | 0.0833 | 0.1667 |
| R38 | service | 28 | 0.0833 | 0.0000 | 0.1429 | 0.2143 |
