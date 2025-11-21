# PackyCode macOS 状态栏应用使用与打包指南

本文件详细说明 PackyCode 状态栏应用（Python + rumps）的使用、配置、打包、签名与常见问题。

## 1. 快速开始

- 运行（开发模式）
  - `cd packycode`
  - `pip3 install -r requirements.txt`
  - `python3 main.py`
- 首次使用
  - 菜单栏图标 → `设置 Token...` 粘贴 JWT 或 API Key（均以 Bearer 发送）
  - `账号类型` 选择：共享（shared）/ 滴滴车（private）/ Codex（codex_shared）
  - `标题格式` 选择：`百分比` 或 `自定义...`（见第 3 节）

## 2. 配置说明

- 配置文件：`~/.packycode/config.json`
- 字段：
  - `account_version`: `shared | private | codex_shared`
  - `token`: 你的 JWT 或 API Key
  - `hidden`: 是否隐藏状态栏标题
  - `poll_interval`: 刷新间隔秒数（默认 180）
  - `title_mode`: `percent | custom`
  - `title_custom`: 自定义模板（见第 3 节）
- 示例：
```json
{
  "account_version": "shared",
  "token": "<your-token>",
  "hidden": false,
  "poll_interval": 180,
  "title_mode": "percent",
  "title_custom": "D {d_pct}% | M {m_pct}%"
}
```

## 3. 标题模板（自定义展示）

- 入口：菜单栏 → `标题格式 → 自定义...`
- 可用占位符：
  - `{d_pct}` / `{m_pct}`：日/周期百分比（0-100，取整）
  - `{d_spent}` / `{m_spent}`：日/周期已用（1 位小数）
  - `{d_limit}` / `{m_limit}`：日/周期预算上限（取整）
  - `{bal}`：余额（2 位小数，shared 模式）
- 示例：
  - `D {d_pct}% | M {m_pct}%`
  - `$ {bal} | D {d_spent}/{d_limit} ({d_pct}%)`

## 4. 打包 .app（py2app）

- 一键脚本（推荐）：
  - `cd packycode`
  - `bash build_app.sh`（默认创建并使用 `.venv`）
  - 可选参数：`--open` 构建后打开；`--clean` 清理重建；`--no-venv` 不使用虚拟环境
  - 产物路径：`packycode/dist/PackyCode.app`
- 手工打包：
  - `pip3 install py2app`
  - `python3 setup.py py2app`
- 图标：
  - 将 PNG 放在 `packycode/assets/icon.png`，构建时会自动打包到 `Resources/icon.png`
  - 运行时优先从 `RESOURCEPATH/icon.png` 加载（`main.py` 已处理）。若缺失，将使用占位图标并继续构建。

## 4.1 使用 GitHub Actions 构建

- 工作流文件：`packycode/.github/workflows/packycode-macos.yml`
- 触发方式：
  - 手动触发（Workflow Dispatch）
  - 推送 tag（以 `v*` 开头），或当 `packycode/**` 变更时
- 产物：
  - 构建 `.app` 后打包为 `PackyCode-macOS.zip` 并作为 artifact 上传
  - 若以 tag 推送，自动创建 Release 并附带该 zip
- 本地预览工作流：
  - 确认 Python 版本（默认使用 3.11）
  - 工作流步骤等同本地执行：安装依赖 → `py2app` 构建 → `ditto` 打包 zip

注意：
- 如果你将 `packycode/` 作为仓库根目录推送至 GitHub（推荐独立仓库方式），上述工作流即可被检测并生效。
- 如果你的仓库根目录是更高一层（例如包含多个项目），GitHub 仅识别仓库根的 `.github/workflows/`，此时需将该工作流移到仓库根的 `.github/workflows/` 下。

## 5.（可选）签名与公证

- Ad-hoc 签名（本地运行/分发测试）：
```bash
codesign --force --deep --sign - "packycode/dist/PackyCode.app"
```
- Developer ID 签名（需 Apple 证书）：
```bash
codesign --force --deep \
  --sign "Developer ID Application: <Your Name> (<TeamID>)" \
  --options runtime "packycode/dist/PackyCode.app"
```
- 公证（可选）：
  - 参考 `xcrun notarytool submit` 或 App Store Connect 文档

> 注：首次打开未签名/未公证应用，需在 `系统设置 → 隐私与安全性` 中允许，或执行：
> `xattr -dr com.apple.quarantine packycode/dist/PackyCode.app`

## 6. 常见问题（Troubleshooting）

- 未设置 Token：
  - 菜单显示“状态：错误 - 未设置 Token...”，请先通过 `设置 Token...` 粘贴有效 JWT 或 API Key。
- 401/403：
  - Token 失效或权限不足，检查账号类型与域名是否匹配（shared/www、private/share、codex_shared/codex）。
- LibreSSL/urllib3 警告（NotOpenSSLWarning）：
  - 这是环境兼容性警告，功能不受影响。可升级 Python/openssl，或临时忽略：
    - 运行时：`PYTHONWARNINGS="ignore:NotOpenSSLWarning" python3 main.py`
- 权限错误（Application Support）：
  - 若遇到写入 `~/Library/Application Support/PackyCode` 权限问题，请以普通用户会话运行，或用已签名的 .app 运行。
- 状态栏无图标/标题：
  - 首次启动已自动刷新一次；若仍无显示，请检查网络、Token、账号类型，以及 `隐藏/展示` 设置。
- 打包报错 `File exists: wheel-*.dist-info`：
  - 先清理：`bash build.sh` 或 `bash build_app.sh --clean`
  - 使用 Python 3.11（py2app 对 3.13 支持尚不稳定）
  - 我们在 `setup.py` 已排除 `pip/wheel/setuptools` 打包，通常可解决。

## 7. 安全说明

- Token 以明文存储在 `~/.packycode/config.json`，请注意本机安全。
- 建议优先使用 API Key（可随时吊销），必要时再使用短期 JWT。

## 8. 代码定位

- 主程序：`packycode/main.py`
- 依赖：`packycode/requirements.txt`
- 打包：`packycode/setup.py`、`packycode/build_app.sh`
- 参考配置与接口：`packycode-cost/`（无需在本地运行，仅供接口字段说明，不参与构建）
