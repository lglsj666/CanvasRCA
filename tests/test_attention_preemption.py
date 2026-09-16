"""CPU regression: KV recomputation must not erase published answer attention."""
import copy
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import numpy as np
import torch

from vlmrca.vlm import attention_probe as probe


class AttentionPreemptionTests(unittest.TestCase):
    def test_recomputed_prefill_keeps_answer_profile(self):
        for visual in (False, True):
            with self.subTest(visual=visual):
                tokens = np.array([[248056 if visual else 7, 8, 9, 11, 12, 13, 14]])
                batch = NS(req_ids=["cpu"], num_prompt_tokens=[3],
                           num_computed_tokens_cpu=[0], token_ids_cpu=tokens)
                state = NS(runner=NS(input_batch=batch), scheduler_output=None)
                layer = NS(layer_name="model.layers.3.self_attn.attn", num_heads=1,
                           num_kv_heads=1, head_size=2, impl=NS(scale=1.0))
                decoder = {11: '{"services":[', 12: '"123"', 13: ']', 14: ',"reason":"ok"}'}
                tokenizer = NS(decode=lambda ids, **_: "".join(decoder.get(i, "") for i in ids))
                published = []
                with (patch.object(probe, "enabled", return_value=True),
                      patch.object(probe, "_model_policy", return_value=(3, 248056, "qwen3.8-27b")),
                      patch.object(probe, "_STATE", state), patch.object(probe, "_KV", {}),
                      patch.object(probe, "_FAILED_REQUESTS", set()),
                      patch.object(probe, "_generation_tokenizer", return_value=tokenizer),
                      patch.object(probe, "_write_sidecar", side_effect=lambda _, v: published.append(copy.deepcopy(v)))):
                    def capture(start, count):
                        batch.num_computed_tokens_cpu = [start]
                        state.scheduler_output = NS(num_scheduled_tokens={"cpu": count})
                        values = torch.arange(count * 2, dtype=torch.float32).reshape(count, 2) / 10
                        probe._capture(layer, values, values, values)

                    capture(0, 3)
                    for position in (3, 4, 5):
                        capture(position, 1)
                    first = copy.deepcopy(published[-1])
                    self.assertEqual(first["generation_target_attention"]["target_token_count"], 2)
                    capture(0, 6)  # Replay prompt and already-counted output after preemption.
                    capture(6, 1)
                    probe._publish_generation_profile(probe._KV["cpu"])
                    self.assertEqual(published[-1]["generation_target_attention"], first["generation_target_attention"])
                    self.assertEqual(published[-1]["prompt_attention_weights"], first["prompt_attention_weights"])
                    self.assertEqual(probe._KV["cpu"]["generation_target_count"], 2)


if __name__ == "__main__":
    unittest.main()
