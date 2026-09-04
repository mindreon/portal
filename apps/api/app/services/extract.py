"""
从合同/发票文本里抽出要素。

这是「人核对之前」的草稿：用正则找常见标签。扫描件 OCR 会认错字，
所以页面上必须让人改完再当正式数据。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation


CONTRACT_NO_RE = re.compile(
    r"(?:合同编号|合同号|合同編號|Contract\s*No\.?)\s*[:：#]?\s*([A-Za-z0-9][A-Za-z0-9\-_/]{2,31})",
    re.I,
)
PARTY_A_RE = re.compile(r"甲\s*方(?:主体)?(?:（[^）]*）|\([^)]*\))?\s*[:：]\s*([^\n]{2,80})")
PARTY_B_RE = re.compile(r"乙\s*方(?:主体)?(?:（[^）]*）|\([^)]*\))?\s*[:：]\s*([^\n]{2,80})")
AMOUNT_RE = re.compile(
    r"(?:合同总金额|合同金额|总金额)\s*[(（]元[)）]?\s*[:：]?\s*[¥￥]?\s*([\d,]+(?:\.\d{1,2})?)"
)
SIGNED_RE = re.compile(
    r"(?:合同签订时间|签订时间|签订日期|签约日期|签署日期)\s*[:：]?\s*"
    r"(\d{4}\s*[-./年]\s*\d{1,2}\s*[-./月]\s*\d{1,2}\s*日?)"
)
PERIOD_RE = re.compile(
    r"(?:履约期限|履行期限|服务期限)(?:（起止）)?\s*[:：]?\s*"
    r"(\d{4}\s*[-./年]\s*\d{1,2}\s*[-./月]\s*\d{1,2}\s*日?)\s*(?:至|—|--|-|~)\s*"
    r"(\d{4}\s*[-./年]\s*\d{1,2}\s*[-./月]\s*\d{1,2}\s*日?)"
)
INVOICE_CODE_RE = re.compile(r"发票代码\s*[:：]?\s*(\d{10,12})")
INVOICE_NO_RE = re.compile(r"发票号码\s*[:：]?\s*(\d{8,20})")
INVOICE_AMOUNT_RE = re.compile(
    r"(?:发票金额|价税合计)\s*[(（]元[)）]?\s*[:：]?\s*[¥￥]?\s*([\d,]+(?:\.\d{1,2})?)"
)
PERCENT_PAY_RE = re.compile(
    r"(首付款|首期款|首期|第一期|第二期|第三期|第四期|尾款|验收款|预付款)"
    r"[^。\n%]{0,24}?(\d{1,3})\s*%"
)


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
    amount: Decimal | None = None
    signed_at: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    invoices: list[ExtractedInvoice] = field(default_factory=list)
    schedules: list[ExtractedSchedule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_date(raw: str | None) -> date | None:
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
    if not raw:
        return None
    try:
        return Decimal(raw.replace(",", "").replace("，", ""))
    except InvalidOperation:
        return None


def _clean_party(raw: str) -> str:
    raw = re.split(r"(?=乙方|甲方|合同总|合同编|合同金|发票|签订|履约)", raw)[0]
    return re.sub(r"\s+", "", raw).strip(" ：:、,，")


def extract_fields(text: str) -> ExtractedFields:
    """从一段纯文本抽出草稿要素。"""
    result = ExtractedFields()
    if not text or not text.strip():
        return result

    nos = [match.group(1) for match in CONTRACT_NO_RE.finditer(text)]
    if nos:
        result.contract_no = nos[0]
        result.extra_contract_nos = [item for item in dict.fromkeys(nos[1:]) if item != nos[0]]
        if result.extra_contract_nos:
            result.warnings.append("同一文件里读到多个合同编号，已按第一个分堆，请人工确认是否要拆开。")

    party_a = PARTY_A_RE.search(text)
    party_b = PARTY_B_RE.search(text)
    if party_a:
        result.party_a = _clean_party(party_a.group(1))
    if party_b:
        result.party_b = _clean_party(party_b.group(1))

    amount = AMOUNT_RE.search(text)
    result.amount = parse_money(amount.group(1) if amount else None)

    signed = SIGNED_RE.search(text)
    result.signed_at = parse_date(signed.group(1) if signed else None)

    period = PERIOD_RE.search(text)
    if period:
        result.start_date = parse_date(period.group(1))
        result.end_date = parse_date(period.group(2))

    invoice_code = INVOICE_CODE_RE.search(text)
    invoice_no = INVOICE_NO_RE.search(text)
    invoice_amount = INVOICE_AMOUNT_RE.search(text)
    if invoice_code or invoice_no:
        result.invoices.append(
            ExtractedInvoice(
                invoice_code=invoice_code.group(1) if invoice_code else "",
                invoice_no=invoice_no.group(1) if invoice_no else "",
                amount=parse_money(invoice_amount.group(1) if invoice_amount else None),
            )
        )

    seen_names: set[str] = set()
    for match in PERCENT_PAY_RE.finditer(text):
        name, percent = match.group(1), int(match.group(2))
        if name in seen_names or percent > 100:
            continue
        seen_names.add(name)
        result.schedules.append(ExtractedSchedule(name=name, percent=percent))

    has_contract = bool(result.contract_no or result.party_a or result.party_b or result.amount)
    has_invoice = bool(result.invoices)
    if has_invoice and not has_contract:
        result.doc_type = "invoice"
    elif has_contract:
        result.doc_type = "contract"
        if result.party_a and result.party_b:
            result.title = f"{result.party_a}与{result.party_b}合同"
        elif result.contract_no:
            result.title = f"合同 {result.contract_no}"
    elif has_invoice:
        result.doc_type = "invoice"

    if result.doc_type == "contract" and not result.contract_no:
        if not result.title:
            result.title = "未编号合同"
        result.warnings.append("未读到合同编号，已单独成一份草稿。系统用内部 ID 区分，编号可后补。")

    return result


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


def derive_counterparty(party_a: str, party_b: str, our_role: str) -> str:
    """列表上的「对方」：己方是甲则对方是乙，反之亦然。"""
    if our_role == "party_a":
        return party_b or party_a
    if our_role == "party_b":
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
