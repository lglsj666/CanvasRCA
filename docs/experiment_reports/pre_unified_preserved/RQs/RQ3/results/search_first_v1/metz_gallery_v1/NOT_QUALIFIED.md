# CPU-only incomplete preview — not qualified

2026-09-12. Actual public-source inspection found MET-Z values with k/M/G
suffixes. The initial SEARCH26 selector/probe incorrectly treated them as
unavailable. Stopped the owned CPU gallery process215239 before any Solver
calls; partial PNGs remain here, not eligible for prepare/run.318 tests had
passed but did not cover these real formatted values. The successor adds
suffix/finite handling and actual-value tests and uses metz_gallery_v2.
