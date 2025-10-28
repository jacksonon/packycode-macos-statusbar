import datetime
import calendar
import base64
import math
import re
import json
import os
import threading
import time
import webbrowser
import tempfile
import zipfile
import shutil
import subprocess
import plistlib
import hashlib
from typing import Any, Dict, Optional, Tuple

import requests
import rumps
try:
    from AppKit import NSAlert
except Exception:
    NSAlert = None  # 运行在无 GUI/无 pyobjc 环境时兜底


# ---------------------------
# 语言与本地化
# ---------------------------

# 支持的语言代码
LANG_ZH_CN = "zh_CN"
LANG_EN = "en"
LANG_ZH_TW = "zh_TW"
LANG_JA = "ja"
LANG_KO = "ko"
LANG_RU = "ru"

_current_language = LANG_ZH_CN


class LocalizedError(Exception):
    def __init__(self, key: str, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)

    def message(self) -> str:
        try:
            return _t(self.key, **self.kwargs)
        except Exception:
            return self.key

    def __str__(self) -> str:
        return self.message()


def set_current_language(lang: str) -> None:
    global _current_language
    if lang in {LANG_ZH_CN, LANG_EN, LANG_ZH_TW, LANG_JA, LANG_KO, LANG_RU}:
        _current_language = lang
    else:
        _current_language = LANG_ZH_CN


# 文本字典
I18N = {
    # 占位符/片段
    "version_prefix": {
        LANG_ZH_CN: "版本：",
        LANG_EN: "Version: ",
        LANG_ZH_TW: "版本：",
        LANG_JA: "バージョン：",
        LANG_KO: "버전: ",
        LANG_RU: "Версия: ",
    },
    "title_req_label": {
        LANG_ZH_CN: "调用",
        LANG_EN: "Req",
        LANG_ZH_TW: "調用",
        LANG_JA: "リクエスト",
        LANG_KO: "요청",
        LANG_RU: "Запрос",
    },

    # 顶部信息区（占位）
    "status_uninitialized": {
        LANG_ZH_CN: "状态：未初始化",
        LANG_EN: "Status: Not initialized",
        LANG_ZH_TW: "狀態：未初始化",
        LANG_JA: "状態：未初期化",
        LANG_KO: "상태: 초기화되지 않음",
        LANG_RU: "Статус: не инициализировано",
    },
    "status_ok": {
        LANG_ZH_CN: "状态：正常",
        LANG_EN: "Status: OK",
        LANG_ZH_TW: "狀態：正常",
        LANG_JA: "状態：正常",
        LANG_KO: "상태: 정상",
        LANG_RU: "Статус: ОК",
    },
    "daily_placeholder": {
        LANG_ZH_CN: "每日：-/- (剩余 -)",
        LANG_EN: "Daily: -/- (left -)",
        LANG_ZH_TW: "每日：-/- (剩餘 -)",
        LANG_JA: "日次：-/- (残り -)",
        LANG_KO: "일일: -/- (잔여 -)",
        LANG_RU: "День: -/- (осталось -)",
    },
    "requests_placeholder": {
        LANG_ZH_CN: "调用次数：-",
        LANG_EN: "Requests: -",
        LANG_ZH_TW: "調用次數：-",
        LANG_JA: "リクエスト数：-",
        LANG_KO: "요청 수: -",
        LANG_RU: "Запросов: -",
    },
    "usage_span_placeholder": {
        LANG_ZH_CN: "近30日：-",
        LANG_EN: "Last 30 days: -",
        LANG_ZH_TW: "近30日：-",
        LANG_JA: "直近30日：-",
        LANG_KO: "최근 30일: -",
        LANG_RU: "За 30 дней: -",
    },
    "monthly_placeholder": {
        LANG_ZH_CN: "每月：-/- (剩余 -)",
        LANG_EN: "Monthly: -/- (left -)",
        LANG_ZH_TW: "每月：-/- (剩餘 -)",
        LANG_JA: "月次：-/- (残り -)",
        LANG_KO: "월간: -/- (잔여 -)",
        LANG_RU: "Месяц: -/- (осталось -)",
    },
    "cycle_placeholder": {
        LANG_ZH_CN: "周期：-",
        LANG_EN: "Cycle: -",
        LANG_ZH_TW: "週期：-",
        LANG_JA: "サイクル：-",
        LANG_KO: "주기: -",
        LANG_RU: "Цикл: -",
    },
    "renew_placeholder": {
        LANG_ZH_CN: "续费提醒：-",
        LANG_EN: "Renewal: -",
        LANG_ZH_TW: "續費提醒：-",
        LANG_JA: "更新通知：-",
        LANG_KO: "갱신 알림: -",
        LANG_RU: "Продление: -",
    },
    "balance_placeholder": {
        LANG_ZH_CN: "余额：-",
        LANG_EN: "Balance: -",
        LANG_ZH_TW: "餘額：-",
        LANG_JA: "残高：-",
        LANG_KO: "잔액: -",
        LANG_RU: "Баланс: -",
    },
    "last_update_placeholder": {
        LANG_ZH_CN: "上次更新：-",
        LANG_EN: "Last Update: -",
        LANG_ZH_TW: "上次更新：-",
        LANG_JA: "最終更新：-",
        LANG_KO: "마지막 업데이트: -",
        LANG_RU: "Последнее обновление: -",
    },
    "token_placeholder": {
        LANG_ZH_CN: "Token：-",
        LANG_EN: "Token: -",
        LANG_ZH_TW: "Token：-",
        LANG_JA: "トークン：-",
        LANG_KO: "토큰: -",
        LANG_RU: "Токен: -",
    },

    # 菜单分组/项
    "menu_refresh": {
        LANG_ZH_CN: "刷新",
        LANG_EN: "Refresh",
        LANG_ZH_TW: "刷新",
        LANG_JA: "更新",
        LANG_KO: "새로고침",
        LANG_RU: "Обновить",
    },
    "menu_account": {
        LANG_ZH_CN: "账号类型",
        LANG_EN: "Account",
        LANG_ZH_TW: "帳號類型",
        LANG_JA: "アカウント種別",
        LANG_KO: "계정 유형",
        LANG_RU: "Аккаунт",
    },
    "menu_title_format": {
        LANG_ZH_CN: "标题格式",
        LANG_EN: "Title Format",
        LANG_ZH_TW: "標題格式",
        LANG_JA: "タイトル形式",
        LANG_KO: "제목 형식",
        LANG_RU: "Формат заголовка",
    },
    "menu_set_token": {
        LANG_ZH_CN: "设置 Token...",
        LANG_EN: "Set Token...",
        LANG_ZH_TW: "設定 Token...",
        LANG_JA: "トークンを設定...",
        LANG_KO: "토큰 설정...",
        LANG_RU: "Указать токен...",
    },
    "menu_toggle_hidden": {
        LANG_ZH_CN: "隐藏/展示",
        LANG_EN: "Hide/Show",
        LANG_ZH_TW: "隱藏/顯示",
        LANG_JA: "非表示/表示",
        LANG_KO: "숨김/표시",
        LANG_RU: "Скрыть/Показать",
    },
    "menu_open_dashboard": {
        LANG_ZH_CN: "打开控制台",
        LANG_EN: "Open Dashboard",
        LANG_ZH_TW: "打開控制台",
        LANG_JA: "ダッシュボードを開く",
        LANG_KO: "대시보드 열기",
        LANG_RU: "Открыть панель",
    },
    "menu_latency_monitor": {
        LANG_ZH_CN: "延迟监控",
        LANG_EN: "Latency Monitor",
        LANG_ZH_TW: "延遲監控",
        LANG_JA: "レイテンシ監視",
        LANG_KO: "지연 모니터",
        LANG_RU: "Мониторинг задержки",
    },
    "menu_check_update": {
        LANG_ZH_CN: "检查更新",
        LANG_EN: "Check Updates",
        LANG_ZH_TW: "檢查更新",
        LANG_JA: "更新を確認",
        LANG_KO: "업데이트 확인",
        LANG_RU: "Проверить обновления",
    },
    # 进度圆环菜单
    "menu_ring": {
        LANG_ZH_CN: "进度圆环",
        LANG_EN: "Ring",
        LANG_ZH_TW: "進度環",
        LANG_JA: "進捗リング",
        LANG_KO: "링",
        LANG_RU: "Кольцо",
    },
    "ring_enable": {
        LANG_ZH_CN: "在图标显示进度圆环",
        LANG_EN: "Show ring in icon",
        LANG_ZH_TW: "在圖示顯示進度環",
        LANG_JA: "アイコンにリングを表示",
        LANG_KO: "아이콘에 링 표시",
        LANG_RU: "Показывать кольцо в иконке",
    },
    "ring_source": {
        LANG_ZH_CN: "圆环来源",
        LANG_EN: "Ring Source",
        LANG_ZH_TW: "環來源",
        LANG_JA: "リングのソース",
        LANG_KO: "링 소스",
        LANG_RU: "Источник кольца",
    },
    "ring_colored": {
        LANG_ZH_CN: "使用彩色圆环",
        LANG_EN: "Use colored ring",
        LANG_ZH_TW: "使用彩色環",
        LANG_JA: "カラー リングを使用",
        LANG_KO: "컬러 링 사용",
        LANG_RU: "Цветное кольцо",
    },
    "ring_reverse": {
        LANG_ZH_CN: "反转模式（高亮未使用）",
        LANG_EN: "Reverse mode (highlight unused)",
        LANG_ZH_TW: "反轉模式（高亮未使用）",
        LANG_JA: "反転表示（未使用を強調）",
        LANG_KO: "반전 모드(미사용 강조)",
        LANG_RU: "Режим инверсии (выделять остаток)",
    },
    "ring_text_enable": {
        LANG_ZH_CN: "在圆环内显示百分比",
        LANG_EN: "Show percentage in ring",
        LANG_ZH_TW: "在圓環內顯示百分比",
        LANG_JA: "リング内に割合を表示",
        LANG_KO: "링 내부에 백분율 표시",
        LANG_RU: "Показывать % в кольце",
    },
    "ring_text_mode": {
        LANG_ZH_CN: "圆环文字",
        LANG_EN: "Ring Text",
        LANG_ZH_TW: "圓環文字",
        LANG_JA: "リング文字",
        LANG_KO: "링 텍스트",
        LANG_RU: "Текст кольца",
    },
    "ring_text_mode_percent": {
        LANG_ZH_CN: "百分比",
        LANG_EN: "Percent",
        LANG_ZH_TW: "百分比",
        LANG_JA: "パーセント",
        LANG_KO: "퍼센트",
        LANG_RU: "Проценты",
    },
    "ring_text_mode_calls": {
        LANG_ZH_CN: "调用次数",
        LANG_EN: "Calls",
        LANG_ZH_TW: "調用次數",
        LANG_JA: "呼び出し回数",
        LANG_KO: "호출 수",
        LANG_RU: "Вызовы",
    },
    "ring_text_mode_spent": {
        LANG_ZH_CN: "使用金额",
        LANG_EN: "Spent",
        LANG_ZH_TW: "使用金額",
        LANG_JA: "使用金額",
        LANG_KO: "사용 금액",
        LANG_RU: "Потрачено",
    },
    "ring_text_show_percent": {
        LANG_ZH_CN: "文本显示百分号",
        LANG_EN: "Show % sign",
        LANG_ZH_TW: "文字顯示百分號",
        LANG_JA: "% 記号を表示",
        LANG_KO: "% 기호 표시",
        LANG_RU: "Показывать знак %",
    },
    "ring_text_show_label": {
        LANG_ZH_CN: "文本显示来源标签 (D/M)",
        LANG_EN: "Show source label (D/M)",
        LANG_ZH_TW: "文字顯示來源標籤 (D/M)",
        LANG_JA: "ソースラベルを表示 (D/M)",
        LANG_KO: "원본 라벨 표시 (D/M)",
        LANG_RU: "Показывать метку (D/M)",
    },
    "ring_color_mode": {
        LANG_ZH_CN: "圆环颜色",
        LANG_EN: "Ring Color",
        LANG_ZH_TW: "圓環顏色",
        LANG_JA: "リング色",
        LANG_KO: "링 색상",
        LANG_RU: "Цвет кольца",
    },
    "ring_color_colorful": {
        LANG_ZH_CN: "彩色",
        LANG_EN: "Colorful",
        LANG_ZH_TW: "彩色",
        LANG_JA: "カラフル",
        LANG_KO: "컬러풀",
        LANG_RU: "Разноцветный",
    },
    "ring_color_green": {
        LANG_ZH_CN: "绿色",
        LANG_EN: "Green",
        LANG_ZH_TW: "綠色",
        LANG_JA: "緑",
        LANG_KO: "초록",
        LANG_RU: "Зелёный",
    },
    "ring_color_blue": {
        LANG_ZH_CN: "蓝色",
        LANG_EN: "Blue",
        LANG_ZH_TW: "藍色",
        LANG_JA: "青",
        LANG_KO: "파랑",
        LANG_RU: "Синий",
    },
    "ring_color_gradient": {
        LANG_ZH_CN: "渐变彩色",
        LANG_EN: "Gradient",
        LANG_ZH_TW: "漸變彩色",
        LANG_JA: "グラデーション",
        LANG_KO: "그라데이션",
        LANG_RU: "Градиент",
    },
    "ring_source_daily": {
        LANG_ZH_CN: "每日进度",
        LANG_EN: "Daily",
        LANG_ZH_TW: "每日進度",
        LANG_JA: "日次",
        LANG_KO: "일일",
        LANG_RU: "День",
    },
    "ring_source_monthly": {
        LANG_ZH_CN: "每月进度",
        LANG_EN: "Monthly",
        LANG_ZH_TW: "每月進度",
        LANG_JA: "月次",
        LANG_KO: "월간",
        LANG_RU: "Месяц",
    },
    "menu_affiliates": {
        LANG_ZH_CN: "推广",
        LANG_EN: "Affiliates",
        LANG_ZH_TW: "推廣",
        LANG_JA: "アフィリエイト",
        LANG_KO: "추천",
        LANG_RU: "Партнёры",
    },
    "menu_quit": {
        LANG_ZH_CN: "退出",
        LANG_EN: "Quit",
        LANG_ZH_TW: "退出",
        LANG_JA: "終了",
        LANG_KO: "종료",
        LANG_RU: "Выход",
    },
    "menu_language": {
        LANG_ZH_CN: "语言",
        LANG_EN: "Language",
        LANG_ZH_TW: "語言",
        LANG_JA: "言語",
        LANG_KO: "언어",
        LANG_RU: "Язык",
    },
    "account_shared": {
        LANG_ZH_CN: "共享（公交车）",
        LANG_EN: "Shared (Bus)",
        LANG_ZH_TW: "共享（公車）",
        LANG_JA: "共有（バス）",
        LANG_KO: "공유(버스)",
        LANG_RU: "Общий (Bus)",
    },
    "account_private": {
        LANG_ZH_CN: "滴滴车（私有）",
        LANG_EN: "Private",
        LANG_ZH_TW: "滴滴車（私有）",
        LANG_JA: "DiDi（プライベート）",
        LANG_KO: "DiDi(개인)",
        LANG_RU: "Частный",
    },
    "account_codex": {
        LANG_ZH_CN: "Codex 公交车",
        LANG_EN: "Codex Shared",
        LANG_ZH_TW: "Codex 公車",
        LANG_JA: "Codex 共有",
        LANG_KO: "Codex 공유",
        LANG_RU: "Codex общий",
    },
    "titlefmt_percent": {
        LANG_ZH_CN: "百分比",
        LANG_EN: "Percent",
        LANG_ZH_TW: "百分比",
        LANG_JA: "パーセント",
        LANG_KO: "퍼센트",
        LANG_RU: "Проценты",
    },
    "titlefmt_custom": {
        LANG_ZH_CN: "自定义...",
        LANG_EN: "Custom...",
        LANG_ZH_TW: "自訂...",
        LANG_JA: "カスタム...",
        LANG_KO: "사용자 지정...",
        LANG_RU: "Пользовательский...",
    },
    "titlefmt_show_requests": {
        LANG_ZH_CN: "显示调用次数",
        LANG_EN: "Show Requests",
        LANG_ZH_TW: "顯示調用次數",
        LANG_JA: "リクエスト数を表示",
        LANG_KO: "요청 수 표시",
        LANG_RU: "Показывать запросы",
    },

    # 动态信息模板
    "status_no_data": {
        LANG_ZH_CN: "状态：无数据",
        LANG_EN: "Status: No data",
        LANG_ZH_TW: "狀態：無資料",
        LANG_JA: "状態：データなし",
        LANG_KO: "상태: 데이터 없음",
        LANG_RU: "Статус: нет данных",
    },
    "title_no_data": {
        LANG_ZH_CN: "无数据",
        LANG_EN: "No data",
        LANG_ZH_TW: "無資料",
        LANG_JA: "データなし",
        LANG_KO: "데이터 없음",
        LANG_RU: "Нет данных",
    },
    "status_error_prefix": {
        LANG_ZH_CN: "状态：错误 - {err}",
        LANG_EN: "Status: Error - {err}",
        LANG_ZH_TW: "狀態：錯誤 - {err}",
        LANG_JA: "状態：エラー - {err}",
        LANG_KO: "상태: 오류 - {err}",
        LANG_RU: "Статус: ошибка - {err}",
    },
    "title_error": {
        LANG_ZH_CN: "错误",
        LANG_EN: "Error",
        LANG_ZH_TW: "錯誤",
        LANG_JA: "エラー",
        LANG_KO: "오류",
        LANG_RU: "Ошибка",
    },
    "last_update_prefix": {
        LANG_ZH_CN: "上次更新：{time}",
        LANG_EN: "Last Update: {time}",
        LANG_ZH_TW: "上次更新：{time}",
        LANG_JA: "最終更新：{time}",
        LANG_KO: "마지막 업데이트: {time}",
        LANG_RU: "Последнее обновление: {time}",
    },
    "requests_prefix": {
        LANG_ZH_CN: "调用次数：{val}",
        LANG_EN: "Requests: {val}",
        LANG_ZH_TW: "調用次數：{val}",
        LANG_JA: "リクエスト数：{val}",
        LANG_KO: "요청 수: {val}",
        LANG_RU: "Запросов: {val}",
    },
    "usage_span_prefix": {
        LANG_ZH_CN: "近30日：{val}",
        LANG_EN: "Last 30 days: {val}",
        LANG_ZH_TW: "近30日：{val}",
        LANG_JA: "直近30日：{val}",
        LANG_KO: "최근 30일: {val}",
        LANG_RU: "За 30 дней: {val}",
    },
    "usage_span_desc": {
        LANG_ZH_CN: "总 {total}，日均 {avg}",
        LANG_EN: "Total {total}, Avg {avg}",
        LANG_ZH_TW: "總 {total}，日均 {avg}",
        LANG_JA: "合計 {total}、日平均 {avg}",
        LANG_KO: "총 {total}, 일평균 {avg}",
        LANG_RU: "Всего {total}, в день {avg}",
    },
    "daily_full": {
        LANG_ZH_CN: "每日：{spent}/{limit} (剩余 {remain})",
        LANG_EN: "Daily: {spent}/{limit} (left {remain})",
        LANG_ZH_TW: "每日：{spent}/{limit} (剩餘 {remain})",
        LANG_JA: "日次：{spent}/{limit} (残り {remain})",
        LANG_KO: "일일: {spent}/{limit} (잔여 {remain})",
        LANG_RU: "День: {spent}/{limit} (ост. {remain})",
    },
    "daily_no_limit": {
        LANG_ZH_CN: "每日：{spent}/- (剩余 -)",
        LANG_EN: "Daily: {spent}/- (left -)",
        LANG_ZH_TW: "每日：{spent}/- (剩餘 -)",
        LANG_JA: "日次：{spent}/- (残り -)",
        LANG_KO: "일일: {spent}/- (잔여 -)",
        LANG_RU: "День: {spent}/- (ост. -)",
    },
    "monthly_full": {
        LANG_ZH_CN: "每月：{spent}/{limit} (剩余 {remain})",
        LANG_EN: "Monthly: {spent}/{limit} (left {remain})",
        LANG_ZH_TW: "每月：{spent}/{limit} (剩餘 {remain})",
        LANG_JA: "月次：{spent}/{limit} (残り {remain})",
        LANG_KO: "월간: {spent}/{limit} (잔여 {remain})",
        LANG_RU: "Месяц: {spent}/{limit} (ост. {remain})",
    },
    "monthly_no_limit": {
        LANG_ZH_CN: "每月：{spent}/- (剩余 -)",
        LANG_EN: "Monthly: {spent}/- (left -)",
        LANG_ZH_TW: "每月：{spent}/- (剩餘 -)",
        LANG_JA: "月次：{spent}/- (残り -)",
        LANG_KO: "월간: {spent}/- (잔여 -)",
        LANG_RU: "Месяц: {spent}/- (ост. -)",
    },
    "cycle_expired": {
        LANG_ZH_CN: "周期：{start}-{end}（已到期）",
        LANG_EN: "Cycle: {start}-{end} (expired)",
        LANG_ZH_TW: "週期：{start}-{end}（已到期）",
        LANG_JA: "サイクル：{start}-{end}（期限切れ）",
        LANG_KO: "주기: {start}-{end} (만료)",
        LANG_RU: "Цикл: {start}-{end} (истёк)",
    },
    "cycle_remaining": {
        LANG_ZH_CN: "周期：{start}-{end}（剩余{days}天）",
        LANG_EN: "Cycle: {start}-{end} (left {days} days)",
        LANG_ZH_TW: "週期：{start}-{end}（剩餘{days}天）",
        LANG_JA: "サイクル：{start}-{end}（残り{days}日）",
        LANG_KO: "주기: {start}-{end} (잔여 {days}일)",
        LANG_RU: "Цикл: {start}-{end} (ост. {days} дн.)",
    },
    "renew_expired": {
        LANG_ZH_CN: "⚠️ 已到期，请尽快续费",
        LANG_EN: "⚠️ Expired, please renew",
        LANG_ZH_TW: "⚠️ 已到期，請儘快續費",
        LANG_JA: "⚠️ 期限切れ、早めの更新を",
        LANG_KO: "⚠️ 만료됨, 갱신 필요",
        LANG_RU: "⚠️ Срок истёк, продлите",
    },
    "renew_soon": {
        LANG_ZH_CN: "⚠️ 即将到期（剩余{days}天），建议提前续费",
        LANG_EN: "⚠️ Expiring soon (left {days} days), renew early",
        LANG_ZH_TW: "⚠️ 即將到期（剩餘{days}天），建議提前續費",
        LANG_JA: "⚠️ まもなく期限（残り{days}日）、早めの更新を",
        LANG_KO: "⚠️ 곧 만료(잔여 {days}일), 미리 갱신 권장",
        LANG_RU: "⚠️ Скоро истекает (ост. {days} дн.), продлите заранее",
    },
    "renew_prefix": {
        LANG_ZH_CN: "续费提醒：{text}",
        LANG_EN: "Renewal: {text}",
        LANG_ZH_TW: "續費提醒：{text}",
        LANG_JA: "更新通知：{text}",
        LANG_KO: "갱신 알림: {text}",
        LANG_RU: "Продление: {text}",
    },
    "balance_prefix": {
        LANG_ZH_CN: "余额：{val}",
        LANG_EN: "Balance: {val}",
        LANG_ZH_TW: "餘額：{val}",
        LANG_JA: "残高：{val}",
        LANG_KO: "잔액: {val}",
        LANG_RU: "Баланс: {val}",
    },

    # Token 展示与提醒
    "token_expired_label": {
        LANG_ZH_CN: "Token：已过期（{date}）",
        LANG_EN: "Token: expired ({date})",
        LANG_ZH_TW: "Token：已過期（{date}）",
        LANG_JA: "トークン：期限切れ（{date}）",
        LANG_KO: "토큰: 만료됨 ({date})",
        LANG_RU: "Токен: истёк ({date})",
    },
    "token_valid_until": {
        LANG_ZH_CN: "Token：{date}（{remain}）",
        LANG_EN: "Token: {date} ({remain})",
        LANG_ZH_TW: "Token：{date}（{remain}）",
        LANG_JA: "トークン：{date}（{remain}）",
        LANG_KO: "토큰: {date} ({remain})",
        LANG_RU: "Токен: {date} ({remain})",
    },
    "notify_token_expired_subtitle": {
        LANG_ZH_CN: "Token 已过期",
        LANG_EN: "Token expired",
        LANG_ZH_TW: "Token 已過期",
        LANG_JA: "トークンの有効期限切れ",
        LANG_KO: "토큰 만료",
        LANG_RU: "Токен истёк",
    },
    "notify_token_expired_message": {
        LANG_ZH_CN: "请在“设置 Token...”中更换 JWT",
        LANG_EN: "Please replace JWT in 'Set Token...'",
        LANG_ZH_TW: "請在「設定 Token...」中更換 JWT",
        LANG_JA: "『トークンを設定...』で JWT を更新してください",
        LANG_KO: "'토큰 설정...'에서 JWT를 교체하세요",
        LANG_RU: "Замените JWT в 'Указать токен...'",
    },

    # 自定义标题
    "custom_title_window": {
        LANG_ZH_CN: "自定义标题格式",
        LANG_EN: "Custom Title Format",
        LANG_ZH_TW: "自訂標題格式",
        LANG_JA: "カスタムタイトル形式",
        LANG_KO: "사용자 지정 제목 형식",
        LANG_RU: "Пользовательский формат заголовка",
    },
    "custom_title_help": {
        LANG_ZH_CN: "自定义标题模板，支持占位符：\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\n例如: D {d_pct}% | M {m_pct}% 或 $ {bal}",
        LANG_EN: "Custom title template with placeholders:\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\nExample: D {d_pct}% | M {m_pct}% or $ {bal}",
        LANG_ZH_TW: "自訂標題模板，支援占位符：\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\n例如: D {d_pct}% | M {m_pct}% 或 $ {bal}",
        LANG_JA: "タイトルテンプレート（プレースホルダー）：\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\n例: D {d_pct}% | M {m_pct}% または $ {bal}",
        LANG_KO: "제목 템플릿, 자리표시자:\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\n예: D {d_pct}% | M {m_pct}% 또는 $ {bal}",
        LANG_RU: "Шаблон заголовка с плейсхолдерами:\n{d_pct} {m_pct} {d_spent} {d_limit} {m_spent} {m_limit} {bal} {d_req}\nПример: D {d_pct}% | M {m_pct}% или $ {bal}",
    },
    "btn_save": {
        LANG_ZH_CN: "保存",
        LANG_EN: "Save",
        LANG_ZH_TW: "保存",
        LANG_JA: "保存",
        LANG_KO: "저장",
        LANG_RU: "Сохранить",
    },
    "btn_cancel": {
        LANG_ZH_CN: "取消",
        LANG_EN: "Cancel",
        LANG_ZH_TW: "取消",
        LANG_JA: "キャンセル",
        LANG_KO: "취소",
        LANG_RU: "Отмена",
    },

    # Token 设置窗口
    "set_token_title": {
        LANG_ZH_CN: "设置 Token (JWT 或 API Key)",
        LANG_EN: "Set Token (JWT or API Key)",
        LANG_ZH_TW: "設定 Token (JWT 或 API Key)",
        LANG_JA: "トークン設定 (JWT または API Key)",
        LANG_KO: "토큰 설정 (JWT 또는 API Key)",
        LANG_RU: "Указать токен (JWT или API Key)",
    },
    "set_token_message": {
        LANG_ZH_CN: "粘贴从 PackyCode 获取的 JWT 或 API Key (将以 Bearer 形式发送)",
        LANG_EN: "Paste JWT or API Key from PackyCode (sent as Bearer)",
        LANG_ZH_TW: "貼上從 PackyCode 取得的 JWT 或 API Key（以 Bearer 方式發送）",
        LANG_JA: "PackyCode から取得した JWT または API Key を貼り付け（Bearer で送信）",
        LANG_KO: "PackyCode에서 받은 JWT 또는 API Key를 붙여넣으세요 (Bearer로 전송)",
        LANG_RU: "Вставьте JWT или API Key из PackyCode (отправляется как Bearer)",
    },

    # 更新检查
    "update_found_title": {
        LANG_ZH_CN: "发现新版本",
        LANG_EN: "New Version Found",
        LANG_ZH_TW: "發現新版本",
        LANG_JA: "新しいバージョンを検出",
        LANG_KO: "새 버전 발견",
        LANG_RU: "Найдена новая версия",
    },
    "update_found_message": {
        LANG_ZH_CN: "发现新版本：{tag}\n当前版本：{cur}\n是否前往发布页下载？",
        LANG_EN: "New version: {tag}\nCurrent: {cur}\nOpen releases page?",
        LANG_ZH_TW: "發現新版本：{tag}\n目前版本：{cur}\n是否前往發布頁下載？",
        LANG_JA: "新バージョン：{tag}\n現在：{cur}\nリリースページを開きますか？",
        LANG_KO: "새 버전: {tag}\n현재: {cur}\n릴리스 페이지를 여시겠습니까?",
        LANG_RU: "Новая версия: {tag}\nТекущая: {cur}\nОткрыть страницу релизов?",
    },
    "btn_go": {
        LANG_ZH_CN: "前往",
        LANG_EN: "Open",
        LANG_ZH_TW: "前往",
        LANG_JA: "開く",
        LANG_KO: "열기",
        LANG_RU: "Открыть",
    },
    "btn_ok": {
        LANG_ZH_CN: "确定",
        LANG_EN: "OK",
        LANG_ZH_TW: "確定",
        LANG_JA: "OK",
        LANG_KO: "확인",
        LANG_RU: "ОК",
    },
    # 不再提供在线更新按钮
    "update_changelog_prefix": {
        LANG_ZH_CN: "更新内容：\n{notes}",
        LANG_EN: "Release Notes:\n{notes}",
        LANG_ZH_TW: "更新內容：\n{notes}",
        LANG_JA: "更新内容:\n{notes}",
        LANG_KO: "업데이트 내용:\n{notes}",
        LANG_RU: "Изменения:\n{notes}",
    },
    "update_check_title": {
        LANG_ZH_CN: "检查更新",
        LANG_EN: "Check Updates",
        LANG_ZH_TW: "檢查更新",
        LANG_JA: "更新を確認",
        LANG_KO: "업데이트 확인",
        LANG_RU: "Проверка обновлений",
    },
    "update_latest_message": {
        LANG_ZH_CN: "当前已是最新版本。",
        LANG_EN: "You are up to date.",
        LANG_ZH_TW: "目前已是最新版本。",
        LANG_JA: "最新バージョンです。",
        LANG_KO: "이미 최신 버전입니다.",
        LANG_RU: "У вас последняя версия.",
    },
    "update_check_failed": {
        LANG_ZH_CN: "检查更新失败",
        LANG_EN: "Update Check Failed",
        LANG_ZH_TW: "檢查更新失敗",
        LANG_JA: "更新確認に失敗",
        LANG_KO: "업데이트 확인 실패",
        LANG_RU: "Сбой проверки обновления",
    },

    # 在线更新
    "online_update": {
        LANG_ZH_CN: "在线更新",
        LANG_EN: "Online Update",
        LANG_ZH_TW: "線上更新",
        LANG_JA: "オンライン更新",
        LANG_KO: "온라인 업데이트",
        LANG_RU: "Онлайн-обновление",
    },
    "online_update_not_found": {
        LANG_ZH_CN: "未找到可下载的发行包，请前往发布页手动下载。",
        LANG_EN: "No downloadable asset found. Please download from releases page.",
        LANG_ZH_TW: "未找到可下載的發行包，請前往發布頁手動下載。",
        LANG_JA: "ダウンロード可能なアセットがありません。リリースページから入手してください。",
        LANG_KO: "다운로드 가능한 자산을 찾지 못했습니다. 릴리스 페이지에서 내려받으세요.",
        LANG_RU: "Не найден загружаемый пакет. Скачайте на странице релизов.",
    },
    "online_update_latest_confirm": {
        LANG_ZH_CN: "当前已是最新版本（{cur}）。是否仍然重新安装？",
        LANG_EN: "Already latest ({cur}). Reinstall anyway?",
        LANG_ZH_TW: "目前已是最新版本（{cur}）。是否仍要重新安裝？",
        LANG_JA: "既に最新（{cur}）。再インストールしますか？",
        LANG_KO: "이미 최신({cur}). 그래도 재설치할까요?",
        LANG_RU: "Уже последняя ({cur}). Переустановить?",
    },
    "btn_continue": {
        LANG_ZH_CN: "继续",
        LANG_EN: "Continue",
        LANG_ZH_TW: "繼續",
        LANG_JA: "続行",
        LANG_KO: "계속",
        LANG_RU: "Продолжить",
    },
    "online_update_checksum_failed": {
        LANG_ZH_CN: "校验失败或无法获取校验文件：{err}",
        LANG_EN: "Checksum failed or missing checksum file: {err}",
        LANG_ZH_TW: "校驗失敗或無法取得校驗檔：{err}",
        LANG_JA: "検証失敗または検証ファイル取得不可：{err}",
        LANG_KO: "검증 실패 또는 체크섬 파일 없음: {err}",
        LANG_RU: "Сбой проверки или нет файла контрольной суммы: {err}",
    },
    "online_update_zip_missing": {
        LANG_ZH_CN: ".zip 内未找到 .app 文件。",
        LANG_EN: "No .app found inside the zip.",
        LANG_ZH_TW: ".zip 內未找到 .app 檔案。",
        LANG_JA: "ZIP 内に .app が見つかりません。",
        LANG_KO: "ZIP 안에 .app 파일이 없습니다.",
        LANG_RU: "В ZIP не найдено .app.",
    },
    "online_update_download_done": {
        LANG_ZH_CN: "下载完成",
        LANG_EN: "Download Completed",
        LANG_ZH_TW: "下載完成",
        LANG_JA: "ダウンロード完了",
        LANG_KO: "다운로드 완료",
        LANG_RU: "Загрузка завершена",
    },
    "online_update_manual_replace": {
        LANG_ZH_CN: "已在 Finder 打开，请手动替换应用。",
        LANG_EN: "Opened in Finder. Replace the app manually.",
        LANG_ZH_TW: "已在 Finder 開啟，請手動替換應用程式。",
        LANG_JA: "Finder で開きました。手動で置き換えてください。",
        LANG_KO: "Finder에서 열렸습니다. 앱을 수동으로 교체하세요.",
        LANG_RU: "Открыто в Finder. Замените приложение вручную.",
    },
    "online_update_bundle_mismatch": {
        LANG_ZH_CN: "包标识不一致：当前 {cur}，新包 {new}。已终止。",
        LANG_EN: "Bundle ID mismatch: current {cur}, new {new}. Aborted.",
        LANG_ZH_TW: "套件識別不一致：目前 {cur}，新包 {new}。已終止。",
        LANG_JA: "バンドルID不一致：現在 {cur}、新 {new}。中止。",
        LANG_KO: "번들 ID 불일치: 현재 {cur}, 새 {new}. 중단.",
        LANG_RU: "Несовпадение Bundle ID: текущий {cur}, новый {new}. Операция прервана.",
    },
    "online_update_codesign_failed": {
        LANG_ZH_CN: "签名校验失败（TeamIdentifier/CodeSign 不匹配）。已终止。",
        LANG_EN: "Code signature verification failed (TeamIdentifier/CodeSign). Aborted.",
        LANG_ZH_TW: "簽名驗證失敗（TeamIdentifier/CodeSign 不匹配）。已終止。",
        LANG_JA: "署名検証に失敗（TeamIdentifier/CodeSign 不一致）。中止。",
        LANG_KO: "서명 검증 실패(TeamIdentifier/CodeSign). 중단.",
        LANG_RU: "Сбой проверки подписи (TeamIdentifier/CodeSign). Операция прервана.",
    },
    "online_update_unverified_prompt": {
        LANG_ZH_CN: "签名未通过或未公证，可能不安全。是否继续安装？",
        LANG_EN: "Signature unverifed or not notarized. Continue anyway?",
        LANG_ZH_TW: "簽名未通過或未公證，可能不安全。是否繼續安裝？",
        LANG_JA: "署名未検証または未ノータライズ。続行しますか？",
        LANG_KO: "서명이 검증되지 않았거나 공증되지 않았습니다. 계속하시겠습니까?",
        LANG_RU: "Подпись не проверена или нет нотариата. Продолжить?",
    },
    "online_update_replace_now": {
        LANG_ZH_CN: "更新包已下载，是否立即替换并重启？",
        LANG_EN: "Package downloaded. Replace and restart now?",
        LANG_ZH_TW: "更新包已下載，是否立即替換並重新啟動？",
        LANG_JA: "パッケージをダウンロードしました。今すぐ置換して再起動しますか？",
        LANG_KO: "패키지 다운로드 완료. 지금 교체 후 재시작할까요?",
        LANG_RU: "Пакет скачан. Заменить и перезапустить сейчас?",
    },
    "btn_replace_and_restart": {
        LANG_ZH_CN: "替换并重启",
        LANG_EN: "Replace & Restart",
        LANG_ZH_TW: "替換並重新啟動",
        LANG_JA: "置換して再起動",
        LANG_KO: "교체 및 재시작",
        LANG_RU: "Заменить и перезапустить",
    },
    "btn_later": {
        LANG_ZH_CN: "稍后",
        LANG_EN: "Later",
        LANG_ZH_TW: "稍後",
        LANG_JA: "後で",
        LANG_KO: "나중에",
        LANG_RU: "Позже",
    },
    "online_update_failed": {
        LANG_ZH_CN: "在线更新失败",
        LANG_EN: "Online Update Failed",
        LANG_ZH_TW: "線上更新失敗",
        LANG_JA: "オンライン更新に失敗",
        LANG_KO: "온라인 업데이트 실패",
        LANG_RU: "Сбой онлайн-обновления",
    },

    # 错误
    "error_no_token": {
        LANG_ZH_CN: "未设置 Token，请通过“设置 Token...”配置",
        LANG_EN: "Token not set. Use 'Set Token...'",
        LANG_ZH_TW: "未設定 Token，請透過「設定 Token...」配置",
        LANG_JA: "トークン未設定。『トークンを設定...』から設定",
        LANG_KO: "토큰이 설정되지 않았습니다. '토큰 설정...' 사용",
        LANG_RU: "Токен не задан. Используйте 'Указать токен...'",
    },
    "error_http": {
        LANG_ZH_CN: "调用失败: HTTP {code}",
        LANG_EN: "Request failed: HTTP {code}",
        LANG_ZH_TW: "調用失敗: HTTP {code}",
        LANG_JA: "リクエスト失敗: HTTP {code}",
        LANG_KO: "요청 실패: HTTP {code}",
        LANG_RU: "Ошибка запроса: HTTP {code}",
    },

    # _fmt_remaining
    "rem_expired": {
        LANG_ZH_CN: "已过期",
        LANG_EN: "expired",
        LANG_ZH_TW: "已過期",
        LANG_JA: "期限切れ",
        LANG_KO: "만료됨",
        LANG_RU: "истёк",
    },
    "rem_days_hours": {
        LANG_ZH_CN: "剩余{days}天{hours}小时",
        LANG_EN: "{days}d {hours}h left",
        LANG_ZH_TW: "剩餘{days}天{hours}小時",
        LANG_JA: "残り{days}日{hours}時間",
        LANG_KO: "{days}일 {hours}시간 남음",
        LANG_RU: "ост. {days}д {hours}ч",
    },
    "rem_hours_minutes": {
        LANG_ZH_CN: "剩余{hours}小时{minutes}分钟",
        LANG_EN: "{hours}h {minutes}m left",
        LANG_ZH_TW: "剩餘{hours}小時{minutes}分鐘",
        LANG_JA: "残り{hours}時間{minutes}分",
        LANG_KO: "{hours}시간 {minutes}분 남음",
        LANG_RU: "ост. {hours}ч {minutes}м",
    },
    "rem_minutes": {
        LANG_ZH_CN: "剩余{minutes}分钟",
        LANG_EN: "{minutes}m left",
        LANG_ZH_TW: "剩餘{minutes}分鐘",
        LANG_JA: "残り{minutes}分",
        LANG_KO: "{minutes}분 남음",
        LANG_RU: "ост. {minutes}м",
    },
}


def _t(key: str, **kwargs) -> str:
    # 防御：若打包的旧版本缺失 I18N，避免 NameError
    lang = _current_language
    table = globals().get('I18N', {}).get(key, {})
    text = table.get(lang) or table.get(LANG_ZH_CN)
    if not text:
        text = _fallback_text(key)
    if not text:
        text = key
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def _fallback_text(key: str) -> Optional[str]:
    """在缺少 I18N 表时提供最小中文兜底，避免界面显示 key 名。"""
    zh = {
        # 顶部信息
        "status_uninitialized": "状态：未初始化",
        "daily_placeholder": "每日：-/- (剩余 -)",
        "requests_placeholder": "调用次数：-",
        "usage_span_placeholder": "近30日：-",
        "monthly_placeholder": "每月：-/- (剩余 -)",
        "cycle_placeholder": "周期：-",
        "renew_placeholder": "续费提醒：-",
        "balance_placeholder": "余额：-",
        "last_update_placeholder": "上次更新：-",
        "token_placeholder": "Token：-",
        "version_prefix": "版本：",
        "status_ok": "状态：正常",
        "status_no_data": "状态：无数据",
        "title_no_data": "无数据",
        "title_error": "错误",

        # 菜单
        "menu_refresh": "刷新",
        "menu_account": "账号类型",
        "menu_title_format": "标题格式",
        "menu_language": "语言",
        "menu_set_token": "设置 Token...",
        "menu_toggle_hidden": "隐藏/展示",
        "menu_open_dashboard": "打开控制台",
        "menu_latency_monitor": "延迟监控",
        "menu_check_update": "检查更新",
        "menu_ring": "进度圆环",
        "menu_affiliates": "推广",
        "menu_quit": "退出",

        # 子菜单项
        "account_shared": "共享（公交车）",
        "account_private": "滴滴车（私有）",
        "account_codex": "Codex 公交车",
        "titlefmt_percent": "百分比",
        "titlefmt_custom": "自定义...",
        "titlefmt_show_requests": "显示调用次数",
        "ring_enable": "在图标显示进度圆环",
        "ring_source": "圆环来源",
        "ring_source_daily": "每日进度",
        "ring_source_monthly": "每月进度",
        "ring_colored": "使用彩色圆环",
        "ring_reverse": "反转模式（高亮未使用）",
        "ring_text_enable": "在圆环内显示百分比",
        "ring_text_show_percent": "文本显示百分号",
        "ring_text_show_label": "文本显示来源标签 (D/M)",
        "ring_color_mode": "圆环颜色",
        "ring_color_colorful": "彩色",
        "ring_color_green": "绿色",
        "ring_color_blue": "蓝色",
        "ring_color_gradient": "渐变彩色",

        # 顶部动态模板与前缀
        "last_update_prefix": "上次更新：{time}",
        "requests_prefix": "调用次数：{val}",
        "usage_span_prefix": "近30日：{val}",
        "balance_prefix": "余额：{val}",
        "daily_full": "每日：{spent}/{limit} (剩余 {remain})",
        "daily_no_limit": "每日：{spent}/- (剩余 -)",
        "monthly_full": "每月：{spent}/{limit} (剩余 {remain})",
        "monthly_no_limit": "每月：{spent}/- (剩余 -)",
        "cycle_expired": "周期：{start}-{end}（已到期）",
        "cycle_remaining": "周期：{start}-{end}（剩余{days}天）",
        "renew_expired": "⚠️ 已到期，请尽快续费",
        "renew_soon": "⚠️ 即将到期（剩余{days}天），建议提前续费",
        "renew_prefix": "续费提醒：{text}",
        "title_req_label": "调用",

        # 错误与 Token 提示
        "status_error_prefix": "状态：错误 - {err}",
        "token_expired_label": "Token：已过期（{date}）",
        "token_valid_until": "Token：{date}（{remain}）",
        "notify_token_expired_subtitle": "Token 已过期",
        "notify_token_expired_message": "请在“设置 Token...”中更换 JWT",
        "error_no_token": "未设置 Token，请通过“设置 Token...”配置",
        "error_http": "调用失败: HTTP {code}",
        # 颜色预设无需手动输入

        # 剩余时间
        "rem_expired": "已过期",
        "rem_days_hours": "剩余{days}天{hours}小时",
        "rem_hours_minutes": "剩余{hours}小时{minutes}分钟",
        "rem_minutes": "剩余{minutes}分钟",
    }
    return zh.get(key)


def _format_error(err: Exception | str) -> str:
    if isinstance(err, LocalizedError):
        return err.message()
    if isinstance(err, Exception):
        return str(err)
    return str(err)


def _alert_buttons(title: str, message: str, buttons: list[str]) -> int:
    """显示原生 NSAlert，多按钮无输入框。返回被点击按钮索引（0..n-1）。
    若 NSAlert 不可用，则退化为 rumps.alert，返回 0 或 1。
    """
    try:
        if NSAlert is None:
            # 退化：仅支持 OK/Cancel 两个按钮
            if not buttons:
                buttons = [_t("btn_ok")]
            if len(buttons) == 1:
                rumps.alert(title=title, message=message, ok=buttons[0])
                return 0
            else:
                res = rumps.alert(title=title, message=message, ok=buttons[0], cancel=True)
                return 0 if res else 1
        alert = NSAlert.alloc().init()
        alert.setMessageText_(str(title))
        alert.setInformativeText_(str(message))
        for b in buttons:
            alert.addButtonWithTitle_(str(b))
        # NSAlertFirstButtonReturn == 1000
        code = int(alert.runModal())
        return max(0, code - 1000)
    except Exception:
        # 最简兜底
        rumps.alert(title=title, message=message)
        return 0


# ---------------------------
# 配置与常量
# ---------------------------

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".packycode")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_UPDATE_REPO = "jacksonon/packycode-macos-statusbar"

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
    # 状态栏进度圆环
    "ring_enabled": False,
    # daily | monthly
    "ring_source": "daily",
    # 是否使用彩色圆环（默认系统单色模板）
    "ring_colored": False,
    # 反转模式：高亮未使用（默认高亮已使用）
    "ring_reverse": False,
    # 颜色模式：colorful | green | blue | gradient
    "ring_color_mode": "colorful",
    # 在圆环内显示百分比文字
    "ring_text_enabled": False,
    # 文本是否显示百分号
    "ring_text_percent_sign": True,
    # 文本是否显示来源标签（D/M）
    "ring_text_show_label": False,
    # 圆环文字内容：percent | calls | spent
    "ring_text_mode": "percent",
    # 期望的 Apple TeamIdentifier（可选，用于强校验签名）
    "update_expected_team_id": "",
    # 界面语言
    "language": LANG_ZH_CN,
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
SUBSCRIPTIONS_PATH = "/api/backend/subscriptions?page=1&per_page=5"

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


def get_app_version() -> str:
    # 1) 打包环境：从 Info.plist 读取 CFBundleShortVersionString/CFBundleVersion
    try:
        rp = os.environ.get("RESOURCEPATH")
        if rp:
            plist_path = os.path.join(os.path.dirname(rp), "Info.plist")
            if os.path.exists(plist_path):
                with open(plist_path, "rb") as f:
                    pl = plistlib.load(f)
                v = pl.get("CFBundleShortVersionString") or pl.get("CFBundleVersion")
                if isinstance(v, (str, int, float)):
                    return str(v)
    except Exception:
        pass
    # 2) 源码环境：从 VERSION 文件读取
    try:
        vf = os.path.join(os.path.dirname(__file__), "VERSION")
        if os.path.exists(vf):
            with open(vf, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    # 3) 兜底：尝试从 setup.py 正则提取
    try:
        sp = os.path.join(os.path.dirname(__file__), "setup.py")
        if os.path.exists(sp):
            with open(sp, "r", encoding="utf-8") as f:
                s = f.read()
            m = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", s)
            if m:
                return m.group(1)
    except Exception:
        pass
    return "0.0.0"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


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
        # 应用语言设置
        set_current_language(self._cfg.get("language", LANG_ZH_CN))
        # 使用自定义的本地化“退出”按钮（避免默认 Quit 文案不可本地化）
        try:
            self.quit_button = None
        except Exception:
            pass
        self._lock = threading.RLock()
        self._last_data: Dict[str, Any] = {}
        self._last_error: Optional[Exception] = None
        self._last_usage: Optional[Dict[str, Any]] = None
        self._last_sub_period: Optional[Tuple[datetime.date, datetime.date]] = None
        self._jwt_expired_notified: bool = False
        self._base_icon_path: Optional[str] = icon
        self._ring_icon_path: Optional[str] = os.path.join(CONFIG_DIR, "ring_icon.png")
        self._last_ring_val: Optional[int] = None  # 0..100 整数缓存，避免频繁重绘
        # 圆环图标上次渲染状态签名（包含百分比、配色与文字内容等），用于决定是否需要重绘
        self._last_ring_key: Optional[str] = None

        # 信息区（只读）
        self.info_title = rumps.MenuItem(_t("status_uninitialized"))
        self.info_title.state = 0
        self.info_title.set_callback(None)

        self.info_daily = rumps.MenuItem(_t("daily_placeholder"))
        self.info_daily.set_callback(None)

        self.info_requests = rumps.MenuItem(_t("requests_placeholder"))
        self.info_requests.set_callback(None)

        # 使用统计扩展
        self.info_usage_span = rumps.MenuItem(_t("usage_span_placeholder"))
        self.info_usage_span.set_callback(None)

        self.info_monthly = rumps.MenuItem(_t("monthly_placeholder"))
        self.info_monthly.set_callback(None)

        # 套餐周期与续费提醒
        self.info_cycle = rumps.MenuItem(_t("cycle_placeholder"))
        self.info_cycle.set_callback(None)

        self.info_renew = rumps.MenuItem(_t("renew_placeholder"))
        self.info_renew.set_callback(None)
        self._renew_shown = False

        self.info_balance = rumps.MenuItem(_t("balance_placeholder"))
        self.info_balance.set_callback(None)

        self.info_last = rumps.MenuItem(_t("last_update_placeholder"))
        self.info_last.set_callback(None)

        # Token 到期信息
        self.info_token_exp = rumps.MenuItem(_t("token_placeholder"))
        self.info_token_exp.set_callback(None)

        # 版本信息（底部显示）
        self._version = get_app_version()
        self.info_version = rumps.MenuItem(f"{_t('version_prefix')}{self._version}")
        self.info_version.set_callback(None)

        # 账号类型子菜单（具体项保留对象引用，便于语言切换与勾选）
        self.item_account_shared = rumps.MenuItem(_t("account_shared"), callback=self._set_shared)
        self.item_account_private = rumps.MenuItem(_t("account_private"), callback=self._set_private)
        self.item_account_codex = rumps.MenuItem(_t("account_codex"), callback=self._set_codex)

        # 标题格式子菜单
        self.item_title_percent = rumps.MenuItem(_t("titlefmt_percent"), callback=self._set_title_percent)
        self.item_title_custom = rumps.MenuItem(_t("titlefmt_custom"), callback=self._set_title_custom)
        self.item_title_show_requests = rumps.MenuItem(_t("titlefmt_show_requests"), callback=self._toggle_title_requests)

        # 进度圆环子菜单
        self.item_ring_enable = rumps.MenuItem(_t("ring_enable"), callback=self._toggle_ring_enable)
        self.item_ring_colored = rumps.MenuItem(_t("ring_colored"), callback=self._toggle_ring_colored)
        self.item_ring_src_daily = rumps.MenuItem(_t("ring_source_daily"), callback=self._set_ring_daily)
        self.item_ring_src_monthly = rumps.MenuItem(_t("ring_source_monthly"), callback=self._set_ring_monthly)

        # 推广链接子菜单在重建时动态创建（避免跨菜单复用）
        self.menu_affiliates = None

        # 语言子菜单（采用语言本地名称）
        self.item_lang_zh_cn = rumps.MenuItem("简体中文", callback=lambda _=None: self._set_language(LANG_ZH_CN))
        self.item_lang_en = rumps.MenuItem("English", callback=lambda _=None: self._set_language(LANG_EN))
        self.item_lang_zh_tw = rumps.MenuItem("繁體中文", callback=lambda _=None: self._set_language(LANG_ZH_TW))
        self.item_lang_ja = rumps.MenuItem("日本語", callback=lambda _=None: self._set_language(LANG_JA))
        self.item_lang_ko = rumps.MenuItem("한국어", callback=lambda _=None: self._set_language(LANG_KO))
        self.item_lang_ru = rumps.MenuItem("Русский", callback=lambda _=None: self._set_language(LANG_RU))

        # 完整菜单
        self._rebuild_menu(False)

        # 初始选中账号类型
        self._update_account_checkmarks()
        self._update_title_format_checkmarks()
        self._update_ring_menu_checkmarks()
        self._update_language_checkmarks()
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

    def _rebuild_menu(self, show_renew: bool):
        # 更新版本标签的语言前缀
        self.info_version.title = f"{_t('version_prefix')}{self._version}"

        items = [
            self.info_title,
            self.info_daily,
            self.info_requests,
            self.info_usage_span,
            self.info_monthly,
            self.info_cycle,
        ]
        if show_renew:
            items.append(self.info_renew)
        # 子菜单分组（每次重建时创建全新子项，避免跨菜单重复插入）

        items.extend([
            self.info_balance,
            self.info_token_exp,
            self.info_last,
            None,
            rumps.MenuItem(_t("menu_refresh"), callback=self.refresh_now),
            {_t("menu_account"): self._build_account_menu_items()},
            {_t("menu_title_format"): self._build_title_menu_items()},
            {_t("menu_ring"): self._build_ring_menu_items()},
            {_t("menu_language"): self._build_language_menu_items()},
            rumps.MenuItem(_t("menu_set_token"), callback=self.set_token),
            rumps.MenuItem(_t("menu_toggle_hidden"), callback=self.toggle_hidden),
            rumps.MenuItem(_t("menu_open_dashboard"), callback=self.open_dashboard),
            rumps.MenuItem(_t("menu_latency_monitor"), callback=self.open_latency_monitor),
            rumps.MenuItem(_t("menu_check_update"), callback=self.check_update_now),
            # 移除根目录“在线更新”入口，改由“检查更新”对话框触发
            {_t("menu_affiliates"): self._build_affiliates_menu_items()},
            None,
            rumps.MenuItem(_t("menu_quit"), callback=self.quit_app),
            None,
            self.info_version,
        ])
        # 先清空旧菜单，避免重复绑定 MenuItem
        try:
            self.menu.clear()
        except Exception:
            pass
        self.menu.update(items)
        self._renew_shown = show_renew
        # 确保勾选状态与配置同步
        try:
            self._update_account_checkmarks()
            self._update_title_format_checkmarks()
            self._update_ring_menu_checkmarks()
            self._update_language_checkmarks()
        except Exception:
            pass

    def _build_account_menu_items(self):
        self.item_account_shared = rumps.MenuItem(_t("account_shared"), callback=self._set_shared)
        self.item_account_private = rumps.MenuItem(_t("account_private"), callback=self._set_private)
        self.item_account_codex = rumps.MenuItem(_t("account_codex"), callback=self._set_codex)
        return [self.item_account_shared, self.item_account_private, self.item_account_codex]

    def _build_title_menu_items(self):
        self.item_title_percent = rumps.MenuItem(_t("titlefmt_percent"), callback=self._set_title_percent)
        self.item_title_custom = rumps.MenuItem(_t("titlefmt_custom"), callback=self._set_title_custom)
        self.item_title_show_requests = rumps.MenuItem(_t("titlefmt_show_requests"), callback=self._toggle_title_requests)
        return [self.item_title_percent, self.item_title_custom, self.item_title_show_requests]

    def _build_ring_menu_items(self):
        # 重建每次都刷新文案
        self.item_ring_enable = rumps.MenuItem(_t("ring_enable"), callback=self._toggle_ring_enable)
        self.item_ring_colored = rumps.MenuItem(_t("ring_colored"), callback=self._toggle_ring_colored)
        self.item_ring_reverse = rumps.MenuItem(_t("ring_reverse"), callback=self._toggle_ring_reverse)
        self.item_ring_text_enable = rumps.MenuItem(_t("ring_text_enable"), callback=self._toggle_ring_text)
        self.item_ring_text_show_percent = rumps.MenuItem(_t("ring_text_show_percent"), callback=self._toggle_ring_text_percent)
        self.item_ring_text_show_label = rumps.MenuItem(_t("ring_text_show_label"), callback=self._toggle_ring_text_label)
        self.item_ring_src_daily = rumps.MenuItem(_t("ring_source_daily"), callback=self._set_ring_daily)
        self.item_ring_src_monthly = rumps.MenuItem(_t("ring_source_monthly"), callback=self._set_ring_monthly)
        # 颜色模式
        self.item_ring_color_colorful = rumps.MenuItem(_t("ring_color_colorful"), callback=self._set_ring_color_mode_colorful)
        self.item_ring_color_green = rumps.MenuItem(_t("ring_color_green"), callback=self._set_ring_color_mode_green)
        self.item_ring_color_blue = rumps.MenuItem(_t("ring_color_blue"), callback=self._set_ring_color_mode_blue)
        self.item_ring_color_gradient = rumps.MenuItem(_t("ring_color_gradient"), callback=self._set_ring_color_mode_gradient)
        # 文本模式
        self.item_ring_text_mode_percent = rumps.MenuItem(_t("ring_text_mode_percent"), callback=self._set_ring_text_mode_percent)
        self.item_ring_text_mode_calls = rumps.MenuItem(_t("ring_text_mode_calls"), callback=self._set_ring_text_mode_calls)
        self.item_ring_text_mode_spent = rumps.MenuItem(_t("ring_text_mode_spent"), callback=self._set_ring_text_mode_spent)
        return [
            self.item_ring_enable,
            self.item_ring_colored,
            self.item_ring_reverse,
            self.item_ring_text_enable,
            self.item_ring_text_show_percent,
            self.item_ring_text_show_label,
            {_t("ring_source"): [self.item_ring_src_daily, self.item_ring_src_monthly]},
            {_t("ring_color_mode"): [
                self.item_ring_color_colorful,
                self.item_ring_color_green,
                self.item_ring_color_blue,
                self.item_ring_color_gradient,
            ]},
            {_t("ring_text_mode"): [
                self.item_ring_text_mode_percent,
                self.item_ring_text_mode_calls,
                self.item_ring_text_mode_spent,
            ]},
        ]

    def _build_language_menu_items(self):
        self.item_lang_zh_cn = rumps.MenuItem("简体中文", callback=lambda _=None: self._set_language(LANG_ZH_CN))
        self.item_lang_en = rumps.MenuItem("English", callback=lambda _=None: self._set_language(LANG_EN))
        self.item_lang_zh_tw = rumps.MenuItem("繁體中文", callback=lambda _=None: self._set_language(LANG_ZH_TW))
        self.item_lang_ja = rumps.MenuItem("日本語", callback=lambda _=None: self._set_language(LANG_JA))
        self.item_lang_ko = rumps.MenuItem("한국어", callback=lambda _=None: self._set_language(LANG_KO))
        self.item_lang_ru = rumps.MenuItem("Русский", callback=lambda _=None: self._set_language(LANG_RU))
        return [
            self.item_lang_zh_cn,
            self.item_lang_en,
            self.item_lang_zh_tw,
            self.item_lang_ja,
            self.item_lang_ko,
            self.item_lang_ru,
        ]

    def _build_affiliates_menu_items(self):
        return [
            rumps.MenuItem("PackyCode", callback=self.open_affiliate_packycode),
            rumps.MenuItem("Codex", callback=self.open_affiliate_codex),
        ]

    def _update_language_checkmarks(self):
        lang = self._cfg.get("language", LANG_ZH_CN)
        self.item_lang_zh_cn.state = 1 if lang == LANG_ZH_CN else 0
        self.item_lang_en.state = 1 if lang == LANG_EN else 0
        self.item_lang_zh_tw.state = 1 if lang == LANG_ZH_TW else 0
        self.item_lang_ja.state = 1 if lang == LANG_JA else 0
        self.item_lang_ko.state = 1 if lang == LANG_KO else 0
        self.item_lang_ru.state = 1 if lang == LANG_RU else 0

    def _set_language(self, lang: str):
        with self._lock:
            self._cfg["language"] = lang
            save_config(self._cfg)
            set_current_language(lang)
        # 重建菜单并按新语言更新文案
        self._rebuild_menu(getattr(self, "_renew_shown", False))
        self._update_account_checkmarks()
        self._update_title_format_checkmarks()
        self._update_language_checkmarks()
        self._render_cached_state()
        self._refresh(force=True)

    def _render_cached_state(self) -> None:
        try:
            if self._last_error is not None:
                self._update_ui_error(self._last_error)
            else:
                self._update_ui_from_info(
                    self._last_data or None,
                    self._last_usage,
                    self._last_sub_period,
                )
        except Exception:
            pass

    # ------------- 菜单回调 -------------
    def refresh_now(self, _: Optional[rumps.MenuItem] = None):
        self._refresh(force=True)

    def quit_app(self, _: Optional[rumps.MenuItem] = None):
        try:
            rumps.quit_application()
        except Exception:
            os._exit(0)

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
            title=_t("set_token_title"),
            message=_t("set_token_message"),
            default_text=self._cfg.get("token", ""),
            ok=_t("btn_save"),
            cancel=_t("btn_cancel"),
        )
        res = win.run()
        if res.clicked:
            token = (res.text or "").strip()
            with self._lock:
                self._cfg["token"] = token
                save_config(self._cfg)
                # 重置过期提醒
                self._jwt_expired_notified = False
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

    def open_latency_monitor(self, _: Optional[rumps.MenuItem] = None):
        webbrowser.open("https://packy.te.sb/")

    def open_affiliate_packycode(self, _: Optional[rumps.MenuItem] = None):
        webbrowser.open("https://www.packycode.com/?aff=prr4jxm7")

    def open_affiliate_codex(self, _: Optional[rumps.MenuItem] = None):
        webbrowser.open("https://codex.packycode.com/?aff=prr4jxm7")

    # ------------- 更新检测 -------------
    def _parse_version_tuple(self, v: str) -> Tuple[int, int, int]:
        try:
            v = (v or "").strip()
            v = v.lstrip("vV")
            nums = re.findall(r"\d+", v)
            major = int(nums[0]) if len(nums) > 0 else 0
            minor = int(nums[1]) if len(nums) > 1 else 0
            patch = int(nums[2]) if len(nums) > 2 else 0
            return (major, minor, patch)
        except Exception:
            return (0, 0, 0)

    def _compare_versions(self, a: str, b: str) -> int:
        ta = self._parse_version_tuple(a)
        tb = self._parse_version_tuple(b)
        return (ta > tb) - (ta < tb)

    def check_update_now(self, _: Optional[rumps.MenuItem] = None):
        repo = DEFAULT_UPDATE_REPO
        api = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "PackyCode-StatusBar/1.0",
            }
            resp = requests.get(api, headers=headers, timeout=10)
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code}")
            data = resp.json()
            tag = (data.get("tag_name") or "").strip()
            html_url = (data.get("html_url") or f"https://github.com/{repo}/releases").strip()
            notes = (data.get("body") or "").strip()
            if not tag:
                raise RuntimeError("响应缺少 tag_name")

            cmp = self._compare_versions(tag, self._version)
            if cmp > 0:
                # 构造更新信息（截断备注）
                excerpt = notes
                if len(excerpt) > 1000:
                    excerpt = excerpt[:1000] + "\n..."
                msg = _t("update_found_message", tag=tag, cur=self._version)
                if excerpt:
                    msg = msg + "\n\n" + _t("update_changelog_prefix", notes=excerpt)
                # 仅提供“前往 / 取消”
                choice = _alert_buttons(
                    _t("update_found_title"),
                    msg,
                    [_t("btn_go"), _t("btn_cancel")],
                )
                if choice == 0:
                    webbrowser.open(html_url)
            else:
                _alert_buttons(_t("update_check_title"), _t("update_latest_message"), [_t("btn_ok")])
        except Exception as e:
            _alert_buttons(_t("update_check_failed"), str(e), [_t("btn_ok")])

    # ------------- 在线更新（下载并替换 .app） -------------
    def _latest_release_asset(self, repo: str) -> Optional[Tuple[str, str, str, Optional[str]]]:
        """返回 (tag, html_url, asset_zip_url, sha256_url|None)"""
        api = f"https://api.github.com/repos/{repo}/releases/latest"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "PackyCode-StatusBar/1.0",
        }
        resp = requests.get(api, headers=headers, timeout=10)
        if resp.status_code >= 400:
            return None
        data = resp.json()
        tag = (data.get("tag_name") or "").strip()
        html_url = (data.get("html_url") or f"https://github.com/{repo}/releases").strip()
        assets = data.get("assets") or []
        if not tag or not isinstance(assets, list):
            return None
        cand = None
        sha = None
        for a in assets:
            try:
                name = (a.get("name") or "").lower()
                url = a.get("browser_download_url")
                if name.endswith(".zip") and ("mac" in name or "macos" in name or "osx" in name):
                    cand = url
                    break
            except Exception:
                pass
        if not cand:
            for a in assets:
                try:
                    name = (a.get("name") or "").lower()
                    url = a.get("browser_download_url")
                    if name.endswith(".zip"):
                        cand = url
                        break
                except Exception:
                    pass
        # 寻找 sha256 文件
        for a in assets:
            try:
                name = (a.get("name") or "").lower()
                url = a.get("browser_download_url")
                if name.endswith(".sha256") or name.endswith(".sha256sum") or name.endswith("sha256.txt"):
                    sha = url
                    break
            except Exception:
                pass
        if not cand:
            return None
        return (tag, html_url, cand, sha)

    def _current_app_bundle(self) -> Optional[str]:
        rp = os.environ.get("RESOURCEPATH")
        if not rp:
            return None
        app_path = os.path.abspath(os.path.join(rp, os.pardir, os.pardir))
        if app_path.endswith(".app") and os.path.isdir(app_path):
            return app_path
        return None

    def update_online_now(self, _: Optional[rumps.MenuItem] = None):
        repo = DEFAULT_UPDATE_REPO
        try:
            latest = self._latest_release_asset(repo)
            if not latest:
                _alert_buttons(_t("online_update"), _t("online_update_not_found"), [_t("btn_ok")])
                return
            tag, html_url, download_url, sha_url = latest
            cmp = self._compare_versions(tag, self._version)
            if cmp <= 0:
                choice = _alert_buttons(
                    _t("online_update"),
                    _t("online_update_latest_confirm", cur=self._version),
                    [_t("btn_continue"), _t("btn_cancel")],
                )
                if choice != 0:
                    return
            tmp_dir = tempfile.mkdtemp(prefix="packycode-update-")
            zip_path = os.path.join(tmp_dir, "update.zip")
            with requests.get(download_url, stream=True, timeout=30) as r:
                if r.status_code >= 400:
                    raise RuntimeError(_t("error_http", code=r.status_code))
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            # SHA256 校验（若提供校验文件）
            if sha_url:
                try:
                    resp = requests.get(sha_url, timeout=10)
                    if resp.status_code < 400:
                        text = resp.text.strip()
                        # 提取 64 位 hex
                        m = re.search(r"([a-fA-F0-9]{64})", text)
                        if m:
                            expected = m.group(1).lower()
                            actual = _sha256_file(zip_path)
                            if expected != actual:
                                raise RuntimeError("校验失败：SHA256 不匹配")
                except Exception as e:
                    _alert_buttons(_t("online_update"), _t("online_update_checksum_failed", err=str(e)), [_t("btn_ok")])
                    return
            extract_dir = os.path.join(tmp_dir, "unzipped")
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            new_app = None
            for root, dirs, files in os.walk(extract_dir):
                for d in dirs:
                    if d.endswith('.app'):
                        new_app = os.path.join(root, d)
                        break
                if new_app:
                    break
            if not new_app:
                _alert_buttons(_t("online_update"), _t("online_update_zip_missing"), [_t("btn_ok")])
                return

            target_app = self._current_app_bundle()
            if not target_app:
                # 源码运行，打开解压目录供手动替换
                try:
                    rumps.notification(title=_t("online_update"), subtitle=_t("online_update_download_done"), message=_t("online_update_manual_replace"))
                except Exception:
                    pass
                subprocess.Popen(["open", extract_dir])
                return

            # 读取 bundle id 并校验与当前一致
            def _bundle_id(app: str) -> Optional[str]:
                try:
                    ip = os.path.join(app, 'Contents', 'Info.plist')
                    if os.path.exists(ip):
                        with open(ip, 'rb') as f:
                            pl = plistlib.load(f)
                        bid = pl.get('CFBundleIdentifier')
                        return str(bid) if bid else None
                except Exception:
                    return None
                return None

            cur_bid = _bundle_id(target_app)
            new_bid = _bundle_id(new_app)
            if cur_bid and new_bid and cur_bid != new_bid:
                _alert_buttons(_t("online_update"), _t("online_update_bundle_mismatch", cur=cur_bid, new=new_bid), [_t("btn_ok")])
                return

            # 签名校验：codesign/spctl 与 TeamIdentifier（如配置）
            def _run(cmd: list) -> Tuple[int, str, str]:
                try:
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    return p.returncode, p.stdout, p.stderr
                except Exception as e:
                    return 1, '', str(e)

            # codesign --verify
            rc1, out1, err1 = _run(["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2", new_app])
            # spctl --assess
            rc2, out2, err2 = _run(["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose", new_app])

            expected_team = (self._cfg.get("update_expected_team_id") or "").strip()
            team_ok = True
            if expected_team:
                rc3, _o3, e3 = _run(["/usr/bin/codesign", "-dv", "--verbose=4", new_app])
                tid = None
                if e3:
                    m = re.search(r"TeamIdentifier=([A-Z0-9]+)", e3)
                    if m:
                        tid = m.group(1)
                team_ok = (tid == expected_team)

            if expected_team:
                if not team_ok or rc1 != 0:
                    _alert_buttons(_t("online_update"), _t("online_update_codesign_failed"), [_t("btn_ok")])
                    return
            else:
                # 无强制 team，若校验失败，给出确认提示
                if rc1 != 0 or rc2 != 0:
                    idx = _alert_buttons(_t("online_update"), _t("online_update_unverified_prompt"), [_t("btn_continue"), _t("btn_cancel")])
                    if idx != 0:
                        return

            script_path = os.path.join(tmp_dir, "install.sh")
            script = f"""#!/bin/bash
set -euo pipefail
NEW_APP=\"{new_app}\"
TARGET_APP=\"{target_app}\"
for i in {{1..60}}; do
  if ! pgrep -f \"{os.path.basename(target_app)}\" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
rm -rf \"$TARGET_APP\"
ditto \"$NEW_APP\" \"$TARGET_APP\"
/usr/bin/xattr -dr com.apple.quarantine \"$TARGET_APP\" || true
chmod +x "$TARGET_APP/Contents/MacOS/*" || true
open "$TARGET_APP"
"""
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            idx = _alert_buttons(_t("online_update"), _t("online_update_replace_now"), [_t("btn_replace_and_restart"), _t("btn_later")])
            if idx != 0:
                subprocess.Popen(["open", extract_dir])
                return

            subprocess.Popen(["bash", script_path])
            rumps.quit_application()
        except Exception as e:
            _alert_buttons(_t("online_update_failed"), str(e), [_t("btn_ok")])

    # ------------- 标题格式相关 -------------
    def _update_title_format_checkmarks(self):
        mode = self._cfg.get("title_mode", "percent")
        self.item_title_percent.state = 1 if mode == "percent" else 0
        # 自定义是一个操作项（...），不打勾
        include_requests = bool(self._cfg.get("title_include_requests"))
        self.item_title_show_requests.state = 1 if include_requests else 0

    def _update_ring_menu_checkmarks(self):
        enabled = bool(self._cfg.get("ring_enabled", False))
        src = self._cfg.get("ring_source", "daily")
        colored = bool(self._cfg.get("ring_colored", False))
        reverse = bool(self._cfg.get("ring_reverse", False))
        mode = (self._cfg.get("ring_color_mode") or "colorful").lower()
        show_text = bool(self._cfg.get("ring_text_enabled", False))
        text_mode = (self._cfg.get("ring_text_mode") or "percent").lower()
        try:
            self.item_ring_enable.state = 1 if enabled else 0
            self.item_ring_colored.state = 1 if colored else 0
            self.item_ring_reverse.state = 1 if reverse else 0
            self.item_ring_text_enable.state = 1 if show_text else 0
            # 文本显示细项
            self.item_ring_text_show_percent.state = 1 if bool(self._cfg.get("ring_text_percent_sign", True)) else 0
            self.item_ring_text_show_label.state = 1 if bool(self._cfg.get("ring_text_show_label", False)) else 0
            self.item_ring_src_daily.state = 1 if src == "daily" else 0
            self.item_ring_src_monthly.state = 1 if src == "monthly" else 0
            # 颜色模式勾选
            self.item_ring_color_colorful.state = 1 if mode == "colorful" else 0
            self.item_ring_color_green.state = 1 if mode == "green" else 0
            self.item_ring_color_blue.state = 1 if mode == "blue" else 0
            self.item_ring_color_gradient.state = 1 if mode == "gradient" else 0
            # 文本模式勾选
            self.item_ring_text_mode_percent.state = 1 if text_mode == "percent" else 0
            self.item_ring_text_mode_calls.state = 1 if text_mode == "calls" else 0
            self.item_ring_text_mode_spent.state = 1 if text_mode == "spent" else 0
        except Exception:
            pass

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
        help_text = _t("custom_title_help")
        win = rumps.Window(
            title=_t("custom_title_window"),
            message=help_text,
            default_text=self._cfg.get("title_custom", DEFAULT_CONFIG["title_custom"]),
            ok=_t("btn_save"),
            cancel=_t("btn_cancel"),
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

    # 进度圆环相关
    def _toggle_ring_enable(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_enabled", False))
            self._cfg["ring_enabled"] = not cur
            save_config(self._cfg)
        self._update_ring_menu_checkmarks()
        # 立即渲染
        self._render_cached_state()

    def _set_ring_daily(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_source"] = "daily"
            save_config(self._cfg)
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_monthly(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_source"] = "monthly"
            save_config(self._cfg)
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _toggle_ring_colored(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_colored", False))
            self._cfg["ring_colored"] = not cur
            save_config(self._cfg)
            # 强制下次重绘
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _toggle_ring_reverse(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_reverse", False))
            self._cfg["ring_reverse"] = not cur
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _toggle_ring_text(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_text_enabled", False))
            self._cfg["ring_text_enabled"] = not cur
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _toggle_ring_text_percent(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_text_percent_sign", True))
            self._cfg["ring_text_percent_sign"] = not cur
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _toggle_ring_text_label(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            cur = bool(self._cfg.get("ring_text_show_label", False))
            self._cfg["ring_text_show_label"] = not cur
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_text_mode_percent(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_text_mode"] = "percent"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_text_mode_calls(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_text_mode"] = "calls"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_text_mode_spent(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_text_mode"] = "spent"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_color_mode_colorful(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_color_mode"] = "colorful"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_color_mode_green(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_color_mode"] = "green"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_color_mode_blue(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_color_mode"] = "blue"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    def _set_ring_color_mode_gradient(self, _: Optional[rumps.MenuItem] = None):
        with self._lock:
            self._cfg["ring_color_mode"] = "gradient"
            save_config(self._cfg)
            self._last_ring_val = None
            self._last_ring_key = None
        self._update_ring_menu_checkmarks()
        self._render_cached_state()

    # ------------- 定时逻辑 -------------
    def _on_tick(self, _timer: rumps.Timer):
        self._refresh(force=False)

    # ------------- 内部逻辑 -------------
    def _update_account_checkmarks(self):
        current = self._cfg.get("account_version", "shared")
        self.item_account_shared.state = 1 if current == "shared" else 0
        self.item_account_private.state = 1 if current == "private" else 0
        self.item_account_codex.state = 1 if current == "codex_shared" else 0

    def _get_base_and_dashboard(self) -> Tuple[str, str]:
        account = self._cfg.get("account_version", "shared")
        env = ACCOUNT_ENV.get(account, ACCOUNT_ENV["shared"])  # type: ignore
        return env["base"], env["dashboard"]

    def _update_token_status(self) -> None:
        """更新菜单中的 Token 到期信息，并在过期后提醒一次。"""
        try:
            token = (self._cfg.get("token") or "").strip()
            if not token or not _is_probable_jwt(token):
                self.info_token_exp.title = _t("token_placeholder")
                return
            exp = _extract_exp_from_jwt(token)
            if not exp:
                self.info_token_exp.title = _t("token_placeholder")
                return
            # 本地时间展示
            dt_local = datetime.datetime.fromtimestamp(exp)
            remaining = int(exp - time.time())
            remain_text = _fmt_remaining(remaining)
            if remaining <= 0:
                self.info_token_exp.title = _t("token_expired_label", date=dt_local.strftime('%Y-%m-%d %H:%M'))
                if not self._jwt_expired_notified:
                    try:
                        rumps.notification(
                            title="PackyCode",
                            subtitle=_t("notify_token_expired_subtitle"),
                            message=_t("notify_token_expired_message"),
                        )
                    except Exception:
                        pass
                    self._jwt_expired_notified = True
            else:
                self.info_token_exp.title = _t(
                    "token_valid_until",
                    date=dt_local.strftime('%Y-%m-%d %H:%M'),
                    remain=remain_text,
                )
                # 未过期时允许再次提醒（比如用户换新 Token 后）
                self._jwt_expired_notified = False
        except Exception:
            self.info_token_exp.title = _t("token_placeholder")

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
            # 尝试拉取订阅周期
            try:
                sub_period = self._maybe_fetch_subscription_period()
            except Exception:
                sub_period = None
            self._last_sub_period = sub_period
            self._last_error = None
            self._update_ui_from_info(info, usage, sub_period)
        except Exception as e:
            self._last_error = e
            self._last_sub_period = None
            self._update_ui_error(e)

    def _fetch_user_info(self) -> Optional[Dict[str, Any]]:
        token = (self._cfg.get("token") or "").strip()
        if not token:
            raise LocalizedError("error_no_token")

        base, _dashboard = self._get_base_and_dashboard()
        url = f"{base}{USER_INFO_PATH}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PackyCode-StatusBar/1.0",
        }

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 400:
            raise LocalizedError("error_http", code=resp.status_code)

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

    def _maybe_fetch_subscription_period(self) -> Optional[Tuple[datetime.date, datetime.date]]:
        """调用订阅接口，返回 (current_period_start_date, current_period_end_date)。

        - 优先选取 status == 'active' 的订阅；若无则取第一条。
        - 失败或无数据返回 None。
        """
        token = (self._cfg.get("token") or "").strip()
        if not token:
            return None

        base, _ = self._get_base_and_dashboard()
        url = f"{base}{SUBSCRIPTIONS_PATH}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "PackyCode-StatusBar/1.0",
        }

        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 400:
            return None
        try:
            payload = resp.json()
        except Exception:
            return None

        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list) or not items:
            return None

        selected = None
        for it in items:
            if isinstance(it, dict) and it.get("status") == "active":
                selected = it
                break
        if selected is None:
            selected = items[0] if isinstance(items[0], dict) else None
        if not isinstance(selected, dict):
            return None

        try:
            start_s = (selected.get("current_period_start") or "").replace("Z", "+00:00")
            end_s = (selected.get("current_period_end") or "").replace("Z", "+00:00")
            if not start_s or not end_s:
                return None
            ds = datetime.datetime.fromisoformat(start_s).date()
            de = datetime.datetime.fromisoformat(end_s).date()
            return (ds, de)
        except Exception:
            return None

    def _update_ui_from_info(self, info: Optional[Dict[str, Any]], usage: Optional[Dict[str, Any]], sub_period: Optional[Tuple[datetime.date, datetime.date]]):
        if not info:
            self.info_title.title = _t("status_no_data")
            self.title = "" if self._cfg.get("hidden") else _t("title_no_data")
            self.info_last.title = _t("last_update_prefix", time=now_str())
            self.info_requests.title = _t("requests_prefix", val="-")
            self.info_usage_span.title = _t("usage_span_prefix", val="-")
            self.info_cycle.title = _t("cycle_placeholder")
            self.info_renew.title = _t("renew_placeholder")
            self._update_token_status()
            # 隐藏续费提醒
            if getattr(self, "_renew_shown", False):
                self._rebuild_menu(False)
            # 复位图标
            self._apply_ring_icon(None, None)
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
                        span_desc = _t("usage_span_desc", total=total, avg=round_half_up(total / cnt))
            except Exception:
                span_desc = None

        daily_remaining = max(0.0, daily_limit - daily_spent) if daily_limit else 0.0
        monthly_remaining = max(0.0, monthly_limit - monthly_spent) if monthly_limit else 0.0

        # 更新菜单详情
        self.info_title.title = _t("status_ok")
        self.info_daily.title = (
            _t("daily_full", spent=f"{daily_spent:.2f}", limit=f"{daily_limit:.2f}", remain=f"{daily_remaining:.2f}")
            if daily_limit > 0
            else _t("daily_no_limit", spent=f"{daily_spent:.2f}")
        )
        if today_calls is not None:
            self.info_requests.title = _t("requests_prefix", val=today_calls)
        else:
            self.info_requests.title = _t("requests_prefix", val="-")

        self.info_usage_span.title = _t("usage_span_prefix", val=span_desc) if span_desc else _t("usage_span_placeholder")
        self.info_monthly.title = (
            _t("monthly_full", spent=f"{monthly_spent:.2f}", limit=f"{monthly_limit:.2f}", remain=f"{monthly_remaining:.2f}")
            if monthly_limit > 0
            else _t("monthly_no_limit", spent=f"{monthly_spent:.2f}")
        )

        # 周期与续费提醒（优先使用订阅 current_period_start/end；其次 plan_expires_at；否则按自然月）
        today = datetime.date.today()
        exp_str = (info.get("plan_expires_at") or "").strip() if isinstance(info, dict) else ""
        cycle_start: datetime.date
        cycle_end: datetime.date
        if sub_period and isinstance(sub_period, tuple):
            cycle_start, cycle_end = sub_period
        elif exp_str:
            try:
                iso = exp_str.replace("Z", "+00:00")
                dt_exp = datetime.datetime.fromisoformat(iso)
                cycle_end = dt_exp.date()
                cycle_start = cycle_end.replace(day=1)
            except Exception:
                total_days_fallback = calendar.monthrange(today.year, today.month)[1]
                cycle_start = today.replace(day=1)
                cycle_end = today.replace(day=total_days_fallback)
        else:
            total_days_fallback = calendar.monthrange(today.year, today.month)[1]
            cycle_start = today.replace(day=1)
            cycle_end = today.replace(day=total_days_fallback)

        # 基于周期起止计算天数
        cycle_total_days = (cycle_end - cycle_start).days + 1
        # 将 today 钳制到周期范围内用于“已用天数”
        today_clamped = min(max(today, cycle_start), cycle_end)
        elapsed_days = (today_clamped - cycle_start).days + 1
        days_left = (cycle_end - today).days + 1  # 含今天，可能为<=0

        start_str = f"{cycle_start.month:02d}.{cycle_start.day:02d}"
        end_str = f"{cycle_end.month:02d}.{cycle_end.day:02d}"
        if days_left <= 0:
            self.info_cycle.title = _t("cycle_expired", start=start_str, end=end_str)
        else:
            self.info_cycle.title = _t("cycle_remaining", start=start_str, end=end_str, days=days_left)

        # 续费提醒：到期前 3 天显示；其他时间不显示
        show_renew = days_left <= 3
        if days_left <= 0:
            renew_text = _t("renew_expired")
        elif days_left <= 3:
            renew_text = _t("renew_soon", days=days_left)
        else:
            renew_text = "-"
        self.info_renew.title = _t("renew_prefix", text=renew_text)
        if balance is not None:
            self.info_balance.title = _t("balance_prefix", val=fmt_money(balance))
        else:
            self.info_balance.title = _t("balance_placeholder")

        self.info_last.title = _t("last_update_prefix", time=now_str())
        # 更新 Token 到期信息与提醒
        self._update_token_status()

        # 状态栏标题（根据设置）
        if self._cfg.get("hidden"):
            self.title = ""
            # 仍然更新圆环图标
            d_pct_val = min(100.0, (daily_spent / daily_limit) * 100.0) if daily_limit > 0 else 0.0
            m_pct_val = min(100.0, (monthly_spent / monthly_limit) * 100.0) if monthly_limit > 0 else 0.0
            self._apply_ring_icon(d_pct_val, m_pct_val)
            return

        self.title = self._make_title(info, usage)
        # 更新图标圆环
        d_pct_val = min(100.0, (daily_spent / daily_limit) * 100.0) if daily_limit > 0 else 0.0
        m_pct_val = min(100.0, (monthly_spent / monthly_limit) * 100.0) if monthly_limit > 0 else 0.0
        self._apply_ring_icon(d_pct_val, m_pct_val)
        # 重建菜单以切换“续费提醒”的可见性
        if getattr(self, "_renew_shown", False) != show_renew:
            self._rebuild_menu(show_renew)

    def _update_ui_error(self, err: Exception | str):
        err_text = _format_error(err)
        self.info_title.title = _t("status_error_prefix", err=err_text)
        self.info_last.title = _t("last_update_prefix", time=now_str())
        self.info_requests.title = _t("requests_prefix", val="-")
        self.info_usage_span.title = _t("usage_span_placeholder")
        self.info_cycle.title = _t("cycle_placeholder")
        self.info_renew.title = _t("renew_placeholder")
        self._update_token_status()
        if not self._cfg.get("hidden"):
            self.title = _t("title_error")
        # 错误时复位图标
        self._apply_ring_icon(None, None)
        # 隐藏续费提醒
        if getattr(self, "_renew_shown", False):
            self._rebuild_menu(False)

    # ------------- 标题格式化 -------------
    def _make_title(self, info: Dict[str, Any], usage: Optional[Dict[str, Any]]) -> str:
        # 构造上下文
        daily_limit = parse_float(info.get("daily_budget_usd"))
        daily_spent = parse_float(info.get("daily_spent_usd"))
        monthly_limit = parse_float(info.get("monthly_budget_usd"))
        monthly_spent = parse_float(info.get("monthly_spent_usd"))
        balance_str = info.get("balance_usd")
        balance = parse_float(balance_str) if balance_str is not None else None
        # 从 usage 获取今日调用数
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
                title = f"{title} | {_t('title_req_label')} {ctx['d_req']}"
            return title
        elif mode == "custom":
            tpl = self._cfg.get("title_custom") or DEFAULT_CONFIG["title_custom"]
            title = _safe_format_template(tpl, ctx)
            if include_requests and daily_requests is not None and "{d_req}" not in tpl:
                title = f"{title} | {_t('title_req_label')} {ctx['d_req']}"
            return title
        else:
            # 兜底：百分比
            title = f"D {ctx['d_pct']}% | M {ctx['m_pct']}%"
            if include_requests and daily_requests is not None:
                title = f"{title} | {_t('title_req_label')} {ctx['d_req']}"
            return title

    # ------------- 圆环图标渲染 -------------
    def _compute_ring_text(self, percent: int) -> str:
        """根据当前配置与数据，计算圆环内部需显示的文本。如果未启用则返回空串。"""
        try:
            if not bool(self._cfg.get("ring_text_enabled", False)):
                return ""
            src = (self._cfg.get("ring_source") or "daily").lower()
            mode_txt = (self._cfg.get("ring_text_mode") or "percent").lower()
            if mode_txt == "calls":
                calls = None
                try:
                    u = getattr(self, "_last_usage", None) or {}
                    tu = u.get("today_usage") or {}
                    calls = int(tu.get("api_calls")) if (tu and tu.get("api_calls") is not None) else None
                except Exception:
                    calls = None
                text = str(calls) if calls is not None else "-"
            elif mode_txt == "spent":
                v = None
                try:
                    info = getattr(self, "_last_data", None) or {}
                    if src == "monthly":
                        v = float(info.get("monthly_spent_usd")) if info.get("monthly_spent_usd") is not None else None
                    else:
                        v = float(info.get("daily_spent_usd")) if info.get("daily_spent_usd") is not None else None
                except Exception:
                    v = None
                if v is None:
                    text = "-"
                else:
                    if v >= 1000:
                        text = "999+"
                    elif v >= 10:
                        text = f"{int(v):d}"
                    else:
                        text = f"{v:.1f}"
            else:
                val = int(percent)
                show_pct = bool(self._cfg.get("ring_text_percent_sign", True))
                text = f"{val}%" if show_pct else f"{val}"
            if bool(self._cfg.get("ring_text_show_label", False)):
                prefix = "D" if src != "monthly" else "M"
                text = f"{prefix} {text}"
            return text
        except Exception:
            return ""

    def _apply_ring_icon(self, d_pct: Optional[float], m_pct: Optional[float]) -> None:
        try:
            enabled = bool(self._cfg.get("ring_enabled", False))
            if not enabled:
                # 关闭圆环：恢复非模板图标
                try:
                    self.template = None
                except Exception:
                    pass
                if self._base_icon_path:
                    if self.icon != self._base_icon_path:
                        self.icon = self._base_icon_path
                self._last_ring_val = None
                self._last_ring_key = None
                return

            # 选择来源
            src = (self._cfg.get("ring_source") or "daily").lower()
            val = None
            if src == "monthly":
                val = m_pct
            else:
                val = d_pct
            if val is None:
                # 无数据时恢复基础图标
                if self._base_icon_path and self.icon != self._base_icon_path:
                    self.icon = self._base_icon_path
                self._last_ring_val = None
                return
            iv = int(max(0, min(100, round(val))))
            # 计算当前渲染签名：百分比、配色模式/反转、以及内部文字
            colored = bool(self._cfg.get("ring_colored", False))
            mode = (self._cfg.get("ring_color_mode") or "colorful").lower()
            reverse = bool(self._cfg.get("ring_reverse", False))
            text = self._compute_ring_text(iv)
            cur_key = f"{iv}|{colored}|{mode}|{reverse}|{text}"
            if self._last_ring_key is not None and self._last_ring_key == cur_key:
                return

            # 绘制 PNG，并将应用图标切换为模板模式
            out_path = self._draw_ring_png(iv)
            if out_path and os.path.exists(out_path):
                # 根据配置选择彩色或系统模板着色
                colored = bool(self._cfg.get("ring_colored", False))
                try:
                    self.template = False if colored else True
                except Exception:
                    pass
                self.icon = out_path
                self._last_ring_val = iv
                self._last_ring_key = cur_key
            else:
                # 失败退回基础图标
                try:
                    self.template = None
                except Exception:
                    pass
                if self._base_icon_path:
                    self.icon = self._base_icon_path
                    self._last_ring_val = None
                    self._last_ring_key = None
        except Exception:
            try:
                if self._base_icon_path:
                    self.icon = self._base_icon_path
                    self._last_ring_val = None
                    self._last_ring_key = None
            except Exception:
                pass

    def _draw_ring_png(self, percent: int) -> Optional[str]:
        # 使用 AppKit 绘制进度圆环，导出 PNG 文件，供 rumps 加载为模板图标
        try:
            from AppKit import (
                NSBitmapImageRep,
                NSGraphicsContext,
                NSBezierPath,
                NSColor,
                NSFont,
                NSFontAttributeName,
                NSForegroundColorAttributeName,
                NSParagraphStyleAttributeName,
                NSMutableParagraphStyle,
                NSStrokeWidthAttributeName,
                NSStrokeColorAttributeName,
                NSCalibratedRGBColorSpace,
                NSBitmapImageFileTypePNG,
                NSMakeRect,
            )
            from Foundation import NSString
        except Exception:
            return None

        try:
            # 画布尺寸用 20x20 像素以适配 rumps 的默认大小
            size = 20
            stroke = 2.0
            width = height = int(size)

            rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
                None, width, height, 8, 4, True, False, NSCalibratedRGBColorSpace, 0, 0
            )
            if rep is None:
                return None
            NSGraphicsContext.saveGraphicsState()
            ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
            NSGraphicsContext.setCurrentContext_(ctx)

            rect = NSMakeRect(stroke / 2.0, stroke / 2.0, width - stroke, height - stroke)

            # 轨道（淡色）
            track = NSBezierPath.bezierPathWithOvalInRect_(rect)
            track.setLineWidth_(stroke)
            NSColor.blackColor().colorWithAlphaComponent_(0.25).set()
            track.stroke()

            # 进度弧（从 12 点方向开始，顺时针）
            draw_pct = float(percent)
            try:
                if bool(self._cfg.get("ring_reverse", False)):
                    draw_pct = max(0.0, min(100.0, 100.0 - draw_pct))
            except Exception:
                pass
            angle = 360.0 * (draw_pct / 100.0)
            path = NSBezierPath.bezierPath()
            path.setLineWidth_(stroke)
            path.setLineCapStyle_(1)  # round caps for better look
            try:
                path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_((width / 2.0, height / 2.0), (width - stroke) / 2.0, 90.0, 90.0 - angle, True)
            except Exception:
                path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_((width / 2.0, height / 2.0), (width - stroke) / 2.0, 90.0, 90.0 - angle, True)
            # 颜色：若启用彩色圆环，则按模式着色；否则使用黑色交由模板着色
            try:
                colored = bool(self._cfg.get("ring_colored", False))
            except Exception:
                colored = False
            if colored:
                mode = (self._cfg.get("ring_color_mode") or "colorful").lower()
                if mode == "green":
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.12, 0.75, 0.39, 1.0).set()
                    path.stroke()
                elif mode == "blue":
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.26, 0.52, 0.96, 1.0).set()
                    path.stroke()
                elif mode == "gradient":
                    # 以多段弧模拟渐变
                    segs = max(1, int(max(6.0, angle) / 8.0))
                    for i in range(segs):
                        t0 = float(i) / float(segs)
                        t1 = float(i + 1) / float(segs)
                        a0 = 90.0 - (t0 * angle)
                        a1 = 90.0 - (t1 * angle)
                        seg = NSBezierPath.bezierPath()
                        seg.setLineWidth_(stroke)
                        seg.setLineCapStyle_(1)
                        try:
                            seg.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_((width / 2.0, height / 2.0), (width - stroke) / 2.0, a0, a1, True)
                        except Exception:
                            seg.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_((width / 2.0, height / 2.0), (width - stroke) / 2.0, a0, a1, True)
                        # 颜色从绿->黄->红渐变
                        tm = (t0 + t1) / 2.0
                        if tm <= 0.5:
                            # 绿(0.12,0.75,0.39) 到 黄(1.0,0.84,0.26)
                            k = tm / 0.5
                            r = 0.12 + (1.0 - 0.12) * k
                            g = 0.75 + (0.84 - 0.75) * k
                            b = 0.39 + (0.26 - 0.39) * k
                        else:
                            # 黄(1.0,0.84,0.26) 到 红(0.94,0.33,0.31)
                            k = (tm - 0.5) / 0.5
                            r = 1.0 + (0.94 - 1.0) * k
                            g = 0.84 + (0.33 - 0.84) * k
                            b = 0.26 + (0.31 - 0.26) * k
                        NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0).set()
                        seg.stroke()
                else:
                    # colorful：阈值配色（绿/橙/红按已用百分比）
                    used_pct = float(percent)
                    if used_pct <= 60:
                        col = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.12, 0.75, 0.39, 1.0)
                    elif used_pct <= 85:
                        col = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.00, 0.67, 0.26, 1.0)
                    else:
                        col = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.94, 0.33, 0.31, 1.0)
                    col.set()
                    path.stroke()
            else:
                NSColor.blackColor().set()
                path.stroke()

            # 文字：在圆环内显示内容（百分比/调用次数/使用金额）
            try:
                text = self._compute_ring_text(percent)
                if text:
                    # 字号根据位数微调
                    fs = 8.0 if percent < 100 else 7.0
                    para = NSMutableParagraphStyle.alloc().init()
                    try:
                        para.setAlignment_(1)  # center
                    except Exception:
                        pass
                    # 颜色：模板模式下用黑色（交给系统反色）；彩色模式下用白+黑描边增强对比
                    if bool(self._cfg.get("ring_colored", False)):
                        attrs = {
                            NSFontAttributeName: NSFont.boldSystemFontOfSize_(fs),
                            NSForegroundColorAttributeName: NSColor.whiteColor(),
                            NSStrokeWidthAttributeName: -3.0,
                            NSStrokeColorAttributeName: NSColor.blackColor(),
                            NSParagraphStyleAttributeName: para,
                        }
                    else:
                        attrs = {
                            NSFontAttributeName: NSFont.boldSystemFontOfSize_(fs),
                            NSForegroundColorAttributeName: NSColor.blackColor(),
                            NSParagraphStyleAttributeName: para,
                        }
                    ns_str = NSString.stringWithString_(text)
                    # 文本矩形（略微上移与缩放）
                    trh = 9.0
                    rect_text = NSMakeRect(0.0, (height - trh) / 2.0 - 0.5, width, trh)
                    ns_str.drawInRect_withAttributes_(rect_text, attrs)
            except Exception:
                pass

            NSGraphicsContext.restoreGraphicsState()

            data = rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, None)
            if not data:
                return None
            out_path = self._ring_icon_path or os.path.join(CONFIG_DIR, "ring_icon.png")
            try:
                ensure_config_dir()
            except Exception:
                pass
            ok = data.writeToFile_atomically_(out_path, True)
            if not ok:
                return None
            return out_path
        except Exception:
            return None


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


def _extract_exp_from_jwt(token: str) -> Optional[int]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        pad = '=' * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode((payload_b64 + pad).encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)
        exp = payload.get("exp")
        return int(exp) if exp is not None else None
    except Exception:
        return None


def _fmt_remaining(sec: int) -> str:
    try:
        if sec <= 0:
            return _t("rem_expired")
        days = sec // 86400
        sec %= 86400
        hours = sec // 3600
        sec %= 3600
        minutes = sec // 60
        if days > 0:
            return _t("rem_days_hours", days=days, hours=hours)
        if hours > 0:
            return _t("rem_hours_minutes", hours=hours, minutes=minutes)
        return _t("rem_minutes", minutes=minutes)
    except Exception:
        return "-"


if __name__ == "__main__":
    PackycodeStatusApp().run()
