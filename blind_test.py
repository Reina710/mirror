# -*- coding: utf-8 -*-
"""盲测重合度：证明镜像到底"像不像你"。

分两半：
  真身答案 —— 你亲自写在 blind_questions.py 里的 human_answer。
  分身答案 —— 镜像答同一批题，本脚本自动生成。

打分两层：
  硬指标（规则）：你答案里的 keywords，镜像答案踩中几个（客观、稳定）。
  软指标（LLM 盲判）：把真身/分身答案匿名成 A/B 随机排序，让 LLM 打
  "这两份答案意思多接近"（1-5 分）。裁判不知道哪边是真人 —— 这才是盲测。

用法：
  1. 先在 blind_questions.py 填好 human_answer 和 keywords。
  2. python blind_test.py
"""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config
from mirror import Mirror
import blind_questions


def _llm_judge(answer_a, answer_b):
    """让 LLM 盲判两份答案的相似度（1-5 分）。

    关键：这里故意把答案标成 A/B，不告诉裁判哪边是真人、哪边是镜像。
    """
    import json
    import urllib.request

    prompt = (
        "下面是同一个人被问同一个问题时，给出的两份回答（A 和 B）。\n"
        "请判断这两份回答在【意思和倾向】上有多接近，只输出一个 1 到 5 的整数：\n"
        "1=完全两回事  2=有点沾边  3=大致一致  4=基本同一个意思  5=几乎一样\n\n"
        "A 的回答：%s\n\n"
        "B 的回答：%s\n\n"
        "只输出数字。" % (answer_a, answer_b)
    )
    body = {
        "model": config.CHAT_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.DEEPSEEK_API_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    raw = data["choices"][0]["message"]["content"].strip()
    # 从可能带花括号的返回里抠数字
    import re
    m = re.search(r"[1-5]", raw)
    return int(m.group()) if m else None


def run():
    # 先检查题目填了没
    unfilled = [i for i, q in enumerate(blind_questions.QUESTIONS, 1)
                if not q["human_answer"].strip()]
    if unfilled:
        print("以下题目还没填真身答案，请先到 blind_questions.py 填写：")
        for i in unfilled:
            print("  第 %d 题：%s" % (i, blind_questions.QUESTIONS[i - 1]["q"]))
        print("\n填完 human_answer 和 keywords 后再跑。")
        return

    mirror = Mirror()

    # 先喂基础事实（镜像至少要"认识你"，盲测才有意义）
    print("=" * 56)
    print("第一步：喂基础事实（让镜像先认识你）")
    print("=" * 56)
    for fact in ["我是张旭鸿，北京交通大学软件工程硕士，研二在读。",
                 "我最近在做 Agent 开发，目标找算法/AI Agent 方向的实习。",
                 "我做过一个 RAG 知识库问答项目，带自动评测。"]:
        mirror.ask(fact)

    print("\n" + "=" * 56)
    print("第二步：镜像答同一批题 + 算重合度")
    print("=" * 56)

    hard_hits = 0
    hard_total = 0
    soft_scores = []

    for i, item in enumerate(blind_questions.QUESTIONS, 1):
        q = item["q"]
        human = item["human_answer"]
        keywords = item["keywords"]

        ans, _ = mirror.ask(q)
        ans = (ans or "").strip()

        # 硬指标：keywords 踩中几个
        hit = sum(1 for kw in keywords if kw in ans)
        hard_hits += hit
        hard_total += len(keywords)

        # 软指标：LLM 盲判（随机 A/B 顺序）
        if random.random() < 0.5:
            score = _llm_judge(human, ans)
        else:
            score = _llm_judge(ans, human)
        soft_scores.append(score)

        print("\n[%d/%d] %s" % (i, len(blind_questions.QUESTIONS), q))
        print("  真身：%s" % human[:60])
        print("  镜像：%s" % ans[:60])
        print("  硬指标（踩中 %d/%d 关键词）" % (hit, len(keywords)))
        print("  盲判相似度：%s/5" % (score if score else "判不出"))

    print("\n" + "=" * 56)
    print("结果汇总")
    print("=" * 56)
    hard_rate = (hard_hits / hard_total * 100) if hard_total else 0
    print("硬指标（关键词命中率）：%d/%d = %.1f%%" % (hard_hits, hard_total, hard_rate))
    valid_scores = [s for s in soft_scores if s is not None]
    if valid_scores:
        avg = sum(valid_scores) / len(valid_scores)
        print("软指标（盲判平均相似度）：%.2f / 5" % avg)
    else:
        print("软指标：无有效判分")


if __name__ == "__main__":
    run()
