export type Currency = 'NGN' | 'GBP' | 'USD' | 'EUR';

export type PaymentStatus = 'PENDING' | 'PROCESSING' | 'SUCCEEDED' | 'FAILED' | 'REFUNDED';

export interface BalanceDetail {
  available: number; // in minor currency units (e.g. kobo, pence, cents)
  escrow: number;    // in minor currency units
}

export interface MerchantBalancesResponse {
  merchant_id: string;
  balances: Record<Currency, BalanceDetail>;
}

export interface PaymentTransaction {
  id: string;
  reference: string;
  idempotency_key: string;
  merchant_id: string;
  amount: number; // in minor units
  fee: number;    // in minor units
  currency: Currency;
  status: PaymentStatus;
  payment_method: string;
  provider: string;
  provider_reference?: string;
  customer_email: string;
  customer_name?: string;
  created_at: string;
}

export interface PaymentInitializeRequest {
  amount: number; // in minor units
  currency: Currency;
  customer_email: string;
  customer_name?: string;
  payment_method?: string;
  metadata?: Record<string, any>;
}

export interface PaymentInitializeResponse {
  transaction_id: string;
  reference: string;
  amount: number;
  fee: number;
  currency: Currency;
  status: PaymentStatus;
  checkout_url?: string;
  provider: string;
}

export interface VirtualAccount {
  id: string;
  currency: Currency;
  account_number: string;
  account_name: string;
  bank_name: string;
  routing_code?: string;
  status: string;
  merchant_customer_id: string;
  bvn_verified: boolean;
  created_at: string;
}

export interface FXQuote {
  quote_reference: string;
  source_currency: Currency;
  target_currency: Currency;
  source_amount: number;
  target_amount: number;
  exchange_rate: number;
  spread_bps: number;
  expires_at: string;
  is_executed: boolean;
}

export interface EscrowMilestone {
  id: string;
  title: string;
  amount: number; // in minor units
  status: 'PENDING' | 'COMPLETED' | 'RELEASED';
}

export interface EscrowContract {
  id: string;
  contract_reference: string;
  title: string;
  buyer_email: string;
  seller_email: string;
  currency: Currency;
  total_amount: number; // in minor units
  status: 'CREATED' | 'FUNDED' | 'IN_INSPECTION' | 'RELEASED' | 'REFUNDED' | 'DISPUTED';
  milestones: EscrowMilestone[];
  created_at: string;
}

export interface ReconDiscrepancy {
  id: string;
  discrepancy_type: 'UNMATCHED_IN_BANK' | 'UNMATCHED_IN_LEDGER' | 'AMOUNT_MISMATCH' | 'STATUS_MISMATCH';
  external_reference?: string;
  internal_reference?: string;
  variance_amount: number;
  notes?: string;
  resolved: boolean;
}

export interface ReconBatch {
  id: string;
  batch_reference: string;
  provider: string;
  statement_date: string;
  total_records: number;
  matched_records: number;
  unmatched_records: number;
  status: 'IN_PROGRESS' | 'BALANCED' | 'DISCREPANCIES_FOUND';
  discrepancies: ReconDiscrepancy[];
  created_at: string;
}

export interface BankingPartner {
  partner: string;
  rail: string;
  status: 'OPERATIONAL' | 'DEGRADED' | 'DOWN';
  latency_ms: number;
}

export interface TreasuryData {
  currencies: Record<string, {
    asset_float: number;
    merchant_liabilities: number;
    revenue_collected: number;
  }>;
  banking_partners: BankingPartner[];
}

export interface DLQMessage {
  message_id: string;
  receipt_handle: string;
  body: Record<string, any>;
  receive_count: string;
  sent_timestamp: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  raw_key: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'TREASURY' | 'MERCHANT_ADMIN' | 'DEVELOPER' | 'AUDITOR';
  merchant_id?: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  merchant_id?: string;
  email: string;
}
