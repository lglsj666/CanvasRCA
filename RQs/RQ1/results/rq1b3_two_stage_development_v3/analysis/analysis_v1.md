# RQ1b3 two-stage analysis — gemma-4-26b-a4b

- Status: **valid_failed**
- Paired incidents: 90 / 90
- Final accuracy T/V/H: 0.6222 / 0.1667 / 0.5889
- Final H−T: -0.0333 (diagnostic Pratt-Wilcoxon p=0.531615; p is not a development gate)
- Stage-1 panel accuracy T/V/H: 0.8944 / 0.5083 / 0.8917
- Stage-1 H−T: -0.0028
- H repairs / breaks: 10 / 13
- Oracle Stage-2 accuracy: 0.8000
- Gate checks: `{"final_h_minus_t_at_least_0.05": false, "hybrid_mean_ledger_error_below_text": false, "hybrid_repairs_exceed_breaks": false, "integrity_passed": false, "ledger_h_minus_t_at_least_0.05": false, "oracle_stage2_accuracy_at_least_0.95": false}`

This exposed-development analysis uses no confidence interval and no p-value
promotion threshold. Passing only authorizes the already-frozen independent
gate; it is not confirmatory evidence.
