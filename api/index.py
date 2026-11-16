"""Vercel serverless entry point for the Cloud Address Book Flask app."""
import os
import sys

# Configure DATABASE_URL in the hosting dashboard before merging/deploying.

# 把项目根目录（app.py 所在目录）加入 import 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402,F401
