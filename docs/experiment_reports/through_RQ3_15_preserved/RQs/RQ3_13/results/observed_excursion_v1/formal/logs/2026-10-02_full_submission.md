# RQ3.13 全量启动交接 — 2026-10-02

用户明确授权启动全量，解除前一轮停在smoke的执行暂停。原始config、注册140病例、输入/渲染/模型配方/评分/预算均保持冻结，未修改历史资格或烟测结果。仅gates.py执行授权门禁的局部后继更新；128个其他冻结文件字节未变，非门禁AST及所有原资格检查结构一致。独立执行授权receipt和新operational source archive保存于qualification/activation_v1/。源兼容、11个授权有效/拒绝检查、7组CPU函数回归及静态检查通过；原完整CPU与18-call smoke资格继承，无新增烟测调用。

本次scope为AIOPS2022/2025各60、Aegis20，exposed eval；140×6=840位置。819真实formal请求，21相同输入引用；280个文字/图形重复位置均真实独立调用，不择优。原smoke18/18、900总allocation及882formal limit保留，不重置旧RQ3.12的829调用。仅Qwen本地GPU，36并发、8writer；不跑test/Gemma/attention/训练。

进程启动使用独立setsid会话。首个普通nohup launcher未保持运行且未发出模型调用；该启动方式已调整，实验输入和模型程序没有修订。当前supervisor21497、server21505、runner21930。模型加载99.195秒后正式runner开始；启动核对时25原子commit、36请求started、61调用累计、0失败flags，GPU100%/78946MiB。首3已提交完整graph和actual input/PNG/policy核对通过。当前只是完整队列已运行，不是完整840结果或方法效果确认。

启动receipt formal/submission.json；实时摘要可执行 bash RQs/RQ3_13/scripts/local.sh status；日志formal/logs/、状态formal/supervisor.json、计数formal/calls.sqlite、结果formal/flags和completed。后台正常结束时写phase_complete.qwen3.8-27b.json并关闭owned server。不得根据部分MRR调整方法或停止未完成臂。无需重复旧烟测、重渲染或重新确认授权；恢复先信任atomic markers，跳过完成调用/phase，保留失败和实际消耗。

预计全量约60–90分钟，取决于队列与300秒请求超时。分析应待完整终态和writer drain；保持预注册主要/次要族、配对infra缺失、模型失效零分和未知usage，解释审核局限不因资格通过而消失。暂无自动分析或后续实验。

启动后再次核对：105个complete、36started、1个request_timeout（INC-807CFFCD9D3F/EVENT_VISUAL）。此300秒请求超时按预注册保留消耗/partial/未知usage，不重试、不调配方，队列继续；不把它误报为无失败。详见formal/launch_followup.json。
