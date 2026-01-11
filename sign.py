#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
米游社崩坏：星穹铁道自动签到脚本
"""

import os
import time
import random
import hashlib
import string
import requests

# ============ 配置区 ============
# 从环境变量读取（GitHub Secrets）
COOKIE = os.environ.get("MIYOUSHE_COOKIE", "")
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")  # PushPlus 微信推送

# 星穹铁道签到配置
ACT_ID = "e202304121516551"
SIGN_URL = "https://api-takumi.mihoyo.com/event/luna/sign"
INFO_URL = "https://api-takumi.mihoyo.com/event/luna/info"
REWARD_URL = "https://api-takumi.mihoyo.com/event/luna/home"

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G977N Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36 miHoYoBBS/2.55.1",
    "Referer": "https://webstatic.mihoyo.com/",
    "Origin": "https://webstatic.mihoyo.com",
    "x-rpc-app_version": "2.55.1",
    "x-rpc-client_type": "5",
    "x-rpc-device_id": "",
}


def generate_device_id():
    """生成随机设备ID"""
    return str(hashlib.md5(str(time.time()).encode()).hexdigest())


def generate_ds():
    """生成DS签名"""
    # 米游社 DS 算法 (Salt for version 2.55.1)
    salt = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    text = f"salt={salt}&t={timestamp}&r={random_str}"
    md5_hash = hashlib.md5(text.encode()).hexdigest()

    return f"{timestamp},{random_str},{md5_hash}"


def get_cookie_dict(cookie_str):
    """解析Cookie字符串为字典"""
    cookie_dict = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookie_dict[key.strip()] = value.strip()
    return cookie_dict


def get_uid_region(cookie_dict):
    """获取UID和服务器区域"""
    # 优先使用 ltuid 或 account_id
    uid = cookie_dict.get('ltuid') or cookie_dict.get('account_id') or cookie_dict.get('login_uid', '')
    return uid


def get_sign_info(headers, cookies):
    """获取签到信息"""
    params = {"act_id": ACT_ID}
    try:
        resp = requests.get(INFO_URL, headers=headers, cookies=cookies, params=params, timeout=10)
        data = resp.json()
        if data.get("retcode") == 0:
            return data.get("data", {})
    except Exception as e:
        print(f"获取签到信息失败: {e}")
    return None


def do_sign(headers, cookies):
    """执行签到"""
    payload = {"act_id": ACT_ID}

    headers = headers.copy()
    headers["DS"] = generate_ds()
    headers["x-rpc-device_id"] = generate_device_id()

    try:
        resp = requests.post(SIGN_URL, headers=headers, cookies=cookies, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"签到请求失败: {e}")
        return {"retcode": -1, "message": str(e)}


def push_wechat(title, content):
    """PushPlus 微信推送"""
    if not PUSHPLUS_TOKEN:
        print("未配置 PushPlus Token，跳过推送")
        return

    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }

    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        if result.get("code") == 200:
            print("微信推送成功")
        else:
            print(f"微信推送失败: {result}")
    except Exception as e:
        print(f"微信推送异常: {e}")


def main():
    print("=" * 50)
    print("米游社崩坏：星穹铁道自动签到")
    print("=" * 50)

    if not COOKIE:
        msg = "错误：未配置 MIYOUSHE_COOKIE 环境变量"
        print(msg)
        push_wechat("星穹铁道签到失败", msg)
        return

    # 解析Cookie
    cookies = get_cookie_dict(COOKIE)
    uid = get_uid_region(cookies)

    print(f"当前账号UID: {uid}")

    # 获取签到信息
    sign_info = get_sign_info(HEADERS, cookies)

    if sign_info is None:
        msg = "获取签到信息失败，Cookie可能已过期"
        print(msg)
        push_wechat("星穹铁道签到失败", msg)
        return

    is_sign = sign_info.get("is_sign", False)
    total_sign_day = sign_info.get("total_sign_day", 0)

    if is_sign:
        msg = f"今日已签到，本月累计签到 {total_sign_day} 天"
        print(msg)
        push_wechat("星穹铁道签到提醒", msg)
        return

    # 随机延迟，避免检测
    delay = random.randint(3, 10)
    print(f"等待 {delay} 秒后签到...")
    time.sleep(delay)

    # 执行签到
    result = do_sign(HEADERS, cookies)
    retcode = result.get("retcode", -1)
    message = result.get("message", "未知错误")

    if retcode == 0:
        # 签到成功
        new_total = total_sign_day + 1
        msg = f"签到成功！本月累计签到 {new_total} 天"
        print(msg)
        push_wechat("星穹铁道签到成功", msg)
    elif retcode == -5003:
        # 已经签到过
        msg = f"今日已签到，本月累计签到 {total_sign_day} 天"
        print(msg)
        push_wechat("星穹铁道签到提醒", msg)
    elif "验证码" in message or retcode == 1034:
        # 触发验证码
        msg = f"签到失败：触发验证码，请手动签到或更换IP<br>错误信息: {message}"
        print(msg)
        push_wechat("星穹铁道签到失败", msg)
    else:
        msg = f"签到失败<br>错误码: {retcode}<br>错误信息: {message}"
        print(msg)
        push_wechat("星穹铁道签到失败", msg)

    print("=" * 50)


if __name__ == "__main__":
    main()
