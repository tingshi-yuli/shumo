# A题论文修订支撑材料

## 来源与状态

本目录只取自 `数模项目_续接/工作区/改进模型`、同级 `附件` 和 `qa` 中的支撑记录；没有以旧发布目录的数据替代续接工作区的数值对照。源码中的 `v0.4` 是冻结数值模型的原版本标识，不代表从旧发布目录取数。模型、P2求解和独立参考程序保持原字节，避免使记录内的源码指纹失效。

本次仅整理文件、阅读代码与核对文献，未执行求解、测试、逐值回读、P2复验或论文构建。JSON中原有的 `passed` 等状态属于续接工作区的历史记录，不是本次运行结论。`验证/Excel回读_续接留存.json` 与 `验证/P2汇总_续接留存.json` 保存原记录；后续运行可能更新工作文件，但不更新这两份留存件。

## 文件结构

```text
支撑材料/
  README.md
  reproduce.py                    # 统一入口，调用下列原脚本
  SHA256SUMS.txt                   # 整理时文件指纹，不是数值验证结论
  文件来源.json                   # 逐文件来源与未执行事项
  科学假设诊断.json                # 续接工作区已有结构诊断
  附件/
    附件1.xlsx                    # 题给环境输入
    附件2.xlsx                    # 题给收缩输入
    附件3/result1.xlsx ... result4.xlsx  # 原题结果模板，非结果副本
  改进模型/
    model.py                      # 主模型与离散求解
    run_study.py                   # 指纹约束的轨迹缓存入口
    run_all.py                     # 主结果计算配置
    build_outputs.py              # 四份Excel输出
    p2_study.py                    # 容差、边界及独立参考算例
    p2_reference.py                # 独立BDF2实现
    p2_report.py                   # 对照汇总与旧版图表生成
    tests.py                      # 原有小实例测试
    verify_outputs.py             # Excel与完整轨迹逐值回读
    audit_assumptions.py           # 条件性密度质量及环境覆盖诊断
    make_figures.py                # 冻结模型配套旧版绘图入口
    requirements.txt
    requirements-verified.txt     # 原运行环境的锁定版本
    result1.xlsx ... result4.xlsx  # 续接工作区结果
    verification.json             # 原有Excel回读记录；重跑时更新
    p2/runs/*.json                # 22份完整对照记录
  验证/
    Excel回读_续接留存.json
    P2汇总_续接留存.json
    引用核对.json
```

附件已按原脚本要求的位置复制，解压即可找到输入，不依赖机器上的原工作区。不得把 `改进模型/result*.xlsx` 移到 `附件/附件3/` 覆盖空模板。较大的 `改进模型/runs/*.json.gz` 主轨迹缓存不随此精简包分发；完整求解会生成它们。

## 环境与统一入口

推荐 Python 3.12。锁定依赖来自续接工作区，版本为 NumPy 2.3.5、SciPy 1.15.3、openpyxl 3.1.5、Matplotlib 3.10.3；不表示本次重新安装或验证。以下 PowerShell 命令从 `v0.6-论文修订` 目录执行，虚拟环境建在支撑目录之外：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\支撑材料\改进模型\requirements-verified.txt

# 完整重建主结果：先求解，再生成四份结果表
.\.venv\Scripts\python.exe .\支撑材料\reproduce.py results

# P2对照：指纹匹配时使用已有22份记录，不冒称重新积分
.\.venv\Scripts\python.exe .\支撑材料\reproduce.py p2 --workers 3

# 验证入口：须先完成results，确保runs及results副本存在
.\.venv\Scripts\python.exe .\支撑材料\reproduce.py verify

# 或按results -> p2 -> verify一次执行
.\.venv\Scripts\python.exe .\支撑材料\reproduce.py all --workers 3
```

统一入口使用当前Python解释器、固定各子程序工作目录，任一步失败即终止，不把失败转换为成功。原始入口也可在 `改进模型` 目录依次运行：`python run_all.py`、`python build_outputs.py`、`python p2_study.py --group all --workers 3`、`python p2_report.py`、`python audit_assumptions.py --output ../科学假设诊断.json`、`python tests.py`、`python verify_outputs.py`。这些命令均未在本次整理中执行。

主缓存和P2缓存仅在程序各自要求的源码、配置与输入指纹相符时复用；如需强制重算P2，应先将 `p2/runs` 重命名留存，再运行P2入口。没有主缓存时，主结果需要完整积分；第二问轨迹反序列化需数GB空闲内存。`build_outputs.py` 还会生成 `改进模型/results/` 结果副本，`verify_outputs.py` 同时核对它们，不能只拷入主缓存后直接验证而省略导出步骤。

## 绘图与输出位置

本包中的 `make_figures.py`、`p2_report.py` 原样保留其历史输出路径，分别生成 `改进模型/figures/` 和包内 `完整论文-LaTeX/`；不会改写原工作区。这些旧版图不是本次论文的600DPI排版图。

本次论文新版图源入口在本支撑目录的上一级：`redraw_figures.py`，配套 `绘图工具/`。完成主缓存重建后，可在 `v0.6-论文修订` 目录执行：

```powershell
.\.venv\Scripts\python.exe .\redraw_figures.py --source-dir .\支撑材料\改进模型
```

新版入口及样式辅助文件属于论文图源，未在本精简数值包中重复分发；单独下载支撑包时，可使用包内旧绘图入口复现数值来源图。新版图源的执行与图面验收由论文主流程记录。

## 结果解释边界

四份结果保留规定的时间、空间间隔及实际终点行；状态输出四位小数，但终点判定使用未舍入含水率。问题4域外单元格留空，表面值与半径另列。续接回读记录登记六张表、8,838,954个状态值；该数量是原记录内容，不是本次再次比较的数量。跨库导出可改变Excel元数据与文件哈希，应区分数值合同与字节同一性。

环境四小时后沿用最后观测；有效浓度边界、未计汽化潜热、条件性湿密度与固定长度解释是模型假设边界。P2参数扫描是确定性情景，不是统计置信区间；独立数值实现一致不等于物理模型得到实验验证。

## 打包与尺寸风险

本次复制的数值源码、结果、输入及留存记录合计32,032,458字节（尚未计入此README、统一入口和文件清单）。其中 `result2.xlsx` 为27,454,995字节。省略的五份压缩主缓存共77,953,826字节，第二问缓存单独62,962,743字节。若上传限制为20,000,000字节，不能按未压缩目录判断，也不能把历史压缩包的大小当作本版大小：续接工作区旧打包报告记载12,381,766字节，仅可作为量级参考。

在任何复算之前，可从 `v0.6-论文修订` 执行以下打包命令。复算后的目录会多出缓存、重复结果及图表，应另存复算目录后再按本节列出的静态文件打包，不把新增大文件直接全收进压缩包：

```powershell
Compress-Archive -Path .\支撑材料\* -DestinationPath .\支撑材料.zip -CompressionLevel Optimal
(Get-Item .\支撑材料.zip).Length
```

压缩与大小检查命令尚未执行，本次未声称压缩包满足上传限额。`SHA256SUMS.txt` 是本次静态交付快照的指纹清单；重算覆盖文件后它自然不再代表修改后的目录，应重新生成并记录新的来源与运行状态。
