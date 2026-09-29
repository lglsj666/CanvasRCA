## root_level

| model | root_level | n | covered | ever_ac3 | ever_ac5 |
| --- | --- | --- | --- | --- | --- |
| gemma-4-26b-a4b | node | 51 | 22 | 39.0000 | 43.0000 |
| gemma-4-26b-a4b | pod | 38 | 32 | 35.0000 | 37.0000 |
| gemma-4-26b-a4b | pod+service | 35 | 25 | 27.0000 | 29.0000 |
| gemma-4-26b-a4b | service | 356 | 335 | 353.0000 | 355.0000 |
| qwen3.8-27b | node | 51 | 25 | 37.0000 | 45.0000 |
| qwen3.8-27b | pod | 38 | 27 | 33.0000 | 33.0000 |
| qwen3.8-27b | pod+service | 35 | 23 | 29.0000 | 30.0000 |
| qwen3.8-27b | service | 356 | 319 | 353.0000 | 356.0000 |

## fault_family

| model | fault_family | n | covered | ever_ac3 | ever_ac5 |
| --- | --- | --- | --- | --- | --- |
| gemma-4-26b-a4b | application_jvm | 18 | 17 | 18.0000 | 18.0000 |
| gemma-4-26b-a4b | availability | 31 | 22 | 23.0000 | 25.0000 |
| gemma-4-26b-a4b | cpu | 64 | 54 | 59.0000 | 61.0000 |
| gemma-4-26b-a4b | disk_io | 68 | 55 | 64.0000 | 66.0000 |
| gemma-4-26b-a4b | http_injection | 54 | 48 | 53.0000 | 54.0000 |
| gemma-4-26b-a4b | memory_gc | 77 | 66 | 73.0000 | 74.0000 |
| gemma-4-26b-a4b | network_config_socket | 38 | 35 | 38.0000 | 38.0000 |
| gemma-4-26b-a4b | network_corrupt | 20 | 19 | 20.0000 | 20.0000 |
| gemma-4-26b-a4b | network_delay | 48 | 41 | 47.0000 | 48.0000 |
| gemma-4-26b-a4b | network_duplicate | 7 | 4 | 5.0000 | 6.0000 |
| gemma-4-26b-a4b | network_loss | 47 | 45 | 46.0000 | 46.0000 |
| gemma-4-26b-a4b | network_partition_bandwidth | 8 | 8 | 8.0000 | 8.0000 |
| qwen3.8-27b | application_jvm | 18 | 15 | 18.0000 | 18.0000 |
| qwen3.8-27b | availability | 31 | 21 | 26.0000 | 27.0000 |
| qwen3.8-27b | cpu | 64 | 54 | 60.0000 | 61.0000 |
| qwen3.8-27b | disk_io | 68 | 58 | 65.0000 | 67.0000 |
| qwen3.8-27b | http_injection | 54 | 45 | 53.0000 | 54.0000 |
| qwen3.8-27b | memory_gc | 77 | 63 | 69.0000 | 74.0000 |
| qwen3.8-27b | network_config_socket | 38 | 32 | 37.0000 | 37.0000 |
| qwen3.8-27b | network_corrupt | 20 | 17 | 20.0000 | 20.0000 |
| qwen3.8-27b | network_delay | 48 | 39 | 47.0000 | 47.0000 |
| qwen3.8-27b | network_duplicate | 7 | 3 | 5.0000 | 6.0000 |
| qwen3.8-27b | network_loss | 47 | 40 | 45.0000 | 45.0000 |
| qwen3.8-27b | network_partition_bandwidth | 8 | 7 | 7.0000 | 8.0000 |
