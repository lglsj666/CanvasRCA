# Qwen targeted completion audit

Reason: the first formal pass left four `infrastructure_error` timeouts and one
otherwise completed trajectory whose mandatory generation-target attention was
`not_captured`. The original files were moved here before an identical-contract
resume. The resume made exactly five calls, completed all five targets with
required attention, and skipped the other 1,915 Qwen records.

Original trajectory hashes:

| File | SHA256 |
|---|---|
| `INC-028FABE30ADE__V_NEUTRAL.json` | `0b7b1bdf94955973ef7fa8f26958b64bb0e87a647d0294dbc157bfa754a26847` |
| `INC-028FABE30ADE__V_NEUTRAL.md` | `8316f227a9a271d4ac164714df39f0e5756cbedbd3a26680cafe264fa1ed2e2f` |
| `INC-11AFCDDD7B6E__V_NEUTRAL.json` | `7697922925935ba78fc073df50f116c60bcf9a0f48bf83b9fc4aface2d49d5c1` |
| `INC-11AFCDDD7B6E__V_NEUTRAL.md` | `7af4584f3a01cd47db40e05becb30cac3b9956b147e7b3dd8c0bf700053ac5f5` |
| `INC-133324A21C16__V_PLACEBO.json` | `fc5b9404d17bc1575648cc9eee639731b6bdfe1d98ecbf1bc1187dec9041e296` |
| `INC-133324A21C16__V_PLACEBO.md` | `6c4458147ca5e4e74a66f67776f29147abed65dd24ba95851944a85f8d634c3a` |
| `INC-0D58D7514724__V_NEUTRAL.json` | `e740f75b0364f181987699eece6df98c65d3567a6b094f35a5a46cb266db5cd6` |
| `INC-0D58D7514724__V_NEUTRAL.md` | `8edb847c981474a0a25e11375e0041c41e7be8241e218cf05173f338377947a2` |
| `INC-64E5D665C311__V_NEUTRAL.json` | `419b60b2b7359ca3b2513122323dd3facac56968643bb55df994c2fe49b43dc6` |
| `INC-64E5D665C311__V_NEUTRAL.md` | `7b8334eef6a2e7739553c54b22fcb7d71f6dbb05705b32a858a28190ab9b64a7` |

Original partial-attention directory:
`attention/0af2d34177cb63bfc36c7ceaca753538ee6de20c58fc478a20c6bb837bd21fb8/`.
Its file hashes were:

- `image_00.json`: `7126ca2f5785e33bae78558a3e5fbd215776d6b030e9708b799ea737b494a334`
- `image_00.png`: `9cfa687c8dc76ac79e7b1c8080c1265ddef263c9b8189bcea11e926818fe1bd1`
- `raw_probe.json`: `aa4f3f6593035651ed1ec98eb008ef6f726af8a7488dde01098bfc0ab8d5d1b0`
- `text_attention.json`: `613352f4ebf376cfc62631cb4b8bddcfa3c26b2f402dd87438b3915f1b50d0f8`
