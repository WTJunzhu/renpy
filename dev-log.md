# GyakutenMaker 开发日志

## 2026-05-22 首次开发

### 项目初始化

- 创建 Monorepo 结构（pnpm workspaces）
- `packages/core` — 引擎核心（TypeScript）
- `packages/player` — 播放器 UI（React + Vite + TypeScript）

### 核心引擎 (packages/core)

**数据格式定义 (`types.ts`)：**
- `Scene` — 场景顶级结构（版本、元信息、角色、证物、节点）
- `DialogueNode` — 对话节点（支持富文本片段 TextSegment）
- `TitleNode` — 标题卡片节点（"证言开始"、"询问开始"）
- `TestimonyDisplayNode` — 证言展示节点（证人念证言，只读）
- `TestimonyNode` — 询问节点（可交互，威慑/举证）
- `InvestigationNode` — 搜证节点（支持 hybrid/investigations/classic 模式）
- `InvestigationHotspot` — 可调查热点（位置、感应半径、证物奖励）
- `InvestigationNPC` — NPC（问候对话、聊天话题、出示证物）
- `ChoiceNode` — 选择分支节点
- `PsycheLockNode` — 心锁节点（预留）

**引擎 (`engine.ts`)：**
- 状态机管理（节点跳转、血量、证物）
- 事件系统（nodeChanged, healthChanged, evidenceAdded 等）
- 证言系统（威慑、举证、扣血、完成判定）
- 搜证系统（玩家移动、热点感应、NPC 交互状态机）
- NPC 多级交互（问候 → 菜单 → 聊天/出示证物 → 返回）
- 标题卡片自动跳转
- 证言展示逐条播放
- 动态证物发现（热点调查时自动添加到证物列表）

**加载器 (`loader.ts`)：**
- 从 JSON 字符串/对象/URL 加载场景
- 基础校验（版本、入口节点、节点引用）

### 播放器 UI (packages/player)

**组件：**
- `GameScreen` — 主场景（全局键盘快捷键、节点类型路由）
- `DialogueBox` — 对话框（逐字显示、底部快捷键提示）
- `TitleCard` — 标题卡片（金色大字、缩放动画）
- `TestimonyDisplay` — 证言展示（"证言中"标签、逐条播放、进度点）
- `TestimonyPanel` — 询问面板（绿色证言、左右切换、威慑/举证按钮）
- `EvidencePanel` — 证物选择面板
- `ChoicePanel` — 选择分支面板
- `HealthBar` — 血槽
- `InvestigationScene` — 搜证主场景
- `PlayerCharacter` — 可操控角色（SVG 占位符）
- `Hotspot` — 可调查热点（靠近高亮、脉冲动画）
- `InvestigationDialogue` — 搜证对话
- `NPCDialogue` — NPC 交互（菜单、聊天话题列表、出示证物选择）

**快捷键：**
- `C` — 打开/关闭证物面板
- `Z` — 威慑（询问环节）
- `X` — 举证（询问环节）
- `空格/回车` — 推进对话
- `ESC/Q` — 返回/关闭
- `←/→` — 切换证言（询问环节）
- `WASD/方向键` — 移动角色（搜证环节）
- `E/空格` — 互动（搜证环节）

### 示例场景

**demo-investigation.json — 完整流程演示：**
1. 搜证环节：案发现场调查
   - 4 个可调查热点（破碎的花瓶、书桌、窗户、信箱）
   - 1 个 NPC（糸锯圭介）— 3 个聊天话题 + 3 种证物出示反应
   - 收集 3 件证物后可前往法庭
2. 法庭环节：
   - 大标题"证言开始" → 证人念 4 条证言
   - 大标题"询问开始" → 询问环节（威慑/举证）
   - 对第 3 条证言出示"快递员的证词"即可通关

### 待办事项

- [ ] 音效系统（嘟嘟声、异议语音、BGM）
- [ ] 角色动画（拍桌、指向、崩溃）
- [ ] 心锁系统
- [ ] 看穿系统
- [ ] 可视化编辑器
- [ ] 场景背景图片
- [ ] 角色立绘
- [ ] 存档/读档
- [ ] 多章节支持
- [ ] 导出/分享功能
