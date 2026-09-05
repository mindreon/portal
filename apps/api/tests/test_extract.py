from datetime import date
from decimal import Decimal

from app.services.extract import (
    ExtractedFields,
    ExtractedInvoice,
    ExtractedSchedule,
    derive_our_role,
    extraction_complete,
    fields_from_llm_payload,
    finalize_fields,
    grouping_key,
    identity_key,
    merge_extracted_fields,
    normalize_contract_no,
    still_needed_from_payload,
)


def test_fields_from_llm_payload_types() -> None:
    fields = fields_from_llm_payload(
        {
            "doc_type": "contract",
            "contract_no": "HT-2026-001",
            "party_a": "星河科技有限公司",
            "party_b": "本地运营主体",
            "amount": "120,000.00",
            "signed_at": "2026年1月1日",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "invoices": [{"code": "012001900104", "no": "12345678", "amount": "40000"}],
            "schedules": [{"name": "第一期", "percent": 30}, {"name": "尾款", "percent": 70}],
        }
    )
    assert fields.contract_no == "HT-2026-001"
    assert fields.subject_name == ""
    assert fields.amount == Decimal("120000.00")
    assert fields.signed_at == date(2026, 1, 1)
    assert fields.start_date == date(2026, 1, 1)
    assert fields.invoices[0].invoice_no == "12345678"
    assert [item.name for item in fields.schedules] == ["第一期", "尾款"]


def test_merge_does_not_overwrite_with_empty() -> None:
    first = fields_from_llm_payload({"party_a": "甲公司", "party_b": "乙公司", "amount": "10"})
    second = fields_from_llm_payload({"party_a": "", "contract_no": "HT-2", "amount": ""})
    merged, added = merge_extracted_fields(first, second)
    assert added is True
    assert merged.party_a == "甲公司"
    assert merged.contract_no == "HT-2"
    assert merged.amount == Decimal("10")


def test_extraction_complete_waits_for_missing_then_stops() -> None:
    partial = fields_from_llm_payload({"party_a": "甲", "party_b": "乙", "amount": "1"})
    assert extraction_complete(partial, ["contract_no", "signed_at"]) is False
    full = fields_from_llm_payload(
        {
            "contract_no": "HT-1",
            "party_a": "甲",
            "party_b": "乙",
            "amount": "1",
            "signed_at": "2026-01-01",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }
    )
    assert extraction_complete(full, ["schedules"]) is False
    assert extraction_complete(full, []) is False
    full_with_subject = fields_from_llm_payload(
        {
            "contract_no": "HT-1",
            "party_a": "甲",
            "party_b": "乙",
            "amount": "1",
            "signed_at": "2026-01-01",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "subject_name": "AI 调度软件",
        }
    )
    assert extraction_complete(full_with_subject, []) is True


def test_extraction_complete_invoice() -> None:
    fields = ExtractedFields(
        doc_type="invoice",
        invoices=[ExtractedInvoice(invoice_code="012001900104", invoice_no="12345678")],
    )
    assert extraction_complete(fields, []) is True
    assert extraction_complete(fields, ["invoice_code"]) is False


def test_model_says_done_without_optional_dates() -> None:
    fields = fields_from_llm_payload(
        {"party_a": "甲", "party_b": "乙", "amount": "88", "subject_name": "交换机"}
    )
    assert extraction_complete(fields, []) is True
    assert extraction_complete(fields, ["signed_at"]) is False
    without_subject = fields_from_llm_payload({"party_a": "甲", "party_b": "乙", "amount": "88"})
    assert extraction_complete(without_subject, []) is False


def test_still_needed_ignores_unknown_keys() -> None:
    assert still_needed_from_payload({"still_needed": ["party_a", "foobar", "amount"]}) == ["party_a", "amount"]


def test_identity_without_contract_no() -> None:
    fields = finalize_fields(
        ExtractedFields(
            party_a="星河科技有限公司",
            party_b="本地运营主体",
            amount=Decimal("120000.00"),
            signed_at=date(2026, 1, 1),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            schedules=[
                ExtractedSchedule(name="第一期", percent=30),
                ExtractedSchedule(name="尾款", percent=70),
            ],
        )
    )
    assert fields.contract_no == ""
    assert grouping_key(fields.contract_no, 9) == "file:9"
    assert identity_key(fields, 9).startswith("fp:")
    assert normalize_contract_no("") is None
    assert "未编号" in fields.title or fields.warnings


def test_identity_with_contract_no_and_invoice() -> None:
    fields = ExtractedFields(
        doc_type="contract",
        contract_no="HT-2026-001",
        invoices=[ExtractedInvoice(invoice_code="012001900104", invoice_no="12345678", amount=Decimal("40000"))],
    )
    assert grouping_key(fields.contract_no, 1) == "no:HT-2026-001"
    assert fields.invoices[0].invoice_code == "012001900104"


def test_subject_name_from_payload_and_merge() -> None:
    first = fields_from_llm_payload({"party_a": "甲", "subject_name": "AI 调度软件"})
    assert first.subject_name == "AI 调度软件"
    merged, added = merge_extracted_fields(first, fields_from_llm_payload({"subject_name": ""}))
    assert added is False
    assert merged.subject_name == "AI 调度软件"
    filled, added = merge_extracted_fields(
        fields_from_llm_payload({"party_a": "甲"}),
        fields_from_llm_payload({"subject_name": "防火墙维保"}),
    )
    assert added is True
    assert filled.subject_name == "防火墙维保"


def test_reject_company_and_generic_subject_names() -> None:
    party_a = "哈尔滨医科大学附属第一医院"
    party_b = "北京时序天成技术有限公司"
    assert (
        fields_from_llm_payload(
            {"party_a": party_a, "party_b": party_b, "subject_name": "北京时序天成技术有限公司"}
        ).subject_name
        == ""
    )
    assert fields_from_llm_payload({"subject_name": "软件产品"}).subject_name == ""
    assert fields_from_llm_payload({"subject_name": "软件产品销售合同"}).subject_name == ""
    assert fields_from_llm_payload({"subject_name": "产品及/或服务"}).subject_name == ""
    assert (
        fields_from_llm_payload({"subject_name": "乙方自有产品及/或服务将被视为保密信息"}).subject_name
        == ""
    )
    goods = "AI 调度软件、交换机、防火墙等设备"
    assert fields_from_llm_payload({"subject_name": goods}).subject_name == goods
    upgraded, added = merge_extracted_fields(
        fields_from_llm_payload({"subject_name": "软件产品"}),
        fields_from_llm_payload({"subject_name": goods}),
    )
    assert added is True
    assert upgraded.subject_name == goods


def test_main_subject_is_not_overwritten_by_attachment_item_list() -> None:
    merged, added = merge_extracted_fields(
        fields_from_llm_payload({"subject_name": "AI 调度软件"}),
        fields_from_llm_payload(
            {"subject_name": "AI 调度软件、配套智能知识库工作流系统、配套智算资源调度监控系统"}
        ),
    )
    assert added is False
    assert merged.subject_name == "AI 调度软件"


def test_derive_our_role_from_maineng_name() -> None:
    assert derive_our_role("医大一", "深圳市迈能同行科技有限公司") == "party_b"
    assert derive_our_role("迈能同行科技有限公司", "某医院") == "party_a"
    assert derive_our_role("医大一", "时序天成") == ""
    assert still_needed_from_payload({"still_needed": ["subject_name"]}) == ["subject_name"]
