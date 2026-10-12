# RQ3.1 单 Agent 实现与静态检查交接 — 2026-09-16

状态：本轮代码集成完成，静态检查通过，按用户指示暂停。
**没有运行 CPU 测试、preparation、渲染、smoke、训练或模型推理。**
没有启动或恢复子 Agent。没有打开 test 遥测进行开发。

## 实现范围与修复

1. 完整 public evidence source 接收已授权的 case identity，不再把新 test
   cases 错送到旧 RQ2.1 的 eval480 专用入口。原 RQ2.1 源码保持不变。
2. Evidence pool、原生 SIRCL comparator 和零模型调用排名共用一次 case
   准备结果。公共来源绑定错误显式失败，不回退到另一套 preparation。
3. P0 校准和 X 使用同一公共事实投影；原 T/V/TPV 保留原构造。
   原基线→校准的差异不能算作纯选择增益。
4. 主 arms、机制干预、重复调用、预算/重复负载和非语义变换统一进入
   request builder。重复调用的 replicate 身份进入请求复用边界。
5. 运行器采用有界提交（最多 36 个在途请求），不将全批图像堆在内存中。
   相同模型、case、实际输入及 replicate 的合法复用保留明确来源记录。
6. 修正 retry conversation 路径、完成标记与原始响应校验；保留两个模型
   的已完成记录以重建汇总。中断恢复不拼接半截模型回答。
7. 代码/config/source-bound 缓存、方法锁定前 test 入口阻断、磁盘保护、
   进程互斥和写盘排空接入执行路径。静态检查不自动解除运行资格门禁。
8. 修复继承 renderer 的四个失效 imports，以及 smoke 嵌套计时器返回后
   未恢复外层时限的问题。移除运行时 mock/fallback；测试夹具只保留在 tests。

## 静态检查结果

| 检查 | 结果 |
|---|---|
| Python AST 解析及内存 compile（不 import/execute 项目） | 44 个文件通过 |
| 本地显式 import 符号源码核查 | 233 个符号，无未解析项 |
| JSON 语法 | 两份配置通过 |
| Ruff F | RQ3.1 src 和三个根目录测试文件通过 |
| Ruff I | 本轮功能模块、contrast renderer 和测试文件通过 |
| Shell `bash -n` | 六个脚本通过，不运行脚本 |
| `git diff --check` | 通过 |
| 五个功能模块加 init 行数 | 5,985 / 7,500（非空非注释，含 docstrings；上限于本报告后由用户提高） |

静态工具来自 `/home/lglsj/CanvasRCA/venvs/tools/`，工作树为
`/home/lglsj/CanvasRCA_nibi/`；首次误用工作树下不存在的 venv 路径未执行检查，
随后改用共享 tools 环境并完整重跑以上静态检查。未以命令外壳返回值掩盖失败。
代码审阅覆盖数据语义/隔离、请求分支/对照、缓存/恢复/持久化；这不是已执行的
故障注入测试，也不保证动态依赖、资源容量或所有数据边界没有问题。

## 尚未验证；下一步不能自动开始

- 旧 68-test CPU 通过记录先于本轮集成，不能视为当前代码通过。
- 候选 semantic budget=96 尚未通过当前代码的完整 capacity、视觉可读性
  和模型 processor/token preflight。旧 2/9-case partial 不是完成证明。
- 新增/修改的 CPU 回归测试、原工具同输入对照和断电恢复故障注入均未运行。
- 六百秒 smoke 的实时进程/计时器行为、原始输出持久化及模型切换未 live 验证。
- case 准备目前逐 case 执行；没有测量吞吐，不能承诺性能或宣称八 worker 已启用。
- 没有生成 `cpu_acceptance.json`，没有 smoke 通过记录，不能开始正式实验。

收到下一步授权后，先进行上述运行验证，再判断是否具备 smoke 资格。
所有实验结果和共享 corpus 保留，旧 RQ 与统一模型配置不修改。
