"""Verify the configured chat and embedding models without displaying the API key."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    key = os.getenv("LLM_API_KEY", "")
    if not key or "在这里粘贴" in key:
        print("请先在项目根目录的 .env 文件中填写 LLM_API_KEY。")
        return 1

    from config.model_provider import create_chat_model, create_embedding_model

    try:
        reply = create_chat_model(temperature=0).invoke("请只回复：连接成功")
        print(f"聊天模型连接成功，回复：{reply.content}")
    except Exception as exc:
        print(f"聊天模型连接失败：{type(exc).__name__}。请检查 Key、模型名和账户额度。")
        return 1

    try:
        vector = create_embedding_model().embed_query("高中物理力学")
        if not vector:
            raise ValueError("empty vector")
        print(f"向量模型连接成功，向量长度：{len(vector)}")
    except Exception as exc:
        print(f"向量模型连接失败：{type(exc).__name__}。请检查 Key、模型名和账户额度。")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
