# -*- coding: utf-8 -*-
"""镜像项目的配置：所有参数集中在这一个文件里，改这里全项目生效。"""

import os

# ------------------------------------------------------------
# 密钥：从环境变量读。优先 DEEPSEEK_API_KEY，兼容 kb-agent 的 DEEPSEEK_KEY。
# 建议运行时先 export，或在这里用 .env 加载（见 _load_env）。
# ------------------------------------------------------------
def _load_env():
    """从项目根的 .env 读密钥（不引入第三方库）。"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_file):
        return
    for line in open(env_file, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

# DeepSeek 密钥（memory-hub 的适配器认 DEEPSEEK_API_KEY 这个名字）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_KEY", "")

# ------------------------------------------------------------
# 身份：这个镜像要复制的对象是谁
# ------------------------------------------------------------
SUBJECT = "zxh"            # 记忆作用域里的"你"的标识（对应 memory-hub 的 subject）
MIRROR_OF = "张旭鸿"        # 镜像扮演/复制的对象姓名

# ------------------------------------------------------------
# 模型与记忆参数
# ------------------------------------------------------------
CHAT_MODEL = "deepseek-chat"    # 对话 + 抽取 + 冲突消解都用它

# 数据库文件（放项目根下，方便查看；也可进 runtime/）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twin.db")

# 回答时召回多少条相关记忆注入
RECALL_K = 4

# 短期记忆：每轮对话带进多少轮"最近历史"（让镜像记得刚才聊到哪）
# 设太大上下文会变长、变贵；设太小又会"健忘"。6 轮是个折中。
HISTORY_K = 6
