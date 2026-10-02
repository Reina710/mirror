# -*- coding: utf-8 -*-
"""镜像（Mirror）：一个会聊天、边聊边记住"你"的 Agent。

站在 memory-hub（通用记忆引擎）的肩膀上，补上它没有的"最后一公里"：
  1. 会聊天 —— memory-hub 只提供 write/recall，不会对话，这里接 DeepSeek 让它说话。
  2. 有具体对象 —— memory-hub 的记忆是给任意 subject 用的，这里固定成"你"。
  3. 边聊边记 —— 每轮结束，自动从对话里抽取"关于你"的事实入库。

流程（每轮对话）：
  轮前：recall 召回相关记忆 + profile 读画像 → 拼进 system，让回答"懂你"。
  轮中：调 DeepSeek 生成回答。
  轮末：extract_items 抽取值得记的事实 → write 入库（自动去重/冲突消解）。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from memory_hub import MemoryHub, deps, backend_local
from memory_hub.extract import extract_items


class Mirror:
    """镜像分身。初始化时接好 DeepSeek，绑定记忆库，设定要复制的对象。"""

    def __init__(self, subject=None):
        self.subject = subject or config.SUBJECT
        os.environ.setdefault("DEEPSEEK_API_KEY", config.DEEPSEEK_API_KEY)
        # 接 DeepSeek（memory-hub 自带的适配器，纯 urllib 零依赖）
        backend_local.install()
        # 建记忆库
        self.hub = MemoryHub(config.DB_PATH)
        # 短期记忆：最近几轮对话，让镜像"记得刚才聊到哪"（否则每句都像失忆）
        self.history = []

    # ------------------------------------------------------------
    # 轮前：召回记忆 + 画像，拼进提示词
    # ------------------------------------------------------------
    def _build_system(self, question):
        hits = self.hub.recall(question, subject=self.subject, k=config.RECALL_K)
        prof = self.hub.profile(self.subject)

        mem_block = ""
        if hits:
            mem_block = "【关于这个人的记忆】\n" + "\n".join(
                "- " + h["content"] for h in hits) + "\n"

        prof_block = ""
        prefs = (prof.get("persona") or {}).get("preferences") or []
        if prefs:
            prof_block = "【这个人目前的画像】" + "；".join(prefs[:10]) + "\n"

        system = (
            "你是 %s 的数字分身，正在模仿他本人说话。\n"
            "你就是他，不是\"一个了解他的助手\"。记住你的边界：\n"
            "1. 涉及\"他这个人\"的具体信息，只依据下面【记忆】和【画像】，用第一人称（我）。\n"
            "2. 对方在问【关于我的具体信息】或【具体知识】而记忆里没有时，不许编，\n"
            "   直接说\"这个我还没聊过\"。\n"
            "3. 但打招呼、玩笑、玩梗、互损、起哄（比如对方自称你爹、骂骂咧咧）\n"
            "   是社交，不是信息请求——正常接、正常损回去，不需要记忆依据，\n"
            "   绝不许答\"这个我还没聊过\"。\n"
            "4. 不要主动展示、科普、整理任何\"知识\"。对具体的人/作品/技术做评价或\n"
            "   断言前先想：这事他跟你聊过吗？没有就别装懂。\n"
            "5. 说话要像他：短、直接、口语化，不要\"首先/其次/总结一下\"，不要主动帮忙、\n"
            "   不要显得比本人更懂、更会来事。\n" % config.MIRROR_OF
        )
        return system + "\n" + mem_block + prof_block

    # ------------------------------------------------------------
    # 问一个问题，拿一个回答（同时完成"边聊边记"）
    # ------------------------------------------------------------
    def ask(self, question):
        system = self._build_system(question)
        answer = self._chat(system, question, self.history)

        # 短期记忆：把这一轮的"你问 + 它答"记进历史，下一轮它就知道刚才聊到哪
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})
        # 只保留最近几轮，避免历史越滚越长、越滚越贵
        if len(self.history) > config.HISTORY_K * 2:
            self.history = self.history[-(config.HISTORY_K * 2):]

        # 轮末：抽取值得记的事实，入库（自动去重、冲突消解）
        existing = [m["content"] for m in
                    self.hub.list_memories(subject=self.subject, limit=50)]
        items = extract_items(question, answer, existing=existing)
        remembered = []
        if items:
            receipt = self.hub.write(items, actor="mirror", subject=self.subject)
            remembered = [a["content"] for a in receipt["added"]]
            for a in receipt["added"]:
                print("  [记住] %s: %s" % (a["kind"], a["content"]))
            for mid in receipt["invalidated"]:
                print("  [改口] 旧记忆已失效 %s" % mid)

        return answer, remembered

    # ------------------------------------------------------------
    # 底层：调 DeepSeek 对话
    # ------------------------------------------------------------
    @staticmethod
    def _chat(system, user, history=None):
        # memory-hub 的 llm_chat 是 json_mode 的，不适合对话；
        # 这里直接用它的后端能力，单独写一个非 json 的对话调用。
        import json
        import urllib.request

        # 拼消息：system + 最近几轮历史 + 当前这句。
        # 有了历史，镜像才"记得刚才聊到哪"，而不是每句都像第一次见你。
        messages = [{"role": "system", "content": system}]
        for msg in (history or [])[-(config.HISTORY_K * 2):]:
            messages.append(msg)
        messages.append({"role": "user", "content": user})

        body = {
            "model": config.CHAT_MODEL,
            "messages": messages,
            "temperature": 0.7,
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
        return data["choices"][0]["message"]["content"]

    # ------------------------------------------------------------
    # 查看：它现在记住了"你"什么
    # ------------------------------------------------------------
    def what_you_remember(self):
        memories = self.hub.list_memories(subject=self.subject, limit=100)
        return memories

    def show_profile(self):
        return self.hub.profile(self.subject)


if __name__ == "__main__":
    # 直接运行：进交互，跟"自己"聊天
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    twin = Mirror()
    print("=" * 56)
    print("镜像分身启动：我是 %s 的镜像，越聊越像他。" % config.MIRROR_OF)
    print("正常聊天即可，每轮结束它会自动记住关于你的事。")
    print("输入 q 退出；输入 /记忆 看它记住了什么。")
    print("=" * 56)

    while True:
        try:
            user = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user.lower() in ("q", "quit", "exit"):
            break
        if user == "/记忆":
            mems = twin.what_you_remember()
            print("它现在记住了这些：")
            for m in mems:
                print("  [%s] %s" % (m["kind"], m["content"]))
            continue
        if user == "/画像":
            prof = twin.show_profile()
            print("它眼中的你：", prof)
            continue

        answer, _ = twin.ask(user)
        print("分身：" + answer)

    print("\n再见。它一共记住了 %d 条关于你的事。" %
          len(twin.what_you_remember()))
