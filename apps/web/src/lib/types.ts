export type CurrentUser = {
  id: number;
  name: string;
  email: string | null;
  avatar_url: string | null;
  role: string;
  /** 当前账号能进的模块 id，和侧栏菜单对应。 */
  modules: string[];
};

export type ManagedUser = {
  id: number;
  name: string;
  email: string | null;
  role: string;
  modules: string[];
};

export type AuthConfig = {
  feishu_enabled: boolean;
  dev_login_enabled: boolean;
};

export type PageResult<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Contract = {
  id: number;
  title: string;
  contract_no: string | null;
  party_a: string;
  party_b: string;
  our_role: string;
  counterparty: string;
  subject_name: string;
  amount: string;
  currency: string;
  status: string;
  signed_at: string | null;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  billed_amount: string;
  collected_amount: string;
  account_kind: string;
  source_filename: string | null;
  parse_status: string;
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
  original_name: string | null;
  has_file: boolean;
};

export type InvoiceUploadResult = {
  items: Invoice[];
  warning_text: string | null;
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
  parsing_count: number;
  receivable_amount: string;
  receivable_collected: string;
  receivable_outstanding: string;
  payable_amount: string;
  payable_paid: string;
  payable_outstanding: string;
};

export type InvoiceSummary = {
  count: number;
  issued_count: number;
};

export type CollectionRow = Collection & {
  contract_title: string;
  contract_no: string | null;
  party_a: string;
  party_b: string;
  schedule_name: string | null;
  account_kind: string;
};

export type CollectionPage = PageResult<CollectionRow> & {
  total_amount: string;
  receivable_count: number;
  receivable_amount: string;
  payable_count: number;
  payable_amount: string;
};

export const CONTRACT_STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  active: "履约中",
  expired: "已到期",
  terminated: "已终止",
};

export const PARSE_STATUS_LABEL: Record<string, string> = {
  pending: "待识别",
  processing: "识别中",
  done: "已识别",
  failed: "识别失败",
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

export const ACCOUNT_KIND_LABEL: Record<string, string> = {
  receivable: "应收账款",
  payable: "应付账款",
  "": "未判定",
};

/** 我方是乙方收钱，我方是甲方付钱。文案要跟着变，不能一律叫回款。 */
export function paymentWords(kind: string) {
  if (kind === "payable") {
    return {
      tab: "付款",
      settled: "已付款",
      outstanding: "待付款",
      total: "应付账款",
      plan: "付款计划",
      addPlan: "增加付款计划",
      confirm: "登记付款",
      date: "付款日",
      link: "付款",
      empty: "还没有付款计划。可以在下方增加一期，或等识别完成后自动生成。",
      hint: "一期一行。改名称或计划金额点编辑；付了点登记付款；输错了可以删。一次性会自动生成一期。",
      deletePlan: "确定删除这一期付款计划？",
      deleteReceipt: "确定删除这笔付款？删除后合同已付款金额会重新计算。",
      deletePlanWithReceipts: "该期已有付款。删除会一并去掉付款记录，合同已付款会重新汇总。确定删除？",
    };
  }
  if (kind === "receivable") {
    return {
      tab: "收款",
      settled: "已收款",
      outstanding: "待收款",
      total: "应收账款",
      plan: "收款计划",
      addPlan: "增加收款计划",
      confirm: "登记收款",
      date: "收款日",
      link: "收款",
      empty: "还没有收款计划。可以在下方增加一期，或等识别完成后自动生成。",
      hint: "一期一行。改名称或计划金额点编辑；钱到了点登记收款；输错了可以删。一次性会自动生成一期。",
      deletePlan: "确定删除这一期收款计划？",
      deleteReceipt: "确定删除这笔收款？删除后合同已收款金额会重新计算。",
      deletePlanWithReceipts: "该期已有收款。删除会一并去掉收款记录，合同已收款会重新汇总。确定删除？",
    };
  }
  return {
    tab: "收付款",
    settled: "已结算",
    outstanding: "待结算",
    total: "合同额",
    plan: "收付款计划",
    addPlan: "增加收付款计划",
    confirm: "登记收付",
    date: "收付日",
    link: "收付款",
    empty: "还没有收付款计划。可以在下方增加一期，或等识别完成后自动生成。",
    hint: "一期一行。改名称或计划金额点编辑；钱到了点登记；输错了可以删。一次性会自动生成一期。",
    deletePlan: "确定删除这一期收付款计划？",
    deleteReceipt: "确定删除这笔记录？删除后合同已结算金额会重新计算。",
    deletePlanWithReceipts: "该期已有收付记录。删除会一并去掉记录，合同金额会重新汇总。确定删除？",
  };
}
