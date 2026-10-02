# memory_hub —— 复用的第三方记忆引擎

> 这不是我写的，是我**复用**的一个通用记忆引擎（memory-hub）。
> 它负责最底层的「记忆怎么存、怎么召回、怎么消解冲突」，是一套完整的三层记忆 + 三路召回（RRF）系统。

## 我为什么复用它，而不是自己写

一个数字分身，记忆引擎是地基，但它不是我项目的核心价值。我项目的价值在**镜像这一层**——怎么让一个 LLM「边聊边记、像一个人、又不泄露」。所以地基我用成熟的，把精力花在真正难的地方。

**复用开源组件、读懂它、修它的 bug，本身就是一种能力**（真实工作里 90% 的时间就是在改别人的代码）。

## 我改了哪几个文件（这些才是我的改动，其余原样复用）

| 文件 | 我的改动 | 为什么 |
|---|---|---|
| `extract.py` | ① 抽取纪律第 4 条加「重要度判定」（身份/目标/决定必须记，治 M3 漏存）；② `KINDS` 新增 `style` 类别（说话方式，治 M9 语气写死） | 让抽取器抽得全、且能抽「语气」 |
| `backend_local.py` | 把 fastembed 换成 DashScope text-embedding-v3（1024→512 维） | 治 M1「没接向量召回不到」 |
| `core.py` | `KINDS` 同步加 `style` | 让 style 能正常写库 |

其余文件（`core.py` 的主体、`deps.py`、`schema.py`、`dbutil.py` 等）**原样复用，未改**。

## 目录里那些我没用到的文件

`chatdemo.py`、`bench.py`、`seed_demo.py`、`feed_sessions.py`、`ingest.py`、`maintain.py`、`webapp.py`、`webui.py`、`backends_ollama.py` 等，是 memory-hub 原项目自己的演示/入口/可选后端，mirror 用不到，保留仅为完整性。
