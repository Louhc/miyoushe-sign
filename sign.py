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
import json
import requests

# ============ 配置区 ============
COOKIE = os.environ.get("MIYOUSHE_COOKIE", "")
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# 星穹铁道签到配置
ACT_ID = "e202304121516551"
GAME_BIZ = "hkrpg_cn"

# API 地址
ROLE_URL = "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie"
SIGN_URL = "https://api-takumi.mihoyo.com/event/luna/sign"
INFO_URL = "https://api-takumi.mihoyo.com/event/luna/info"

# 候车室（论坛）打卡 API（新域名 miyoushe.com）
BBS_SIGN_URL = "https://bbs-api.miyoushe.com/apihub/app/api/signIn"
BBS_SIGN_INFO_URL = "https://bbs-api.miyoushe.com/apihub/api/getSignInInfo"

# 星穹铁道的 gids (游戏论坛ID)
STAR_RAIL_GID = "6"

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.55.1",
    "Referer": "https://webstatic.mihoyo.com/",
    "Origin": "https://webstatic.mihoyo.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "x-rpc-app_version": "2.55.1",
    "x-rpc-client_type": "5",
    "x-rpc-platform": "ios",
    "x-rpc-device_model": "iPhone",
    "x-rpc-sys_version": "16.0",
}


def generate_device_id():
    """生成随机设备ID"""
    return ''.join(random.choices('0123456789abcdef', k=32))


def generate_ds(body="", query=""):
    """生成DS签名 (DS2算法)"""
    # 最新 salt (2.44.1 web)
    salt = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    text = f"salt={salt}&t={timestamp}&r={random_str}&b={body}&q={query}"
    md5_hash = hashlib.md5(text.encode()).hexdigest()
    return f"{timestamp},{random_str},{md5_hash}"


def generate_ds_simple():
    """生成简单DS签名 (旧版本)"""
    salt = "YVEIkzDFNHLeKXLxzqCA9TzxCpWwbIbk"
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


def get_game_roles(cookies):
    """获取绑定的游戏角色"""
    params = {"game_biz": GAME_BIZ}
    try:
        resp = requests.get(ROLE_URL, headers=HEADERS, cookies=cookies, params=params, timeout=10)
        print(f"获取角色响应: {resp.text[:500]}")
        data = resp.json()
        if data.get("retcode") == 0:
            roles = data.get("data", {}).get("list", [])
            return roles
        else:
            print(f"获取角色失败: retcode={data.get('retcode')}, message={data.get('message')}")
    except Exception as e:
        print(f"获取角色异常: {e}")
    return []


def get_sign_info(cookies, region, game_uid):
    """获取签到信息"""
    params = {
        "act_id": ACT_ID,
        "region": region,
        "uid": game_uid,
        "lang": "zh-cn"
    }
    # 构建 query string 用于 DS
    query = f"act_id={ACT_ID}&lang=zh-cn&region={region}&uid={game_uid}"

    headers = HEADERS.copy()
    headers["DS"] = generate_ds(body="", query=query)
    headers["x-rpc-device_id"] = generate_device_id()
    headers["x-rpc-signgame"] = "hkrpg"

    try:
        resp = requests.get(INFO_URL, headers=headers, cookies=cookies, params=params, timeout=10)
        print(f"签到信息响应: {resp.text[:500]}")
        data = resp.json()
        if data.get("retcode") == 0:
            return data.get("data", {})
        else:
            error_msg = f"retcode={data.get('retcode')}, message={data.get('message')}"
            print(f"获取签到信息失败: {error_msg}")
            return {"error": error_msg}
    except Exception as e:
        print(f"获取签到信息异常: {e}")
        return {"error": str(e)}
    return None


def do_sign(cookies, region, game_uid):
    """执行签到"""
    payload = {
        "act_id": ACT_ID,
        "region": region,
        "uid": game_uid,
        "lang": "zh-cn"
    }
    body = json.dumps(payload, separators=(',', ':'))

    headers = HEADERS.copy()
    headers["DS"] = generate_ds(body=body, query="")
    headers["x-rpc-device_id"] = generate_device_id()
    headers["x-rpc-signgame"] = "hkrpg"
    headers["Content-Type"] = "application/json"

    try:
        resp = requests.post(SIGN_URL, headers=headers, cookies=cookies, json=payload, timeout=10)
        print(f"签到响应: {resp.text}")
        return resp.json()
    except Exception as e:
        print(f"签到请求异常: {e}")
        return {"retcode": -1, "message": str(e)}


def get_bbs_sign_info(cookies):
    """获取候车室打卡信息"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G977N Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36 miHoYoBBS/2.55.1",
        "Referer": "https://app.mihoyo.com",
        "x-rpc-app_version": "2.55.1",
        "x-rpc-client_type": "2",
        "x-rpc-device_id": generate_device_id(),
    }

    params = {"gids": STAR_RAIL_GID}

    # 重试机制
    for attempt in range(3):
        try:
            resp = requests.get(BBS_SIGN_INFO_URL, headers=headers, cookies=cookies, params=params, timeout=30)
            print(f"候车室打卡状态码: {resp.status_code}")
            print(f"候车室打卡信息响应: {resp.text[:500]}")

            # 检查是否为 JSON
            if not resp.text.startswith('{'):
                print(f"响应不是 JSON 格式")
                return {"error": f"非JSON响应: {resp.text[:100]}"}

            data = resp.json()
            if data.get("retcode") == 0:
                return data.get("data", {})
            else:
                error_msg = f"retcode={data.get('retcode')}, message={data.get('message')}"
                print(f"获取打卡信息失败: {error_msg}")
                return {"error": error_msg}
        except Exception as e:
            print(f"获取打卡信息异常 (尝试 {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(3)
            else:
                return {"error": str(e)}


def do_bbs_sign(cookies):
    """执行候车室打卡"""
    # 论坛签到使用的 salt
    salt = "X3txHqSlrpgc7t5vCuTrG2tqhBRO2vME"
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    text = f"salt={salt}&t={timestamp}&r={random_str}"
    ds = f"{timestamp},{random_str},{hashlib.md5(text.encode()).hexdigest()}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G977N Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36 miHoYoBBS/2.55.1",
        "Referer": "https://app.mihoyo.com",
        "x-rpc-app_version": "2.55.1",
        "x-rpc-client_type": "2",
        "x-rpc-device_id": generate_device_id(),
        "DS": ds,
        "Content-Type": "application/json",
    }

    payload = {"gids": STAR_RAIL_GID}

    # 重试机制
    for attempt in range(3):
        try:
            resp = requests.post(BBS_SIGN_URL, headers=headers, cookies=cookies, json=payload, timeout=30)
            print(f"候车室打卡响应: {resp.text}")
            return resp.json()
        except Exception as e:
            print(f"候车室打卡异常 (尝试 {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(3)
            else:
                return {"retcode": -1, "message": str(e)}


def bbs_sign_task(cookies):
    """候车室打卡任务"""
    print("\n" + "=" * 50)
    print("米游社候车室打卡")
    print("=" * 50)

    # 随机延迟
    delay = random.randint(2, 5)
    print(f"等待 {delay} 秒后打卡...")
    time.sleep(delay)

    # 直接执行打卡
    result = do_bbs_sign(cookies)
    retcode = result.get("retcode", -1)
    message = result.get("message", "未知错误")

    if retcode == 0:
        msg = "打卡成功！"
        print(msg)
        return f"候车室: {msg}"
    elif retcode == 1008:
        msg = "今日已打卡"
        print(msg)
        return f"候车室: {msg}"
    else:
        msg = f"打卡失败 (错误码:{retcode}, {message})"
        print(msg)
        return f"候车室: {msg}"


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

    # 打印Cookie关键字段（脱敏）
    print("Cookie 关键字段检查:")
    for key in ['account_id', 'cookie_token', 'ltoken_v2', 'ltuid_v2', 'ltoken', 'ltuid']:
        value = cookies.get(key, '')
        if value:
            print(f"  {key}: {value[:10]}...（已找到）")
        else:
            print(f"  {key}: 未找到")

    # 获取绑定的游戏角色
    print("\n正在获取绑定的游戏角色...")
    roles = get_game_roles(cookies)

    if not roles:
        msg = "未找到绑定的星穹铁道角色<br>请检查：<br>1. Cookie是否完整<br>2. 账号是否绑定了星穹铁道角色"
        print(msg)
        push_wechat("星穹铁道签到失败", msg)
        return

    # 遍历所有角色签到
    results = []
    for role in roles:
        nickname = role.get("nickname", "未知")
        game_uid = role.get("game_uid", "")
        region = role.get("region", "")
        level = role.get("level", 0)

        print(f"\n角色: {nickname} (UID: {game_uid}, 等级: {level}, 服务器: {region})")

        # 获取签到信息
        sign_info = get_sign_info(cookies, region, game_uid)

        if sign_info is None or "error" in sign_info:
            error_detail = sign_info.get("error", "未知错误") if sign_info else "请求失败"
            results.append(f"{nickname}: 获取签到信息失败 ({error_detail})")
            continue

        is_sign = sign_info.get("is_sign", False)
        total_sign_day = sign_info.get("total_sign_day", 0)

        if is_sign:
            msg = f"今日已签到，本月累计 {total_sign_day} 天"
            print(msg)
            results.append(f"{nickname}: {msg}")
            continue

        # 随机延迟
        delay = random.randint(2, 5)
        print(f"等待 {delay} 秒后签到...")
        time.sleep(delay)

        # 执行签到
        result = do_sign(cookies, region, game_uid)
        retcode = result.get("retcode", -1)
        message = result.get("message", "未知错误")

        if retcode == 0:
            new_total = total_sign_day + 1
            msg = f"签到成功！本月累计 {new_total} 天"
            results.append(f"{nickname}: {msg}")
        elif retcode == -5003:
            msg = f"今日已签到，本月累计 {total_sign_day} 天"
            results.append(f"{nickname}: {msg}")
        elif "验证码" in message or retcode == 1034:
            msg = f"触发验证码，请手动签到"
            results.append(f"{nickname}: {msg}")
        else:
            msg = f"签到失败 (错误码:{retcode}, {message})"
            results.append(f"{nickname}: {msg}")

        print(msg)

    # 执行候车室打卡
    bbs_result = bbs_sign_task(cookies)
    results.append(bbs_result)

    # 推送汇总结果
    summary = "<br>".join(results)
    title = "星穹铁道签到完成"
    push_wechat(title, summary)

    print("\n" + "=" * 50)
    print("全部任务完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
