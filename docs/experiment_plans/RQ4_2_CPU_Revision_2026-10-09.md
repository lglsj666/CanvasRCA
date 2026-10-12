# RQ4.2 CPU修订：来源字段作用域与实际完整准入

用户在第一次容量失败后授权修改代码、测试及必要的计划调整；本次终点改为**全部CPU测试和门槛通过后停止，GPU smoke与正式运行不启动**。原失败报告与源码快照保留，不改写为通过。

核心假设、五臂、完整事实、单调用纯视觉、模型/解码、复用历史基线、1500调用登记和统计主比较不变。本轮没有模型调用。

前次容量估计约为最大画布的117%–129%，主要开销为重复字段路径、逐卡片标题/留白，以及完整关系图；不能将一个不紧凑的实现失败当作所有完整表示都不可能。

## 本次允许的编译调整

- 新增显式 `source_scopes_v2` 可读操作。原字段名称按已有分隔符组织为连续作用域标题，下级字段只画后缀；独立解码须恢复原完整字段名、值、顺序和出现次数。不是合并相同数值或删除来源记录。
- 短字段以两列排放，长值占整行；数字拼写原样，禁止竖向拆数字或舍入。图形仍用已有统一renderer组件；旧profile和默认语义不变。
- 所有诊断字形实际至少18px，基准标题由旧实现的24px改为18px，保持统一字形下限；卡片内部留白由16px改为8px、间隙9px改为4px。明确这是新版本显示规格，而非声称旧规格通过。
- 普通卡片仍512px、四区域等面积，保留既有四种画布和16384图像token上限。不删除任何诊断事实、不改数值、不调processor限制。只有实际完整装箱、真实processor、全图几何和来源绑定同时合格才算通过。
- 四区布局、来源关系分组、算子CPU等价性、QA构造、运行离线替身及恢复路径全部补齐；真实GPU特征一致性留待用户下一次授权的smoke，不能假称已经测试。

若任何进一步的科学定义需要调整，先记录理由和版本，再作未使用排名/标签的CPU核验；不能只为拿到通过标记降低科学强度。

## CPU几何评估后的明确修订

作用域共享后，原四象限面积必要条件为A22 59/60、A25 60/60、Aegis 80/100。剩余主要阻碍是完整宽关系图及来源单元在短区域内装箱。改用四个等面积**竖向区域**：主图宽4096，高先试3072再4096，各区域宽1024且等高；普通卡片仍512，关系图/目录最多1024。所有patch、原始位置、图像token上限、四组等容量及23/4块调度保持。NATIVE4相应输入四个同像素竖区，仍作为边界/位置也改变的系统对照。

此变更在模型调用前由公开几何驱动，属于共同编译器修订，所有臂共享；没有按任何MRR或标签选布局。旧四象限失败如实保留。新增profile允许DOM测量的小卡片小于历史180px最小面板，但仍须完整字段、18px实际字形、无溢出与32px网格，不以减少字体通过。已有layered_grid去掉无图元的尾部留白，仅显式新profile启用。

## Implementation clarifications and repairs (CPU v3)

These decisions are based only on public inputs and CPU geometry; no new model answers are available.

- The generic header occupies 32 px. All panels and source-unit rectangles align to the 32 px merger-cell grid. Ordinary panels stay 512 px wide. Only graphs and the **exhaustive candidate directory** may occupy a full 1024 px region.
- Source units close records by source identity; request-pair collections additionally use their explicit `PAIRxx` record key. Aggregated graph components are separate global units: sharing an endpoint/source reference does not merge a whole graph with every record it mentions. Both entity directories are global components without owner-derived optimization edges. Entity ordering comes from the unique `Candidate IDs · exhaustive fixed order` directory, never the shorter `Observed entities` directory.
- Packing first follows deterministic candidate/source order. If fragmentation prevents packing, a bounded deterministic column-allocation search tries complete units, then restores source order within each column. It never omits, splits, scales or revalues a unit. A failed bounded search remains a failure.
- The explicit `source_scopes_v2` profile factors contiguous field-name prefixes, wraps prose values, and preserves scalar spellings and source occurrences. The curve's horizontal domain and every available observation remain unchanged. Its compact time axis places the generic axis label beside its endpoints. Event rows have an intrinsic height determined by their count; all event readings and five grid lines remain, with endpoint time labels. Existing default component semantics remain unchanged.
- All rendered scopes are independently decoded back to original name/value pairs. SVG and HTML overflow, candidate coverage, source bindings, actual processor resizing and processed font size remain admission checks.
- `CardDiagnosticInkV1` measures alpha-weighted **diagnostic ink**, excluding HTML backing colors, panel frames, generic header, and the constant interior background of graph nodes. Node outlines, text, axes, data marks, edge strokes and arrowheads remain. Earlier v2 masks mistakenly counted constant node backgrounds as evidence foreground; their failure report and masks are retained. This corrects the measurement, not the 20% intervention threshold.
- v2 also confused the two entity directories when assigning source owners. Its preliminary intervention pass is superseded and is not a qualification credential. v3 corrects directory roles and independently repeats affected rendering and grouping checks. The interrupted v2 processor audit is preserved as incomplete.
- QA uses four fixed colors and underlines on existing value glyphs through the new registered `question_colors` operation. It adds no answer, diagnostic fact or geometry displacement. Static instructions map pink/yellow/blue/orange to 1A/1B/2A/2B. Two transcriptions, two binding questions and two phase comparisons use the same inputs across FULL/GEOM/SEM/NATIVE4. When no suitable directed relation connects the selected records, only the cross-card relation question is not applicable. Fewer than two qualifying phase records makes that fixed case's QA inapplicable; there is no replacement case.
- The original SEM and SHAM intervention thresholds are unchanged. SHAM is cancelled if its registered population gate fails. Final active-arm and statistical-family status is frozen from the **v3** report, not a prior CPU attempt.

The current user-authorized endpoint remains complete CPU qualification and a pause. GPU smoke and all diagnostic/QA model calls remain disabled. CPU random-weight architecture tests do not load the real checkpoint or use CUDA.


## Final CPU disposition — 2026-10-09

The corrected v3 common representation passes packing/rendering on all 220 cases. The registered SEM intervention qualifies 50/60 AIOPS-2022, 55/60 AIOPS-2025 and 38/100 AegisLab cases; the last dataset fails the unchanged 50% gate. SHAM itself qualifies on all three datasets. Superseded v2 outcomes do not authorize cancelling SHAM and proceeding with four arms.

Under the user's revision authority, evaluated ink-proportional distribution of each normalized entity-edge weight among its source-unit pairs (total edge weight conserved). A fixed 30-case probe preceded the full 220-case audit. Counts 53/60, 54/60, 44/100 still fail; the variant is not adopted or added as an arm. A deterministic third-group-cycle escape was tested only on the same 30-case probe, with strict cut reduction and unchanged background/source closure constraints; it did not resolve the issue and was not adopted. Both attempts remain separately auditable. Do not pool successes across versions or search seeds/layouts to satisfy the gate.

The candidate stops at the registered scientific gate. Current-version QA, actual processor and complete runtime admission are not claimed complete; no CPU qualification credential is issued. GPU smoke and formal execution remain disabled. No new model calls, GPU feature extraction or checkpoint inference occurred. See the [CPU report](../experiment_reports/RQ4_2_CPU_Revision_2026-10-09.md).
