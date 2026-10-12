# Qwen 单模型重分析记录

2026-10-11 清理补记：用户要求删除 RQ3.8 之前实验的原始结果和中间产物，本目录的重复 `staged_assets/` 已删除，已发布报告及其外部图表保留。下文“历史原始实验仍留在对应 results”是 2026-09-30 当时的记录，已不适用；脚本保留不表示旧原始结果仍可读取。详见[清理审计](../../issues/Pre_Unified_Artifact_Deletion_2026-10-11.md)。

日期：2026-09-30。范围：11 份主报告及其统计附件、图表和报告索引。

## 当前研究口径

当前问题是：**Qwen3.8-27B 在哪些证据、故障机制和表示条件下改善或退化？**
Qwen 自身的正向结果不需要另一个模型支持才成立；负向结果也不被删除。
多模型验证留给后续阶段，不作为本轮结论的否决条件。不将这些结论推广为所有模型的性质。

只改变报告的研究范围及相应统计，不改变原调用的模型身份、输入、输出、标签、分数或有效性状态。
这是现有数据的事后重分析，不伪称新的独立预注册试验。

## 完整备份

编辑前已将整个 `docs/` 复制至：

`/home/lglsj/CanvasRCA-report-backup-20260930.zJzQJW/docs`

复制后 `diff -qr` 无差异。报告原文件的逐文件 SHA-256、字节数保存在
[backup_manifest.json](backup_manifest.json)。原版图表、解释、分析脚本和来源记录均可从该副本恢复。
历史原始实验仍留在对应 `RQs/*/results/`，没有删除或改写。

## 统计规则

1. 仅纳入 Qwen 模型记录；公共数据特征与明确标注的 CPU 基线可保留。
2. 保留各实验原来的病例集合、共同掩码/成对掩码、失败处理、分组和全部 Qwen 对照。
3. MRR/AC/AVG 沿用冻结样本级分数，不因输出不合偏好重新评分；缺失不补成完成。
4. 用可用的逐病例记录、析因差值和稳健性记录重新计算主配对统计。先核对 N 和均值，不能仅为匹配原 p 任意换病例。
5. Holm 只覆盖当前 Qwen 科学比较集合；不按显著与否、方向、数据集好坏删掉 Qwen 假设。
6. 同一 Qwen 病例对的原始 p 和 dz 不依赖其他模型。附件中未重新构造的探索统计保留原 Qwen 原始统计、重新校正，并在 `raw_statistic_source` 中说明，不冒称全部从原始轨迹重跑。
7. 浮点 CSV 往返或差值运算顺序可能将数学相等的秩差拆成近似并列。主结果保留历史数值并列规则；发生差异时在 `*_recomputed_sensitivity` 中保存本次复算值，而不是静默换检验。
8. 病例级与事件组级分析分开。组均差改变事件权重，不能以组级显著冒充病例级显著。
9. 显著改善、显著退化、有希望但未显著、没有可识别动作、证据不足分别陈述。未显著不等于无效；正点估计也不自动等于确认。
10. 不报告 CI；不把 arms、重复回答或复用回答当额外病例。模型失败、基础设施缺失、设计不可执行保持原阶段口径。

## 比较 family

| 报告 | Qwen-only 校正范围 |
|---|---|
| RQ1.1 | 主比较按数据范围×指标；factorial 按数据范围×指标×阶数；补充跨表示保留全部 7 项 |
| RQ1.1 QA V2 | 数据范围×P 的全部表示对照；端点仍为已核验的语义 V2 |
| RQ2.1 | 原 experiment/subset/dataset 已编码的 family；不只留下改进方案 |
| Tournament | 每数据范围的全部 37 个相邻轮共同剩余集对照；特征另成 family |
| RQ3.1 | final 12 项视觉部署主比较；eval 独立 family；机制按实验列示 |
| RQ3.2 | 原 family×数据范围；跨阶段引用的对照仍用原病例掩码 |
| RQ3.3 | 每阶段全部 Qwen 对照与原范围；组级敏感性单独校正 |
| RQ3.4 | 每阶段原比较；7 项 PHK 析因单列 |
| RQ3.5 | experiment×family；条件比较为另外的探索 family |
| RQ3.6-A | 原 evidence/instruction/components/calibration family；补充病例、数据集、层次分别列示 |
| RQ3.6-B | 原 stat_family；carrier 另给跨三个实验全部 17 项的敏感性校正 |
| RQ3.7 | 4 项病例级主比较、4 项组级敏感性、3 项析因；6 项等价编码比较和6项翻转对重复比较分开 |
| 跨实验画像 | study×stage×scope×dimension；全部 Qwen 方法/分层，不挑显著子组 |

未被原科学 family 元数据明确区分的辅助表，统一采用该表内全部 Qwen 检验的保守探索 family。
它们不承担主结论。未校正原始 p 不能单独作为“显著”的依据。

## 重要结论修订

- RQ1.1：TPV 与 G 区正向贡献成立；M/R 的视觉代价、文字截图不足仍需保留。
- RQ2.1：较高分辨率是 Qwen 的有效方向，但成本和数据集异质性不可省略。
- RQ3.3–3.6-A：W、去 K 和部分 S 证据是值得继续研究的 Qwen 候选；不再用跨模型要求否定它们。接口校准是有显著证据的文本贡献。
- RQ3.6-B：HP_DEDUP 的 Graph−Text 在 B2 carrier family 内有支持；跨全部 carrier 的更宽敏感性未支持普遍显著。
- RQ3.7：LOCAL_LINK 对 TPV 的提升成立；对 T_MATCH 的事件组分析有显著正结果，病例级主比较则经校正后未达显著。两者都明确保留。
- X/SC 的 node/资源损害和视觉退化仍是真实的 Qwen 结果，不能为正向故事删掉。

## 可复算

离线统计；不加载模型、不调用 API、不执行 preparation、不启动 CPU 回归或 GPU smoke。

```bash
cd /home/lglsj/CanvasRCA_nibi
/home/lglsj/CanvasRCA/venvs/tools/bin/python \
  docs/experiment_reports/_qwen_only_reanalysis/reanalyze.py \
  --backup /home/lglsj/CanvasRCA-report-backup-20260930.zJzQJW \
  --root /home/lglsj/CanvasRCA_nibi
```

该命令从不可变备份重建 `staged_assets/`，不会覆盖主报告。
`publish.py` 使用 `narratives.py` 的人工审订解释和生成表格发布报告；它仅接受仍与备份一致的待替换报告附件，防止误覆盖后续人工修改。
不要在已经修订的目录上盲目再执行发布；需要再次编辑时，先备份当前版本。

[重分析清单](reanalysis_summary.json)、[校正后显著状态变化审计](significance_changes.json)、[发布清单](publication.json)与最终检查文件保留本轮来源。
显著状态变化文件仅作版本审计，不用于选择哪些结论进入报告。
