# 按用户请求导出各臂/数据集例图

用户在代码暂停后追加请求：查看今天运行的实验，导出已完成实验和新版每个arm×数据集的一个例图到 Windows `C:\Users\10511\Downloads\例图\10_01`。该请求授权有限预览与文件复制，没有恢复完整CPU回归、GPU smoke或formal。

今天结束的完整formal队列为RQ3.10（840位置，836 done/4 timeout）和RQ3.11（1120位置，1108 done/12 timeout）；各自final verification passed，unexplained missing=0。RQ3.9的12单元smoke完成，formal interrupted，不计作已完成全量。RQ3.12 v1停在CPU方法资格失败。

完成实验直接复制原PNG，逐张对照实际input中的SHA及atomic completion receipt，不重绘旧图。每个数据集优先固定原smoke案例；RQ3.11 AIOPS2022的COARSE_VISUAL_HIGH原固定例超时，该臂按同数据集opaque ID排序选首个已提交完成例，单独注明，没有按诊断正确率挑图。纯文本臂没有真实dashboard，导出完整system/user输入及JSON。相同预算的COARSE/PROTECTED视觉臂可能共享PNG，其差异在附属文本补丁，不用编造不同图片。

新版使用相同三个固定exposed-eval案例，仅运行公共采样支持、派生编译和六PNG预览，不加载tokenizer/模型，不访问私有评分。独立 `render.preview_20261001.mjs` 构建包，canonical `render.mjs` 保持原字节；canonical preparation、registration、资格build/freeze未建立。

第一次预览发现继承renderer的600最小高度拒绝新版360；第二次发现候选行SVG的未使用尾部空间造成panel overflow。修复仅对单卡diagnostic.compact放行360高度，并删除SVG尾部40像素空白，保留旧组件600下限和字段位置。两次失败数据/日志/旧预览bundle保留。第三次六PNG的实际DOM/字段/边界审计通过，三张COND实际目视可读；AIOPS2025 COND重复渲染PNG SHA完全相同。

三例有效观测列7/9/12，预测行0/1/0：展示修复仍不能证明方法达到资格门槛。完整CPU、token成本、竞争覆盖、预算/科学review和GPU仍待用户继续。

导出四个版本/阶段：RQ3.10完成、RQ3.11完成、额外RQ3.12 v1旧失败对照、新版RQ3.12 v2预览。共78条arm×数据集记录，30张原尺寸PNG、48条纯文本输入；`index.html`支持实验/数据集筛选及显示文本臂，`例图索引.csv`使用UTF-8 BOM，`manifest.json`保留路径和SHA/完成调用出处。实际浏览器索引筛选检查通过；导出receipt位于 `../preview_gallery_20261001/windows_export.json`。
