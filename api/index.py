"""Vercel serverless entry point for the Cloud Address Book Flask app."""
import os
import sys

# Vercel 的文件系统只读，SQLite 必须放到 /tmp
os.environ.setdefault("DB_PATH", "/tmp/contacts.db")
# 空库时自动灌入演示数据，方便评审直接体验
os.environ.setdefault("SEED_DEMO", "1")

# 把项目根目录（app.py 所在目录）加入 import 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402,F401
