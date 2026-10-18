# 数据字典与复算边界

公开日期：2026-10-18。所有耗时单位为秒，MiB/GiB 为二进制单位。CSV 使用 UTF-8，缺失值留空，不以零代替。

## 文件

- `data/runs.csv`：逐次测量，每行是一次版本/输入观测；含被拒绝方案和不利结果。字段使用显式允许清单导出，没有附带原始日志。
- `data/paired_summary.csv`：正文选用的七组比较。重复实验先对每版求算术均值，再计算减少比例。
- `assets/*.png`：由公开数字生成的三张统计图与一张流程图。
- `tools/reproduce.py`：只访问本仓库，检查/复算表格与百分比，并生成图表，不发起网络请求或 GPU 测试。
- `checksums.sha256`：公开内容的 SHA256；不包含自身和 Git 元数据。

## 实验组与样本

| 组 | 日期 | 输入关系与解释 |
| --- | --- | --- |
| E00 | 2026-10-03 | H99，5951.059625 秒；早期 batch1 串行版 stable2 与有限重叠 stable3 各一次 |
| E01 / E01-R11 | 2026-10-16—17 | 同日 R3、R12 五输入，以及被拒绝 R11；阶段数据来自当轮已保存的两位小数报告 |
| E01-screen | 2026-10-16—17 | 夜间/跨时段 R3、R6、R8 的五输入筛选轨迹；非同条件确认性 A/B，不与同日 R3 混用 |
| E02 | 2026-10-17 | R12/R15，五输入各一次，同原音、模型和解码参数；阶段调用方式不同 |
| E03 | 2026-10-17 | L193 新鲜相邻 R15/R16 各一次；不用其他轮次的 R15 替代分母 |
| E04 | 2026-10-18 | A54 M4A，3256.832 秒；同轮 R16、R17、R19、R20 各一次，包含中间候选 |
| E05 | 2026-10-18 | R20/R21 五输入；L193 各两次，其他各一次 |
| E06 | 2026-10-18 | R21/R22 主样本 L193 各两次，反转第二组顺序；保留非相邻旧参考及额外短样本回归 |
| E07 | 2026-10-18 | 四份另外的完整录音 T-A/B/C/D，外加一次 T-A 重复；属于跨录音稳定性，不是四组版本 A/B |
| E07-control | 2026-10-18 | 为核查 T-C 近似词时间戳，追加一次同输入 R21；不是新一轮性能筛选 |

命名注意：早期 stable3 与后来的 R3 不同。H99 与 D99 是不同录音。S02（119.9945625 秒）与 M15（900.010875 秒）来自同一父录音，不能当成独立语料。D99 为 5910.3869375 秒，C102 为 6128.0653125 秒，L193 为 11599.9608125 秒。匿名编号可连接公开表格，不能恢复原始课程或人物。

## 字段

| 字段 | 含义与限制 |
| --- | --- |
| `experiment`, `recording`, `version`, `replicate` | 实验组、匿名输入、版本、重复号；重复号只在本实验组内有效 |
| `comparison_scope` | `fresh_primary_pair_*` 为 E06 主配对；`same_day_existing_*` 是非相邻参考，不能当作同等强度的因果证据；其他范围按字面解释 |
| `audio_seconds` | 解码时长；E01 本次导出复用同一输入已确认的时长，阶段计时仍为报告圆整值 |
| `worker_seconds` | 首次有效 Worker 尝试开始到最后尝试结束的记录跨度；含其中恢复、装载、等待，不含上传和取回，不是后台总排队时长 |
| `client_seconds` | 实际客户端完整调用墙钟；包括上传/等待/取回/校验。不能把 Worker 与客户端相加 |
| `*_realtime_factor` | 对应耗时 ÷ 音频时长，越小越快 |
| `*_audio_seconds_per_second` | 音频时长 ÷ 对应耗时，即实时速度，越大越快 |
| `community_outer_seconds` | Community 完整外层阶段，包含后端和外围等待/资源观察 |
| `community_backend_seconds` | Community 后端内部耗时，包含于外层阶段 |
| `community_embedding_related_window_seconds` | 嵌入相关窗口，含 CPU/GPU 准备、计算及等待；不是纯 GPU 时间，也不与 Community 外层相加 |
| `alignment_outer_seconds`, `alignment_rpc_outer_seconds` | 本轮记录的对齐 RPC/外层累计；嵌套于 Worker，历史实现粒度不同 |
| `alignment_rpc_count` | 对齐 RPC 数量；RPC 合并不等于模型真正批量 Forward |
| `asr_successful_inference_lower_bound_seconds` | 累计成功返回的 ASR 模型时间，可能不含失败 OOM/装载，是下限，不是完整 ASR 阶段 |
| `asr_reported_seconds` | E00 当时记录的 ASR 计时，不能假定与后来下限列完全相同 |
| `retry_model_reported_seconds` | E04 成功返回的恢复推理累计，包含于总耗时；不是所有失败成本的完整计量 |
| `retry_calls`, `retry_4096_calls` | 对应恢复调用和 4096 token 恢复调用数；零是日志确认的观测，不是缺失 |
| `pre_community_critical_path_seconds`, `after_community_critical_path_seconds` | 同一运行中 Community 前后墙钟段，可与该次 Community 外层核对 Worker 关键路径 |
| `upload_and_seal_seconds` | 上传及 seal 的累计操作计时，包含于客户端总耗时，不是纯链路吞吐 |
| `*_peak_allocated_bytes`, `*_peak_reserved_bytes` | 对应 PyTorch 阶段/成功尝试报告的峰值；两列不是可相加的独立内存，不等同 nvidia-smi 整卡值，不覆盖全部失败瞬时峰值 |
| `oom_shrink_events`, `oom_shrinks_per_enclosing_request_sum` | 对应外层请求记录的缩批计数，保留原粒度；不是任务失败次数 |
| `embedding_calls`, `waveform_rows`, `unique_frame_rows` | 原接口调用/波形-mask 行，以及真正执行的不同声学帧行数；定义随优化路径明确记录 |
| `empty_mask_*` | 仅严格全零 mask 快路径的资格、校准、复用、回退计数；不代表跳过说话人分析 |
| `diarized_activity_fraction` | 神经说话人分析时间区间并集 ÷ 总音频时长，未经人工标注，不能据此测漏词率 |

## 模型权重与执行条件

| 模型 | 固定 revision |
| --- | --- |
| Qwen/Qwen3-ASR-1.7B | `7278e1e70fe206f11671096ffdd38061171dd6e5` |
| Qwen/Qwen3-ForcedAligner-0.6B | `c7cbfc2048c462b0d63a45797104fc9db3ad62b7` |
| pyannote/speaker-diarization-community-1 | `3533c8cf8e369892e6b79ff1bf80f7b0286a54ee` |

Qwen SDK 0.0.6，PyTorch 2.8.0+cu126，Transformers 4.57.6，pyannote.audio 4.0.7。权重没有重新训练。完整任务使用新 GPU 子进程，模型文件/操作系统缓存、GPU 频率和其他用户负载未完全隔离。共享策略保留约 2GiB 显存余量和额外安全缓冲，CPU 按实时余量进入；未终止他人任务。客户端传输预算为 2MiB/s。

R22 的同一结果中模型和参数通过一致性检查；这不表示整个十多天实验的客户端、调度和冷暖条件都完全相同。E00 的早期并行策略也不是当前默认策略。

## 复算

Python 3.12 及以上。仅检查数值使用标准库：

```sh
python tools/reproduce.py --check
```

重绘需 Matplotlib 及其依赖，建议使用独立虚拟环境；具体安装版本见 `requirements.txt`。不需要模型、CUDA、原音或访问凭据：

```sh
python -m pip install -r requirements.txt
python tools/reproduce.py
```

减少比例 = `1 - candidate_seconds / baseline_seconds`；相对速度倍数 = `baseline_seconds / candidate_seconds`。两次实验均值先按版本取平均，不能先挑最快一次。脚本会检查 80 条已导出观测、主配对、关键路径和图片引用。表格数量随本次版本固定，不是全部历史实验的总次数。

没有公开原音、正文、内网地址、账户、学校/群组标识、内部任务 ID、原音哈希或私有工程源码。保留公共模型 revision 和匿名测量，以便复算；这不构成全量独立 benchmark 复现包。未获得人工 Gold，所有质量结论限于输出回归和结构/代理检查。

## 官方推荐配置对照的缺口

本次没有实测 Qwen 官方推荐的 vLLM / 适用 FlashAttention 2 路径，也没有把官方 Qwen ASR/Aligner 与原生 Community 组合成同口径完整基线。自建 R12 等版本不能代替该基线。批量 ASR 是官方已经支持的能力；外围 RPC 与融合循环属于本系统实现。公开数字不支持“比官方推荐部署快 X%”或“新 ASR 推理算法”的结论。

下一次对照应固定同卡、原音与权重 revision，单独记录官方建议 ASR/Aligner 与当前后端的冷/暖耗时，再为两侧加入完整 Community 和相同输出处理，配对、交错测试 Worker 及客户端；同时核对文本、词边界与说话人差异。本次未为这份文章临时运行这项新基准，不把计划当作实测。

## 未采用及未充分验证的路径

- 45 秒合段和 R11 组合策略：出现不完整/新空白风险或显著退化，拒绝采用。
- 原生 ForcedAligner 列表 Forward：英文微基准快，但 23/3808 边界变化，最大约 0.4 秒；中文、混合语言和 Gold 未充分验证。
- CUDA Graph、channels-last、Conv-BN 融合及更大 embedding batch：捕获失败、数值变化或无可靠端到端收益，未纳入最终路径。
- 更大的 ASR batch：个别局部测试更快但文本变化，未用于替换既有回归通过路径。
- 正常 EOS 的异常重复、其他循环周期：仍需针对性质量验证；不能声称所有异常长尾已解决。
- 未保存完整独占硬件控制和充分重复：小幅差异不能宣称统计显著，也不外推跨机器速度排名。
