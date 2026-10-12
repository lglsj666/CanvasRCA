# Corrected runtime trial — pre-live review, 2026-09-12

The same reviewed 12-target gallery is reused. It remains byte-identical in
PNG, packet, manifest and prompt to the corrected-trace non-thinking parent.
No candidate-panel is painted; the exhaustive candidate list remains in text.

After fixing explicit local-profile preservation, the complete CPU regression
passed **205/205**, zero skipped, in 72.81 seconds (`cpu_thinking_low_v2.xml`).
Tests include sourced local-shell default/explicit selection, live-command
mismatch rejection, reasoning aliases, partial response and end-to-end RQ3
persistence/resume. Source audit: 5,982 counted lines. Shell syntax and diff
whitespace checks pass. The run manifest now hashes both environment scripts.

Do not reuse v1 responses as intended thinking outputs. This new run uses the
same twelve input targets and bounded config, with actual service-argv
verification before any model request. Inspect server.log and reasoning fields
again after completion; planned runtime metadata alone is insufficient.
