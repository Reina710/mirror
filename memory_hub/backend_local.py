# -*- coding: utf-8 -*-
"""本地真后端适配器：bge-small-zh-v1.5（fastembed 本地推理）+ DeepSeek API。

用法（独立部署时在宿主入口处）：
    from memory_hub import deps, backend_local
    backend_local.install()          # 一行注入全部后端

说明：
- embedding 模型与 DESIGN-MEMORY §三阈值校准所用一致（512 维归一化 bge），
  阈值（召回 0.40 / 冲突候选 0.60 / 判重 0.85）无需重标。
- LLM 走 DeepSeek /chat/completions（纯 urllib，零第三方依赖）。
- 下载模型若 HF 直连超时，设 HF_ENDPOINT=https://hf-mirror.com。
- 所有调用失败返回 None/False（接缝纪律：绝不抛给宿主）。
"""
import json
import os
import re
import threading
import urllib.request

_DS_URL = "https://api.deepseek.com/chat/completions"
_LOCK = threading.Lock()
_embedder = None


def _get_embedder():
    """改接 DashScope 云端 embedding（text-embedding-v3），复用 kb-agent 的密钥。

    原来这里是本地 fastembed（bge-small-zh-v1.5），要下载模型且首次很慢。
    换成云端后：不用下载、快，但每次调用走网络。
    """
    global _embedder
    with _LOCK:
        if _embedder is None:
            from openai import OpenAI
            key = os.environ.get("DASHSCOPE_KEY")
            base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            _embedder = OpenAI(api_key=key, base_url=base)
        return _embedder


def embed(texts):
    """批量向量化。text-embedding-v3 一次最多 10 段，这里分 10 段一批循环。"""
    try:
        client = _get_embedder()
        out = []
        for i in range(0, len(texts), 10):
            chunk = texts[i:i + 10]
            resp = client.embeddings.create(
                model="text-embedding-v3", input=chunk, dimensions=512)
            out.extend(item.embedding for item in resp.data)
        return out
    except Exception:
        return None


def embed_one(text):
    try:
        client = _get_embedder()
        resp = client.embeddings.create(
            model="text-embedding-v3", input=[str(text)], dimensions=512)
        return resp.data[0].embedding
    except Exception:
        return None


def embed_available():
    return bool(os.environ.get("DASHSCOPE_KEY"))


def llm_chat(messages, temperature=0.1, json_mode=True, max_tokens=1024):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        return None
    body = {"model": "deepseek-chat", "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        req = urllib.request.Request(
            _DS_URL, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def llm_available():
    return bool(os.environ.get("DEEPSEEK_API_KEY"))


def parse_json(text):
    """尽力解析：剥 markdown 围栏 → 截取首个 {...} 或 [...]。"""
    if not text:
        return None
    t = re.sub(r"```(?:json)?|```", "", text).strip()
    for cand in (t, t[t.index("{"):t.rindex("}") + 1] if "{" in t and "}" in t else None,
                 t[t.index("["):t.rindex("]") + 1] if "[" in t and "]" in t else None):
        if not cand:
            continue
        try:
            return json.loads(cand)
        except Exception:
            continue
    return None


def install():
    """把本模块的实现注入 deps 接缝（覆盖先前绑定）。"""
    from . import deps
    deps.configure(llm_chat=llm_chat, llm_available=llm_available,
                   parse_json=parse_json, embed=embed, embed_one=embed_one,
                   embed_available=embed_available)
