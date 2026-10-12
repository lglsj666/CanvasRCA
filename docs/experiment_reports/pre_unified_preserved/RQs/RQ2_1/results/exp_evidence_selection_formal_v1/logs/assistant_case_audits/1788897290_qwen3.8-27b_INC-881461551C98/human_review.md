# Whole-case audit outcome

All 16 logical targets, all 253 distinct input lines with their ordering map,
all complete responses and all six submitted PNGs were inspected. Fourteen
model calls had normal stop reasons, 140–233 output tokens, valid persistence
and both registered attention phases. Two conditions were zero-call L-card
infeasible outcomes. Unsupported diagnostic assertions were model behavior.

One public-input defect was identified: a selected P_RANDOM log's embedded
calendar date entered numeric previews. It was not established to be the fault
injection time. The relative-time-only input rule nevertheless requires a
common projection correction. Broader scope, immutable original inputs and
record-level replay decisions are recorded in
`RQs/RQ2_1/results/qualification/log_calendar_repair/`. This audit must not be
treated as an unconditional pass of the original P_RANDOM input.
