# Native change-detection cost component

Upstream: https://github.com/deepcharles/ruptures
Commit: `ee1c8ff8a548d54c641b2bb471562165931f31c7` (retrieved 2026-09-14).
License: BSD-2-Clause, retained in `LICENSE`.

`original/` contains byte-identical `src/ruptures/base.py`,
`src/ruptures/exceptions.py`, and `src/ruptures/costs/costl2.py`.
SHA256, respectively:

- `8da7b0e9007f7fb9c8ddf8216630c5863f8325f08172b2ba405d3ebdfe6565ff`
- `f62a5580911b13d81ab162347595395f14f7b308cfb9539e2abd151d915f3964`
- `eddf850c9aee63382296f0fa27e523b77bdaba2215a395ec7aa06941729ca8b8`

`adapted/` differs only in two local imports in CostL2 and use of Python's
`itertools.pairwise` instead of ruptures' equivalent pairwise helper in BaseCost.
It requires NumPy and typing_extensions, already in the CPU environment.
No import of an external checkout or installation/build of ruptures is needed.

The RQ3 selector uses the native L2 cost and its algebraically equivalent
vectorized two-window gain. Its multi-width search, finite-observation masking,
normalization, evidence budgets and RCA application are **CanvasRCA adaptations**,
not a reproduction of the complete ruptures detector or a published RCA system.
CPU tests compare vectorized gains against the copied cost component.
