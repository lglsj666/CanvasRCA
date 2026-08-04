# RQ1b2 compositional-complexity analysis

- stage: `development`
- status: `failed`
- primary model: `gemma-4-26b-a4b`
- inferential unit: opaque incident (queries are not independent)

| Model | High V-T | Interaction | Policy-best fixed | Repairs / breaks | Status |
|---|---:|---:|---:|---:|---|
| gemma-4-26b-a4b | -0.3250 | +0.0000 | -0.1812 | 4 / 30 | failed |

The development gate is descriptive and does not use a p-value for promotion. The disjoint 150-case gate applies the registered Pratt-Wilcoxon tests.
