# NPC Talk Demo (Agentscope)

NPC 群聊（无 KP）的最小可跑通 Demo。基于真实 Agentscope（`agentscope.pipeline`），通过 Kimi 的 OpenAI 兼容接口驱动 LLM NPC。

## Quick Start（推荐 Conda）

```bash
# 一次性：创建并激活环境（进入本仓库根目录）
cd /Users/administrator/syncdisk/rhodes_resonance
conda env create -f environment.yml
conda activate npc-talk

# 必填：Kimi API Key
export MOONSHOT_API_KEY=你的Kimi密钥
# 可选：自定义 Kimi 接口与模型（如需）
export KIMI_BASE_URL=https://api.moonshot.cn/v1
export KIMI_MODEL=kimi-k2-turbo-preview

# 运行
python src/main.py      # 入口（已内联引擎逻辑）
```

## 目录结构（当前）

```
repo/
  src/
    main.py               # 入口 + 回合驱动（原 runtime/engine.py 已内联至此）
    actions/
      npc.py              # 动作适配层（将世界工具包装为 Agent 可调用的工具）
    agents/
      factory.py          # Kimi ReActAgent 构造器（系统提示拼装 + 工具注册）
    world/
      tools.py            # 世界状态与工具（时间、关系、物品、D&D、事件时钟…）
    eventlog/
      *.py                # 事件总线与日志（结构化 JSONL + 文本）
    settings/
      loader.py           # 配置加载与项目路径工具
  configs/
    characters.json       # 角色配置（人设/D&D数值/关系）
    story.json            # 场景配置、初始位置、剧情节拍
    model.json            # LLM 接入（base_url、npc 模型等）
    prompts.json          # 可选：NPC 提示词模板（若缺省将使用内置默认模板）
    weapons.json          # 武器定义（reach_steps/ability/damage_expr）
  docs/
    spec.md               # 项目规范（设计/接口/约定）
  environment.yml         # Conda 环境（Python 3.11 + Agentscope）
  pyproject.toml          # 打包/开发工具（ruff/mypy/pytest），可 `pip install -e .[dev]`
  logs/
    run_events.jsonl      # 结构化事件日志（JSONL）
    run_story.log         # 人类可读对话日志

备注：自本次变更起，`src/runtime/engine.py` 已删除，其内容合并到 `src/main.py` 的 `run_demo()` 与辅助函数中。
```



## 架构与期望

- 中心-子部件：`main` 作为编排器；子部件分离：
  - world：关于环境-攻击-位置-角色（包含外貌、人设、口癖等元信息）
  - actions：将 world 的接口包装为工具，供 agents 直接调用
  - agents：角色的调用（LLM NPC），仅依赖提示词与工具，不直接耦合 world
- 以数据为起点：
  - 参与者来源于 `story.json` 的坐标键；若无参与者，运行会在进入 Hub 前自动结束（本次更新）。
  - 角色数值/物品来自 `characters.json`；武器触及与伤害来自 `weapons.json`。
- Prompt 组合（每次行动前）：
  - 世界概要（Host 生成、当前状态）+ 行动记忆（最近播报，含工具结果）+ 指导 prompt（Agent 的系统提示，人设/外观/关系/武器/工具规则）
- 行为约束：
  - 攻击不会自动靠近：若距离不足，请先 `advance_position()` 再 `perform_attack()`。
  - 工具调用 JSON 必须包含 `reason` 字段（行为理由）。
  - 需要武器“持有”才能攻击；守护（`set_protection`）要求相邻且有反应可用。
- 错误与可观测性（本次更新）：
  - 世界概要广播失败与场景细节写入失败、武器表载入失败，均会记录 error 事件，但不中断流程。

## 运行时交互

- KP/裁决已移除；仅 NPC 轮流行动，输出对白与 CALL_TOOL。
- 每回合流程：
  1) 开场公告（含参与者与初始坐标）；
  2) 对于每名 NPC 的行动：先广播一份世界概要与“最近播报”（行动记忆），随后由 NPC 发言并调用工具；
  3) 回合推进；若无敌对则退出战斗；若 `story` 无参与者则在进入 Hub 前直接结束；

## 日志输出

- `logs/run_events.jsonl`：结构化事件流（JSONL）。可通过 `npc-talk-logs --actor Amiya --turn 2 --pretty` 快速筛选。
- `logs/run_story.log`：面向玩家的对话文本，直接镜像游戏内广播。
- 初次运行会覆盖旧日志；如需长期存档可在 `logs/` 下按运行复制备份。
- 说明：不再生成 `*_context_dev.log`（开发态 context 卡片），统一以上述 prompt 日志为准。
 - `logs/prompts/<actor>_prompt.txt`：每个角色的“系统 Prompt + 注入内存”调试转储，仅保留最新；每次运行开始会清空历史（由 `DEBUG_DUMP_PROMPTS` 控制是否输出）。

## 必要环境变量

- `MOONSHOT_API_KEY`（必填）：Kimi API Key
- `KIMI_BASE_URL`（可选，默认 `https://api.moonshot.cn/v1`）
- `KIMI_MODEL`（可选，默认 `kimi-k2-turbo-preview`）

注：也可通过 `configs/model.json` 调整 base_url/模型与温度/是否流式。

## 配置要点（configs）

 - `characters.json`：角色人设与数值、关系、初始物品
  - 角色项：`type: "player"|"npc"`，`persona`（人设），`dnd`（AC/HP/能力/熟练），`inventory`
  - 武器与范围：不再从角色卡读取攻击距离。请在 `configs/weapons.json` 定义武器并给出 `reach_steps`（步）；在 `characters.json` 通过 `inventory` 声明角色初始拥有的武器（例如 `"inventory": {"amiya_focus": 1}`）。`perform_attack(attacker, defender, weapon, reason)` 会从武器表自动获取触及范围与伤害表达式，且只有“持有”的武器才允许使用；若距离不足不会自动靠近。
- `story.json`：场景名称、胜利条件、初始坐标与剧情节拍（acts/beats）；参与者与出场顺序由 `initial_positions` 或 `positions` 的键顺序决定
- `prompts.json`（可选）：玩家人设、名称映射、NPC/敌人提示词模板（示例见 `prompts.json.example`）
- `model.json`：`base_url`、`npc` 模型名、温度、是否流式
- `time_rules.json`：各意图的时间消耗（分钟）
 - `relation_rules.json`：默认关系变更策略

## 世界工具（节选）

- 时间与事件：`advance_time(mins)`, `schedule_event(name, at_min, ...)`（自动触发）
- 关系与物品：`change_relation(a,b,delta,reason)`, `grant_item(target,item,n)`
- 角色：`set_dnd_character(...)`, `get_stat_block(name)`, `damage(name,n)`, `heal(name,n)`
- 检定/攻击（D&D风格）：`skill_check_dnd(name, skill, dc, advantage?)`；武器攻击用 `perform_attack(attacker, defender, weapon, reason)`（触及范围与伤害由武器决定）
  - 注意：攻击不会自动移动到目标位置。若距离不足，请先使用 `advance_position()` 显式移动至触及范围，再进行 `perform_attack()`。
- 氛围：`adjust_tension(delta)`, `add_mark(text)`
- 查询：使用 `WORLD.snapshot()` 获取原始世界状态（由上层渲染人类可读概要）
- 目标：`add_objective(name)`, `complete_objective(name, note?)`, `block_objective(name, reason?)`

工具返回 `ToolResponse`；本版本不再自动裁决（仅展示 NPC 对白与工具调用）。

## 开发与规范

- 代码布局采用 src/ 包结构；`pyproject.toml` 提供脚本入口与开发工具。
- 统一格式与检查：`ruff`、`mypy`（见 `.pre-commit-config.yaml`）。可启用 pre-commit：`pre-commit install`。
- 最小单测样例见 `tests/`，包含世界工具的健壮性校验。

## 常见问题

## 发布前端到 GitHub Pages

- 一键发布：
  - ./scripts/deploy_frontend.sh  # 默认从 main 的 web/ 同步到 gh-pages
  - 或指定分支：./scripts/deploy_frontend.sh feat/your-branch
- 脚本会：
  - 将 web/index.html、app.js、style.css、config.js 同步到 gh-pages 根目录
  - 在 index.html 为静态资源追加 ?v=<短哈希> 以规避缓存
  - 提交并推送 gh-pages
- 注意：运行前需保证工作区无未提交改动。

- `ModuleNotFoundError: agentscope`：确认已在 `npc-talk` 环境中，并已按 `environment.yml` 安装。
- Kimi 报错/无响应：检查 `MOONSHOT_API_KEY`、网络连通、`KIMI_BASE_URL` 与模型名。

## 后续可做
- 扩展剧情 JSON（configs/story.json），若未来恢复导演逻辑可用于触发事件
- 引入结构化输出校验/重试与可视化
- 接入游戏引擎（HTTP/MCP 工具）
