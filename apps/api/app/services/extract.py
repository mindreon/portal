"""
合同/发票草稿要素。

正文不再用正则抠字段：每一页交给通义千问理解，这里只负责
- 把模型 JSON 转成类型
- 把多页结果合并
- 判断草稿信息是否已经齐了（齐了就停止翻页）
- 入库时按编号/指纹分堆
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

# 草稿需要从合同里尽量抽全的字段。模型说还缺其中某项时继续翻页。
CONTRACT_DRAFT_KEYS = (
    "contract_no",
    "party_a",
    "party_b",
    "subject_name",
    "amount",
    "signed_at",
    "start_date",
    "end_date",
    "schedules",
)
# 我方主体固定，用来从甲/乙名称自动判断角色，页面上不必再选手动选。
OUR_COMPANY_MARKERS = ("迈能同行",)
# 封面标题、保密条款里常见的空泛说法，不能当采购物。
_GENERIC_SUBJECTS = {
    "软件产品",
    "软件",
    "硬件",
    "产品",
    "服务",
    "货物",
    "设备",
    "项目",
    "系统",
    "产品及服务",
    "产品和服务",
    "产品或服务",
    "产品及或服务",
    "软硬件",
    "相关产品",
    "相关服务",
    "技术服务",
    "销售",
    "采购",
    "信息技术服务",
    "信息化建设",
}
_SUBJECT_COMPANY_MARKERS = ("有限公司", "股份有限", "集团有限", "医院", "大学")
_SUBJECT_PUNCT_RE = re.compile(r"[\s、，,。；;：:：/／\\（）()【】\[\]\-—_]+")
INVOICE_DRAFT_KEYS = ("invoice_code", "invoice_no", "invoices", "amount")
KNOWN_STILL_NEEDED = set(CONTRACT_DRAFT_KEYS) | set(INVOICE_DRAFT_KEYS) | {"title"}


@dataclass
class ExtractedInvoice:
    invoice_code: str = ""
    invoice_no: str = ""
    amount: Decimal | None = None


@dataclass
class ExtractedSchedule:
    name: str
    percent: int | None = None
    amount: Decimal | None = None


@dataclass
class ExtractedFields:
    doc_type: str = "unknown"  # contract | invoice | unknown
    contract_no: str = ""
    extra_contract_nos: list[str] = field(default_factory=list)
    title: str = ""
    party_a: str = ""
    party_b: str = ""
    subject_name: str = ""
    amount: Decimal | None = None
    signed_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    invoices: list[ExtractedInvoice] = field(default_factory=list)
    schedules: list[ExtractedSchedule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_date(raw: str | None) -> date | None:
    """把模型返回的日期字符串变成 date。不是对合同正文做标签匹配。"""
    if not raw:
        return None
    digits = re.findall(r"\d+", raw)
    if len(digits) < 3:
        return None
    try:
        return date(int(digits[0]), int(digits[1]), int(digits[2]))
    except ValueError:
        return None


def parse_money(raw: str | None) -> Decimal | None:
    """把模型返回的金额字符串变成 Decimal。"""
    if not raw:
        return None
    cleaned = (
        str(raw)
        .replace(",", "")
        .replace("，", "")
        .replace("¥", "")
        .replace("￥", "")
        .replace("元", "")
        .strip()
    )
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _compact_subject(name: str) -> str:
    return _SUBJECT_PUNCT_RE.sub("", name or "")


def is_usable_subject_name(
    name: str,
    *,
    party_a: str = "",
    party_b: str = "",
    title: str = "",
) -> bool:
    """具体货物/服务名称才算数；公司名、合同标题、保密套话都不要。"""
    raw = (name or "").strip()
    if len(raw) < 2:
        return False
    compact = _compact_subject(raw)
    if not compact or compact in _GENERIC_SUBJECTS:
        return False
    if compact.endswith("合同") or compact.endswith("协议"):
        return False
    if "保密" in compact:
        return False
    if any(marker in compact for marker in _SUBJECT_COMPANY_MARKERS):
        return False
    title_compact = _compact_subject(title)
    if title_compact and compact == title_compact:
        return False
    for party in (party_a, party_b):
        party_compact = _compact_subject(party)
        if party_compact and compact == party_compact:
            return False
    return True


def normalize_subject_name(
    name: str,
    *,
    party_a: str = "",
    party_b: str = "",
    title: str = "",
) -> str:
    cleaned = (name or "").strip()
    if is_usable_subject_name(cleaned, party_a=party_a, party_b=party_b, title=title):
        return cleaned
    return ""


def _subject_more_specific(incoming: str, current: str) -> bool:
    """清单更长、分项更多，视为更像合同标的页，而不是封面四个字。"""
    if incoming.count("、") > current.count("、"):
        return True
    return len(_compact_subject(incoming)) >= len(_compact_subject(current)) + 6


def pick_subject_name(
    current: str,
    incoming: str,
    *,
    party_a: str = "",
    party_b: str = "",
    title: str = "",
) -> tuple[str, bool]:
    current_ok = is_usable_subject_name(current, party_a=party_a, party_b=party_b, title=title)
    incoming_ok = is_usable_subject_name(incoming, party_a=party_a, party_b=party_b, title=title)
    if incoming_ok and not current_ok:
        return incoming.strip(), True
    if incoming_ok and current_ok and incoming.strip() != current.strip() and _subject_more_specific(
        incoming, current
    ):
        return incoming.strip(), True
    return current, False


def already_as_prompt_dict(fields: ExtractedFields) -> dict:
    """给下一页模型看：前面已经抽到了什么。"""
    return {
        "doc_type": fields.doc_type,
        "contract_no": fields.contract_no,
        "party_a": fields.party_a,
        "party_b": fields.party_b,
        "subject_name": fields.subject_name,
        "amount": str(fields.amount) if fields.amount is not None else "",
        "signed_at": fields.signed_at.isoformat() if fields.signed_at else "",
        "start_date": fields.start_date.isoformat() if fields.start_date else "",
        "end_date": fields.end_date.isoformat() if fields.end_date else "",
        "title": fields.title,
        "invoices": [
            {
                "code": item.invoice_code,
                "no": item.invoice_no,
                "amount": str(item.amount) if item.amount is not None else "",
            }
            for item in fields.invoices
        ],
        "schedules": [
            {"name": item.name, "percent": item.percent}
            for item in fields.schedules
        ],
    }


def fields_from_llm_payload(data: dict) -> ExtractedFields:
    """把一页模型返回的 JSON 转成 ExtractedFields。空值表示本页没看到。"""
    result = ExtractedFields()
    if not isinstance(data, dict):
        return result

    doc_type = str(data.get("doc_type") or "unknown").strip().lower()
    if doc_type in {"contract", "invoice", "unknown"}:
        result.doc_type = doc_type

    result.contract_no = str(data.get("contract_no") or "").strip()
    extras = data.get("extra_contract_nos") or []
    if isinstance(extras, list):
        result.extra_contract_nos = [
            str(item).strip() for item in extras if str(item).strip() and str(item).strip() != result.contract_no
        ]

    result.party_a = str(data.get("party_a") or "").strip()
    result.party_b = str(data.get("party_b") or "").strip()
    result.title = str(data.get("title") or "").strip()
    result.subject_name = normalize_subject_name(
        str(data.get("subject_name") or "").strip(),
        party_a=result.party_a,
        party_b=result.party_b,
        title=result.title,
    )
    result.amount = parse_money(_optional_str(data.get("amount")))
    result.signed_at = parse_date(_optional_str(data.get("signed_at")))
    result.start_date = parse_date(_optional_str(data.get("start_date")))
    result.end_date = parse_date(_optional_str(data.get("end_date")))

    for inv in data.get("invoices") or []:
        if not isinstance(inv, dict):
            continue
        code = str(inv.get("code") or inv.get("invoice_code") or "").strip()
        number = str(inv.get("no") or inv.get("invoice_no") or "").strip()
        money = parse_money(_optional_str(inv.get("amount")))
        if code or number:
            result.invoices.append(ExtractedInvoice(invoice_code=code, invoice_no=number, amount=money))

    for row in data.get("schedules") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        percent_raw = row.get("percent")
        percent: int | None = None
        if percent_raw is not None and str(percent_raw).strip() != "":
            try:
                percent = int(percent_raw)
            except (TypeError, ValueError):
                percent = None
        if percent is not None and not 0 <= percent <= 100:
            continue
        result.schedules.append(ExtractedSchedule(name=name, percent=percent))

    return result


def still_needed_from_payload(data: dict) -> list[str]:
    raw = data.get("still_needed") or []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        key = str(item).strip()
        if key in KNOWN_STILL_NEEDED and key not in out:
            out.append(key)
    return out


def merge_extracted_fields(base: ExtractedFields, incoming: ExtractedFields) -> tuple[ExtractedFields, bool]:
    """后面的页只补充空缺，不会用空值把已有字段盖掉。返回是否新增了信息。"""
    added = False
    out = ExtractedFields(
        doc_type=base.doc_type,
        contract_no=base.contract_no,
        extra_contract_nos=list(base.extra_contract_nos),
        title=base.title,
        party_a=base.party_a,
        party_b=base.party_b,
        subject_name=base.subject_name,
        amount=base.amount,
        signed_at=base.signed_at,
        start_date=base.start_date,
        end_date=base.end_date,
        invoices=list(base.invoices),
        schedules=list(base.schedules),
        warnings=list(base.warnings),
    )

    if incoming.doc_type != "unknown" and (out.doc_type == "unknown" or incoming.doc_type == "contract"):
        if out.doc_type != incoming.doc_type:
            out.doc_type = incoming.doc_type
            added = True

    def fill_str(current: str, new: str) -> str:
        nonlocal added
        if not current and new:
            added = True
            return new
        return current

    out.contract_no = fill_str(out.contract_no, incoming.contract_no)
    out.title = fill_str(out.title, incoming.title)
    out.party_a = fill_str(out.party_a, incoming.party_a)
    out.party_b = fill_str(out.party_b, incoming.party_b)
    picked, subject_added = pick_subject_name(
        out.subject_name,
        incoming.subject_name,
        party_a=out.party_a,
        party_b=out.party_b,
        title=out.title,
    )
    if subject_added:
        out.subject_name = picked
        added = True

    if incoming.contract_no and incoming.contract_no != out.contract_no:
        if incoming.contract_no not in out.extra_contract_nos:
            out.extra_contract_nos.append(incoming.contract_no)
            added = True
    for extra in incoming.extra_contract_nos:
        if extra and extra != out.contract_no and extra not in out.extra_contract_nos:
            out.extra_contract_nos.append(extra)
            added = True

    if out.amount is None and incoming.amount is not None:
        out.amount = incoming.amount
        added = True
    if out.signed_at is None and incoming.signed_at is not None:
        out.signed_at = incoming.signed_at
        added = True
    if out.start_date is None and incoming.start_date is not None:
        out.start_date = incoming.start_date
        added = True
    if out.end_date is None and incoming.end_date is not None:
        out.end_date = incoming.end_date
        added = True

    seen_invoices = {(item.invoice_code, item.invoice_no) for item in out.invoices}
    for item in incoming.invoices:
        key = (item.invoice_code, item.invoice_no)
        if key in seen_invoices:
            continue
        out.invoices.append(item)
        seen_invoices.add(key)
        added = True

    seen_schedules = {item.name for item in out.schedules}
    for item in incoming.schedules:
        if item.name in seen_schedules:
            continue
        out.schedules.append(item)
        seen_schedules.add(item.name)
        added = True

    for warning in incoming.warnings:
        if warning and warning not in out.warnings:
            out.warnings.append(warning)

    return out, added


def finalize_fields(fields: ExtractedFields) -> ExtractedFields:
    """全部页读完后补标题、未编号提示。"""
    has_contract = bool(fields.contract_no or fields.party_a or fields.party_b or fields.amount)
    has_invoice = bool(fields.invoices)
    if has_invoice and not has_contract:
        fields.doc_type = "invoice"
    elif has_contract:
        fields.doc_type = "contract"
        if fields.party_a and fields.party_b:
            fields.title = fields.title or f"{fields.party_a}与{fields.party_b}合同"
        elif fields.contract_no:
            fields.title = fields.title or f"合同 {fields.contract_no}"
        if not fields.contract_no:
            fields.title = fields.title or "未编号合同"
            note = "未读到合同编号，已单独成一份草稿。系统用内部 ID 区分，编号可后补。"
            if note not in fields.warnings:
                fields.warnings.append(note)
        if fields.extra_contract_nos:
            note = "同一文件里读到多个合同编号，已按第一个分堆，请人工确认是否要拆开。"
            if note not in fields.warnings:
                fields.warnings.append(note)
    elif has_invoice:
        fields.doc_type = "invoice"
    return fields


def extraction_complete(fields: ExtractedFields, still_needed: list[str] | None) -> bool:
    """
    草稿信息齐了就停止翻页。

    1. 模型列出的 still_needed（只认我们关心的键）为空，并且核心主体/金额已有；
    2. 或者合同草稿字段都已填上（分期若模型仍说缺，就继续找）。
    """
    pending = [key for key in (still_needed or []) if key in KNOWN_STILL_NEEDED]
    invoice_only = bool(fields.invoices) and not (fields.party_a or fields.party_b or fields.contract_no)
    if invoice_only or fields.doc_type == "invoice":
        invoice = fields.invoices[0] if fields.invoices else None
        invoice_ok = bool(invoice and invoice.invoice_no)
        if invoice_ok and not any(key in pending for key in INVOICE_DRAFT_KEYS):
            return True

    looks_like_contract = fields.doc_type == "contract" or bool(
        fields.party_a or fields.party_b or fields.contract_no
    )
    subject_ready = (not looks_like_contract) or is_usable_subject_name(
        fields.subject_name,
        party_a=fields.party_a,
        party_b=fields.party_b,
        title=fields.title,
    )

    required_filled = bool(
        fields.contract_no
        and fields.party_a
        and fields.party_b
        and fields.amount is not None
        and fields.signed_at is not None
        and fields.start_date is not None
        and fields.end_date is not None
        and subject_ready
    )
    if required_filled and "schedules" not in pending:
        return True
    if required_filled:
        return not pending

    core = bool(fields.party_a and fields.party_b and fields.amount is not None and subject_ready)
    if core and not pending:
        # 模型认为这份文件里本来就没有编号或日期，不必为找不到的字段读完整本附录。
        return True
    return False


def normalize_contract_no(value: str | None) -> str | None:
    """空编号存 NULL，这样多份未编号合同不会撞唯一约束。"""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def grouping_key(contract_no: str | None, file_id: int) -> str:
    """
    有编号：同一编号合成一堆（正本+补充协议）。
    没编号：每个文件单独一堆，避免把不相干的扫描件捏成一份。
    """
    normalized = normalize_contract_no(contract_no)
    if normalized:
        return f"no:{normalized}"
    return f"file:{file_id}"


def unnumbered_fingerprint(fields: ExtractedFields) -> str | None:
    """
    没编号时，用「甲方+乙方+金额+签订日」认同一份合同。
    四项缺任何一项就返回 None，宁可拆开也不要误并。
    """
    if normalize_contract_no(fields.contract_no):
        return None
    if not fields.party_a or not fields.party_b or fields.amount is None or fields.signed_at is None:
        return None
    amount = fields.amount.quantize(Decimal("0.01"))
    raw = f"{fields.party_a}|{fields.party_b}|{amount}|{fields.signed_at.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def identity_key(fields: ExtractedFields, file_id: int) -> str:
    """入库分堆：编号优先，其次指纹，再不行就按文件拆开。"""
    numbered = normalize_contract_no(fields.contract_no)
    if numbered:
        return f"no:{numbered}"
    fingerprint = unnumbered_fingerprint(fields)
    if fingerprint:
        return f"fp:{fingerprint}"
    return grouping_key(fields.contract_no, file_id)


def name_is_our_company(name: str) -> bool:
    """名称里出现「迈能同行」即视为我方，深圳市迈能同行科技有限公司及其简称都算。"""
    compact = re.sub(r"[\s（）()]", "", name or "")
    if not compact:
        return False
    return any(marker in compact for marker in OUR_COMPANY_MARKERS)


def derive_our_role(party_a: str, party_b: str) -> str:
    """我方公司名固定，甲/乙里哪边是迈能同行，角色就定下来。"""
    a = name_is_our_company(party_a)
    b = name_is_our_company(party_b)
    if a and not b:
        return "party_a"
    if b and not a:
        return "party_b"
    return ""


def derive_counterparty(party_a: str, party_b: str, our_role: str) -> str:
    """列表上的「对方」：己方是甲则对方是乙，反之亦然。"""
    role = our_role or derive_our_role(party_a, party_b)
    if role == "party_a":
        return party_b or party_a
    if role == "party_b":
        return party_a or party_b
    return party_b or party_a or ""


def build_schedules(amount: Decimal | None, extracted: list[ExtractedSchedule]) -> list[ExtractedSchedule]:
    """抽到付款比例就按比例拆期；否则一次性 = 一期，金额等于合同总额。"""
    total = amount or Decimal("0")
    if extracted:
        rows: list[ExtractedSchedule] = []
        for item in extracted:
            money = (total * Decimal(item.percent) / Decimal(100)).quantize(Decimal("0.01")) if item.percent else None
            rows.append(ExtractedSchedule(name=item.name, percent=item.percent, amount=money))
        return rows
    return [ExtractedSchedule(name="一次性", percent=100, amount=total)]


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
