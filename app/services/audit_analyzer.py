"""Audit Analyzer - natural language interface for audit data."""
import re
from datetime import datetime, timedelta
from typing import Any

from app.db.clickhouse import get_clickhouse


class AuditAnalyzer:
    """Analyze audit data through natural language questions."""

    def __init__(self, user_id: int, username: str):
        self.user_id = user_id
        self.username = username
        self.client = get_clickhouse()

    async def analyze(self, question: str) -> str:
        """Main entry: parse question and generate answer."""
        q = question.lower().strip()

        # Intent routing
        if self._match(q, ["最多token", "最活跃", "谁用了最多", "top user", "most active", "most tokens"]):
            return await self._top_users()

        if self._match(q, ["风险", "risk", "告警", "alert", "异常", "安全问题"]):
            return await self._risk_events()

        if self._match(q, ["模型", "model", "哪个模型", "model usage", "热门模型"]):
            return await self._model_stats()

        if self._match(q, ["趋势", "trend", "最近几天", "这几天", "走势", "变化"]):
            return await self._usage_trend()

        if self._match(q, ["我的", "我自己", "my usage", "我用了多少", "我的调用"]):
            return await self._my_usage()

        if self._match(q, ["统计", "summary", "概览", "dashboard", "总体", "总计", "一共多少", "总请求", "总token"]):
            return await self._summary_stats()

        if self._match(q, ["帮助", "help", "你能做什么", "会什么", "功能"]):
            return self._help_message()

        # Fallback: try to answer with summary
        return await self._summary_stats()

    def _match(self, q: str, keywords: list[str]) -> bool:
        for kw in keywords:
            if kw.lower() in q:
                return True
        return False

    def _help_message(self) -> str:
        return (
            "🤖 **审计分析助手**\n\n"
            "我可以帮你分析审计数据库，支持以下查询：\n\n"
            "- **总体统计**：最近7天/30天的总请求数、总Token数、活跃用户等\n"
            "- **用户排行**：谁是最活跃的用户，谁消耗了最多的Token\n"
            "- **模型分析**：哪个模型最受欢迎，各模型的调用分布\n"
            "- **风险告警**：最近的风险事件、异常访问、安全告警\n"
            "- **趋势走势**：最近几天的调用量和Token消耗趋势\n"
            "- **个人用量**：你自己的调用记录和配额使用情况\n\n"
            "请直接输入你的问题，例如：\"最近7天谁用了最多token？\""
        )

    async def _summary_stats(self) -> str:
        """Dashboard-like summary."""
        # Today
        result = self.client.execute(
            "SELECT count(), sum(total_tokens), uniqExact(user_id) FROM audit_logs WHERE toDate(timestamp) = today()"
        )
        today_reqs, today_tokens, today_users = result[0] if result else (0, 0, 0)

        # Last 7 days
        result = self.client.execute(
            "SELECT count(), sum(total_tokens), uniqExact(user_id) FROM audit_logs WHERE timestamp >= now() - INTERVAL 7 DAY"
        )
        week_reqs, week_tokens, week_users = result[0] if result else (0, 0, 0)

        # Risk events today
        result = self.client.execute(
            "SELECT count() FROM risk_events WHERE toDate(timestamp) = today()"
        )
        today_risks = result[0][0] if result else 0

        return (
            f"📊 **审计数据概览**\n\n"
            f"**今日**\n"
            f"- 请求数：`{today_reqs or 0}`\n"
            f"- Token 消耗：`{today_tokens or 0}`\n"
            f"- 活跃用户：`{today_users or 0}`\n"
            f"- 风险事件：`{today_risks or 0}`\n\n"
            f"**近7天**\n"
            f"- 请求数：`{week_reqs or 0}`\n"
            f"- Token 消耗：`{week_tokens or 0}`\n"
            f"- 活跃用户数：`{week_users or 0}`\n"
        )

    async def _top_users(self) -> str:
        """Top users by tokens."""
        result = self.client.execute(
            """
            SELECT user_name, count(), sum(total_tokens), avg(latency_ms)
            FROM audit_logs
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY user_name
            ORDER BY sum(total_tokens) DESC
            LIMIT 5
            """
        )
        if not result:
            return "近7天暂无语义数据。"

        lines = ["🏆 **近7天最活跃用户（按 Token 消耗）**\n"]
        for i, row in enumerate(result, 1):
            lines.append(
                f"{i}. **{row[0]}** — 请求数 `{row[1]}`，Token `{row[2]}`，平均延迟 `{int(row[3] or 0)}ms`"
            )
        return "\n".join(lines)

    async def _risk_events(self) -> str:
        """Recent risk events."""
        result = self.client.execute(
            """
            SELECT risk_level, count(), sum(is_resolved)
            FROM risk_events
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY risk_level
            ORDER BY count() DESC
            """
        )
        if not result:
            return "近7天暂无风险事件。"

        lines = ["🚨 **近7天风险告警统计**\n"]
        total = 0
        resolved = 0
        for row in result:
            level, cnt, res = row
            total += cnt
            resolved += res
            lines.append(f"- **{level}**：`{cnt}` 条（已处理 `{int(res)}`）")

        lines.append(f"\n总计：`{total}` 条风险事件，已处理 `{int(resolved)}` 条，待处理 `{total - int(resolved)}` 条。")

        # Recent 3 details
        details = self.client.execute(
            """
            SELECT risk_level, risk_reason, description, user_name, is_resolved
            FROM risk_events
            WHERE timestamp >= now() - INTERVAL 7 DAY
            ORDER BY timestamp DESC
            LIMIT 3
            """
        )
        if details:
            lines.append("\n**最新风险事件：**")
            for d in details:
                status = "✅ 已处理" if d[4] else "⚠️ 待处理"
                lines.append(f"- [{d[0]}] {d[1]} — {d[2]}（用户：{d[3]}）{status}")

        return "\n".join(lines)

    async def _model_stats(self) -> str:
        """Model usage stats."""
        result = self.client.execute(
            """
            SELECT model_name, count(), sum(total_tokens)
            FROM audit_logs
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY model_name
            ORDER BY count() DESC
            LIMIT 5
            """
        )
        if not result:
            return "近7天暂无模型调用数据。"

        lines = ["🤖 **近7天模型使用排行**\n"]
        for i, row in enumerate(result, 1):
            lines.append(f"{i}. **{row[0]}** — 请求 `{row[1]}`，Token `{row[2]}`")
        return "\n".join(lines)

    async def _usage_trend(self) -> str:
        """7-day trend."""
        result = self.client.execute(
            """
            SELECT toDate(timestamp) as date, count(), sum(total_tokens)
            FROM audit_logs
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY date
            ORDER BY date
            """
        )
        if not result:
            return "近7天暂无趋势数据。"

        lines = ["📈 **近7天调用趋势**\n"]
        lines.append("| 日期 | 请求数 | Token 消耗 |")
        lines.append("|------|--------|------------|")
        for row in result:
            date_str = row[0].strftime("%Y-%m-%d") if hasattr(row[0], "strftime") else str(row[0])
            lines.append(f"| {date_str} | {row[1]} | {row[2]} |")
        return "\n".join(lines)

    async def _my_usage(self) -> str:
        """Current user's usage."""
        result = self.client.execute(
            """
            SELECT count(), sum(total_tokens), avg(latency_ms)
            FROM audit_logs
            WHERE user_id = %(user_id)s
              AND timestamp >= now() - INTERVAL 7 DAY
            """,
            {"user_id": self.user_id}
        )
        row = result[0] if result else (0, 0, 0)

        result2 = self.client.execute(
            """
            SELECT count(), sum(total_tokens)
            FROM audit_logs
            WHERE user_id = %(user_id)s
              AND toDate(timestamp) = today()
            """,
            {"user_id": self.user_id}
        )
        today = result2[0] if result2 else (0, 0)

        return (
            f"👤 **你的调用统计（{self.username}）**\n\n"
            f"**今日**\n"
            f"- 请求数：`{today[0] or 0}`\n"
            f"- Token 消耗：`{today[1] or 0}`\n\n"
            f"**近7天**\n"
            f"- 请求数：`{row[0] or 0}`\n"
            f"- Token 消耗：`{row[1] or 0}`\n"
            f"- 平均延迟：`{int(row[2] or 0)}ms`\n"
        )
