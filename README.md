# PackyCode 状态栏应用（macOS）

![product](https://github.com/jacksonon/packycode-macos-statusbar/blob/main/product.png)

一个用 Python 编写的 macOS 状态栏应用，用于展示 PackyCode 额度/预算使用情况。

- 参考实现：`GPO/`（macOS 状态栏应用框架，rumps，非构建依赖）
- 数据来源：`packycode-cost/`（三种账号模式与 API 端点约定，非构建依赖）

## 功能
- 状态栏实时展示：
  - 公交车（shared）：显示账户余额 `$12.34`
  - 滴滴车（private）/ Codex 公交车（codex_shared）：显示每日/周期消费与预算进度 `D 1.2/20 | M 15.0/300`
- 菜单展示详细数据：每日/周期已用、限额、剩余、上次更新时间
  - 新增：显示周期与续费提醒
    - 周期：优先使用订阅接口 `current_period_start/current_period_end`（`/api/backend/subscriptions`），其次使用 `plan_expires_at`；若都无则按自然月，展示 `MM.DD-MM.DD`
    - 续费提醒：到期前 3 天显示“即将到期/建议续费”，平时不展示
- 语言切换：支持 简体中文、English、繁體中文、日本語、한국어、Русский（菜单“语言”中切换）
- 菜单内设置：
  - 账号类型切换：共享（shared）/ 滴滴车（private）/ Codex（codex_shared）
  - 设置 Token（支持 JWT 或 API Key，均使用 Bearer 头）
  - 标题格式：百分比 或 自定义模板
  - 刷新/隐藏标题/打开控制台/延迟监控（测速：https://packy.te.sb/）/推广（PackyCode / Codex）
  - 检查更新：对比 GitHub 最新 release 的 tag 与本地版本（固定仓库：`jacksonon/packycode-macos-statusbar`）。若检测到新版本，将在弹窗中展示“在线更新”按钮，可直接下载安装并替换应用。

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
   - {d_pct} / {m_pct}：日/周期百分比（0-100，取整）
   - {d_spent} / {m_spent}：日/周期已用（1位小数）
   - {d_limit} / {m_limit}：日/周期预算上限（取整）
   - {bal}：余额（2位小数）
   示例：`D {d_pct}% | M {m_pct}%` 或 `$ {bal}`

## 打包（可选）
如需打包为 macOS .app（基于 py2app）：
```bash
pip3 install py2app
python3 setup.py py2app
```

> 注意：图标现已固定为仓库内的 `assets/icon.png`。请将你提供的 PNG 放到该路径；若缺失，构建会使用占位图标并继续。

## 配置存储
配置持久化在：`~/.packycode/config.json`
```json
{
  "account_version": "shared | private | codex_shared",
  "token": "<your-token>",
  "hidden": false,
  "poll_interval": 180,
  "title_mode": "percent | custom",
  "title_custom": "D {d_pct}% | M {m_pct}%",
  "update_expected_team_id": "",
  "language": "zh_CN"
}
```

检查更新：
- 固定使用 `jacksonon/packycode-macos-statusbar`
- 菜单中点击“检查更新”，会调用 GitHub Releases API 比较最新 `tag_name` 与当前版本，若有新版本会提示并可跳转至发布页下载

在线更新（从“检查更新”弹窗进入）：
- 固定使用 `jacksonon/packycode-macos-statusbar`
- 下载最新 release 的 zip，解压并自动替换 `.app`（通过临时脚本在退出后替换），随后尝试自动重启；若当前以源码方式运行，会打开 Finder 供你手动拖拽替换。
- 安全校验：
  - 若 Release 同时提供 `.sha256`/`.sha256sum`/`sha256.txt`，会自动核对压缩包 SHA256，不匹配则中止
  - 下载后校验签名：优先运行 `codesign --verify` 与 `spctl --assess`；如在配置中设置 `update_expected_team_id`（Apple TeamIdentifier），会强制比对，不匹配则中止；若未配置但校验失败，会提示风险并让你确认是否继续
  - 更新脚本会在拷贝后执行 `xattr -dr com.apple.quarantine "$TARGET_APP"`，以减少首次打开时的 Gatekeeper 阻拦（请确保仅信任来源可靠的发行包）

版本号来源：
- 打包环境优先从 `.app/Contents/Info.plist` 的 `CFBundleShortVersionString` 读取
- 源码环境读取仓库根的 `VERSION` 文件；`setup.py` 也从该文件读取版本，避免手动同步

## 已知限制
- 运行环境需 macOS（依赖 rumps/pyobjc）
- 本地无法读取浏览器 Cookie，因此需要手动粘贴 JWT 或 API Key
- 网络调用失败时会在菜单显示错误提示，不会崩溃
