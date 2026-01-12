#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送通知模块
支持：Telegram、企业微信群机器人、PushPlus
"""

import os
import re
import requests

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 企业微信群机器人 Webhook
WECOM_WEBHOOK = os.environ.get("WECOM_WEBHOOK", "")

# PushPlus Token (备用)
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")


def html_to_markdown(html: str) -> str:
    """Convert simple HTML to Markdown"""
    text = html
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def push_telegram(title: str, content: str) -> bool:
    """
    Telegram Bot 推送

    Args:
        title: 消息标题
        content: 消息内容 (HTML格式会转换为Markdown)

    Returns:
        是否推送成功
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    # Convert HTML to Markdown
    md_content = html_to_markdown(content)
    message = f"*{title}*\n\n{md_content}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        if result.get("ok"):
            print(f"Telegram推送成功: {title}")
            return True
        else:
            print(f"Telegram推送失败: {result}")
            return False
    except Exception as e:
        print(f"Telegram推送异常: {e}")
        return False


def push_wecom(title: str, content: str) -> bool:
    """
    企业微信群机器人推送

    Args:
        title: 消息标题
        content: 消息内容 (HTML格式会转换为Markdown)

    Returns:
        是否推送成功
    """
    if not WECOM_WEBHOOK:
        return False

    # Convert HTML to Markdown
    md_content = html_to_markdown(content)
    message = f"## {title}\n\n{md_content}"

    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": message
        }
    }

    try:
        resp = requests.post(WECOM_WEBHOOK, json=data, timeout=10)
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"企业微信推送成功: {title}")
            return True
        else:
            print(f"企业微信推送失败: {result}")
            return False
    except Exception as e:
        print(f"企业微信推送异常: {e}")
        return False


def push_pushplus(title: str, content: str, template: str = "html") -> bool:
    """
    PushPlus 微信推送

    Args:
        title: 消息标题
        content: 消息内容
        template: 模板类型 (html, txt, json, markdown)

    Returns:
        是否推送成功
    """
    if not PUSHPLUS_TOKEN:
        return False

    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": template
    }

    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        if result.get("code") == 200:
            print(f"PushPlus推送成功: {title}")
            return True
        else:
            print(f"PushPlus推送失败: {result}")
            return False
    except Exception as e:
        print(f"PushPlus推送异常: {e}")
        return False


def push_wechat(title: str, content: str, template: str = "html") -> bool:
    """
    推送消息 (优先级: Telegram > 企业微信 > PushPlus)

    Args:
        title: 消息标题
        content: 消息内容
        template: 模板类型

    Returns:
        是否推送成功
    """
    # 优先使用 Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        return push_telegram(title, content)

    # 企业微信
    if WECOM_WEBHOOK:
        return push_wecom(title, content)

    # 备用 PushPlus
    if PUSHPLUS_TOKEN:
        return push_pushplus(title, content, template)

    print("未配置任何推送方式")
    return False
