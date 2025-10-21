import datetime
import base64
import math
import json
import os
import threading
import time
import webbrowser
from typing import Any, Dict, Optional, Tuple

import requests
import rumps


# ---------------------------
# 配置与常量
# ---------------------------

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".packycode")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "account_version": "shared",  # shared | private | codex_shared
    "token": "",
    "hidden": False,
    "poll_interval": 180,  # seconds
    # 标题显示模式：percent | custom
    "title_mode": "percent",
    "title_include_requests": False,
    # 自定义模板占位符：{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}
    "title_custom": "D {d_pct}% | M {m_pct}%",
}

# 参考 packycode-cost/api/config.ts
ACCOUNT_ENV = {
    "shared": {
        "base": "https://www.packycode.com",
        "dashboard": "https://www.packycode.com/dashboard",
        "pricing": "https://www.packycode.com/pricing",
    },
    "private": {
        "base": "https://share.packycode.com",
        "dashboard": "https://share.packycode.com/dashboard",
        "pricing": "https://share.packycode.com/pricing",
    },
    "codex_shared": {
        "base": "https://codex.packycode.com",
        "dashboard": "https://codex.packycode.com/dashboard",
        "pricing": "https://codex.packycode.com/pricing",
    },
}

USER_INFO_PATH = "/api/backend/users/info"
USAGE_STATS_PATH_TMPL = "/api/backend/users/{user_id}/usage-stats?days=30"

# 候选图标
def _resource_path_candidate(filename: str) -> Optional[str]:
    rp = os.environ.get("RESOURCEPATH")
    if rp:
        p = os.path.join(rp, filename)
        if os.path.exists(p):
            return p
    return None


ICON_CANDIDATES = list(filter(None, [
    _resource_path_candidate("icon.png"),  # 优先使用打包在 .app Resources 的图标
    os.path.join(os.path.dirname(__file__), "assets", "icon.png"),  # 仓库内置图标
]))


# ---------------------------
# 工具函数
# ---------------------------


def ensure_config_dir() -> None:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    ensure_config_dir()
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 合并默认值
        merged = DEFAULT_CONFIG.copy()
        merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_config_dir()
    safe_cfg = DEFAULT_CONFIG.copy()
    safe_cfg.update({k: v for k, v in cfg.items() if k in DEFAULT_CONFIG})
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe_cfg, f, ensure_ascii=False, indent=2)


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def round_half_up(value: float) -> int:
    if value >= 0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "-"
    try:
        return f"${value:.2f}"
    except Exception:
        return str(value)


def now_str() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def find_icon() -> Optional[str]:
    for p in ICON_CANDIDATES:
        # 允许相对路径存在 ..
        ap = os.path.abspath(p)
        if os.path.exists(ap):
            return ap
    return None


# ---------------------------
# 主应用
# ---------------------------


class PackycodeStatusApp(rumps.App):
    def __init__(self):
        icon = find_icon()
        super().__init__("PackyCode", icon=icon, title="")

        self._cfg = load_config()
        self._lock = threading.RLock()
        self._last_data: Dict[str, Any] = {}
        self._last_error: Optional[str] = None
        self._last_usage: Optional[Dict[str, Any]] = None

        # 信息区（只读）
        self.info_title = rumps.MenuItem("状态：未初始化")
        self.info_title.state = 0
        self.info_title.set_callback(None)

        self.info_daily = rumps.MenuItem("每日：-/- (剩余 -)")
        self.info_daily.set_callback(None)

        self.info_requests = rumps.MenuItem("请求次数：-")
        self.info_requests.set_callback(None)

        # 使用统计扩展
        self.info_usage_span = rumps.MenuItem("近30日：-")
        self.info_usage_span.set_callback(None)

        self.info_monthly = rumps.MenuItem("每月：-/- (剩余 -)")
        self.info_monthly.set_callback(None)

        self.info_balance = rumps.MenuItem("余额：-")
        self.info_balance.set_callback(None)

        self.info_last = rumps.MenuItem("上次更新：-")
        self.info_last.set_callback(None)

        # 账号类型子菜单
        self.menu_account = {
            "共享（公交车）": rumps.MenuItem("共享（公交车）", callback=self._set_shared),
            "滴滴车（私有）": rumps.MenuItem("滴滴车（私有）", callback=self._set_private),
            "Codex 公交车": rumps.MenuItem("Codex 公交车", callback=self._set_codex),
        }

        # 标题格式子菜单
        self.menu_title_fmt = {
            "百分比": rumps.MenuItem("百分比", callback=self._set_title_percent),
            "自定义...": rumps.MenuItem("自定义...", callback=self._set_title_custom),
            "显示请求次数": rumps.MenuItem("显示请求次数", callback=self._toggle_title_requests),
        }

        # 完整菜单
        self.menu = [
            self.info_title,
            self.info_daily,
            self.info_requests,
            self.info_usage_span,
            self.info_monthly,
            self.info_balance,
            self.info_last,
            None,
            rumps.MenuItem("刷新", callback=self.refresh_now),
            {"账号类型": self.menu_account},
            {"标题格式": self.menu_title_fmt},
            rumps.MenuItem("设置 Token...", callback=self.set_token),
            rumps.MenuItem("隐藏/展示", callback=self.toggle_hidden),
            rumps.MenuItem("打开控制台", callback=self.open_dashboard),
        ]

        # 初始选中账号类型
        self._update_account_checkmarks()
        self._update_title_format_checkmarks()
        # 如果配置为隐藏，应用标题置空
        if self._cfg.get("hidden"):
            self.title = ""

        # 定时刷新
        self._timer = rumps.Timer(self._on_tick, interval=self._cfg.get("poll_interval", 180))
        self._timer.start()

        # 立即刷新一次，避免首次启动状态栏为空
        try:
            self._refresh(force=True)
        except Exception:
            pass

    # ------------- 菜单回调 -------------
    def refresh_now(self, _: Optional[rumps.MenuItem] = None):
        self._refresh(force=True)

    def toggle_hidden(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            hidden = not bool(self._cfg.get("hidden"))
            self._cfg["hidden"] = hidden
            save_config(self._cfg)
            if hidden:
                self.title = ""
            else:
                # 立即刷新一个周期，更新标题
                self._refresh(force=True)

    def set_token(self, _: Optional[rumps.MenuItem] = None):
        win = rumps.Window(
            title="设置 Token (JWT 或 API Key)",
            message="粘贴从 PackyCode 获取的 JWT 或 API Key (将以 Bearer 形式发送)",
            default_text=self._cfg.get("token", ""),
            ok="保存",
            cancel="取消",
        )
        res = win.run()
        if res.clicked:
            token = (res.text or "").strip()
            with self._lock:
                self._cfg["token"] = token
                save_config(self._cfg)
            self._refresh(force=True)

    def _set_shared(self, _: Optional[rumps.MenuItem] = None):
        self._set_account("shared")

    def _set_private(self, _: Optional[rumps.MenuItem] = None):
        self._set_account("private")

    def _set_codex(self, _: Optional[rumps.MenuItem] = None):
        self._set_account("codex_shared")

    def _set_account(self, account: str):
        with self._lock:
            self._cfg["account_version"] = account
            save_config(self._cfg)
            self._update_account_checkmarks()
        self._refresh(force=True)

    def open_dashboard(self, _: Optional[rumps.MenuItem] = None):
        base, dashboard = self._get_base_and_dashboard()
        webbrowser.open(dashboard or base)

    # ------------- 标题格式相关 -------------
    def _update_title_format_checkmarks(self):
        mode = self._cfg.get("title_mode", "percent")
        self.menu_title_fmt["百分比"].state = 1 if mode == "percent" else 0
        # 自定义是一个操作项（...），不打勾
        include_requests = bool(self._cfg.get("title_include_requests"))
        self.menu_title_fmt["显示请求次数"].state = 1 if include_requests else 0

    def _set_title_percent(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["title_mode"] = "percent"
            # 如果自定义模板为空，给个默认
            if not self._cfg.get("title_custom"):
                self._cfg["title_custom"] = DEFAULT_CONFIG["title_custom"]
            save_config(self._cfg)
        self._update_title_format_checkmarks()
        self._refresh(force=True)

    def _set_title_custom(self, _: Optional[rumps.MenuItem] = None):
        help_text = (
            "自定义标题模板，支持占位符：\n"
            "{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\n"
            "例如: D {d_pct}% | M {m_pct}% 或 $ {bal}"
        )
        win = rumps.Window(
            title="自定义标题格式",
            message=help_text,
            default_text=self._cfg.get("title_custom", DEFAULT_CONFIG["title_custom"]),
            ok="保存",
            cancel="取消",
        )
        res = win.run()
        if res.clicked:
            tpl = (res.text or "").strip()
            if tpl:
                with self._lock:
                    self._cfg["title_mode"] = "custom"
                    self._cfg["title_custom"] = tpl
                    save_config(self._cfg)
                self._update_title_format_checkmarks()
                self._refresh(force=True)

    def _toggle_title_requests(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            include = not bool(self._cfg.get("title_include_requests"))
            self._cfg["title_include_requests"] = include
            save_config(self._cfg)
        self._update_title_format_checkmarks()
        self._refresh(force=True)

    # ------------- 定时逻辑 -------------
    def _on_tick(self, _timer: rumps.Timer):
        self._refresh(force=False)

    # ------------- 内部逻辑 -------------
    def _update_account_checkmarks(self):
        current = self._cfg.get("account_version", "shared")
        self.menu_account["共享（公交车）"].state = 1 if current == "shared" else 0
        self.menu_account["滴滴车（私有）"].state = 1 if current == "private" else 0
        self.menu_account["Codex 公交车"].state = 1 if current == "codex_shared" else 0

    def _get_base_and_dashboard(self) -> Tuple[str, str]:
        account = self._cfg.get("account_version", "shared")
        env = ACCOUNT_ENV.get(account, ACCOUNT_ENV["shared"])  # type: ignore
        return env["base"], env["dashboard"]

    def _refresh(self, force: bool = False):
        # 避免过于频繁的刷新
        if not force:
            # 允许最短 2 秒间隔
            if getattr(self, "_last_refresh_ts", 0) and time.time() - self._last_refresh_ts < 2:
                return

        self._last_refresh_ts = time.time()
        try:
            info = self._fetch_user_info()
            self._last_data = info or {}
            # 若为 JWT，尝试拉取使用次数统计
            try:
                usage = self._maybe_fetch_usage_stats()
            except Exception:
                usage = None
            self._last_usage = usage
            self._last_error = None
            self._update_ui_from_info(info, usage)
        except Exception as e:
            self._last_error = str(e)
            self._update_ui_error(str(e))

    def _fetch_user_info(self) -> Optional[Dict[str, Any]]:
        token = (self._cfg.get("token") or "").strip()
        if not token:
            raise RuntimeError("未设置 Token，请通过“设置 Token...”配置")

        base, _dashboard = self._get_base_and_dashboard()
        url = f"{base}{USER_INFO_PATH}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PackyCode-StatusBar/1.0",
        }

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 400:
            raise RuntimeError(f"请求失败: HTTP {resp.status_code}")

        data = resp.json()
        # 兼容 { success, data } 或直接数据
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        return data

    def _maybe_fetch_usage_stats(self) -> Optional[Dict[str, Any]]:
        """Token 为 JWT 时，调用 codex 接口获取使用次数统计。

        返回示例：
        {
          "today_usage": {"date": "YYYY-MM-DD", "api_calls": N},
          "daily_trend": [{"date": "YYYY-MM-DD", "api_calls": M}, ...]
        }
        失败或不可用时返回 None。
        """
        token = (self._cfg.get("token") or "").strip()
        if not _is_probable_jwt(token):
            return None

        user_id = _extract_user_id_from_jwt(token)
        if not user_id:
            return None

        # 统一使用 codex 域（接口示例提供于该域）
        env = ACCOUNT_ENV.get("codex_shared", ACCOUNT_ENV["shared"])  # type: ignore
        url = f"{env['base']}{USAGE_STATS_PATH_TMPL.format(user_id=user_id)}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PackyCode-StatusBar/1.0",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 400:
            return None
        try:
            return resp.json()
        except Exception:
            return None

    def _update_ui_from_info(self, info: Optional[Dict[str, Any]], usage: Optional[Dict[str, Any]]):
        if not info:
            self.info_title.title = "状态：无数据"
            self.title = "" if self._cfg.get("hidden") else "无数据"
            self.info_last.title = f"上次更新：{now_str()}"
            self.info_requests.title = "请求次数：-"
            self.info_usage_span.title = "近30日：-"
            return

        # 解析字段（参考 packycode-cost UserApiResponse 与转换逻辑）
        daily_limit = parse_float(info.get("daily_budget_usd"))
        daily_spent = parse_float(info.get("daily_spent_usd"))
        monthly_limit = parse_float(info.get("monthly_budget_usd"))
        monthly_spent = parse_float(info.get("monthly_spent_usd"))
        balance_str = info.get("balance_usd")
        balance = parse_float(balance_str) if balance_str is not None else None

        # 使用次数接口（若为 JWT）
        today_calls: Optional[int] = None
        span_desc: Optional[str] = None
        if usage and isinstance(usage, dict):
            try:
                tu = usage.get("today_usage") or {}
                if tu and tu.get("api_calls") is not None:
                    today_calls = int(tu.get("api_calls"))
            except Exception:
                today_calls = None
            try:
                trend = usage.get("daily_trend") or []
                if isinstance(trend, list) and trend:
                    total = 0
                    cnt = 0
                    for it in trend:
                        try:
                            total += int(it.get("api_calls", 0))
                            cnt += 1
                        except Exception:
                            pass
                    if cnt > 0:
                        span_desc = f"总 {total}，日均 {round_half_up(total / cnt)}"
            except Exception:
                span_desc = None

        daily_remaining = max(0.0, daily_limit - daily_spent) if daily_limit else 0.0
        monthly_remaining = max(0.0, monthly_limit - monthly_spent) if monthly_limit else 0.0

        # 更新菜单详情
        self.info_title.title = "状态：正常"
        self.info_daily.title = (
            f"每日：{daily_spent:.2f}/{daily_limit:.2f} (剩余 {daily_remaining:.2f})"
            if daily_limit > 0
            else f"每日：{daily_spent:.2f}/- (剩余 -)"
        )
        if today_calls is not None:
            self.info_requests.title = f"请求次数：{today_calls}"
        else:
            self.info_requests.title = "请求次数：-"

        self.info_usage_span.title = f"近30日：{span_desc}" if span_desc else "近30日：-"
        self.info_monthly.title = (
            f"每月：{monthly_spent:.2f}/{monthly_limit:.2f} (剩余 {monthly_remaining:.2f})"
            if monthly_limit > 0
            else f"每月：{monthly_spent:.2f}/- (剩余 -)"
        )
        if balance is not None:
            self.info_balance.title = f"余额：{fmt_money(balance)}"
        else:
            self.info_balance.title = "余额：-"

        self.info_last.title = f"上次更新：{now_str()}"

        # 状态栏标题（根据设置）
        if self._cfg.get("hidden"):
            self.title = ""
            return

        self.title = self._make_title(info, usage)

    def _update_ui_error(self, err: str):
        self.info_title.title = f"状态：错误 - {err}"
        self.info_last.title = f"上次更新：{now_str()}"
        self.info_requests.title = "请求次数：-"
        self.info_usage_span.title = "近30日：-"
        if not self._cfg.get("hidden"):
            self.title = "错误"

    # ------------- 标题格式化 -------------
    def _make_title(self, info: Dict[str, Any], usage: Optional[Dict[str, Any]]) -> str:
        # 构造上下文
        daily_limit = parse_float(info.get("daily_budget_usd"))
        daily_spent = parse_float(info.get("daily_spent_usd"))
        monthly_limit = parse_float(info.get("monthly_budget_usd"))
        monthly_spent = parse_float(info.get("monthly_spent_usd"))
        balance_str = info.get("balance_usd")
        balance = parse_float(balance_str) if balance_str is not None else None
        # 从 usage 获取今日请求数
        daily_requests: Optional[int] = None
        if usage and isinstance(usage, dict):
            try:
                tu = usage.get("today_usage") or {}
                if tu and tu.get("api_calls") is not None:
                    daily_requests = int(tu.get("api_calls"))
            except Exception:
                daily_requests = None

        d_pct = 0.0
        m_pct = 0.0
        if daily_limit > 0:
            d_pct = min(100.0, (daily_spent / daily_limit) * 100.0)
        if monthly_limit > 0:
            m_pct = min(100.0, (monthly_spent / monthly_limit) * 100.0)

        ctx = {
            "d_spent": f"{daily_spent:.1f}",
            "d_limit": f"{daily_limit:.0f}",
            "d_pct": f"{d_pct:.0f}",
            "m_spent": f"{monthly_spent:.1f}",
            "m_limit": f"{monthly_limit:.0f}",
            "m_pct": f"{m_pct:.0f}",
            "bal": f"{balance:.2f}" if balance is not None else "-",
            "d_req": str(daily_requests) if daily_requests is not None else "-",
        }

        mode = self._cfg.get("title_mode", "percent")
        include_requests = bool(self._cfg.get("title_include_requests"))
        if mode == "percent":
            # 缺省百分比样式
            title = f"D {ctx['d_pct']}% | M {ctx['m_pct']}%"
            if include_requests and daily_requests is not None:
                title = f"{title} | Req {ctx['d_req']}"
            return title
        elif mode == "custom":
            tpl = self._cfg.get("title_custom") or DEFAULT_CONFIG["title_custom"]
            title = _safe_format_template(tpl, ctx)
            if include_requests and daily_requests is not None and "{d_req}" not in tpl:
                title = f"{title} | Req {ctx['d_req']}"
            return title
        else:
            # 兜底：百分比
            title = f"D {ctx['d_pct']}% | M {ctx['m_pct']}%"
            if include_requests and daily_requests is not None:
                title = f"{title} | Req {ctx['d_req']}"
            return title


def _safe_format_template(tpl: str, ctx: Dict[str, str]) -> str:
    # 仅替换允许的键，避免 KeyError
    out = tpl
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", v)
    # 简单清理多余空格
    return " ".join(out.split())


def _is_probable_jwt(token: str) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False
    try:
        for i in (0, 1):
            p = parts[i]
            pad = '=' * ((4 - len(p) % 4) % 4)
            base64.urlsafe_b64decode((p + pad).encode("utf-8"))
        return True
    except Exception:
        return False


def _extract_user_id_from_jwt(token: str) -> Optional[str]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        pad = '=' * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode((payload_b64 + pad).encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)
        uid = payload.get("user_id") or payload.get("sub")
        return uid if isinstance(uid, str) and uid else None
    except Exception:
        return None


if __name__ == "__main__":
    PackycodeStatusApp().run()
