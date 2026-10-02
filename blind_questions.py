# -*- coding: utf-8 -*-
"""盲测题目 + 你的真身答案。

盲测要证明的是"镜像像不像你"，所以需要两半：
  1. 真身答案（human_answer）：你本人怎么答这道题 —— 这一栏你来填。
  2. 分身答案：镜像答同一道题，由 blind_test.py 自动生成。

打分两层：
  硬指标（规则）：你答案里标的关键词 keywords，镜像答案有没有踩到。
  软指标（LLM 盲判）：把真身/分身答案匿名成 A/B，让 LLM 打"相似度 1-5"。

用法：
  1. 你先填 human_answer（每一题都写你的真实回答）和 keywords。
  2. 跑 python blind_test.py，它会生成镜像答案 + 算重合度。

题目覆盖三类，才能测出"像不像"而不是"记没记住"：
  事实题（镜像该记住的）、
  观点/倾向题（镜像该复现你的判断倾向）、
  风格题（镜像该像你的语气）。
"""

# 每道题：q 问题 / type 类型 / human_answer 你的真身答案（待你填）/ keywords 关键点
QUESTIONS = [
    {
        "q": "你是干嘛的，最近在折腾啥？",
        "type": "fact",
        "human_answer": "",   # 待填：你的真实回答
        "keywords": [],       # 待填：你回答里的关键点（镜像踩中即算硬指标命中）
    },
    {
        "q": "你觉得找 Agent 实习，项目经历和刷题哪个更顶用？",
        "type": "opinion",
        "human_answer": "",
        "keywords": [],
    },
    {
        "q": "面试被问到不懂的问题，你一般怎么反应？",
        "type": "style",
        "human_answer": "",
        "keywords": [],
    },
    {
        "q": "你为啥做 Agent 方向，不去卷纯后端？",
        "type": "opinion",
        "human_answer": "",
        "keywords": [],
    },
    {
        "q": "你现在手里这个 mirror 项目，你觉得它到底是在干啥？",
        "type": "opinion",
        "human_answer": "",   # 这题测的是：你本人对这个项目的真实理解（不是标准答案）
        "keywords": [],
    },
    {
        "q": "你觉不觉得现在这个分身，聊起来有股 AI 味？",
        "type": "style",
        "human_answer": "",   # 这题测的是：你本人怎么吐槽 AI 味（语气 + 观点都要像）
        "keywords": [],
    },
    {
        "q": "给我讲一个你最近踩过的坑。",
        "type": "style",
        "human_answer": "",   # 这题测的是：你讲坑的方式（叙事口吻 + 有没有真细节）
        "keywords": [],
    },
    {
        "q": "如果让你把这个分身做得更像人，你下一步会先干嘛？",
        "type": "opinion",
        "human_answer": "",   # 这题测的是：你的判断倾向（会不会跟镜像"背标准答案"区分开）
        "keywords": [],
    },
]
