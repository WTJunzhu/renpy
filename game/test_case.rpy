# ============================================================
# Ace Attorney Ren'Py — 示例案件测试脚本
# 最小化验证所有已实现的功能，无需剧情连贯性。
# ============================================================

# ─── 加载数据 ──────────────────────────────────────────────────

init python:
    aa_load_evidence("aa/evidence.json")
    aa_load_profiles("aa/characters.json")
    aa_load_locations("aa/locations.json")

# ─── 定义角色（使用 AA 嘟嘟声系统）──────────────────────────────

define phoenix = aa_make_character("phoenix")
define payne = aa_make_character("payne")
define sahwit = aa_make_character("sahwit")
define larry = aa_make_character("larry")
define judge_aa = aa_make_character("judge")

# ─── 开始 ─────────────────────────────────────────────────────

label start:

    scene bg courtroom

    # 测试旁白嘟嘟声
    "这是逆转裁判 Ren'Py 制作引擎的功能测试。"
    "接下来将依次测试法庭询问和搜证系统。"

    jump test_courtroom


# ============================================================
# 第一部分：法庭询问测试
# 覆盖功能：证言展示、威慑、举证、扣血、血槽
# ============================================================

label test_courtroom:

    scene bg courtroom

    judge_aa "现在开始对证人山崎正夫的证言进行询问。"

    # 测试血槽显示
    show screen aa_health_bar

    # 给玩家初始证物
    get_evidence autopsy_report
    get_evidence thinker

    # 测试 begin_testimony + stmt
    begin_testimony "事件目击证言" by sahwit:

        stmt "那天晚上9点左右，我路过被害人公寓楼下。"
        stmt "我听到楼上传来争吵声。"
        stmt "于是我上楼查看，发现门是开着的。"
        stmt "我走进去，看到一个男人站在房间里。"
        stmt "我确信那个人就是被告！"

        # 测试 press — 威慑第3条证言（门开着）
        press 2:
            sahwit "门是开着的……所以我就直接走进去了。"
            phoenix "（门开着？这有点可疑……）"

        # 测试 present — 举证第5条证言（确认被告）
        present 5 using thinker:
            phoenix "等一下！你说你看到了被告……"
            phoenix "但你有没有注意到这个雕像？"
            sahwit "那、那是……"
            penalty 2

        # 测试 present 正确 — 用尸检报告反驳时间
        present 1 using autopsy_report:
            phoenix "你说是9点左右……但尸检报告显示死亡时间更早！"
            sahwit "这……这不可能……！"

    # 证言结束后
    judge_aa "证人的证词出现重大矛盾！"

    end_testimony

    hide screen aa_health_bar

    jump test_investigation


# ============================================================
# 第二部分：搜证测试
# 覆盖功能：hotspot、examine、talk、topic、move、get_evidence
# ============================================================

label test_investigation:

    scene bg apartment

    "进入搜证阶段。使用 WASD 移动，E 键交互，ESC 退出。"

    # 测试 begin_investigation (使用 investigate 语句)
    investigate "辛迪·斯通的公寓" at crime_scene:

        # 测试 hotspot 1 — 雕像底座
        hotspot "雕像底座" at (800, 400) size (150, 150) radius 120:
            examine statue_spot:
                "雕像底座上有明显的血迹反应。"
                "看起来这里曾经放置过什么东西。"
                get_evidence floor_plan

        # 测试 hotspot 2 — 窗户
        hotspot "窗户" at (1200, 200) size (200, 300) radius 130:
            examine window:
                "窗户面向大街。从这里可以看到楼下的情况。"
                "窗台上有一些灰尘痕迹。"

        # 测试 hotspot 3 — 书架
        hotspot "书架" at (200, 300) size (180, 400) radius 120:
            examine bookshelf:
                "书架上摆满了各种书籍。"
                "其中一本关于美术的书引起了注意。"
                get_evidence newspaper

    end_investigate

    jump test_talk


# ============================================================
# 第三部分：NPC 对话测试
# 覆盖功能：talk、topic、present（搜证版）
# ============================================================

label test_talk:

    scene bg detention_center

    "前往拘留所与矢张政志对话。"

    # 测试 talk 语句
    talk larry:

        # 测试 topic — 闲聊话题
        topic "事件当天":
            larry "那天晚上我确实在辛迪公寓附近……"
            larry "但我没有进去！我发誓！"
            phoenix "（矢张看起来很紧张……）"

        topic "与被害人的关系":
            larry "辛迪是我的前女友……"
            larry "我们上个月分手了。"
            phoenix "（分手……这给了他动机？）"

        topic "关于雕像":
            larry "那个雕像？辛迪很喜欢它。"
            larry "是一个叫山崎的人送的。"
            phoenix "山崎……等等，那不就是证人吗！"

        # 测试 present（搜证版）— 向 NPC 出示证物
        present thinker:
            larry "这个雕像！就是辛迪房间里的那个！"
            larry "我之前见过它，就在书架旁边。"

        present autopsy_report:
            larry "死亡时间是9点到10点……"
            larry "那个时候我确实在附近……但我没进去！"

    "对话结束。"

    jump test_end


# ============================================================
# 第四部分：结束测试
# 覆盖功能：set_flag、game over 测试
# ============================================================

label test_end:

    set_flag test_complete to true

    judge_aa "测试项目全部完成。"

    # 测试 Game Over 画面（可选）
    # penalty 100

    "所有功能测试完毕。感谢测试！"

    return
