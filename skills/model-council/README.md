# model-council

> Fusion-enhanced blind multi-model deliberation, niche knowledge-distribution relay, and spec-grade execution handoffs.

**English** | [中文](#中文版)

`model-council` fuses three complementary multi-model paradigms into one self-contained skill package:

- **Perplexity Model Council (Epistemic Independence & Tail Recall):** Replicates one question across $2\text{--}8$ distinct model families with **zero Round-1 lateral visibility**, mapping outputs into **Convergence**, **Fault Lines**, and **Unique `1/N` Surfaces**.
- **Perplexity Multiagent (Bounded Cross-Examination):** Runs at most **1 Round-1.5 seam relay** to test compatibility across partial domain fragments surfaced by different models or resolve falsifiable assumption splits.
- **Cognition Devin Fusion (`1x` Fact Pack + `Lead -> Sidekick` Handoff):** Gathers one opinion-free `Fact Pack` (`<= 1,500` tokens) upfront to eliminate $N\times$ redundant repo crawls and KV-cache thrashing, and closes with a constraint-first execution brief carrying an **Ordered Alternatives Ladder** (*"Try alternatives in this order and keep the first that passes"*).

---

## When to Trigger

1. **Multi-model synthesis:** Explicit requests for `Model Council`, cross-model deliberation, or a synthesized second/third opinion on a high-stakes architectural, product, or risk call.
2. **Multi-model comparison:** Scenarios asking how distinct models answer or weigh in on a contested prompt.
3. **Niche / long-tail knowledge-distribution relay:** Obscure hardware/firmware errata, rare RFC/protocol clauses, compiler/kernel internals, or cross-disciplinary edge cases where pretraining tails are sparse and `1/N` exact anchors must be shielded from majority-vote erasure.

**Routing boundaries:**
- Designing or debugging multi-agent application codebases, VFS locks, or A2A protocols -> `orchestrating-multi-agent-workflows`
- Quantitative payoff tables, CARA certainty equivalents, or `VaR`/`ES` threshold math -> `analyzing-risk-decisions`

---

## Technical Architecture (ASCII)

```text
+========================================================================================+
|                        USER / HOST AGENT INVOCATION LAYER                              |
|  Triggers:                                                                             |
|   [1] Synthesis Verdict : "$model-council" | multi-model discussion & final bet        |
|   [2] Multi-Model Query : side-by-side stances across distinct model families          |
|   [3] Niche Relay       : obscure/long-tail domains needing 1/N prior relay            |
|  Mutual Routing Exclusions:                                                            |
|   -> Multi-agent app code/VFS/A2A : orchestrating-multi-agent-workflows                |
|   -> Payoff / CARA / VaR math     : analyzing-risk-decisions                           |
+===========================================+============================================+
                                            |
                                            v
+========================================================================================+
|                     ORCHESTRATION & CONTROL LAYER (SKILL.md)                           |
|                                                                                        |
|  +---------------------------+   +--------------------------------------------------+  |
|  | Devin Fusion Upstream     |   | Perplexity Model Council Core                    |  |
|  | - 1x Neutral Fact Pack    |   | - Zero lateral visibility in Round 1 (Blind)     |  |
|  |   (<=1.5k tok, 0 opinion) |   | - 4-Slot Seat Output: Verdict / Exact Anchors /  |  |
|  | - KV-Cache isolation      |   |   UNKNOWN Seams / Steelman Flip Condition        |  |
|  +---------------------------+   +--------------------------------------------------+  |
|  +---------------------------+   +--------------------------------------------------+  |
|  | Multiagent Mesh Relay     |   | Devin Fusion Downstream Closeout                 |  |
|  | - Bounded Round-1.5 (<=1) |   | - Constraint-first Lead -> Sidekick Spec Brief   |  |
|  | - Stitch Seat A Piece 1 + |   | - Ordered Alternatives Ladder:                   |  |
|  |   Seat B Piece 2 on seam  |   |   "Try in order and keep the first that passes"  |  |
|  +---------------------------+   +--------------------------------------------------+  |
+===========================================+============================================+
                                            |
                                            v
+========================================================================================+
|            DETERMINISTIC ENGINE LAYER (scripts/council_runner.py, 0-dep)               |
|                                                                                        |
|  +------------------------+  +--------------------------+  +------------------------+  |
|  | 1. `probe`             |  | 2. `dispatch`            |  | 3. `ledger`            |  |
|  | - Secret-safe PATH &   |  | - Allowlisted CLI argv   |  | - Family diversity idx |  |
|  |   env-key bool check   |  |   (`shell=False`, temp)  |  | - Same-family echo     |  |
|  | - `--discover-models`  |  | - `--dry-run` preview &  |  |   detector             |  |
|  |   parses 56+ families  |  |   neutrality bias lint   |  | - `PROTECT_1_OF_N`     |  |
|  | - `parse_fusion_...`   |  | - ThreadPool + hard      |  |   anti-majority shield |  |
|  |   extracts Lead family |  |   timeout + key redact   |  | - Tier-3 honesty gate  |  |
|  +------------------------+  +--------------------------+  +------------------------+  |
+===========================================+============================================+
                                            |
                                            v
+========================================================================================+
|                      EXECUTION & EPISTEMIC DIVERSITY SUBSTRATE                         |
|                                                                                        |
|  [Tier 1: Cross-Family CLIs / Fusion Seats] (Preferred: True Pretraining Orthogonality)|
|   +-- devin -p --process-model in-process --model <opus|gpt-6-2|gemini-4|deepseek|...> |
|   +-- devin -p ... --model fusion-<lead>-sidekick-<sidekick>   ("Council of Fusions")  |
|   +-- codex exec --ephemeral --color never -s read-only -m <model>                     |
|   +-- claude -p / gemini / opencode / llm / ollama                                     |
|                                                                                        |
|  [Tier 2: Host Isolated Subagents]           (Partial Diversity: Fresh Contexts)       |
|   +-- subagent_explore (router model) + model-pinned custom profiles                   |
|                                                                                        |
|  [Tier 3: Counterfactual Single-Model Pass]  (Degraded Fallback: Explicitly Labeled)   |
|   +-- Mechanism Anchor Pass | Adversarial Falsifier Pass | Edge-Case Prior Pass        |
+========================================================================================+
```

---

## End-to-End Execution Flowchart (ASCII)

```text
                              [ User Question / Task ]
                                         |
                                         v
                    +----------------------------------------+
                    | §0. Single-Fact Local Lookup Check     |
                    | Verifiable by 1 file/cmd & no explicit |---- YES ---> [ Verify Locally & ]
                    | multi-model comparison requested?      |              [ Answer Directly  ]
                    +--------------------+-------------------+
                                         | NO
                                         v
                    +----------------------------------------+
                    | Lock Active Track:                     |
                    | - Track A: judgment (trade-offs/risk)  |
                    | - Track B: comparison (multi-model)    |
                    | - Track C: niche_relay (long-tail 1/N) |
                    +--------------------+-------------------+
                                         |
                                         v
                    +----------------------------------------+
                    | §1. `council_runner.py probe`          |
                    | Select Tier 1 > Tier 2 > Tier 3        |
                    | (Pause once ONLY if paid CLI/API spend |
                    |  consent or core constraint is needed) |
                    +--------------------+-------------------+
                                         |
                                         v
                    +----------------------------------------+
                    | §2. Fusion 1x Reconnaissance           |
                    | Build Opinion-Free Fact Pack (<=1.5k)  |
                    | Lint: strip Chair hypothesis/anchoring |
                    +--------------------+-------------------+
                                         |
          +------------------------------+------------------------------+
          |                              |                              |
          v                              v                              v
+-------------------+          +-------------------+          +-------------------+
| Seat 1 (Family A) |          | Seat 2 (Family B) |          | Seat 3..K (Fam C) |
| Blind Round 1     |   X      | Blind Round 1     |   X      | Blind Round 1     |
| - Verdict         | (Zero    | - Verdict         | (Zero    | - Verdict         |
| - Exact Anchors   |  Peer    | - Exact Anchors   |  Peer    | - Exact Anchors   |
| - UNKNOWN Seams   |  Talk)   | - UNKNOWN Seams   |  Talk)   | - UNKNOWN Seams   |
| - Flip Condition  |          | - Flip Condition  |          | - Flip Condition  |
+---------+---------+          +---------+---------+          +---------+---------+
          |                              |                              |
          +------------------------------+------------------------------+
                                         |
                                         v
                    +----------------------------------------+
                    | §4. `council_runner.py ledger`         |
                    | Classify atomic claims across seats:   |
                    +--------------------+-------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
[>=2 Families Agree]           [Conflict / Split]               [1/N Singleton Recall]
CONVERGENT_HIGH_TRUST          DISPUTED_FAULT_LINE              Specific anchor/mechanism?
(or HOMOGENEOUS_ECHO           (isolate hidden premise)          |-- YES -> PROTECT_1_OF_N
 if same model family!)                  |                       |   UNIQUE_1_OF_N_RELAY
     |                                   |                       +-- NO  -> LOW_SIGNAL
     |                                   +---------------+-------------------+
     |                                                   |
     |                                                   v
     |                         +---------------------------------------------+
     |                         | Need Round-1.5 Probe or Niche Seam Relay?   |
     |                         | (Hard Stop-Loss Cap: AT MOST 1 Relay Pass)  |
     |                         +--------------------+------------------------+
     |                                              | YES
     |                                              v
     |                         +---------------------------------------------+
     |                         | Step 4a (Fusion Sidekick Reality Probe):    |
     |                         |  Check repo / docs / compiler / REPL first  |
     |                         |  -> VERIFIED_MINORITY_GOLD or FALSIFIED     |
     |                         | Step 4b (Multiagent 1-Hop Seam Relay):      |
     |                         |  Pass {Verified Piece A + Open Seam B} to   |
     |                         |  complementary seat to test compatibility   |
     |                         +--------------------+------------------------+
     |                                              |
     +----------------------------------------------+
                                         |
                                         v
                    +----------------------------------------+
                    | Re-verify `ledger` Invariants:         |
                    | - tier_honesty == true                 |
                    | - minority_anchor_protected == true    |
                    | - relay_stop_loss_respected (<=1)      |
                    +--------------------+-------------------+
                                         |
                                         v
                    +========================================+
                    | §6. Structured Output Contract         |
                    | 1. Council Verdict & Switching Bound   |
                    | 2. Epistemic Map (Consensus / Fault    |
                    |    Lines / Verified 1-of-N Relay)      |
                    | 3. Concise Per-Seat Stance Snapshot    |
                    | 4. Devin Fusion Execution Brief        |
                    |    (Invariants + Ordered Ladder + Test)|
                    +========================================+
```

---

## Package Layout & Quick CLI Usage

- [SKILL.md](SKILL.md) — Canonical 6-step orchestration contract, fast paths, and stop-loss guardrails.
- [references/paradigm-synthesis-and-schemas.md](references/paradigm-synthesis-and-schemas.md) — Verified comparison matrix across Model Council, Multiagent, and Devin Fusion, prompt contracts, and JSON schemas.
- `scripts/council_runner.py` — Zero-dependency Python stdlib CLI (`probe`, `dispatch`, `ledger`, `selftest`).
- `tests/test_council_runner.py` — Unit and CLI regression suite.

```bash
# 1. Probe callable multi-model CLIs and live Devin model/Fusion families
python3 scripts/council_runner.py probe --discover-models

# 2. Preview blind Round-1 seat diversity and Fact Pack neutrality (zero spend)
python3 scripts/council_runner.py dispatch --dry-run --input brief.json

# 3. Classify claims and enforce anti-majority-vote 1/N protection
python3 scripts/council_runner.py ledger --input ledger.json --format markdown

# 4. Run built-in invariants & unit tests
python3 scripts/council_runner.py selftest
python3 -m unittest discover -s tests -v
```

---

<a id="中文版"></a>

# 中文版

> 融合 Devin Fusion 契约式委派、Model Council 跨模型盲审与 Multiagent 跨缝核验的多模型会诊与冷门知识接力技能。

[English](#model-council) | **中文**

`model-council` 将三种互补的多模型范式收敛为一套自包含工程技能：

- **Perplexity Model Council（首轮认知独立与长尾点亮）：** 同一问题并发派发给 $2\text{--}8$ 个跨家族模型，**首轮严禁横向可见**（杜绝锚定从众），结构化提炼 **跨模型共识**、**核心分歧断层** 与 **`1/N` 独有盲区发现**。
- **Perplexity Multiagent（受控跨缝交叉核验）：** 针对模型间互补的知识碎片或可证伪假设冲突，执行**最多 1 轮 `Round-1.5` 跨缝接力核验**，严防多轮空谈导致迎合退化。
- **Cognition Devin Fusion（`1x` 中立取证 + `Lead -> Sidekick` 执行简报）：** 扇出前仅做 **1 次无倾向 `Fact Pack` 客观侦察**（`<= 1,500` tokens，避免 $N$ 倍重复扫仓与 KV Cache 击穿），收尾输出带**有序备选阶梯**（*“按顺序尝试并保留首个通过验收的方案”*）的落地执行简报。

---

## 适用触发场景

1. **多模型讨论综合结果：** 显式要求运行 `Model Council`、多模型会诊/圆桌裁决，或在架构选型、策略权衡、高风险拍板上获取综合结论。
2. **询问多个模型看法：** 想对比不同模型家族对同一争议问题的独立立场与推理差异。
3. **冷门/长尾领域跨模型知识分布接力：** 底层芯片寄存器/固件 errata、生僻协议/RFC 条款、编译器/内核边缘机制等长尾场景——单一模型预训练尾部覆盖不全，需提取并保护 `1/N` 精确技术锚点免遭“少数服从多数”抹杀，再跨模型拼接完整链路。

**相邻技能分流边界：**
- 设计或排查业务代码中的多 Agent 拓扑、虚拟文件系统锁或 A2A 协议 -> `orchestrating-multi-agent-workflows`
- 含明确收益/损失概率表、CARA 效用或 `VaR`/`ES` 尾部约束反推 -> `analyzing-risk-decisions`

---

## 技术架构图（中文 ASCII）

```text
+======================================================================================+
|                              用户请求与宿主触发路由层                                |
|  三类核心触发：                                                                      |
|   [1] 多模型讨论综合裁决 : "$model-council" | 架构/策略/高风险分歧拍板               |
|   [2] 询问多个模型看法   : 跨模型家族独立立场对比与优劣归纳                          |
|   [3] 冷门长尾知识接力   : 单模型语料尾部稀疏，需跨模型提取并拼接 1/N 精确锚点       |
|  正交互排分流：                                                                      |
|   -> 多 Agent 业务代码拓扑 / VFS 锁 / A2A 协议 : orchestrating-multi-agent-workflows |
|   -> 显式概率损益表 / CARA 效用 / VaR 数学反推 : analyzing-risk-decisions            |
+==========================================+===========================================+
                                           |
                                           v
+======================================================================================+
|                             编排与认知控制层 (SKILL.md)                              |
|                                                                                      |
|  +------------------------------+    +--------------------------------------------+  |
|  | Devin Fusion 上游减负        |    | Perplexity Model Council 盲审内核          |  |
|  | - 1x 无倾向 Fact Pack 取证   |    | - 首轮零横向通信（防锚定与从众羊群效应）   |  |
|  |   (<=1.5k tok, 剥离主脑倾向) |    | - 四槽位强制输出：核心结论机制 / 精确锚点  |  |
|  | - 独立持久上下文护住缓存     |    |   / UNKNOWN 未知边界 / Steelman 反转条件   |  |
|  +------------------------------+    +--------------------------------------------+  |
|  +------------------------------+    +--------------------------------------------+  |
|  | Multiagent 横向跨缝接力      |    | Devin Fusion 下游契约收口                  |  |
|  | - 最多 1 轮 Round-1.5 止损   |    | - 约束优先的 Lead -> Sidekick 规格简报     |  |
|  | - 拼接 A 模型片段 1 与 B 模  |    | - 有序备选阶梯：按序尝试并保留首个通过     |  |
|  |   型片段 2 并做接口互审证伪  |    |   可观察验收命令的方案                     |  |
|  +------------------------------+    +--------------------------------------------+  |
+==========================================+===========================================+
                                           |
                                           v
+======================================================================================+
|                   确定性校验与调度引擎 (scripts/council_runner.py)                   |
|                                                                                      |
|  +------------------------+  +--------------------------+  +----------------------+  |
|  | 1. `probe` 环境探测    |  | 2. `dispatch` 并发盲审   |  | 3. `ledger` 认知账本 |  |
|  | - 零密钥泄露探测 PATH  |  | - 白名单 CLI 模板调用    |  | - 模型家族多样性指数 |  |
|  |   与环境变量布尔存在性 |  |   (shell=False + 临时目录|  | - 同族回声伪共识告警 |  |
|  | - --discover-models    |  |    隔离防污染本地会话库) |  | - PROTECT_1_OF_N 反  |  |
|  |   解析 56+ 模型家族    |  | - --dry-run 倾向性静态检 |  |   多数票抹杀长尾护盾 |  |
|  | - 解析 fusion-* 主脑族 |  | - 超时熔断与密钥自动脱敏 |  | - Tier 3 防伪共识门禁|  |
|  +------------------------+  +--------------------------+  +----------------------+  |
+==========================================+===========================================+
                                           |
                                           v
+======================================================================================+
|                              底层异构模型执行基座                                    |
|                                                                                      |
|  [Tier 1: 跨模型家族 CLI / Fusion 席位] （首选：真正独立的预训练知识分布）           |
|   +-- devin -p --process-model in-process --model <opus|gpt-6-2|gemini-4|deepseek>   |
|   +-- devin -p ... --model fusion-<lead>-sidekick-<sidekick>  （嵌套 Fusion 席位）   |
|   +-- codex exec --ephemeral --color never -s read-only -m <model>                   |
|   +-- claude -p / gemini / opencode / llm / ollama                                   |
|                                                                                      |
|  [Tier 2: 宿主隔离子代理]               （部分异构：独立干净上下文防串味）           |
|   +-- subagent_explore（路由模型）+ 固定 model: 的自定义子代理                       |
|                                                                                      |
|  [Tier 3: 单模型正交反事实视角]         （受限环境诚实降级：严禁冒充跨模型共识）     |
|   +-- 机制与规范锚点视角 | 反方证伪挑刺视角 | 运行时边界与长尾异常视角               |
+======================================================================================+
```

---

## 端到端执行流程图（中文 ASCII）

```text
                               [ 用户问题 / 决策任务 ]
                                          |
                                          v
                     +-----------------------------------------+
                     | §0. 单一本地事实快速旁路检查            |
                     | 读 1 个文件或跑 1 条命令即可确证，且用  |--- 是 ---> [ 本地直接核验回答 ]
                     | 户未显式要求多模型对比？                |            [ 不额外烧多模型   ]
                     +--------------------+--------------------+
                                          | 否
                                          v
                     +-----------------------------------------+
                     | 自动锁定会诊轨道：                      |
                     | - Track A: judgment（权衡拍板/争议裁决）|
                     | - Track B: comparison（多模型立场对比） |
                     | - Track C: niche_relay（冷门知识接力）  |
                     +--------------------+--------------------+
                                          |
                                          v
                     +-----------------------------------------+
                     | §1. 运行 `council_runner.py probe`      |
                     | 自动优选 Tier 1 > Tier 2 > Tier 3       |
                     | （仅当需确认外部付费调用或缺失核心业务  |
                     |   前提时合并单轮询问，技术默认项自决）  |
                     +--------------------+--------------------+
                                          |
                                          v
                     +-----------------------------------------+
                     | §2. Fusion 1x 无倾向客观取证            |
                     | 组装 Fact Pack（<=1,500 tokens）        |
                     | 静态检查：剥离主脑预设倾向与诱导性措辞  |
                     +--------------------+--------------------+
                                          |
          +-------------------------------+-------------------------------+
          |                               |                               |
          v                               v                               v
+-------------------+           +-------------------+           +-------------------+
| 席位 1（家族 A）  |           | 席位 2（家族 B）  |           | 席位 3..K（族 C） |
| 首轮独立盲审      |     X     | 首轮独立盲审      |     X     | 首轮独立盲审      |
| - 结论与因果链    | （零横向  | - 结论与因果链    | （零横向  | - 结论与因果链    |
| - 精确技术锚点    |   串通）  | - 精确技术锚点    |   串通）  | - 精确技术锚点    |
| - UNKNOWN 缺口    |           | - UNKNOWN 缺口    |           | - UNKNOWN 缺口    |
| - 反转押注条件    |           | - 反转押注条件    |           | - 反转押注条件    |
+---------+---------+           +---------+---------+           +---------+---------+
          |                               |                               |
          +-------------------------------+-------------------------------+
                                          |
                                          v
                     +-----------------------------------------+
                     | §4. 运行 `council_runner.py ledger`     |
                     | 提取跨席位原子命题并做确定性分桶：      |
                     +--------------------+--------------------+
                                          |
     +------------------------------------+------------------------------------+
     |                                    |                                    |
     v                                    v                                    v
[>=2 个不同家族一致]             [席位间正面冲突]                  [仅 1/N 单席位点亮]
CONVERGENT_HIGH_TRUST            DISPUTED_FAULT_LINE               含精确锚点或具体机制？
（若仅同家族一致则标             （拆解隐含前提差异）               |-- 是 -> PROTECT_1_OF_N
 HOMOGENEOUS_ECHO 告警）                  |                         |   免多数票抹杀保护
     |                                    |                         +-- 否 -> LOW_SIGNAL
     |                                    +----------------+-------------------+
     |                                                     |
     |                                                     v
     |                         +-----------------------------------------------+
     |                         | 是否存在待核验 1/N 锚点、互补碎片或可证伪冲突 |
     |                         | （硬止损上限：最多执行 1 轮 Round-1.5 接力）  |
     |                         +---------------------+-------------------------+
     |                                               | 是
     |                                               v
     |                         +-----------------------------------------------+
     |                         | 4a. Fusion Sidekick 实证探针优先：            |
     |                         |  直接查源码 / 规范文档 / 编译器 / REPL 实测   |
     |                         |  -> 晋升 VERIFIED_MINORITY_GOLD 或证伪剔除    |
     |                         | 4b. Multiagent 1 跳跨缝知识接力：             |
     |                         |  仅把 {已核验片段 A + 待解接缝 B} 发给互补席  |
     |                         |  位检验端到端兼容性                           |
     |                         +---------------------+-------------------------+
     |                                               |
     +-----------------------------------------------+
                                          |
                                          v
                     +-----------------------------------------+
                     | 复核 `ledger` 四项硬不变量：            |
                     | - tier_honesty == true（无伪装跨模共识）|
                     | - minority_anchor_protected == true     |
                     | - relay_stop_loss_respected (<=1 轮)    |
                     +--------------------+--------------------+
                                          |
                                          v
                     +=========================================+
                     | §6. 结构化交付契约（Output Contract）   |
                     | 1. 综合裁决、实跑席位层级与结论切换边界 |
                     | 2. 三域认知图谱（跨族共识 / 分歧断层 /  |
                     |    1/N 独有盲区点亮与长尾知识接力）     |
                     | 3. 各席位独立摘要表                     |
                     | 4. Devin Fusion 落地执行简报            |
                     |    （刚性约束 + 有序备选阶梯 + 验收项） |
                     +=========================================+
```

---

## 目录组成与常用命令

- [SKILL.md](SKILL.md) — 六步主控协议、快速旁路与防造假/防死循环止损门禁。
- [references/paradigm-synthesis-and-schemas.md](references/paradigm-synthesis-and-schemas.md) — Model Council、Multiagent 与 Devin Fusion 三范式对照矩阵、提示词契约与 JSON Schema。
- `scripts/council_runner.py` — 零第三方依赖的 Python 标准库工具（`probe`、`dispatch`、`ledger`、`selftest`）。
- `tests/test_council_runner.py` — 家族推断、Fusion 复合 ID 解析、密钥脱敏与 `1/N` 保护回归测试。

```bash
# 1. 探测本机多模型 CLI 与实时 Devin 异构家族 / Fusion 目录
python3 scripts/council_runner.py probe --discover-models

# 2. 零开销预检首轮盲审多样性比率与 Fact Pack 倾向性告警
python3 scripts/council_runner.py dispatch --dry-run --input brief.json

# 3. 运行反多数票认知账本分桶并输出 Markdown 表格
python3 scripts/council_runner.py ledger --input ledger.json --format markdown

# 4. 运行内置不变量自检与单元测试
python3 scripts/council_runner.py selftest
python3 -m unittest discover -s tests -v
```
