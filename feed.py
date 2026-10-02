# -*- coding: utf-8 -*-
"""喂料脚本：你把「关于你自己的真话」一句句喂给镜像。

为什么要有这个脚本：
  镜像不是天生认识你，它要靠你「喂」。
  但这个「喂」要有靶子、能看吸收，不然就是往黑洞里倒东西。

用法：
  1. 打开下面的 FEED 列表，把每一句换成你自己的原话（用你的语气说）。
  2. 跑 python feed.py
  3. 看每一轮后面打印的 [记住] xxx —— 那就是它「吸收」成了什么。
     如果你喂的是「我觉得项目经历比刷题重要」，它却存成一句无关的话，
     说明抽取漏了，这就是问题。

喂完之后：
  跑 python blind_test.py 看盲测分数，对比喂之前（4%），看涨没涨。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from mirror import Mirror

# ============================================================
# 下面就是「喂料清单」。每一条 = 你想让镜像记住的一句真话。
# 建议对着 blind_questions.py 里那 6 道题来填，这样喂完才能直接考。
# 用你的原话、你的语气写，别写得像简历。
# ============================================================
FEED = [
    "我叫张旭鸿，北京交通大学软件工程硕士，研二在读。",
    "我最近在找 Agent 方向的实习，同时在做项目。",
    "我觉得找 Agent 实习，项目经历比刷题更重要，因为现在很多公司手撕都少了。",
    "我做过一个校园 RAG 知识库问答项目，能回答新生一些校园信息，还带自动评测。",
    "我选 Agent 方向而不是纯后端，主要是学历刚好够用、Java 现在比较饱和。",
    "面试被问到不懂的问题，我一般听得懂一点就试着编一编，实在听不懂就明牌说不会。",
]

# 需要喂的条数（默认全喂；想先试几条就改成数字，比如 3）
FEED_COUNT = len(FEED)


def main():
    mirror = Mirror()

    print("=" * 56)
    print("开始喂料：一共 %d 句，喂完自动记忆。" % FEED_COUNT)
    print("每一句后面的 [记住] 就是镜像吸收成的东西。")
    print("=" * 56)

    for i, line in enumerate(FEED[:FEED_COUNT], 1):
        print("\n[%d/%d] 喂：%s" % (i, FEED_COUNT, line))
        _, remembered = mirror.ask(line)
        if not remembered:
            print("      （这一句没抽出新记忆 —— 可能被当成废话过滤了）")

    print("\n" + "=" * 56)
    print("喂完。它现在记住的关于你的一切：")
    print("=" * 56)
    for m in mirror.what_you_remember():
        print("  [%s] %s" % (m["kind"], m["content"]))

    print("\n下一步：跑 python blind_test.py，看它这次答得像不像你。")


if __name__ == "__main__":
    main()
