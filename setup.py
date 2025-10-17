"""
setup.py for py2app

Usage:
    python3 setup.py py2app
"""

from setuptools import setup
import os

APP = ["main.py"]
APP_NAME = "PackyCode"

# 本仓库内置图标路径（请将 PNG 放置在 packycode/assets/icon.png）
BASE_DIR = os.path.dirname(__file__)
ICON_SRC = os.path.join(BASE_DIR, "assets", "icon.png")

# 仅当图标存在时才打包资源并设置 iconfile，避免外部依赖
DATA_FILES = []
if os.path.exists(ICON_SRC):
    # 将 PNG 打包到 .app 的 Resources 根目录，运行时使用 RESOURCEPATH/icon.png 加载
    DATA_FILES.append(("", [ICON_SRC]))

OPTIONS = {
    "argv_emulation": False,
    # Finder 图标（建议 .icns）。当前使用 PNG，如需自定义请替换为 .icns。
    # 若 icon.png 不存在，则不设置 iconfile，构建继续进行。
    **({"iconfile": ICON_SRC} if os.path.exists(ICON_SRC) else {}),
    "plist": {
        "LSUIElement": True,  # 仅状态栏图标，不显示 Dock 图标
    },
    "packages": ["rumps", "requests"],
    # 避免将非运行时依赖（pip/wheel/setuptools等）打入包，解决偶发 File exists: wheel-*.dist-info 冲突
    "excludes": [
        "pip",
        "wheel",
        "setuptools",
        "pkg_resources",
        "distutils",
    ],
    # 明确包含 requests 的依赖子模块，避免某些环境下被遗漏
    "includes": [
        "idna",
        "charset_normalizer",
        "urllib3",
    ],
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
