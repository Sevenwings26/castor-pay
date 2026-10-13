import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import {
  ApiKey,
  AuthResponse,
  Currency,
  DLQMessage,
  EscrowContract,
  FXQuote,
  MerchantBalancesResponse,
  PaymentInitializeRequest,
  PaymentInitializeResponse,
  PaymentTransaction,
  ReconBatch,
  TreasuryData,
  VirtualAccount,
} from '../types';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    prepareHeaders: (headers, { getState }) => {
      const state = getState() as { auth: { token: string | null } };
      const token = state.auth.token;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Balance', 'Transactions', 'VirtualAccounts', 'Escrow', 'Recon', 'DLQ', 'ApiKeys'],
  endpoints: (builder) => ({
    // Auth & Users
    login: builder.mutation<
      AuthResponse,
      { email: string; password: string }
    >({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation<
      AuthResponse,
      { email: string; password: string; full_name: string; merchant_name?: string }
    >({
      query: (body) => ({
        url: '/auth/register',
        method: 'POST',
        body: {
          ...body,
          role: 'MERCHANT_ADMIN',
        },
      }),
    }),
    getApiKeys: builder.query<ApiKey[], void>({
      query: () => '/auth/api-keys',
      providesTags: ['ApiKeys'],
    }),
    createApiKey: builder.mutation<ApiKey, { name: string }>({
      query: (body) => ({
        url: '/auth/api-keys',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ApiKeys'],
    }),

    // Ledger Balances
    getBalances: builder.query<MerchantBalancesResponse, void>({
      query: () => '/ledger/balances',
      providesTags: ['Balance'],
    }),

    // Payments & Transactions
    getTransactions: builder.query<PaymentTransaction[], void>({
      query: () => '/payments/',
      providesTags: ['Transactions'],
    }),
    initializePayment: builder.mutation<
      PaymentInitializeResponse,
      PaymentInitializeRequest & { idempotency_key: string }
    >({
      query: ({ idempotency_key, ...body }) => ({
        url: '/payments/initialize',
        method: 'POST',
        headers: {
          'Idempotency-Key': idempotency_key,
        },
        body,
      }),
      invalidatesTags: ['Transactions', 'Balance'],
    }),
    settlePayment: builder.mutation<PaymentTransaction, { transaction_id: string }>({
      query: ({ transaction_id }) => ({
        url: `/payments/${transaction_id}/settle`,
        method: 'POST',
      }),
      invalidatesTags: ['Transactions', 'Balance'],
    }),

    // Dedicated Virtual Accounts
    getVirtualAccounts: builder.query<VirtualAccount[], void>({
      query: () => '/virtual-accounts/',
      providesTags: ['VirtualAccounts'],
    }),
    createVirtualAccount: builder.mutation<
      VirtualAccount,
      {
        currency: Currency;
        customer_name: string;
        customer_email: string;
        merchant_customer_id: string;
        bvn?: string;
      }
    >({
      query: (body) => ({
        url: '/virtual-accounts/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['VirtualAccounts'],
    }),
    simulateDeposit: builder.mutation<
      any,
      {
        account_number: string;
        amount: number;
        session_id: string;
        sender_name: string;
        sender_bank: string;
      }
    >({
      query: (body) => ({
        url: '/virtual-accounts/simulate-inbound-deposit',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Balance', 'VirtualAccounts'],
    }),

    // Cross-Border FX
    getLiveRates: builder.query<
      { benchmark_pairs: { pair: string; rate: number }[]; spread_bps: number; guaranteed_quote_window_seconds: number },
      void
    >({
      query: () => '/fx/rates',
    }),
    createFXQuote: builder.mutation<
      FXQuote,
      {
        source_currency: Currency;
        target_currency: Currency;
        source_amount: number;
      }
    >({
      query: (body) => ({
        url: '/fx/quotes',
        method: 'POST',
        body,
      }),
    }),
    executeFXQuote: builder.mutation<FXQuote, { quote_reference: string }>({
      query: (body) => ({
        url: '/fx/quotes/execute',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Balance'],
    }),

    // Escrow & Gaming Micropayments
    getEscrowContracts: builder.query<EscrowContract[], void>({
      query: () => '/escrow/',
      providesTags: ['Escrow'],
    }),
    createEscrowContract: builder.mutation<
      EscrowContract,
      {
        title: string;
        buyer_email: string;
        seller_email: string;
        currency: Currency;
        total_amount: number;
        milestones: { title: string; amount: number }[];
      }
    >({
      query: (body) => ({
        url: '/escrow/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Escrow'],
    }),
    fundEscrowContract: builder.mutation<EscrowContract, { contract_reference: string }>({
      query: ({ contract_reference }) => ({
        url: `/escrow/${contract_reference}/fund`,
        method: 'POST',
      }),
      invalidatesTags: ['Escrow', 'Balance'],
    }),
    releaseMilestone: builder.mutation<EscrowContract, { contract_reference: string; milestone_id: string }>({
      query: ({ contract_reference, milestone_id }) => ({
        url: `/escrow/${contract_reference}/milestones/${milestone_id}/release`,
        method: 'POST',
      }),
      invalidatesTags: ['Escrow', 'Balance'],
    }),

    // Automated 3-Way Reconciliation
    getReconBatches: builder.query<ReconBatch[], void>({
      query: () => '/reconciliation/batches',
      providesTags: ['Recon'],
    }),
    simulateDailyRecon: builder.mutation<ReconBatch, void>({
      query: () => ({
        url: '/reconciliation/batches/simulate-daily-run',
        method: 'POST',
      }),
      invalidatesTags: ['Recon'],
    }),

    // Admin Treasury & DLQ
    getTreasury: builder.query<TreasuryData, void>({
      query: () => '/admin/treasury',
    }),
    getDLQ: builder.query<{ dlq_queue_url: string; total_messages_inspected: number; messages: DLQMessage[] }, void>({
      query: () => '/admin/dlq',
      providesTags: ['DLQ'],
    }),
    replayDLQ: builder.mutation<{ status: string; message_id: string }, { message_id: string }>({
      query: (body) => ({
        url: `/admin/dlq/replay?message_id=${encodeURIComponent(body.message_id)}`,
        method: 'POST',
      }),
      invalidatesTags: ['DLQ'],
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useGetApiKeysQuery,
  useCreateApiKeyMutation,
  useGetBalancesQuery,
  useGetTransactionsQuery,
  useInitializePaymentMutation,
  useSettlePaymentMutation,
  useGetVirtualAccountsQuery,
  useCreateVirtualAccountMutation,
  useSimulateDepositMutation,
  useGetLiveRatesQuery,
  useCreateFXQuoteMutation,
  useExecuteFXQuoteMutation,
  useGetEscrowContractsQuery,
  useCreateEscrowContractMutation,
  useFundEscrowContractMutation,
  useReleaseMilestoneMutation,
  useGetReconBatchesQuery,
  useSimulateDailyReconMutation,
  useGetTreasuryQuery,
  useGetDLQQuery,
  useReplayDLQMutation,
} = apiSlice;
