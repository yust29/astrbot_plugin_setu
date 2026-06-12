"""
AstrBot 色图插件 — 基于 Lolicon API (https://api.lolicon.app)
提供 /st 指令在 QQ 群中发送二次元插画/色图，并支持通过 WebUI 配置 API 参数。
"""

import json
import re
from typing import Optional

import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.message_components import Image, Plain

# ---------------------------------------------------------------------------
# Lolicon API 封装
# ---------------------------------------------------------------------------

DEFAULT_API_URL = "https://api.lolicon.app/setu/v2"


class LoliconAPI:
    """Lolicon API v2 的轻量封装。"""

    @staticmethod
    async def fetch_setu(
        *,
        r18: int = 0,
        num: int = 1,
        keyword: Optional[str] = None,
        tags: Optional[list[list[str]]] = None,
        size: str = "regular",
        proxy: str = "",
        exclude_ai: bool = False,
        api_url: str = "",
        request_proxy: str = "",
    ) -> dict:
        """调用 Lolicon API 获取图片数据。

        Args:
            api_url: 自定义 API 地址，留空则使用默认地址。
            request_proxy: 请求 API 时使用的 HTTP 代理，如 http://127.0.0.1:7890。

        Returns:
            API 返回的完整 JSON dict，含 ``data`` 列表。
        Raises:
            RuntimeError: 网络或 API 报错时抛出。
        """
        url = api_url.strip() if api_url else DEFAULT_API_URL

        payload: dict = {
            "r18": r18,
            "num": num,
            "size": size,
        }
        if keyword:
            payload["keyword"] = keyword
        if tags:
            payload["tag"] = tags
        if proxy:
            payload["proxy"] = proxy
        if exclude_ai:
            payload["excludeAI"] = True

        logger.debug(f"[Setu] 请求 API: {url}, payload={payload}")

        try:
            # 为 aiohttp 会话配置代理
            connector = None
            if request_proxy:
                connector = aiohttp.TCPConnector(force_close=True)
            session_kwargs: dict = {}
            if connector:
                session_kwargs["connector"] = connector

            async with aiohttp.ClientSession(**session_kwargs) as session:
                # 通过 request_proxy 设置代理
                proxy_kwarg = request_proxy.strip() if request_proxy else None
                async with session.post(
                    url,
                    json=payload,
                    proxy=proxy_kwarg,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    body = await resp.json()
        except aiohttp.ClientError as exc:
            hint = ""
            err_str = str(exc)
            if "getaddrinfo failed" in err_str or "Cannot connect to host" in err_str:
                hint = (
                    "\n💡 提示: 无法连接 Lolicon API，可能被网络屏蔽。"
                    "请在 WebUI 插件配置中设置「API 请求代理」(request_proxy)"
                    "或更换「API 请求地址」(api_base_url)。"
                )
            raise RuntimeError(f"网络请求失败: {exc}{hint}") from exc
        except ValueError as exc:
            raise RuntimeError(f"API 返回数据解析失败: {exc}") from exc

        if body.get("error"):
            raise RuntimeError(f"API 返回错误: {body['error']}")
        return body


# ---------------------------------------------------------------------------
# 配置辅助
# ---------------------------------------------------------------------------

def parse_tags(raw: str) -> Optional[list[list[str]]]:
    """将用户输入的标签字符串解析为 Lolicon API 所需的二维数组格式。

    格式:
        - 组内 AND 逻辑: ``"tag1,tag2"``  -> ``[["tag1","tag2"]]``
        - 组间 OR 逻辑:  ``"a,b|c,d"``   -> ``[["a","b"],["c","d"]]``
    """
    if not raw or not raw.strip():
        return None

    groups = raw.strip().split("|")
    result: list[list[str]] = []
    for g in groups:
        items = [t.strip() for t in g.split(",") if t.strip()]
        if items:
            result.append(items)
    return result if result else None


# ---------------------------------------------------------------------------
# 消息构建
# ---------------------------------------------------------------------------

def build_result_message(data: dict) -> str:
    """根据 API 返回的第一条数据构建文字摘要。"""
    item = data
    title = item.get("title", "无标题")
    author = item.get("author", "未知")
    pid = item.get("pid", "N/A")
    width = item.get("width", 0)
    height = item.get("height", 0)
    tags = item.get("tags", [])
    r18 = item.get("r18", False)
    ai_type = item.get("aiType", 0)

    tag_str = "、".join(tags[:6])  # 展示前 6 个 tag
    ai_label = {0: "未知", 1: "AI", 2: "非 AI"}.get(ai_type, "?")
    r18_label = "🔞 R-18" if r18 else "全年龄"

    return (
        f"📷 **{title}**\n"
        f"🎨 作者: {author}  |  PID: {pid}\n"
        f"📐 尺寸: {width}x{height}  |  {r18_label}\n"
        f"🏷️ 标签: {tag_str}\n"
        f"🤖 AI 类型: {ai_label}"
    )


# ---------------------------------------------------------------------------
# 插件主体
# ---------------------------------------------------------------------------

@register("astrbot_plugin_setu", "Rec0ilL", "基于 Lolicon API 的色图/插画发送插件", "1.0.0")
class SetuPlugin(Star):
    """色图插件主类。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        logger.info("[Setu] 插件已加载。")

    # ------------------------------------------------------------------
    # 指令: /st — 获取一张色图
    # ------------------------------------------------------------------
    @filter.command("st")
    async def cmd_st(
        self,
        event: AstrMessageEvent,
        keyword: Optional[str] = None,
    ):
        """获取一张随机色图/插画。可选参数: /st <关键词>"""
        # 合并命令行关键词与默认关键词
        keyword = keyword or self.config.get("keyword", "").strip() or None

        tags_raw = self.config.get("tags", "").strip()
        tags = parse_tags(tags_raw) if tags_raw else None

        try:
            resp = await LoliconAPI.fetch_setu(
                r18=self.config.get("r18", 0),
                num=1,
                keyword=keyword,
                tags=tags,
                size=self.config.get("size", "regular"),
                proxy=self.config.get("proxy", ""),
                exclude_ai=self.config.get("excludeAI", False),
                api_url=self.config.get("api_base_url", ""),
                request_proxy=self.config.get("request_proxy", ""),
            )
        except RuntimeError as exc:
            logger.error(f"[Setu] 请求失败: {exc}")
            yield event.plain_result(f"❌ 获取图片失败: {exc}")
            return

        data_list = resp.get("data", [])
        if not data_list:
            yield event.plain_result("😢 没有找到符合条件的图片，请尝试更换关键词或标签。")
            return

        item = data_list[0]
        text_summary = build_result_message(item)

        # 根据请求的 size 获取对应 URL，若不存在则取 urls 中任意可用 URL
        size = self.config.get("size", "regular")
        urls = item.get("urls", {})
        image_url = urls.get(size) or urls.get("original") or urls.get("regular") or next(iter(urls.values()), "")
        if not image_url:
            logger.error(f"[Setu] 图片 URL 为空，urls 内容: {urls}")
            yield event.plain_result("❌ 图片 URL 为空，请稍后再试。")
            return

        # 发送图片 + 文字信息
        chain = [
            Plain(text_summary),
            Image.fromURL(image_url),
        ]
        yield event.chain_result(chain)

    # ------------------------------------------------------------------
    # 指令组: /st set — 管理配置参数
    # ------------------------------------------------------------------
    @filter.command_group("st")
    def st_group(self):
        pass

    @st_group.command("set")
    async def cmd_st_set(self, event: AstrMessageEvent, param: str = "", value: str = ""):
        """动态设置 API 参数。用法: /st set <参数名> <值>"""
        param = param.strip().lower()
        valid_params = ["r18", "num", "size", "proxy", "excludeai", "keyword", "tags", "api_base_url", "request_proxy"]

        if not param or param not in valid_params:
            tips = "、".join(valid_params)
            yield event.plain_result(
                f"⚠️ 请提供有效参数名。\n"
                f"用法: /st set <参数名> <值>\n"
                f"可用参数: {tips}\n"
                f"示例: /st set r18 0"
            )
            return

        if not value:
            current = self.config.get(param, "（未设置）")
            yield event.plain_result(f"📋 当前 {param} = {current}")
            return

        # 类型转换
        try:
            if param == "r18":
                value = int(value)
                if value not in (0, 1, 2):
                    raise ValueError("r18 必须为 0/1/2")
            elif param == "num":
                value = int(value)
                if not 1 <= value <= 20:
                    raise ValueError("num 范围 1-20")
            elif param == "excludeai":
                value = value.lower() in ("true", "1", "yes", "on")
        except ValueError as exc:
            yield event.plain_result(f"❌ 参数值无效: {exc}")
            return

        self.config[param] = value
        self.config.save_config()
        yield event.plain_result(f"✅ 已将 {param} 设置为 {value}")

    # ------------------------------------------------------------------
    # 指令: /st config — 查看当前配置
    # ------------------------------------------------------------------
    @st_group.command("config")
    async def cmd_st_config(self, event: AstrMessageEvent):
        """查看当前插件配置。"""
        lines = [
            "⚙️ **当前色图插件配置**",
            f"  R18 模式: {self.config.get('r18', 0)}  (0=非R18, 1=仅R18, 2=混合)",
            f"  数量: {self.config.get('num', 1)}",
            f"  尺寸: {self.config.get('size', 'regular')}",
            f"  图片代理: {self.config.get('proxy', '无')}",
            f"  排除AI: {self.config.get('excludeAI', False)}",
            f"  默认关键词: {self.config.get('keyword', '').strip() or '（无）'}",
            f"  默认标签: {self.config.get('tags', '').strip() or '（无）'}",
            f"  API 地址: {self.config.get('api_base_url', '').strip() or '默认'}",
            f"  请求代理: {self.config.get('request_proxy', '').strip() or '（无）'}",
        ]
        yield event.plain_result("\n".join(lines))

    # ------------------------------------------------------------------
    # 指令: /st help — 帮助
    # ------------------------------------------------------------------
    @st_group.command("help")
    async def cmd_st_help(self, event: AstrMessageEvent):
        """显示帮助信息。"""
        msg = (
            "🌟 **色图插件帮助**\n\n"
            "📷 `/st` — 获取一张随机图片\n"
            "📷 `/st <关键词>` — 按关键词搜索图片\n"
            "⚙️ `/st config` — 查看当前配置\n"
            "🛠️ `/st set <参数> <值>` — 动态修改参数\n"
            "   可用参数: r18, num, size, proxy, excludeai, keyword, tags, api_base_url, request_proxy\n"
            "   示例: `/st set size original`\n"
            "ℹ️ `/st help` — 显示本帮助\n\n"
            "🌐 国内网络无法访问 API 时，请在 WebUI 配置页设置:\n"
            "  • request_proxy (HTTP 代理，如 http://127.0.0.1:7890)\n"
            "  • api_base_url (API 镜像/反代地址)\n\n"
            "🔗 API 文档: https://docs.api.lolicon.app"
        )
        yield event.plain_result(msg)

    # ------------------------------------------------------------------
    # 插件卸载
    # ------------------------------------------------------------------
    async def terminate(self):
        """插件被卸载/停用时调用。"""
        logger.info("[Setu] 插件已卸载。")
