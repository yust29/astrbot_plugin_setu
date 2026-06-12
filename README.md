# astrbot_plugin_setu

[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-blue)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)]()

基于 [Lolicon API](https://docs.api.lolicon.app) 的 AstrBot 色图/插画发送插件，支持在 QQ 群聊中一键获取精美二次元图片，并可通过 WebUI 灵活配置所有 API 参数。

---

## ✨ 功能特性

- 📷 **一键获取** — `/st` 指令快速获取随机插画/色图
- 🔍 **关键词搜索** — 支持按关键词搜索指定主题图片
- ⚙️ **可视化配置** — 在 AstrBot WebUI 中直接修改所有 API 参数
- 🏷️ **标签过滤** — 支持复杂的 AND/OR 标签组合过滤
- 🚫 **R18 控制** — 三种模式：仅非 R18 / 仅 R18 / 混合
- 🤖 **AI 排除** — 可选择排除 AI 生成作品
- 🌐 **代理支持** — 可配置图片代理域名和 API 请求代理，解决国内网络访问问题
- 🔧 **动态调参** — 无需重启，通过指令实时修改配置

---

## 📥 安装

### 方式一：WebUI 安装（推荐）

1. 在 AstrBot WebUI 中进入「插件管理」
2. 点击「安装插件」→ 上传 `astrbot_plugin_setu.zip`
3. 等待安装完成，插件即自动加载

### 方式二：手动安装

```bash
cd AstrBot/data/plugins
git clone https://github.com/yust29/astrbot_plugin_setu.git
# 或将插件文件夹直接放入 plugins 目录
```

---

## 🎮 指令说明

| 指令 | 说明 | 示例 |
|------|------|------|
| `/setu` | 获取一张随机图片 | `/st` |
| `/setu <关键词>` | 按关键词搜索 | `/st 初音未来` |
| `/st config` | 查看当前配置 | `/st config` |
| `/st set <参数> <值>` | 修改配置参数 | `/st set r18 0` |
| `/st set <参数>` | 查看参数当前值 | `/st set size` |
| `/st help` | 显示帮助信息 | `/st help` |

---

## ⚙️ 配置参数

以下参数可在 AstrBot WebUI「插件管理 → 色图插件 → 配置」中修改：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `r18` | int | `0` | R18 模式：`0` 仅非 R18 / `1` 仅 R18 / `2` 混合 |
| `num` | int | `1` | 每次获取数量，范围 1-20 |
| `size` | string | `regular` | 图片尺寸：`original` / `regular` / `small` / `thumb` / `mini` |
| `proxy` | string | `i.pixiv.re` | 图片代理域名，留空则不使用代理 |
| `excludeAI` | bool | `false` | 是否排除 AI 生成作品 |
| `keyword` | string | (空) | 默认搜索关键词，多个用逗号分隔（OR 逻辑） |
| `tags` | string | (空) | 默认标签过滤，格式详见下方说明 |
| `api_base_url` | string | (空) | 自定义 API 地址，国内网络无法直连时使用镜像/反代地址 |
| `request_proxy` | string | (空) | 请求 API 时使用的 HTTP 代理，如 `http://127.0.0.1:7890` |

### 🌐 国内网络注意事项

由于 `api.lolicon.app` 在国内可能被 DNS 污染或封锁，如果出现 `getaddrinfo failed` 错误，请通过以下方式解决：

1. **设置请求代理** — 将 `request_proxy` 设为你的 HTTP 代理地址（如 Clash/V2Ray 的 `http://127.0.0.1:7890`）
2. **使用 API 镜像** — 将 `api_base_url` 设为可访问的镜像/反代地址

### 标签格式说明

```
组内 AND:  "甘雨,原神"       → (甘雨 AND 原神)
组间 OR:   "甘雨,原神|刻晴,原神" → (甘雨 AND 原神) OR (刻晴 AND 原神)
```

---

## 📡 API 参考

本插件基于 [Lolicon API v2](https://docs.api.lolicon.app/#/setu) 构建。

**请求端点**: `POST https://api.lolicon.app/setu/v2`

返回的图片数据包含作者、标题、PID、标签、尺寸等信息，插件会自动将其整理为图文消息发送。

---

## 🖥️ 兼容平台

- ✅ OneBot v11 (aiocqhttp) — QQ 个人号
- ✅ QQ 官方机器人 (qq_official)
- ✅ QQ 官方 Webhook (qq_official_webhook)

---

## 🛠️ 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 在 AstrBot 项目中调试
# 将本目录放入 AstrBot/data/plugins/ 后启动 AstrBot
```

依赖项：

- `aiohttp >= 3.9.0`

---

## 📄 License

GNU Affero General Public License v3.0

> ⚠️ 请合理使用本插件，遵守相关法律法规及平台使用条款。使用者需自行对获取和传播的内容负责。

---

## 🙏 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 多平台智能助手框架
- [Lolicon API](https://docs.api.lolicon.app) — 二次元图片 API 服务
