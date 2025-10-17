"""
setup.py for py2app

Usage:
    python3 setup.py py2app
"""

from setuptools import setup

APP = ["main.py"]
APP_NAME = "PackyCode"
# 将仓库中的 PNG 图标打包到 .app 的 Resources 根目录，运行时使用 RESOURCEPATH/icon.png 加载
DATA_FILES = [
    ("", ["../packycode-cost/assets/icon.png"]),
]
OPTIONS = {
    "argv_emulation": False,
    # Finder 图标（建议 .icns）。当前使用 PNG，如需自定义请替换为 .icns。
    "iconfile": "../packycode-cost/assets/icon.png",
    "plist": {
        "LSUIElement": True,  # 仅状态栏图标，不显示 Dock 图标
    },
    "packages": ["rumps", "requests"],
}

setup(
    app=APP,
    name=APP_NAME,
    author="packy",
    version="0.1",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    install_requires=["rumps", "requests"],
)
