# Ace Attorney Ren'Py — 设计文档

> 本文档定义自定义 Statement 语法规范、JSON 数据格式、文件结构。
> 所有后续步骤的实现以本文档为准。

---

## 一、文件结构

### 1.1 引擎模块（`renpy/common/`）

```
renpy/common/
├── 00aa_core.rpy              # 核心：CourtRecord 数据类、Evidence、Profile、通用工具函数
├── 00aa_screens.rpy           # 所有 AA 专用 Screen（血槽、证言面板、证物面板、询问按钮等）
├── 00aa_courtroom.rpy         # 法庭系统：自定义 Statement 注册、证言/询问逻辑
├── 00aa_investigation.rpy     # 搜证系统：热点、NPC交互、地点导航、角色移动
├── 00aa_text.rpy              # 文本演出：打字机音效、自定义 TextTag
├── 00aa_psyche_lock.rpy       # 心灵枷锁系统（P1，可选加载）
├── 00aa_revisualization.rpy   # 高潮推理系统（P2，可选加载）
├── 00aa_mind_chess.rpy        # 逻辑象棋系统（P2，可选加载）
└── 00aa_effects.rpy           # 演出效果：异议动画、屏幕震动、法官锤等
```

文件以 `00aa_` 为前缀，`00` 保证高加载优先级（在游戏脚本之前初始化），`aa` 表示 Ace Attorney 专用。

### 1.2 游戏项目模板（`game/`）

```
game/
├── script.rpy                 # 主入口，案件流程脚本
├── options.rpy                # 项目配置（窗口标题、分辨率等）
├── screens.rpy                # Ren'Py 原有 Screen（保留）
│
├── aa/
│   ├── case.json              # 案件元信息（章节结构）
│   ├── evidence.json          # 证物定义
│   ├── characters.json        # 角色定义（立绘路径、音色等）
│   ├── locations.json         # 地点定义（背景、热点、NPC）
│   ├── courtroom.rpy          # 法庭阶段脚本（证言、询问）
│   └── investigation.rpy      # 搜证阶段脚本（调查、对话）
│
├── images/
│   ├── bg/                    # 背景图
│   ├── characters/            # 角色立绘
│   ├── evidence/              # 证物图标和检查图
│   ├── ui/                    # UI 元素（血槽、按钮、面板等）
│   └── effects/               # 特效图（异议冲击、闪白等）
│
└── audio/
    ├── bgm/                   # 背景音乐
    ├── sfx/                   # 音效
    └── voice/                 # 语音（嘟嘟声等）
```

---

## 二、自定义 Statement 语法规范

### 2.0 注册框架

所有自定义 Statement 通过统一的注册函数注册：

```python
init python:
    def aa_register_statement(name, parse_func, execute_func, **kwargs):
        """统一的 AA Statement 注册函数"""
        renpy.register_statement(
            name,
            parse=parse_func,
            execute=execute_func,
            **kwargs
        )
```

每个 Statement 需要定义：
- `parse`：解析器，从 lexer 中提取参数，返回 AST 节点数据
- `execute`：执行器，在运行时执行逻辑，返回下一个节点或 None（线性继续）

### 2.1 法庭系统 Statement

---

#### `cross_examination`（粗粒度，包裹整个询问流程）

**语法**：
```renpy
cross_examination "证言标题":
    # 证言展示 + 询问交互全部写在这里
```

**参数**：
- `"证言标题"`：字符串，显示在证言面板上方的标题

**Block 内容**：包含 `stmt`、`press`、`present`、`penalty` 等语句

**执行行为**：
1. 初始化询问上下文（设置 UI 模式为"证言展示"）
2. 顺序执行 block 内的子节点
3. block 结束后自动清理 UI 状态

---

#### `begin_testimony`（细粒度，仅开启证言展示）

**语法**：
```renpy
begin_testimony "证言标题" by 角色名
```

**参数**：
- `"证言标题"`：字符串，如 "证言 ~~ ～事件的概要～"
- `by 角色名`：可选，证人角色名（用于自动切换立绘）

**执行行为**：
1. 显示 "证言中" 标签
2. 初始化证言进度指示点（根据后续 stmt 数量）
3. 切换到证言展示模式 UI
4. 如果指定了 `by`，自动 `show` 该角色的证言立绘

---

#### `stmt`（证言陈述）

**语法**：
```renpy
stmt "证言文本内容"
```

**参数**：
- `"证言文本内容"`：一条证言陈述的文本

**执行行为**：
1. 在证言面板中显示当前文本
2. 更新进度指示点（高亮当前条目）
3. 播放 "叮" 音效（切换到新证言时）
4. 等待玩家点击继续（或按左右键切换到其他 stmt）

**数据记录**：每条 stmt 按顺序编号（从 0 开始），供 `press` 和 `present` 引用

---

#### `press`（威慑）

**语法**：
```renpy
press 目标:
    "威慑后的追问对话"
    "可以有多行"
    # 可选：追加新证言
    add_stmt "追加的证言内容"
    # 可选：扣血
    penalty 1
    # 可选：获得新证物
    get_evidence 证物id
```

**参数**：
- `目标`：以下三种形式之一
  - 数字（如 `1`）：威慑第 N 条 stmt（0-based）
  - `current`：威慑当前正在查看的 stmt
  - `all`：对所有 stmt 都可威慑（配合 block 内的条件判断）

**Block 内容**：
- 字符串行：威慑后的追问对话
- `add_stmt "文本"`：在 stmt 列表末尾追加新证言
- `penalty N`：扣 N 格血
- `get_evidence id`：获得新证物
- `jump label`：跳转到指定标签

**执行行为**：
1. 验证目标 stmt 是否可威慑（标记为 pressable）
2. 执行 block 内容
3. 如果有 `add_stmt`，更新证言面板（进度指示点数量变化）
4. 如果有 `penalty`，触发扣血流程
5. block 执行完毕后回到证言展示模式

---

#### `present`（举证）

**语法**：
```renpy
present 目标 using 正确证物id:
    # 举证成功后的剧情
    "正确！证言与证物矛盾！"
    jump next_phase

present 目标 using [证物id1, 证物id2]:
    # 双证物举证
    jump next_phase
```

**参数**：
- `目标`：同 `press`（数字 / `current` / `all`）
- `using 正确证物id`：单证物举证
- `using [id1, id2]`：双证物组合举证

**Block 内容**：举证成功后执行的剧情脚本

**执行行为**：
1. 验证目标 stmt 是否可举证（标记为 presentable）
2. 显示证物选择面板（Screen，阻塞等待玩家选择）
3. 玩家选择证物后：
   - **正确**：播放"异议！"动画 → 执行 block 内容
   - **错误**：执行 `on_wrong_present` 回调（默认扣 1 格血）→ 回到证言展示
4. 玩家按 ESC/Q：关闭证物面板，回到证言展示（不扣血）

---

#### `penalty`（扣血）

**语法**：
```renpy
penalty 数量
```

**参数**：
- `数量`：扣几格血（通常为 1，特殊情况为 2）

**执行行为**：
1. 扣减血量
2. 播放扣血动画（血槽红色闪烁 + 减少 + 音效）
3. 屏幕震动
4. 如果血量 ≤ 0：触发 Game Over

---

#### `end_testimony`（结束证言）

**语法**：
```renpy
end_testimony
```

**参数**：无

**执行行为**：
1. 隐藏证言面板和询问按钮
2. 清理询问上下文
3. 继续执行后续脚本

---

### 2.2 搜证系统 Statement

---

#### `hotspot`（定义可调查热点）

**语法**：
```renpy
hotspot "热点名称" at (x, y) size (w, h):
    # 调查后的对话和效果

hotspot "热点名称" at (x, y) size (w, h) radius r:
    # radius：角色靠近此距离时才显示交互提示
```

**参数**：
- `"热点名称"`：显示在交互提示中的名称
- `at (x, y)`：热点在场景中的位置（像素坐标）
- `size (w, h)`：热点的可点击区域大小
- `radius r`：可选，角色靠近交互的距离阈值（默认 100）

**Block 内容**：调查该热点后执行的脚本（对话、获得证物等）

**执行行为**：
1. 在场景中注册一个可点击区域
2. 鼠标悬停时显示高亮提示
3. 玩家点击或角色靠近后按交互键 → 执行 block
4. block 执行完毕后标记为已调查（可配置是否可重复调查）

---

#### `examine`（调查描述）

**语法**：
```renpy
examine "描述文本"
```

**参数**：
- `"描述文本"`：调查某物后的旁白描述

**执行行为**：
1. 显示描述文本（使用旁白 Character）
2. 等待玩家点击继续

**说明**：`examine` 是 `hotspot` block 内的便捷写法，等价于一行旁白对话。用于快速定义"看一眼就出文字"的简单热点。

---

#### `get_evidence`（获得证物）

**语法**：
```renpy
get_evidence 证物id
```

**参数**：
- `证物id`：对应 `evidence.json` 中定义的证物 ID

**执行行为**：
1. 从 `evidence.json` 加载证物数据
2. 添加到 `CourtRecord`
3. 播放证物发现动画 + 音效
4. 显示 "获得证物：XXX" 提示

---

#### `talk`（与 NPC 对话）

**语法**：
```renpy
talk 角色名:
    topic "话题名称":
        "对话内容第一行"
        "对话内容第二行"
    topic "另一个话题":
        "..."
    # 可选：出示证物的反应
    present 证物id:
        "NPC 对此证物的反应"
    present 另一个证物id:
        "另一种反应"
```

**参数**：
- `角色名`：对应 `characters.json` 中定义的角色 ID

**Block 内容**：
- `topic "名称":` — 闲聊话题，可有多个
- `present 证物id:` — 向该 NPC 出示证物的反应

**执行行为**：
1. 显示 NPC 对话菜单（话题列表 + "出示证物" 选项）
2. 选择话题 → 执行 topic block → 标记为已聊
3. 选择"出示证物" → 打开证物选择面板 → 匹配 present block
4. 没有匹配的 present → 显示默认反应 "这个不太相关吧..."

---

#### `move`（切换地点）

**语法**：
```renpy
move 目标地点id
move 目标地点id if 条件
```

**参数**：
- `目标地点id`：对应 `locations.json` 中定义的地点 ID
- `if 条件`：可选，条件不满足时显示 "现在没有必要去那里"

**执行行为**：
1. 检查条件（如有）
2. 播放地点切换音效
3. 切换场景背景
4. 重新注册该地点的 hotspot 和 NPC

---

#### `begin_investigation`（开始搜证阶段）

**语法**：
```renpy
begin_investigation "场景名称" at 地点id
```

**参数**：
- `"场景名称"`：当前场景描述（用于调试/日志）
- `at 地点id`：初始所在地点

**执行行为**：
1. 加载该地点的背景和热点
2. 显示搜证 UI（角色、热点高亮、移动控制）
3. 启用 WASD 移动 + 鼠标点击交互

---

#### `end_investigation`（结束搜证阶段）

**语法**：
```renpy
end_investigation
```

**执行行为**：
1. 退出搜证 UI
2. 清理移动控制和热点注册
3. 继续后续脚本

---

### 2.3 特殊系统 Statement

---

#### `psyche_lock`（心灵枷锁）

**语法**：
```renpy
psyche_lock "角色名" with 锁数:
    lock 1:
        require 证物id
        on_wrong "错误时NPC说的话"
        on_right "正确时NPC说的话"
    lock 2:
        require [证物id1, 证物id2]
        on_wrong "..."
        on_right "..."
    on_complete:
        "全部解锁后的对话"
        get_evidence 新证物id
```

**参数**：
- `"角色名"`：触发心锁的 NPC
- `with 锁数`：锁环数量（1~5）

**Block 内容**：
- `lock N:` — 第 N 层锁环的定义
  - `require 证物id` 或 `require [id1, id2]` — 正确证物
  - `on_wrong "..."` — 错误反应对话
  - `on_right "..."` — 正确反应对话
- `on_complete:` — 全部解锁后的剧情

**执行行为**：
1. 显示心锁 UI（暗色遮罩 + 锁链视觉）
2. 从第 1 层开始，每层：
   - 显示证物选择面板
   - 正确 → 锁链断裂动画 + on_right 对话 → 进入下一层
   - 错误 → 扣血 + on_wrong 对话 → 重试当前层
3. 全部解锁 → on_complete 剧情
4. 血量不足 → 强制退出心锁，不推进剧情

---

#### `mind_chess`（逻辑象棋）

**语法**：
```renpy
mind_chess "对手名":
    round 1:
        prompt "当前博弈局面的描述"
        option "攻击选项A" type attack:
            "正确的攻击！对手露出破绽。"
        option "攻击选项B" type attack:
            penalty 1
            "对手挡住了你的攻击。"
        option "防御选项A" type defend:
            "你成功防御了对手的攻势。"
        option "防御选项B" type defend:
            penalty 1
            "你被对手击中了。"
    round 2:
        prompt "新的局面"
        option "..." type attack:
            ...
    on_win:
        "对弈胜利！你获得了关键线索。"
        get_evidence 线索id
    on_lose:
        "对弈失败..."
```

**参数**：
- `"对手名"`：对弈对手角色名

**Block 内容**：
- `round N:` — 第 N 轮博弈
  - `prompt "..."` — 当前局面描述
  - `option "文本" type attack/defend:` — 选项及后果
- `on_win:` — 胜利后的剧情
- `on_lose:` — 失败后的剧情

**执行行为**：
1. 显示棋盘 UI
2. 每轮：
   - 显示 prompt 描述
   - 启动倒计时
   - 玩家在限时内选择选项
   - 正确 → 推进到下一轮
   - 错误 → 扣宝石 → 重试（或判定失败）
3. 所有轮完成 → on_win
4. 宝石耗尽 → on_lose

---

#### `revisualization`（高潮推理）

**语法**：
```renpy
revisualization:
    question "逻辑问题1":
        answer 证物id:
            "正确！矛盾被指出。"
        answer 证词id:
            "正确！关键证词被确认。"
        on_wrong:
            penalty 1
            "推理有误。"
    question "逻辑问题2":
        answer 证物id:
            "..."
    on_complete:
        "真相揭晓！"
        jump 案件结局
```

**Block 内容**：
- `question "问题":` — 一个推理环节
  - `answer id:` — 正确答案（证物或证词 ID）及反应
  - `on_wrong:` — 错误时的惩罚
- `on_complete:` — 全部推理完成后的剧情

**执行行为**：
1. 显示推理 UI
2. 依次展示每个 question
3. 玩家选择答案：
   - 正确 → 显示 answer block 反应 → 下一题
   - 错误 → 扣血 + on_wrong → 重试
4. 全部完成 → on_complete

---

### 2.4 演出效果 Statement

---

#### `objection`（异议冲击）

**语法**：
```renpy
objection "角色名"
objection "角色名" style defense
objection "角色名" style prosecution
```

**参数**：
- `"角色名"`：喊出异议的角色
- `style defense/prosecution`：可选，默认 defense。决定背景色和文字样式

**执行行为**：
1. 全屏显示角色立绘 + "异议！" 冲击文字
2. 画面闪白 + 屏幕震动
3. 播放异议音效
4. 持续约 0.8 秒后自动消失

---

#### `hold_it`（待った）

**语法**：
```renpy
hold_it "角色名"
```

**执行行为**：同 `objection`，但使用 "待った！" 文字和对应音效

---

#### `take_that`（くらえ）

**语法**：
```renpy
take_that "角色名"
```

**执行行为**：同 `objection`，但使用 "くらえ！" 文字和对应音效

---

#### `screen_shake`（屏幕震动）

**语法**：
```renpy
screen_shake
screen_shake intensity 1.0 duration 0.5
```

**参数**：
- `intensity`：震动强度（默认 1.0）
- `duration`：持续时间秒数（默认 0.3）

---

#### `gavel`（法官敲锤）

**语法**：
```renpy
gavel
gavel 3  # 敲三下
```

**参数**：敲击次数（默认 1）

---

### 2.5 关键绑定

| 按键 | 法庭模式 | 搜证模式 | 心锁/推理/象棋 |
|------|----------|----------|----------------|
| Space / Enter | 推进对话 | 交互（靠近热点时） | 确认选择 |
| Z | 威慑（press） | — | — |
| X | 举证（present） | 出示证物 | — |
| C | 打开/关闭证物面板 | 打开/关闭证物面板 | — |
| ← → | 切换证言条目 | — | 切换选项 |
| WASD / 方向键 | — | 移动角色 | — |
| E / Space | — | 交互 | — |
| ESC / Q | 关闭面板/返回 | 关闭面板/返回 | 取消 |

---

## 三、JSON 数据格式

### 3.1 `evidence.json` — 证物定义

```json
{
  "version": 1,
  "evidence": [
    {
      "id": "autopsy_report",
      "name": "解剖记录",
      "description": "被害者的解剖记录。死亡推定时间为下午4点左右。",
      "icon": "images/evidence/autopsy_report_icon.png",
      "examine_images": [
        "images/evidence/autopsy_report_01.png"
      ],
      "updated_description": null,
      "updated_icon": null,
      "combinable_with": null,
      "tags": ["court_record"]
    },
    {
      "id": "knife",
      "name": "凶器小刀",
      "description": "在案发现场发现的小刀。刀刃上有血迹。",
      "icon": "images/evidence/knife_icon.png",
      "examine_images": [
        "images/evidence/knife_01.png",
        "images/evidence/knife_02.png"
      ],
      "updated_description": "刀刃上的血迹经鉴定为被害者的血。但刀柄上没有指纹。",
      "updated_icon": "images/evidence/knife_icon_updated.png",
      "combinable_with": null,
      "tags": ["court_record"]
    },
    {
      "id": "fingerprint_report",
      "name": "指纹鉴定书",
      "description": "对凶器小刀的指纹鉴定结果。",
      "icon": "images/evidence/fingerprint_icon.png",
      "examine_images": [
        "images/evidence/fingerprint_01.png"
      ],
      "updated_description": null,
      "updated_icon": null,
      "combinable_with": "knife",
      "combine_result": "knife_with_fingerprints",
      "tags": ["court_record"]
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 唯一标识符，脚本中通过此 ID 引用 |
| `name` | string | 是 | 显示名称 |
| `description` | string | 是 | 证物描述文本 |
| `icon` | string | 是 | 证物图标路径（证物面板中显示） |
| `examine_images` | string[] | 否 | 检查证物时显示的大图列表（支持多角度） |
| `updated_description` | string | 否 | 获得新信息后的更新描述（`update_evidence` 时替换） |
| `updated_icon` | string | 否 | 更新后的图标路径 |
| `combinable_with` | string | 否 | 可与之组合的证物 ID（用于双证物举证） |
| `combine_result` | string | 否 | 组合后产生的新证物 ID |
| `tags` | string[] | 否 | 标签（如 `court_record` 表示显示在法庭记录中，`profile` 表示人物档案） |

---

### 3.2 `characters.json` — 角色定义

```json
{
  "version": 1,
  "characters": [
    {
      "id": "phoenix",
      "name": "成步堂龙一",
      "color": "#c8ffc8",
      "beep_sfx": "audio/sfx/beep_defense.ogg",
      "sprites": {
        "idle": "images/characters/phoenix/idle.png",
        "talk": [
          "images/characters/phoenix/talk_01.png",
          "images/characters/phoenix/talk_02.png"
        ],
        "objection": "images/characters/phoenix/objection.png",
        "breakdown": [
          "images/characters/phoenix/breakdown_01.png",
          "images/characters/phoenix/breakdown_02.png",
          "images/characters/phoenix/breakdown_03.png"
        ],
        "sweat": "images/characters/phoenix/sweat.png",
        "slam": [
          "images/characters/phoenix/slam_01.png",
          "images/characters/phoenix/slam_02.png"
        ],
        "think": "images/characters/phoenix/think.png",
        "shock": "images/characters/phoenix/shock.png",
        "smile": "images/characters/phoenix/smile.png",
        "angry": "images/characters/phoenix/angry.png",
        "sad": "images/characters/phoenix/sad.png"
      },
      "position": "left"
    },
    {
      "id": "sahwit",
      "name": "山崎正夫",
      "color": "#c8c8ff",
      "beep_sfx": "audio/sfx/beep_witness.ogg",
      "sprites": {
        "idle": "images/characters/sahwit/idle.png",
        "talk": [
          "images/characters/sahwit/talk_01.png",
          "images/characters/sahwit/talk_02.png"
        ],
        "sweat": "images/characters/sahwit/sweat.png"
      },
      "position": "right"
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 唯一标识符 |
| `name` | string | 是 | 显示名称 |
| `color` | string | 否 | 对话文字颜色（十六进制） |
| `beep_sfx` | string | 否 | 嘟嘟声音效路径（不指定则用默认音色） |
| `sprites` | object | 是 | 立绘资源映射。key 为动画状态名，value 为单帧路径或多帧路径数组 |
| `position` | string | 否 | 默认显示位置（`left` / `center` / `right`） |

**预设动画状态名**（`sprites` 中的 key）：

| 状态名 | 说明 | 帧数 |
|--------|------|------|
| `idle` | 站立待机 | 1 |
| `talk` | 说话 | 2~4（循环播放） |
| `objection` | 异议指人姿势 | 1 |
| `breakdown` | 崩溃动画 | 4~8（单次播放） |
| `sweat` | 紧张流汗 | 1~2 |
| `slam` | 拍桌子 | 2~3 |
| `think` | 思考 | 1 |
| `shock` | 震惊 | 1~2 |
| `smile` | 微笑 | 1 |
| `angry` | 愤怒 | 1 |
| `sad` | 悲伤 | 1 |

---

### 3.3 `locations.json` — 地点定义

```json
{
  "version": 1,
  "locations": [
    {
      "id": "crime_scene",
      "name": "案发现场",
      "background": "images/bg/crime_scene.png",
      "bgm": "audio/bgm/investigation.ogg",
      "hotspots": [
        {
          "id": "vase",
          "name": "花瓶",
          "position": [800, 400],
          "size": [120, 160],
          "radius": 100,
          "examined": false
        },
        {
          "id": "desk",
          "name": "书桌",
          "position": [400, 350],
          "size": [200, 120],
          "radius": 100,
          "examined": false
        }
      ],
      "npcs": [
        {
          "id": "detected",
          "name": "糸锯圭介",
          "position": [1200, 400],
          "sprite": "images/characters/detected/idle.png",
          "topics": ["事件当天的情况", "关于被害者", "关于嫌疑犯"],
          "evidence_reactions": {
            "knife": "这是凶器？让我看看...嗯，上面没有指纹。",
            "photo": "这张照片...拍摄角度很奇怪啊。"
          }
        }
      ],
      "exits": [
        {
          "target": "police_station",
          "name": "前往警察局",
          "position": [0, 500],
          "size": [100, 300],
          "condition": null
        },
        {
          "target": "court",
          "name": "前往法庭",
          "position": [960, 100],
          "size": [200, 100],
          "condition": "has_evidence('autopsy_report') and has_evidence('knife')"
        }
      ]
    },
    {
      "id": "police_station",
      "name": "警察局",
      "background": "images/bg/police_station.png",
      "bgm": "audio/bgm/investigation.ogg",
      "hotspots": [],
      "npcs": [],
      "exits": [
        {
          "target": "crime_scene",
          "name": "返回案发现场",
          "position": [900, 500],
          "size": [100, 200],
          "condition": null
        }
      ]
    }
  ]
}
```

**字段说明**：

**Location**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 唯一标识符 |
| `name` | string | 是 | 显示名称 |
| `background` | string | 是 | 背景图路径 |
| `bgm` | string | 否 | 该地点的 BGM（切换地点时自动切换） |
| `hotspots` | object[] | 否 | 可调查热点列表 |
| `npcs` | object[] | 否 | NPC 列表 |
| `exits` | object[] | 否 | 出口/传送点列表 |

**Hotspot**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识 |
| `name` | string | 显示名称 |
| `position` | [x, y] | 场景中的位置 |
| `size` | [w, h] | 可点击区域大小 |
| `radius` | number | 角色靠近交互的距离 |
| `examined` | bool | 初始是否已调查（运行时状态由 CourtRecord 管理） |

**NPC**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识 |
| `name` | string | 显示名称 |
| `position` | [x, y] | 场景中的位置 |
| `sprite` | string | 立绘路径 |
| `topics` | string[] | 闲聊话题标题列表 |
| `evidence_reactions` | object | 出示证物的反应（key=证物ID，value=对话文本） |

**Exit**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `target` | string | 目标地点 ID |
| `name` | string | 显示名称 |
| `position` | [x, y] | 出口位置 |
| `size` | [w, h] | 可点击区域 |
| `condition` | string | 可选，Python 表达式，为 true 时才可通行 |

---

### 3.4 `case.json` — 案件元信息

```json
{
  "version": 1,
  "title": "第一次逆转",
  "author": "示例作者",
  "chapters": [
    {
      "id": "chapter_1",
      "title": "第一章 逆转的起点",
      "phases": [
        {
          "type": "investigation",
          "label": "ch1_investigation",
          "title": "搜证 ～案发现场～",
          "evidence_pool": ["autopsy_report", "knife", "photo"],
          "characters": ["detected", "maya"],
          "locations": ["crime_scene", "police_station"]
        },
        {
          "type": "trial",
          "label": "ch1_trial",
          "title": "法庭 ～第一次逆转～",
          "evidence_pool": ["autopsy_report", "knife", "photo", "fingerprint_report"],
          "characters": ["phoenix", "sahwit", "judge"]
        }
      ]
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | number | 格式版本 |
| `title` | string | 案件标题 |
| `author` | string | 作者 |
| `chapters` | object[] | 章节列表 |
| `chapters[].id` | string | 章节 ID |
| `chapters[].title` | string | 章节标题 |
| `chapters[].phases` | object[] | 阶段列表（按游戏顺序排列） |
| `phases[].type` | string | `investigation` 或 `trial` |
| `phases[].label` | string | 对应 .rpy 脚本中的 label 名 |
| `phases[].title` | string | 阶段标题（用于标题卡显示） |
| `phases[].evidence_pool` | string[] | 该阶段可获得的所有证物 ID |
| `phases[].characters` | string[] | 该阶段出现的角色 ID |
| `phases[].locations` | string[] | 该阶段可去的地点 ID（仅 investigation） |

---

## 四、数据加载流程

```
游戏启动
  │
  ├─ init python 阶段（Ren'Py 初始化）
  │   ├─ 加载 00aa_core.rpy → 定义 CourtRecord 等类
  │   ├─ 加载 00aa_courtroom.rpy → 注册法庭 Statement
  │   ├─ 加载 00aa_investigation.rpy → 注册搜证 Statement
  │   ├─ 加载 00aa_text.rpy → 设置文本演出 hook
  │   └─ 加载 00aa_effects.rpy → 注册演出 Statement
  │
  ├─ 游戏脚本执行
  │   ├─ label start:
  │   │   ├─ $ load_evidence("aa/evidence.json")   → 加载证物到内存
  │   │   ├─ $ load_characters("aa/characters.json") → 加载角色定义
  │   │   ├─ $ load_locations("aa/locations.json")   → 加载地点定义
  │   │   └─ jump chapter_1
  │   │
  │   ├─ label chapter_1:
  │   │   ├─ begin_investigation "搜证" at crime_scene
  │   │   ├─ ... 搜证脚本 ...
  │   │   ├─ end_investigation
  │   │   ├─ cross_examination "证言 ~~ 事件概要"
  │   │   ├─ ... 法庭脚本 ...
  │   │   └─ end_testimony
  │   │
  │   └─ ...
  │
  └─ 运行时
      ├─ CourtRecord 实例（store.court_record）管理所有动态状态
      ├─ JSON 定义为只读参考数据（不修改原文件）
      └─ 状态变更通过 CourtRecord 方法，自动参与存档/回滚
```

---

## 五、可扩展性设计

### 5.1 注册式架构

所有"可选项列表"通过注册机制管理，而非硬编码。新增类型只需调用注册函数。

**动画状态注册**：
```python
init python:
    # 默认动画状态集（00aa_core.rpy 中注册）
    aa_default_anim_states = {
        "idle":     {"frames": 1, "loop": True},
        "talk":     {"frames": 2, "loop": True},
        "objection": {"frames": 1, "loop": False},
        "breakdown": {"frames": 4, "loop": False},
        "sweat":    {"frames": 1, "loop": False},
        "slam":     {"frames": 2, "loop": False},
        "think":    {"frames": 1, "loop": False},
        "shock":    {"frames": 1, "loop": False},
        "smile":    {"frames": 1, "loop": False},
        "angry":    {"frames": 1, "loop": False},
        "sad":      {"frames": 1, "loop": False},
    }

    def aa_register_animation(name, frames=1, loop=False):
        """注册新的动画状态。创作者可添加自定义状态。"""
        aa_default_anim_states[name] = {"frames": frames, "loop": loop}
```

创作者可以在自己的脚本中扩展：
```renpy
init python:
    # 添加自定义动画状态
    aa_register_animation("dance", frames=6, loop=True)
    aa_register_animation("collapse", frames=10, loop=False)
```

characters.json 中的 sprites 字段不受限——任何 key 都会被加载，代码只在运行时检查该状态是否已注册。未注册的状态打印警告但不报错。

---

**嘟嘟声音色注册**：
```python
init python:
    aa_beep_presets = {
        "defense":    "audio/sfx/beep_defense.ogg",
        "prosecution": "audio/sfx/beep_prosecution.ogg",
        "witness":    "audio/sfx/beep_witness.ogg",
        "judge":      "audio/sfx/beep_judge.ogg",
        "narrator":   "audio/sfx/beep_narrator.ogg",
    }
    aa_default_beep = "defense"  # 默认音色

    def aa_register_beep_preset(name, path):
        """注册新的嘟嘟声预设。"""
        aa_beep_presets[name] = path
```

characters.json 中的 `beep_sfx` 字段可以是：
- 音频文件路径（直接指定）：`"audio/sfx/custom.ogg"`
- 预设名称（引用注册表）：`"preset:defense"`
- 不指定（使用 `aa_default_beep`）

```json
{
  "id": "phoenix",
  "beep_sfx": "preset:defense",
  ...
}
{
  "id": "custom_char",
  "beep_sfx": "audio/sfx/my_beep.ogg",
  ...
}
```

---

### 5.2 回调钩子系统

关键行为节点提供回调函数，创作者可以替换默认行为。

**`present` 语句的举证回调**：
```python
init python:
    # 默认行为：扣 1 格血
    def aa_on_wrong_present_default(evidence_id, testimony_index):
        aa_penalty(1)

    # 创作者可替换
    aa_on_wrong_present = aa_on_wrong_present_default
```

创作者自定义：
```python
init python:
    def my_wrong_present(evidence_id, testimony_index):
        if evidence_id == "fake_evidence":
            # 出示伪证不扣血，触发特殊对话
            renpy.say(None, "等等...这份证物有问题！")
        else:
            aa_penalty(1)

    aa_on_wrong_present = my_wrong_present
```

**可扩展的回调点**：

| 回调 | 默认行为 | 触发时机 |
|------|----------|----------|
| `aa_on_wrong_present(ev_id, idx)` | 扣 1 格血 | 举证错误时 |
| `aa_on_penalty(amount)` | 扣血 + 动画 + 音效 | 任何扣血事件 |
| `aa_on_game_over()` | 显示 Game Over 画面 | 血量归零时 |
| `aa_on_evidence_added(ev_id)` | 显示"获得证物"提示 | 获得新证物时 |
| `aa_on_hotspot_examined(hotspot_id)` | 标记已调查 | 热点调查完毕时 |
| `aa_on_testimony_complete()` | 无 | 所有证言遍历完毕时 |

所有回调都是普通 Python 函数变量，赋值即可替换，无需修改引擎代码。

---

### 5.3 JSON 自由字段

JSON 数据加载时，**未知字段不报错，原样保留**在对象的 `extra` 属性中。

```python
init python:
    class Evidence(renpy.revertable.RevertableObject):
        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.description = data["description"]
            self.icon = data["icon"]
            # ... 已知字段 ...

            # 未知字段全部存入 extra
            known_keys = {"id", "name", "description", "icon", "examine_images",
                          "updated_description", "updated_icon",
                          "combinable_with", "combine_result", "tags"}
            self.extra = renpy.revertable.RevertableDict()
            for k, v in data.items():
                if k not in known_keys:
                    self.extra[k] = v
```

这样创作者可以在 JSON 中添加自定义字段，代码中通过 `evidence.extra["custom_field"]` 读取，不需要修改引擎：

```json
{
  "id": "knife",
  "name": "凶器小刀",
  "description": "...",
  "icon": "...",
  "weight": "heavy",
  "origin": "被害者家中",
  "custom_tag": "key_evidence"
}
```

```renpy
# 创作者脚本中可以读取自定义字段
if court_record.get_evidence("knife").extra.get("weight") == "heavy":
    "这把刀很重，一般人单手很难使用。"
```

---

### 5.4 Screen 可替换机制

所有 AA Screen 提供**默认实现**，创作者可以通过 Ren'Py 原生的 `screen` 覆盖机制替换外观。

```renpy
# 引擎默认（00aa_screens.rpy）
screen aa_health_bar():
    hbox:
        xalign 0.5 ypos 10
        for i in range(5):
            if i < aa_health:
                add "images/ui/health_full.png"
            else:
                add "images/ui/health_empty.png"

# 创作者替换（game/screens.rpy 中同名定义即可覆盖）
screen aa_health_bar():
    bar:
        value aa_health range 5
        xalign 0.5 ypos 10
        left_bar "images/my_ui/bar_full.png"
        right_bar "images/my_ui/bar_empty.png"
```

**可替换的 Screen 清单**：

| Screen 名称 | 说明 | 必须保留的参数/变量 |
|-------------|------|---------------------|
| `aa_health_bar` | 血槽 | `aa_health`（当前血量）、`aa_max_health`（最大血量） |
| `aa_testimony_panel` | 证言面板 | `aa_testimony_stmts`（证言列表）、`aa_testimony_index`（当前索引） |
| `aa_evidence_panel` | 证物选择面板 | `aa_court_record.evidence`（证物字典） |
| `aa_press_present_bar` | 威慑/举证按钮栏 | `aa_can_press`、`aa_can_present`（是否可用） |
| `aa_investigation_hud` | 搜证 HUD | `aa_hotspots`（当前热点列表） |
| `aa_psyche_lock_ui` | 心灵枷锁 UI | `aa_lock_count`、`aa_lock_current` |
| `aa_mind_chess_ui` | 逻辑象棋 UI | `aa_chess_round`、`aa_chess_options` |
| `aa_revisualization_ui` | 高潮推理 UI | `aa_revi_questions`、`aa_revi_index` |

创作者只需定义同名 Screen 即可完全替换 UI 外观，引擎逻辑通过约定的变量名与 Screen 通信。

---

### 5.5 新增特殊系统的方式

如果未来需要添加全新的特殊系统（如"看穿""情绪矩阵"），只需：

1. **新建模块文件**：`renpy/common/00aa_new_system.rpy`
2. **注册新的 Statement**：通过 `aa_register_statement` 注册
3. **定义新的 Screen**：提供默认 UI
4. **注册回调（如需要）**：在 `00aa_core.rpy` 中添加新的回调变量

不需要修改任何已有模块。每个特殊系统是独立的、可选加载的。

```renpy
# 示例：未来添加"看穿"系统
# 文件：00aa_perceive.rpy

init python:
    def parse_perceive(lexer):
        # 解析 perceive 语句参数
        ...

    def execute_perceive(parsed):
        # 执行看穿逻辑
        ...

    aa_register_statement("perceive", parse_perceive, execute_perceive)

screen aa_perceive_ui():
    # 看穿系统的 UI
    ...
```

---

## 六、与 Ren'Py 原生语法的混用规则

自定义 Statement 与 Ren'Py 原生语法完全兼容，可在同一文件中自由混用：

```renpy
label ch1_trial:

    # 原生 Ren'Py
    scene bg courtroom
    with fade
    play music "audio/bgm/court.ogg"

    # 自定义 AA Statement
    begin_testimony "证言 ~~ 事件概要" by sahwit

    # 原生 Ren'Py（角色对话）
    sahwit "那天下午4点左右，我路过案发现场。"

    # 自定义 AA Statement
    stmt "那天下午4点左右，我路过案发现场。"

    # 原生条件判断
    if seen_press_0:
        sahwit "呃...其实我不太确定时间。"

    # 自定义 AA Statement
    press 0:
        sahwit "呃...其实我不太确定时间。"
        add_stmt "我不太确定是不是4点。"

    # 原生菜单
    menu:
        "继续询问":
            pass
        "跳过":
            jump ch1_trial_end

    present 0 using autopsy_report:
        objection "phoenix"
        "这份解剖记录与你的证言矛盾！"
        jump ch1_trial_success

    end_testimony
```
