-- Premium flow manual DB helper for Render/Postgres
-- Project tables confirmed from app/models.py:
-- - user_sessions
-- - reports
-- - orders
-- - paid_surveys
--
-- How identifiers are produced:
-- 1) sid:
--    created by POST /api/survey/free
--    stored in user_sessions.sid
-- 2) report_token:
--    returned as free_token by POST /api/survey/free
--    stored in reports.report_token
-- 3) order_id:
--    created by POST /api/payments/inicis/prepare
--    returned as response.form.oid
--    stored in orders.order_id
--
-- Recommended use:
-- 1) run step 1 and step 2 in dev_test_premium_flow.http
-- 2) replace the placeholders below
-- 3) run the SELECT checks
-- 4) run the FORCE PAID update
-- 5) continue the HTTP flow

-- ============================================================
-- Replace these placeholders before execution
-- ============================================================
-- Example:
-- \set sid 'S_xxxxxxxxxxxx'
-- \set report_token 't_free_xxxxxxxxxxxxxxxxxx'
-- \set order_id 'RCL_1234567890_abcd1234'

-- ============================================================
-- 1) Verify the free survey/report row
-- Expected:
-- - one row
-- - user_sessions.sid == reports.sid
-- - reports.report_token matches the free_token from /api/survey/free
-- ============================================================
SELECT
  u.sid,
  u.created_at,
  u.risk_level,
  r.report_token,
  r.status AS report_status,
  r.generated_at
FROM user_sessions u
JOIN reports r ON r.sid = u.sid
WHERE u.sid = '<sid>'
   OR r.report_token = '<report_token>';

-- ============================================================
-- 2) Verify the prepared order row
-- Expected:
-- - one row
-- - orders.status = PENDING
-- - orders.sid matches reports.sid
-- ============================================================
SELECT
  o.order_id,
  o.sid,
  o.status,
  o.amount,
  o.paid_at,
  r.report_token,
  r.status AS report_status
FROM orders o
JOIN reports r ON r.sid = o.sid
WHERE o.order_id = '<order_id>';

-- ============================================================
-- 3) Force the order to PAID
-- Use this to bypass PG while keeping the premium access checks unchanged.
-- Expected after update:
-- - orders.status = PAID
-- - orders.paid_at is not null
-- ============================================================
UPDATE orders
SET status = 'PAID',
    paid_at = NOW(),
    amount = COALESCE(amount, 29000)
WHERE order_id = '<order_id>';

-- ============================================================
-- 4) Verify the forced PAID update
-- ============================================================
SELECT
  o.order_id,
  o.sid,
  o.status,
  o.amount,
  o.paid_at,
  r.report_token
FROM orders o
JOIN reports r ON r.sid = o.sid
WHERE o.order_id = '<order_id>';

-- ============================================================
-- 5) Check whether the paid survey has been saved yet
-- Run after POST /api/premium/survey/paid
-- Expected:
-- - one row in paid_surveys
-- ============================================================
SELECT
  sid,
  submitted_at,
  answers_json
FROM paid_surveys
WHERE sid = '<sid>';

-- ============================================================
-- 6) Check the premium report row after finalize
-- Run after POST /api/premium/report/finalize
-- Success expectation:
-- - reports.status = READY
-- - generated_at is not null
-- - markdown/html are not empty
-- Failure expectation:
-- - reports.status = FAILED
-- ============================================================
SELECT
  sid,
  report_token,
  status,
  generated_at,
  LENGTH(COALESCE(markdown, '')) AS markdown_len,
  LENGTH(COALESCE(html, '')) AS html_len
FROM reports
WHERE report_token = '<report_token>';

-- ============================================================
-- 7) One-shot joined view for the whole flow
-- Useful for a final sanity check
-- ============================================================
SELECT
  u.sid,
  u.risk_level,
  r.report_token,
  r.status AS report_status,
  r.generated_at,
  o.order_id,
  o.status AS order_status,
  o.paid_at,
  ps.submitted_at AS paid_survey_submitted_at
FROM user_sessions u
LEFT JOIN reports r ON r.sid = u.sid
LEFT JOIN orders o ON o.sid = u.sid
LEFT JOIN paid_surveys ps ON ps.sid = u.sid
WHERE u.sid = '<sid>'
   OR r.report_token = '<report_token>'
   OR o.order_id = '<order_id>';

-- ============================================================
-- Failure-case helpers
-- ============================================================

-- ============================================================
-- F1) Create or inspect an unpaid order candidate
-- Use:
-- - run /api/payments/inicis/prepare
-- - DO NOT force PAID
-- - set that order_id into @unpaid_order_id in dev_test_premium_flow.http
-- Expected:
-- - status remains PENDING
-- ============================================================
SELECT
  order_id,
  sid,
  status,
  paid_at
FROM orders
WHERE order_id = '<unpaid_order_id>';

-- ============================================================
-- F2) Find a mismatch order_id for REPORT_ORDER_MISMATCH
-- Use:
-- - pick an order from a different sid than the current report_token
-- - set it into @mismatch_order_id in dev_test_premium_flow.http
-- Expected:
-- - order_sid != report_sid
-- ============================================================
SELECT
  o.order_id,
  o.sid AS order_sid,
  r.report_token,
  r.sid AS report_sid,
  o.status
FROM orders o
CROSS JOIN reports r
WHERE o.sid <> r.sid
ORDER BY o.order_id DESC
LIMIT 20;

-- ============================================================
-- F3) Remove paid survey for PAID_SURVEY_NOT_FOUND test
-- Use on a PAID order/report pair before calling generate/finalize
-- Expected after delete:
-- - no row in paid_surveys for that sid
-- ============================================================
DELETE FROM paid_surveys
WHERE sid = '<sid_without_paid_survey>';

SELECT
  sid,
  submitted_at
FROM paid_surveys
WHERE sid = '<sid_without_paid_survey>';

-- ============================================================
-- F4) Confirm READY report before overwrite=false reuse test
-- Expected:
-- - status = READY
-- - markdown_len > 0
-- - html_len > 0
-- ============================================================
SELECT
  sid,
  report_token,
  status,
  LENGTH(COALESCE(markdown, '')) AS markdown_len,
  LENGTH(COALESCE(html, '')) AS html_len
FROM reports
WHERE report_token = '<ready_report_token>';

-- ============================================================
-- F5) Force report back to READY fixture view after overwrite=true retest
-- This is a read-only sanity check; no update required for the endpoint itself.
-- ============================================================
SELECT
  sid,
  report_token,
  status,
  generated_at
FROM reports
WHERE report_token = '<ready_report_token>';
