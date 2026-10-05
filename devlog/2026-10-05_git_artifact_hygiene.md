# 2026-10-05 — Git 同步前的大文件检查

## Scope and status

用户要求恢复当前实验，并检查大体积实验产物是否被 Git 忽略；补齐规则后提供同步命令。本记录仅涉及版本控制卫生，实验恢复另记 RQ3.18 执行日志。

## What happened

既有规则已经覆盖 RQ 结果、preparation、renders、attention、模型、缓存和运行日志。检查 Git 可见文件和索引后发现：大型逐病例 CSV、报告发布暂存副本以及部分第三方 benchmark 数据/解压日志仍会被纳入同步。

在 `.gitignore` 增加具体路径和文件名规则，保留源码、实验配置、报告正文、分析脚本、重要文档及小型审计材料。39 个此前已经被跟踪的相关文件仅执行 `git rm --cached`，共 46,010,689 字节；逐文件 SHA-256 验证磁盘内容全部保留不变。没有删除本地实验结果，没有改写 Git 历史，没有提交或推送。

## Validation

更新后 Git 索引中匹配忽略规则的文件数为零；五项代表性大产物忽略检查及五项源码/文档保留检查通过，`.gitignore` diff 检查通过。Git 可见文件中剩余大于 1 MiB 的只有第三方代码 notebook `packages/ReAct/WebShop.ipynb`（1,262,229 字节），作为代码保留。

移除索引的清单、原文件大小和哈希保存在本地 `artifacts/gitignore_audit_20261005.json`；该目录按原规则忽略。上述大小是当前工作树检查，不表示历史 Git 对象已压缩或移除。

## Next steps

用户可在当前 `canvasrca_nibi` 分支暂存和检查变更，再正常 commit、push 到 `origin/canvasrca_nibi`。无需强推；本次尚未执行这些命令。
