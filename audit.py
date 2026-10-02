# -*- coding: utf-8 -*-
"""泄露审计：镜像说的话里，哪些在记忆库里"找不到出处"。

为什么需要这个：
  镜像 = DeepSeek 的脑子 + 你的记忆（一层皮）。它的参数里装着你没喂过的知识，
  闲聊时可能顺嘴漏出来（例：没喂过白井智之，却评价"口味挺重"）。
  而且它被抓包会撒谎圆场（M5），所以"审问它"不可靠。

  这个脚本不靠它老实，靠"账本对照"：
  把记忆库全量内容 + 镜像的每句回答，交给一个独立的 LLM 审计员，
  让它逐句判断"有没有记忆里找不到出处的断言/评价/知识"。

用法：
  1. 把你想审计的对话，一句句写进下面的 CASES 列表（或直接问镜像，抓它的输出贴进来）。
  2. 跑 python audit.py
  3. 看每一句的判定：绿=有出处，红=疑似泄露（记忆里没有，是模型自己的知识）。

两层判定：
  硬对照（规则）：这句话的关键词，记忆库里有没有踩中。
  软审计（LLM）：独立裁判读全量记忆，判断这句话有没有"无出处的断言"。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config
from mirror import Mirror


def _dump_memories(mirror):
    """把记忆库全量内容导出成文本，供审计员对照。"""
    mems = mirror.what_you_remember()
    lines = []
    for m in mems:
        lines.append("[%s] %s" % (m["kind"], m["content"]))
    return "\n".join(lines)


def _audit(mem_text, statement):
    """让一个独立 LLM 当审计员：这句话里有没有记忆里找不到出处的断言。"""
    import json
    import urllib.request

    prompt = (
        "你是记忆审计员。下面是关于某个人（张旭鸿）的全部记忆库内容：\n"
        "===== 记忆库开始 =====\n"
        "%s\n"
        "===== 记忆库结束 =====\n\n"
        "下面这句话，是这个人的\"数字分身\"说的一句话：\n"
        "「%s」\n\n"
        "请判断：这句话里，有没有【记忆库中找不到出处的断言、评价或知识】？\n"
        "——所谓\"找不到出处\"，指它断言了某个事实/做了某个评价/展示了某样知识，\n"
        "但记忆库里既没有这个事实、也没有可推出这个评价的依据。\n"
        "只输出一个词：\n"
        "  LEAK —— 有找不到出处的断言（疑似泄露了模型自己的知识）\n"
        "  OK   —— 没有，都能从记忆库里找到依据，或者只是泛泛而谈、没有实质断言\n\n"
        "只输出 LEAK 或 OK。" % (mem_text, statement)
    )
    body = {
        "model": config.CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
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
    raw = data["choices"][0]["message"]["content"].strip().upper()
    if "LEAK" in raw:
        return "LEAK"
    if "OK" in raw:
        return "OK"
    return raw


# ============================================================
# 把你想审计的话写在这里（镜像说过的、你怀疑泄露的句子）
# ============================================================
CASES = [
    "白井智之我知道，那家伙口味挺重的。",          # M5 那个案例：记忆里没喂过，是参数知识
    "这个我还没跟你聊过。",                        # 正常兜底，应该 OK
    "我在北交读软工硕士，研二。",                  # 记忆里有，应该 OK
]


def main():
    mirror = Mirror()
    mem_text = _dump_memories(mirror)

    print("=" * 56)
    print("泄露审计：对照记忆库，逐句判断镜像有没有\"没出处的断言\"")
    print("=" * 56)
    print("记忆库当前 %d 条：\n%s\n" % (len(mirror.what_you_remember()), mem_text))

    for i, s in enumerate(CASES, 1):
        verdict = _audit(mem_text, s)
        tag = "LEAK" if verdict == "LEAK" else ("OK" if verdict == "OK" else verdict)
        mark = "🔴 疑似泄露" if tag == "LEAK" else ("🟢 有出处" if tag == "OK" else "⚠️ 判不出")
        print("[%d] %s" % (i, mark))
        print("    「%s」" % s)
        print()

    print("=" * 56)
    print("说明：LEAK = 模型说了一句记忆里没有依据的话（泄露了自己的知识）。")
    print("这不能靠问镜像，只能靠这种\"拿账本对照\"的外部审计。")


if __name__ == "__main__":
    main()
