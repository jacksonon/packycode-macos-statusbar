# PackyCode 状态栏应用（macOS）

一个用 Python 编写的 macOS 状态栏应用，用于展示 PackyCode 额度/预算使用情况。

- 参考实现：`GPO/`（macOS 状态栏应用框架，rumps）
- 数据来源：`packycode-cost/`（三种账号模式与 API 端点约定）

## 功能
- 状态栏实时展示：
  - 公交车（shared）：显示账户余额 `$12.34`
  - 滴滴车（private）/ Codex 公交车（codex_shared）：显示每日/每月消费与预算进度 `D 1.2/20 | M 15.0/300`
- 菜单展示详细数据：每日/每月已用、限额、剩余、上次更新时间
- 菜单内设置：
  - 账号类型切换：共享（shared）/ 滴滴车（private）/ Codex（codex_shared）
  - 设置 Token（支持 JWT 或 API Key，均使用 Bearer 头）
  - 标题格式：百分比 或 自定义模板
  - 刷新/隐藏标题/打开控制台

## 运行
```bash
# 进入目录
cd packycode

# 安装依赖（建议使用虚拟环境）
pip3 install -r requirements.txt

# 启动
python3 main.py
```

或使用脚本一键打包 .app：
```bash
# 进入目录
cd packycode

# 构建（使用本地 .venv）
bash build_app.sh

# 构建并打开应用
bash build_app.sh --open

# 清理并重建
bash build_app.sh --clean

# 在当前环境直接构建（不创建 venv）
bash build_app.sh --no-venv
```

首次启动后：
- 点击菜单栏图标 → “设置 Token...” 填写 PackyCode 的 JWT 或 API Key
- 点击“账号类型”选择当前使用的环境（共享/滴滴车/Codex）
 - 点击“标题格式”选择“百分比”或“自定义...”。自定义模板支持占位符：
   - {d_pct} / {m_pct}：日/月百分比（0-100，取整）
   - {d_spent} / {m_spent}：日/月已用（1位小数）
   - {d_limit} / {m_limit}：日/月预算上限（取整）
   - {bal}：余额（2位小数）
   示例：`D {d_pct}% | M {m_pct}%` 或 `$ {bal}`

## 打包（可选）
如需打包为 macOS .app（基于 py2app）：
```bash
pip3 install py2app
python3 setup.py py2app
```

> 注意：图标默认引用 `packycode-cost/assets/icon.png`（已存在于仓库），打包时请确保文件路径有效；或在 `main.py` 中修改 `ICON_CANDIDATES` 指向本地图标。

## 配置存储
配置持久化在：`~/.packycode/config.json`
```json
{
  "account_version": "shared | private | codex_shared",
  "token": "<your-token>",
  "hidden": false,
  "poll_interval": 180,
  "title_mode": "percent | custom",
  "title_custom": "D {d_pct}% | M {m_pct}%"
}
```

## 已知限制
- 运行环境需 macOS（依赖 rumps/pyobjc）
- 本地无法读取浏览器 Cookie，因此需要手动粘贴 JWT 或 API Key
- 网络请求失败时会在菜单显示错误提示，不会崩溃
