export type CurrentUser = {
  id: number;
  name: string;
  email: string | null;
  avatar_url: string | null;
  role: string;
};

export type AuthConfig = {
  feishu_enabled: boolean;
  dev_login_enabled: boolean;
};

export type Contract = {
  id: number;
  title: string;
  contract_no: string | null;
  party_a: string;
  party_b: string;
  our_role: string;
  counterparty: string;
  amount: string;
  currency: string;
  status: string;
  signed_at: string | null;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  billed_amount: string;
  collected_amount: string;
  owner_id: number;
};

export type Invoice = {
  id: number;
  title: string;
  invoice_code: string | null;
  invoice_no: string;
  counterparty: string;
  amount: string;
  tax_amount: string;
  currency: string;
  status: string;
  issued_at: string | null;
  due_at: string | null;
  notes: string | null;
  contract_id: number | null;
  schedule_id: number | null;
  owner_id: number;
};

export type ContractFile = {
  id: number;
  original_name: string;
  source: string;
  doc_type: string;
  parse_status: string;
  extracted_text: string | null;
  error_message: string | null;
  contract_id: number | null;
};

export type PaymentSchedule = {
  id: number;
  contract_id: number;
  period_no: number;
  name: string;
  amount: string;
  due_date: string | null;
  notes: string | null;
  collected_amount: string;
};

export type Collection = {
  id: number;
  contract_id: number;
  schedule_id: number | null;
  amount: string;
  received_at: string | null;
  notes: string | null;
};

export type ImportBatch = {
  id: number;
  status: string;
  warning_text: string | null;
  contracts: Contract[];
  files: ContractFile[];
};

export type ContractSummary = {
  count: number;
  active_count: number;
  total_amount: string;
  collected_amount: string;
  outstanding_amount: string;
};

export type CollectionRow = Collection & {
  contract_title: string;
  contract_no: string | null;
  party_a: string;
  party_b: string;
  schedule_name: string | null;
};

export const CONTRACT_STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  active: "履约中",
  expired: "已到期",
  terminated: "已终止",
};

export const INVOICE_STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  issued: "已开具",
  paid: "已收款",
  void: "已作废",
};

export const OUR_ROLE_LABEL: Record<string, string> = {
  "": "未指定",
  party_a: "我方是甲方",
  party_b: "我方是乙方",
};
