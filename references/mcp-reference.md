# MCP工具引用（精简版）

本文件列出可用的数据采集通道，用于需要外部数据辅助分析时调用。

---

## 数据采集通道

### L1 - SocialDataX MCP（首选）

当需要查找同类视频/竞品内容时使用:

- `socialdatax-xhs` — 小红书笔记搜索/详情/评论/用户/热榜
- `socialdatax-douyin` — 抖音视频搜索/详情/评论/用户/热榜

### L2 - Web 兜底

MCP不可用时自动降级:

- `open-websearch-local` — 通用网页搜索
- `scrapling` — 网页内容抓取
- `bing-search` / `fetch` — 辅助搜索

### L3 - 用户补充

- 本地数据、截图、口述

> **注意:** 本 skill 的核心功能是文案拆解与仿写，外部数据采集为辅助能力。大部分场景下不需要调用MCP。
