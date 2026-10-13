#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " CastorPay End-to-End Live Endpoint Test Suite"
echo "=========================================================="

# 1. Health Probe
echo -e "\n[1] Checking /health probe..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "Response: $HEALTH"

# 2. Login as Demo Merchant
echo -e "\n[2] Logging in as demo merchant (demo@castorpay.dev)..."
TOKEN_RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@castorpay.dev","password":"CastorSecret123!"}')
echo "Response: $TOKEN_RESP"
TOKEN=$(echo "$TOKEN_RESP" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 3. Fetch Balances Before Deposit
echo -e "\n[3] Querying Double-Entry Ledger Balances..."
BALANCES_BEFORE=$(curl -s http://localhost:8000/api/v1/ledger/balances -H "Authorization: Bearer $TOKEN")
echo "Balances: $BALANCES_BEFORE"

# 4. Generate Dedicated Virtual Account (DVA)
echo -e "\n[4] Generating Dynamic Virtual Account (NGN NUBAN)..."
VA_RESP=$(curl -s -X POST http://localhost:8000/api/v1/virtual-accounts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"currency":"NGN","customer_name":"Tunde Bakare","customer_email":"tunde@test.com","merchant_customer_id":"cust_gaming_991","bvn":"22233344455"}')
echo "Response: $VA_RESP"
ACC_NUM=$(echo "$VA_RESP" | grep -o '"account_number":"[^"]*' | cut -d'"' -f4)

# 5. Simulate Inbound Bank Transfer (Deposit 250,000 kobo = 2,500.00 NGN)
echo -e "\n[5] Simulating Inbound Bank Transfer of 250,000 kobo to Account $ACC_NUM..."
DEPOSIT_RESP=$(curl -s -X POST http://localhost:8000/api/v1/virtual-accounts/simulate-inbound-deposit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"account_number\":\"$ACC_NUM\",\"amount\":250000,\"session_id\":\"NIP_SESSION_LIVE_$$$(date +%s)\",\"sender_name\":\"Alhaji Dangote\",\"sender_bank\":\"Access Bank\"}")
echo "Response: $DEPOSIT_RESP"

# 6. Fetch Balances After Deposit (should show +250,000 kobo)
echo -e "\n[6] Re-checking Ledger Balances after Bank Deposit..."
BALANCES_AFTER=$(curl -s http://localhost:8000/api/v1/ledger/balances -H "Authorization: Bearer $TOKEN")
echo "Balances: $BALANCES_AFTER"

# 7. Request 60-Second Guaranteed FX Quote
echo -e "\n[7] Requesting 60-Second Guaranteed FX Quote (GBP to NGN)..."
FX_RESP=$(curl -s -X POST http://localhost:8000/api/v1/fx/quotes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_currency":"GBP","target_currency":"NGN","source_amount":10000}')
echo "Response: $FX_RESP"

# 8. Test Distributed Idempotency on Payment Initialize
IDEM_KEY="test_idem_live_uuid_10928"
echo -e "\n[8] Initializing Payment with Idempotency-Key: $IDEM_KEY..."
PAY_RESP_1=$(curl -s -X POST http://localhost:8000/api/v1/payments/initialize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: $IDEM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"amount":500000,"currency":"NGN","customer_email":"gamer@ab-inbev.com","customer_name":"Gamer Alex","payment_method":"CARD"}')
echo "First Call: $PAY_RESP_1"

echo -e "\n[9] Sending Identical Payment Request with Same Idempotency-Key (Duplicate check)..."
PAY_RESP_2=$(curl -s -X POST http://localhost:8000/api/v1/payments/initialize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: $IDEM_KEY" \
  -H "Content-Type: application/json" \
  -d '{"amount":500000,"currency":"NGN","customer_email":"gamer@ab-inbev.com","customer_name":"Gamer Alex","payment_method":"CARD"}')
echo "Second Call (Cached): $PAY_RESP_2"

echo -e "\n=========================================================="
echo " All Live Endpoint Tests Completed Successfully!"
echo "=========================================================="
