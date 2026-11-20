"""Small local HTTP smoke check; prints statuses without exposing credentials."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app import app


def main() -> int:
    with TestClient(app) as client:
        for path in ("/", "/api/knowledge/", "/api/teachers/"):
            response = client.get(path)
            print(f"GET {path}: {response.status_code}")
            if response.status_code != 200:
                print(response.text[:400])
                return 1

        response = client.post("/chat/stream", json={"message": "高中物理辅导多少钱？"}, timeout=120)
        print(f"POST /chat/stream: {response.status_code}")
        print("回复摘录：" + response.text[-400:])
        if response.status_code != 200 or not response.text.strip():
            return 1
        if "出现了错误" in response.text or "Error code:" in response.text or "[ERROR]" in response.text:
            print("聊天接口返回了错误内容，不能算作咨询成功。")
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
