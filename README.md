# 米游社崩坏：星穹铁道自动签到

基于 GitHub Actions 的米游社星穹铁道每日自动签到脚本，支持微信推送通知。

## 功能

- 每日自动签到崩坏：星穹铁道
- 微信推送签到结果（PushPlus）
- 支持手动触发签到

## 使用教程

### 第一步：Fork 本仓库

点击右上角 `Fork` 按钮，将本仓库复制到你的账号下。

### 第二步：获取米游社 Cookie

1. 电脑浏览器打开 https://www.miyoushe.com 并登录
2. 按 `F12` 打开开发者工具
3. 切换到 `Network`（网络）标签
4. 刷新页面
5. 点击任意请求，在 `Request Headers` 中找到 `Cookie`
6. 复制完整的 Cookie 值

### 第三步：获取 PushPlus Token（微信推送）

1. 打开 http://www.pushplus.plus/
2. 微信扫码登录
3. 复制你的 `Token`

### 第四步：配置 GitHub Secrets

1. 进入你 Fork 的仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 添加以下两个 Secret：

| Name | Value |
|------|-------|
| `MIYOUSHE_COOKIE` | 你的米游社 Cookie |
| `PUSHPLUS_TOKEN` | 你的 PushPlus Token |

### 第五步：启用 Actions

1. 进入仓库的 `Actions` 标签页
2. 点击 `I understand my workflows, go ahead and enable them`
3. 点击左侧的 `米游社星穹铁道签到`
4. 点击 `Enable workflow`

### 手动测试

1. 进入 `Actions` 标签页
2. 选择 `米游社星穹铁道签到`
3. 点击 `Run workflow` → `Run workflow`
4. 等待运行完成，检查是否成功

## 定时说明

- 默认每天北京时间 **早上 8:00** 自动运行
- 可修改 `.github/workflows/sign.yml` 中的 `cron` 表达式调整时间
- GitHub Actions 的 cron 使用 UTC 时间，北京时间 = UTC + 8

常用 cron 示例：
```
0 0 * * *   # UTC 0:00 = 北京 8:00
0 1 * * *   # UTC 1:00 = 北京 9:00
0 23 * * *  # UTC 23:00 = 北京 次日7:00
```

## 注意事项

1. **Cookie 有效期**：Cookie 会过期，过期后需要重新获取并更新 Secret
2. **验证码问题**：米游社可能触发验证码，此时需要手动签到
3. **请勿滥用**：仅供学习交流，请勿用于非法用途

## 文件结构

```
├── sign.py                     # 签到脚本
├── .github/
│   └── workflows/
│       └── sign.yml            # GitHub Actions 配置
└── README.md
```

## 免责声明

本项目仅供学习交流使用，使用本脚本造成的任何后果由使用者自行承担。
