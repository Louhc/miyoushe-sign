#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
米游社签到任务
支持：崩坏星穹铁道、原神、崩坏3、绝区零等
"""

import os
import time
import random
import hashlib
import string
import json
import requests

# 从环境变量读取 Cookie
COOKIE = os.environ.get("MIYOUSHE_COOKIE", "")

# 游戏配置
GAMES = {
    "hkrpg": {  # 崩坏：星穹铁道
        "name": "崩坏：星穹铁道",
        "enabled": True,
        "act_id": "e202304121516551",
        "game_biz": "hkrpg_cn",
        "api_type": "luna",
    },
    "hk4e": {  # 原神
        "name": "原神",
        "enabled": True,
        "act_id": "e202009291139501",
        "game_biz": "hk4e_cn",
        "api_type": "bbs_sign_reward",
    },
    "bh3": {  # 崩坏3
        "name": "崩坏3",
        "enabled": False,
        "act_id": "e202207181446311",
        "game_biz": "bh3_cn",
        "api_type": "luna",
    },
    "nap": {  # 绝区零
        "name": "绝区零",
        "enabled": False,
        "act_id": "e202406242138391",
        "game_biz": "nap_cn",
        "api_type": "luna",
    },
}

# API 地址
ROLE_URL = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie"

# 不同游戏使用不同的签到 API
API_URLS = {
    "luna": {
        "sign": "https://api-takumi.mihoyo.com/event/luna/sign",
        "info": "https://api-takumi.mihoyo.com/event/luna/info",
    },
    "bbs_sign_reward": {
        "sign": "https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign",
        "info": "https://api-takumi.mihoyo.com/event/bbs_sign_reward/info",
    },
}

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.55.1",
    "Referer": "https://webstatic.mihoyo.com/",
    "Origin": "https://webstatic.mihoyo.com",
    "Accept": "application/json, text/plain, */*",
    "x-rpc-app_version": "2.55.1",
    "x-rpc-client_type": "5",
    "x-rpc-platform": "ios",
}


def generate_device_id():
    """生成随机设备ID"""
    return ''.join(random.choices('0123456789abcdef', k=32))


def generate_ds(body="", query=""):
    """生成DS签名"""
    salt = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    text = f"salt={salt}&t={timestamp}&r={random_str}&b={body}&q={query}"
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


def get_game_roles(cookies, game_biz):
    """获取绑定的游戏角色"""
    params = {"game_biz": game_biz}
    try:
        resp = requests.get(ROLE_URL, headers=HEADERS, cookies=cookies, params=params, timeout=10)
        data = resp.json()
        if data.get("retcode") == 0:
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"获取角色异常: {e}")
    return []


def get_sign_info(cookies, act_id, region, game_uid, api_type="luna"):
    """获取签到信息"""
    info_url = API_URLS[api_type]["info"]
    params = {
        "act_id": act_id,
        "region": region,
        "uid": game_uid,
        "lang": "zh-cn"
    }
    query = f"act_id={act_id}&lang=zh-cn&region={region}&uid={game_uid}"

    headers = HEADERS.copy()
    headers["DS"] = generate_ds(body="", query=query)
    headers["x-rpc-device_id"] = generate_device_id()

    try:
        resp = requests.get(info_url, headers=headers, cookies=cookies, params=params, timeout=10)
        data = resp.json()
        if data.get("retcode") == 0:
            return data.get("data", {})
    except Exception as e:
        print(f"获取签到信息异常: {e}")
    return None


def do_sign(cookies, act_id, region, game_uid, api_type="luna"):
    """执行签到"""
    sign_url = API_URLS[api_type]["sign"]
    payload = {
        "act_id": act_id,
        "region": region,
        "uid": game_uid,
        "lang": "zh-cn"
    }
    body = json.dumps(payload, separators=(',', ':'))

    headers = HEADERS.copy()
    headers["DS"] = generate_ds(body=body, query="")
    headers["x-rpc-device_id"] = generate_device_id()
    headers["Content-Type"] = "application/json"

    try:
        resp = requests.post(sign_url, headers=headers, cookies=cookies, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"签到请求异常: {e}")
        return {"retcode": -1, "message": str(e)}


def sign_game(game_key: str) -> list:
    """
    执行单个游戏的签到

    Args:
        game_key: 游戏标识 (hkrpg, hk4e, bh3, nap)

    Returns:
        签到结果列表
    """
    game = GAMES.get(game_key)
    if not game:
        return [f"未知游戏: {game_key}"]

    if not game["enabled"]:
        return []

    results = []
    cookies = get_cookie_dict(COOKIE)

    # 获取游戏角色
    roles = get_game_roles(cookies, game["game_biz"])
    if not roles:
        return [f"{game['name']}: 未找到绑定角色"]

    for role in roles:
        nickname = role.get("nickname", "未知")
        game_uid = role.get("game_uid", "")
        region = role.get("region", "")

        # 获取签到信息
        api_type = game.get("api_type", "luna")
        sign_info = get_sign_info(cookies, game["act_id"], region, game_uid, api_type)

        if sign_info is None:
            results.append(f"{game['name']}-{nickname}: 获取签到信息失败")
            continue

        is_sign = sign_info.get("is_sign", False)
        total_sign_day = sign_info.get("total_sign_day", 0)

        if is_sign:
            results.append(f"{game['name']}-{nickname}: 今日已签到，本月累计 {total_sign_day} 天")
            continue

        # 随机延迟
        time.sleep(random.randint(2, 5))

        # 执行签到
        result = do_sign(cookies, game["act_id"], region, game_uid, api_type)
        retcode = result.get("retcode", -1)
        message = result.get("message", "未知错误")

        if retcode == 0:
            results.append(f"{game['name']}-{nickname}: 签到成功！本月累计 {total_sign_day + 1} 天")
        elif retcode == -5003:
            results.append(f"{game['name']}-{nickname}: 今日已签到，本月累计 {total_sign_day} 天")
        else:
            results.append(f"{game['name']}-{nickname}: 签到失败 ({message})")

    return results


def run() -> list:
    """
    执行所有启用的游戏签到

    Returns:
        所有签到结果列表
    """
    print("=" * 50)
    print("米游社游戏签到")
    print("=" * 50)

    if not COOKIE:
        return ["错误：未配置 MIYOUSHE_COOKIE"]

    all_results = []
    for game_key in GAMES:
        results = sign_game(game_key)
        all_results.extend(results)

    return all_results
