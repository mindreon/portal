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
  contract_no: string;
  counterparty: string;
  amount: string;
  currency: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  owner_id: number;
};

export type Invoice = {
  id: number;
  title: string;
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
  owner_id: number;
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
