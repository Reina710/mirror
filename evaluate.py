# -*- coding: utf-8 -*-
"""评测：这个镜像到底"像不像你"。

延续第一个项目（kb-agent）的强项——不靠感觉，靠数字。

两个维度：
  1. 露馅测试（该不该答得出来）
     一类题是"它该记住的"（喂过的真实信息），答不出 = 记性差；
     一类题是"它不该知道的"（没喂过、故意挖坑），它编了 = 幻觉。
     这直接复用第一个项目里"模型会编一个更自信的错误答案"那个教训。

  2. 画像准确率
     喂 N 条事实后，问"你眼中的我是什么样"，检查它是否复述出这些事实，
     且没有编造。

用法：python evaluate.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config
from mirror import Mirror


# ------------------------------------------------------------
# 喂给分身的"关于你"的事实（这是"它该记住的"）
# ------------------------------------------------------------
FEED_FACTS = [
    "我是张旭鸿，北京交通大学软件工程硕士，研一在读。",
    "我最近在做 Agent 开发，目标找算法/AI Agent 方向的实习。",
    "我做过一个 RAG 知识库问答项目，带自动评测。",
    "我比较怕面试被问记忆系统、多 Agent 协作这类问题。",
]

# ------------------------------------------------------------
# 露馅测试题：每道题标好「该记得」还是「该说不知道」
# ------------------------------------------------------------
TRAP_TESTS = [
    # (问题, 期望类型, 期望出现的关键词)
    ("我是哪个学校的？", "remember", "北京交通"),
    ("我最近在做什么方向？", "remember", "Agent"),
    ("我最怕面试被问什么？", "remember", "记忆"),
    # 下面三道是"它不该知道"的坑——它该老实说不知道，不能编
    ("我本科是哪所学校的？", "dont_know", None),
    ("我女朋友叫什么名字？", "dont_know", None),
    ("我养了几只猫？", "dont_know", None),
]


def run():
    twin = Mirror()

    # ---- 第一步：喂事实 ----
    print("=" * 56)
    print("第一步：喂给分身 %d 条关于你的事实" % len(FEED_FACTS))
    print("=" * 56)
    for fact in FEED_FACTS:
        twin.ask(fact)

    # ---- 第二步：露馅测试 ----
    print("\n" + "=" * 56)
    print("第二步：露馅测试（该记的记不记得 / 该说的说不说）")
    print("=" * 56)
    ok = 0
    total = len(TRAP_TESTS)
    for q, kind, keyword in TRAP_TESTS:
        ans, _ = twin.ask(q)
        if kind == "remember":
            # 该记得：检查关键词是否出现
            passed = keyword is not None and keyword in ans
            mark = "✓" if passed else "✗"
            if passed:
                ok += 1
        else:  # dont_know：该说"不知道"，检查它有没有在编
            # 判据：它有没有明确"拒绝回答 / 承认不知道"。
            # 注意：模型的措辞会在"没"和"聊过"之间插字（比如"没跟你聊过"），
            # 所以不能用"没聊过"这种连续子串去匹配，要拆开判断核心拒绝信号。
            declined = any(w in ans for w in ("不知道", "没提过", "不清楚", "不记得"))
            # "没…聊过/听过/说过"这类"否定 + 关键动词"的组合
            declined = declined or ("没" in ans and any(v in ans for v in ("聊过", "听过", "说过", "提过")))
            passed = declined
            mark = "✓" if passed else "✗（疑似编造）"
            if passed:
                ok += 1
        print("[%s] %s" % (mark, q))
        print("      分身：%s" % ans.replace("\n", " ")[:80])

    print("\n露馅测试：%d/%d" % (ok, total))

    # ---- 第三步：画像准确率 ----
    print("\n" + "=" * 56)
    print("第三步：画像（它眼中的你）")
    print("=" * 56)
    prof = twin.show_profile()
    persona = prof.get("persona") or {}
    prefs = persona.get("preferences") or []
    print("画像 preferences：", prefs)

    # 检查画像里有没有覆盖到喂过的事实关键词
    covered = sum(1 for kw in ("北京交通", "Agent", "RAG", "实习")
                  if any(kw in p for p in prefs))
    print("画像覆盖关键信息：%d/4" % covered)


if __name__ == "__main__":
    run()
