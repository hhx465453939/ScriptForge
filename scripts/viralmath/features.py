"""特征抽取：分句、分词、结构状态、形态判定。

分词近似声明（重要）：
    为避免引入 jieba 等第三方依赖（SPEC §0.1 零依赖），中文采用
    「ASCII 词 + CJK 字符二元组（bigram）」的近似切分。
    该近似对熵 / Zipf / JS 这类**分布型**指标足够（分布形状不受切分粒度影响），
    但**不能**用于词性、句法分析。若后续要做句法层，须另接分词器。

陷阱规避：
  - emoji / 全角标点会污染字数统计 → 字数只计 CJK 与非 emoji 非空白字符
  - 标题抽取不能无脑取第一行（长文第一行常是导语）→ 仅在首行 ≤40 字且非标题标记时视为标题
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import calibration as C

# ------------------------------------------------------------------ 正则
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "\U00002190-\U000021FF"
    "\uFE0F\u200D"
    "]"
)
_ASCII_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")
_TAG_RE = re.compile(r"#[\w\u4e00-\u9fff]{1,30}#?")
_MENTION_RE = re.compile(r"@[\w\u4e00-\u9fff\-]{1,30}")
_HEADING_RE = re.compile(r"^(?:#{1,6}\s|[一二三四五六七八九十]+[、.．]|\d+[、.．]\s)")
_LINE_SPLIT_RE = re.compile(r"\r\n|\r|\n")
_PARA_SPLIT_RE = re.compile(r"\n\s*\n+")


# ------------------------------------------------------------------ 基础切分
def split_sentences(text: str) -> list[str]:
    """按中文句末标点与换行切句，丢弃空白片段。"""
    if not text:
        return []
    buf: list[str] = []
    out: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in C.SENT_SPLIT_CHARS:
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return [s for s in out if _CJK_RE.search(s) or _ASCII_WORD_RE.search(s)]


def split_paragraphs(text: str) -> list[str]:
    """按空行切段；无空行时按单换行切。"""
    if not text:
        return []
    parts = [p.strip() for p in _PARA_SPLIT_RE.split(text) if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in _LINE_SPLIT_RE.split(text) if p.strip()]
    return parts


def count_cjk(text: str) -> int:
    """有效字数：CJK 字符 + ASCII 字母数字，剔除 emoji / 标点 / 空白。"""
    if not text:
        return 0
    stripped = _EMOJI_RE.sub("", text)
    cjk = len(_CJK_RE.findall(stripped))
    ascii_alnum = len(re.findall(r"[A-Za-z0-9]", stripped))
    return cjk + ascii_alnum


def tokenize(text: str) -> list[str]:
    """ASCII 词（小写）+ CJK 二元组。见模块 docstring 的近似声明。"""
    if not text:
        return []
    stripped = _EMOJI_RE.sub(" ", text)
    tokens: list[str] = [w.lower() for w in _ASCII_WORD_RE.findall(stripped)]
    cjk_chars = _CJK_RE.findall(stripped)
    if len(cjk_chars) == 1:
        tokens.append(cjk_chars[0])
    for a, b in zip(cjk_chars, cjk_chars[1:]):
        tokens.append(a + b)
    return tokens


def token_counts(tokens: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return counts


def median_of(xs: list[float]) -> float:
    """中位数。**单一事实来源在 rhythm.median**——此处仅做转发，避免同一逻辑两份实现。"""
    from .rhythm import median as _median
    return _median(xs)


# ------------------------------------------------------------------ 命中计数
def _count_hits(text: str, lexicon) -> int:
    if not text:
        return 0
    n = 0
    for w in lexicon:
        n += text.count(w)
    return n


# 序数 / 枚举后缀：若「第一」后跟这些字符，它是序数或枚举，不是最高级用语
_ORDINAL_TAIL = "天件步次轮个期年月日批层条位季节课章页名句段落周遍部，,、:：;；。. \t\n"

# 「第一」单独出现时绝大多数是序数（第一天）或枚举（第一，… / 第一、…）。
# 只有与明确的最高级语境组合时，才算绝对化用语（相当于宣称“最好”）。
_SUPERLATIVE_FIRST = re.compile(
    r"(?:全国|全球|世界|行业|销量|排名|全网|同类|品类|市场|销量)\s*第一"
    r"|第一\s*(?:品牌|名牌|梯队|大)"
)


def _count_absolute(text: str) -> int:
    """统计绝对化用语，**排除序数与枚举用法**。

    踩过的两个坑（同一根因的两个表现）：
      1. 「第一天 / 第一件事 / 第一步」 → 序数，不是最高级
      2. 「第一，…… 第二，……」 → 枚举，不是最高级（长文总分总结构极常见）
    上一轮只排了序数后缀，枚举依旧被误罚；正解是把**裸「第一」**整体移出绝对化词表，
    只保留明确最高级组合（全国第一 / 销量第一 / 第一品牌）。

    实测后果（修复前）：一篇正常长文 absolute_hits 虚高 → 合规扣分上限 0.30
    → 说服转化维度恒为 0.0000，是假阳性，不是内容差。
    """
    if not text:
        return 0
    n = 0
    for w in C.ABSOLUTE_WORDS:
        if w == "第一":
            continue
        n += text.count(w)
    n += len(_SUPERLATIVE_FIRST.findall(text))
    return n


def _hook_hits(sentences: list[str], limit: int = 3) -> tuple[dict[str, int], float]:
    """前 limit 句内的钩子命中数 + 加权强度。"""
    seg = "".join(sentences[:limit])
    hits: dict[str, int] = {}
    weighted = 0.0
    for kind, words in C.HOOK_LEXICON.items():
        n = _count_hits(seg, words)
        if n:
            hits[kind] = n
            weighted += n * C.HOOK_WEIGHT.get(kind, 1.0)
    return hits, weighted


def _all_hook_hits(text: str) -> dict[str, int]:
    hits: dict[str, int] = {}
    for kind, words in C.HOOK_LEXICON.items():
        n = _count_hits(text, words)
        if n:
            hits[kind] = n
    return hits


def label_structure(sentence: str) -> str:
    """把单句标记为结构功能状态（供马尔可夫熵率使用）。"""
    # CTA 最独特，优先判定
    if _count_hits(sentence, C.CTA_WORDS) > 0:
        return "cta"
    for state in ("hook", "pain", "claim", "evidence"):
        if _count_hits(sentence, C.STRUCTURE_MARKERS[state]) > 0:
            return state
    return "other"


def title_formula(title: str) -> str:
    """判定图文标题公式类型（命中最多者，并列取先）。"""
    if not title:
        return "未判定"
    best, best_n = "未判定", 0
    for name, markers in C.TITLE_FORMULA_MARKERS.items():
        n = sum(title.count(m) for m in markers)
        if n > best_n:
            best, best_n = name, n
    if best_n == 0:
        if _NUMBER_RE.search(title):
            return "数字清单"
        return "未判定"
    return best


# ------------------------------------------------------------------ 形态判定
def detect_genre(text: str) -> dict:
    """按 SPEC-A §4 的优先级短路判定形态。

    返回 {genre, confidence, reason}。
    """
    t = text or ""
    if not t.strip():
        return {"genre": "text", "confidence": "低", "reason": "空文本，按 text 兜底"}

    # 优先级 1：口播元标记
    for marker in ("口播", "镜头", "前3秒", "前 3 秒", "旁白", "字幕", "分镜", "第1秒", "第 1 秒"):
        if marker in t:
            return {"genre": "video", "confidence": "高", "reason": f"命中口播元标记「{marker}」"}

    # 优先级 3：图文信号
    tags = _TAG_RE.findall(t)
    mentions = _MENTION_RE.findall(t)
    emoji_n = len(_EMOJI_RE.findall(t))
    if tags or mentions:
        return {
            "genre": "graphic",
            "confidence": "高",
            "reason": f"命中标签 {len(tags)} 个 / @ 提及 {len(mentions)} 个",
        }
    lines = [ln.strip() for ln in _LINE_SPLIT_RE.split(t) if ln.strip()]
    first_line = lines[0] if lines else ""
    if len(lines) >= 3 and emoji_n >= 3 and count_cjk(first_line) <= 25:
        return {
            "genre": "graphic",
            "confidence": "中",
            "reason": f"首行短（{count_cjk(first_line)}字）+ emoji 密集（{emoji_n}）+ 多行分列",
        }

    # 优先级 4：长文信号
    headings = [ln for ln in lines if _HEADING_RE.match(ln)]
    paras = split_paragraphs(t)
    if headings or "参考文献" in t or re.search(r"图\s?\d|表\s?\d", t):
        return {
            "genre": "text",
            "confidence": "中",
            "reason": f"命中小标题 {len(headings)} 个 / 图表引用 / 参考文献",
        }

    # 优先级 5：口播信号（口语称呼 + 短句密集）
    sents = split_sentences(t)
    avg_len = (sum(count_cjk(s) for s in sents) / len(sents)) if sents else 0.0
    oral = _count_hits(t, frozenset(["姐妹们", "老铁", "宝子", "家人们", "你们", "咱", "我跟你", "说实话", "讲真"]))
    if oral >= 2 and avg_len <= 15:
        return {
            "genre": "video",
            "confidence": "中",
            "reason": f"口语称呼 {oral} 处 + 平均句长 {avg_len:.1f} 字",
        }

    # 优先级 6：兜底
    if avg_len <= 20 and len(paras) <= 5:
        return {"genre": "video", "confidence": "低", "reason": f"兜底：平均句长 {avg_len:.1f} 字，{len(paras)} 段"}
    return {"genre": "text", "confidence": "低", "reason": f"兜底：平均句长 {avg_len:.1f} 字，{len(paras)} 段"}


# ------------------------------------------------------------------ FeatureSet
@dataclass
class FeatureSet:
    # --- 形态与基础
    text: str = ""
    genre: str = "text"
    genre_confidence: str = "低"
    genre_reason: str = ""
    title: str = ""
    n_chars: int = 0

    # --- 分句/分段
    sentences: list[str] = field(default_factory=list)
    sent_lengths: list[float] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    lines_per_para: list[float] = field(default_factory=list)

    # --- 词汇分布
    tokens: list[str] = field(default_factory=list)
    token_counts: dict[str, int] = field(default_factory=dict)

    # --- 标点与符号
    exclaim_count: int = 0
    question_count: int = 0
    dash_count: int = 0
    emoji_count: int = 0

    # --- 冻结节名字段（SPEC-A §5.2 / TRACEABILITY 对齐）
    title_len: int = 0
    para_count: int = 0
    tag_count: int = 0
    median_lines_per_para: float = 0.0
    heading_count: int = 0
    claim_count: int = 0
    evidence_ratio: float = 0.0
    golden_sentence_per_kchar: float = 0.0
    first3_chars: int = 0
    avg_sent_len: float = 0.0
    second_person_count: int = 0
    title_formula: str = "未判定"

    # --- 说服与合规
    trust_hits: int = 0
    number_hits: int = 0
    cta_hits: int = 0
    cta_position_ratio: float = -1.0   # -1 表示无 CTA
    hedge_hits: int = 0
    absolute_hits: int = 0

    # --- 钩子
    hook_hits: dict[str, int] = field(default_factory=dict)      # 前 3 句
    hook_hits_all: dict[str, int] = field(default_factory=dict)  # 全文
    hook_weight_sum: float = 0.0
    first_sent_surprisal: float = 0.0

    # --- 情绪与结构
    emotion_valence: list[float] = field(default_factory=list)
    emotion_arousal: list[float] = field(default_factory=list)
    emotion_hits: int = 0
    structure_states: list[str] = field(default_factory=list)
    structure_labels: list[str] = field(default_factory=list)


def extract(text: str, genre: str = "auto") -> FeatureSet:
    """从原始文本抽取全部特征。genre="auto" 时自动判定形态。"""
    t = (text or "").strip()
    det = detect_genre(t) if genre in ("auto", "", None) else {
        "genre": genre, "confidence": "高", "reason": "用户显式指定"
    }
    g = det["genre"]

    fs = FeatureSet(text=t, genre=g, genre_confidence=det["confidence"], genre_reason=det["reason"])

    fs.sentences = split_sentences(t)
    fs.sent_lengths = [float(count_cjk(s)) for s in fs.sentences]
    fs.paragraphs = split_paragraphs(t)
    fs.para_count = len(fs.paragraphs)
    fs.lines_per_para = [
        float(len([x for x in _LINE_SPLIT_RE.split(p) if x.strip()])) for p in fs.paragraphs
    ]
    fs.median_lines_per_para = median_of(fs.lines_per_para)

    fs.n_chars = count_cjk(t)
    fs.tokens = tokenize(t)
    fs.token_counts = token_counts(fs.tokens)

    fs.exclaim_count = t.count("！") + t.count("!")
    fs.question_count = t.count("？") + t.count("?")
    fs.dash_count = t.count("——") + t.count("—") + t.count("…")
    fs.emoji_count = len(_EMOJI_RE.findall(t))

    # 标题
    lines = [ln.strip() for ln in _LINE_SPLIT_RE.split(t) if ln.strip()]
    first = lines[0] if lines else ""
    if first and count_cjk(first) <= 40 and not _HEADING_RE.match(first) and len(lines) > 1:
        fs.title = first
    elif first and count_cjk(first) <= 40 and len(lines) == 1:
        fs.title = first
    fs.title_len = count_cjk(fs.title)
    fs.title_formula = title_formula(fs.title)

    fs.tag_count = len(_TAG_RE.findall(t))
    fs.heading_count = len([ln for ln in lines if _HEADING_RE.match(ln)])

    fs.avg_sent_len = (sum(fs.sent_lengths) / len(fs.sent_lengths)) if fs.sent_lengths else 0.0
    fs.first3_chars = int(sum(fs.sent_lengths[:3]))
    fs.second_person_count = t.count("你") + t.count("您")

    fs.trust_hits = _count_hits(t, C.TRUST_ANCHOR_WORDS)
    fs.number_hits = len(_NUMBER_RE.findall(t))
    fs.cta_hits = _count_hits(t, C.CTA_WORDS)
    fs.hedge_hits = _count_hits(t, C.HEDGE_WORDS)
    fs.absolute_hits = _count_absolute(t)

    # CTA 相对位置（越靠后 = 越接近 1；无 CTA = -1）
    if fs.sentences and fs.cta_hits:
        positions = [i / max(1, len(fs.sentences) - 1)
                     for i, s in enumerate(fs.sentences) if _count_hits(s, C.CTA_WORDS) > 0]
        fs.cta_position_ratio = sum(positions) / len(positions) if positions else -1.0

    # 钩子
    fs.hook_hits, fs.hook_weight_sum = _hook_hits(fs.sentences, limit=3)
    fs.hook_hits_all = _all_hook_hits(t)

    # 首句 surprisal（在本文自身词分布上，平滑后）
    if fs.sentences and fs.token_counts:
        first_tokens = tokenize(fs.sentences[0])
        total = sum(fs.token_counts.values())
        vocab = len(fs.token_counts)
        from .info import smoothed_probability, surprisal as _surp
        vals = [
            _surp(smoothed_probability(fs.token_counts.get(tk, 0), total, vocab))
            for tk in first_tokens
        ]
        fs.first_sent_surprisal = (sum(vals) / len(vals)) if vals else 0.0

    # 情绪与结构
    for s in fs.sentences:
        val = aro = 0.0
        hit = 0
        for w, (v, a) in C.EMOTION_LEXICON.items():
            n = s.count(w)
            if n:
                hit += n
                val += v * n
                aro += a * n
        fs.emotion_hits += hit
        fs.emotion_valence.append(max(-1.0, min(1.0, val)))
        fs.emotion_arousal.append(max(0.0, min(1.0, aro)))
        lab = label_structure(s)
        fs.structure_labels.append(lab)
        fs.structure_states.append(lab)

    # 长文专属：论点 / 证据 / 金句
    n_claim = sum(1 for lab in fs.structure_labels if lab == "claim")
    n_evidence = sum(1 for lab in fs.structure_labels if lab == "evidence")
    fs.claim_count = n_claim
    fs.evidence_ratio = (n_evidence / n_claim) if n_claim > 0 else 0.0
    if fs.n_chars > 0:
        golden = sum(1 for s in fs.sentences if any(m in s for m in C.GOLDEN_MARKERS))
        fs.golden_sentence_per_kchar = golden * 1000.0 / fs.n_chars

    return fs
