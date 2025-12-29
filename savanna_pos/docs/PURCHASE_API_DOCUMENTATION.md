# Purchase Management API Documentation

This document provides comprehensive documentation for all Purchase Management endpoints. These endpoints support both **eTIMS-registered** and **non-registered** users, allowing seamless purchase management regardless of eTIMS registration status.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoint Categories](#endpoint-categories)
4. [Purchase Invoice Management](#purchase-invoice-management)
5. [Registered Purchases (eTIMS)](#registered-purchases-etims)
6. [Purchase Returns](#purchase-returns)
7. [Bulk Operations](#bulk-operations)
8. [Bank and Account Management](#bank-and-account-management)
9. [Supplier Management](#supplier-management)
10. [Warehouse Management](#warehouse-management)
11. [Utility Endpoints](#utility-endpoints)
12. [Error Handling](#error-handling)
13. [Examples](#examples)

---

## Overview

The Purchase Management API provides endpoints for:

- Creating and managing Purchase Invoices
- Submitting purchases to eTIMS (for registered users)
- Fetching registered purchases from eTIMS
- Managing purchase returns
- Managing suppliers and supplier groups
- Managing Cash/Bank accounts
- Bulk operations
- Checking eTIMS registration status

### Key Features

- **Dual Mode Support**: Works seamlessly for both eTIMS-registered and non-registered users
- **Automatic Detection**: Automatically detects eTIMS registration status
- **Flexible Operations**: Supports standard ERPNext purchase operations with optional eTIMS integration
- **Error Handling**: Comprehensive error handling with clear error messages

---

## Authentication

All endpoints require authentication via Frappe's standard authentication mechanism. Include authentication headers in your requests:

```http
Authorization: token <api_key>:<api_secret>
```

Or use session-based authentication for web requests.

---

## Endpoint Categories

### 1. Purchase Invoice Management
Endpoints for creating, updating, retrieving, and managing Purchase Invoices.

### 2. Registered Purchases (eTIMS)
Endpoints for fetching and managing purchases registered with eTIMS.

### 3. Purchase Returns
Endpoints for creating and managing purchase returns (credit notes).

### 4. Bulk Operations
Endpoints for performing bulk operations on multiple purchase invoices.

### 5. Bank and Account Management
Endpoints for managing Cash/Bank accounts and Bank Account records.

### 6. Supplier Management
Endpoints for managing suppliers, supplier groups, and supplier-related operations.

### 7. Warehouse Management
Endpoints for managing warehouses, warehouse types, and staff-warehouse assignments.

### 8. Utility Endpoints
Helper endpoints for checking status and configuration.

---

## Purchase Invoice Management

### Create Purchase Invoice

Create a new Purchase Invoice. Works for both eTIMS-registered and non-registered users.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supplier` | string | Yes | Supplier name or ID |
| `company` | string | Yes | Company name |
| `items` | array | Yes | List of items (see Item Object below) |
| `posting_date` | string | No | Posting date (YYYY-MM-DD), defaults to today |
| `bill_no` | string | No | Supplier bill number |
| `bill_date` | string | No | Supplier bill date (YYYY-MM-DD) |
| `branch` | string | No | Branch name |
| `warehouse` | string | No | Default warehouse for items |
| `currency` | string | No | Currency code, defaults to company currency |
| `taxes` | array | No | List of tax entries (see Tax Object below) |
| `update_stock` | boolean | No | Whether to update stock on submission (default: false) |
| `prevent_etims_submission` | boolean | No | Prevent submission to eTIMS even if registered (default: false) |
| `settings_name` | string | No | Specific eTIMS settings name (optional) |
| `is_paid` | boolean | No | Whether the invoice is paid immediately (default: false) |
| `paid_amount` | float | No | Amount paid (required if is_paid=true, defaults to grand_total) |
| `cash_bank_account` | string | No | Cash/Bank account for payment (required if is_paid=true) |
| `mode_of_payment` | string | No | Mode of payment name (e.g., "Cash", "Bank") |

**Item Object:**

```json
{
  "item_code": "ITEM-001",
  "qty": 10,
  "rate": 100.00,
  "warehouse": "Warehouse - Company",
  "custom_item_classification": "Classification Code",  // Optional, for eTIMS
  "custom_packaging_unit": "Packaging Unit",           // Optional, for eTIMS
  "custom_unit_of_quantity": "Unit of Quantity",       // Optional, for eTIMS
  "custom_taxation_type": "Taxation Type"              // Optional, for eTIMS
}
```

**Tax Object:**

```json
{
  "account_head": "VAT - Company",
  "charge_type": "On Net Total",
  "rate": 16.0,
  "description": "VAT"
}
```

**Request Example (Unpaid Invoice):**

```json
{
  "supplier": "Supplier Name",
  "company": "Company Name",
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 10,
      "rate": 100.00,
      "warehouse": "Warehouse - Company"
    }
  ],
  "posting_date": "2024-01-15",
  "bill_no": "BILL-001",
  "bill_date": "2024-01-15",
  "update_stock": true
}
```

**Request Example (Cash Payment):**

```json
{
  "supplier": "Supplier Name",
  "company": "Company Name",
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 10,
      "rate": 100.00,
      "warehouse": "Warehouse - Company"
    }
  ],
  "posting_date": "2024-01-15",
  "bill_no": "BILL-001",
  "bill_date": "2024-01-15",
  "update_stock": true,
  "is_paid": true,
  "paid_amount": 1160.00,
  "cash_bank_account": "Cash - Company",
  "mode_of_payment": "Cash"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Invoice created successfully",
  "name": "PI-00001",
  "has_etims": true,
  "etims_submission": "enabled",
  "is_paid": true,
  "paid_amount": 1160.00,
  "outstanding_amount": 0.00
}
```

**Cash Payment Handling:**

When `is_paid=true`, the system:
1. Marks the invoice as paid (`is_paid=1`)
2. Records the payment amount (`paid_amount`)
3. Debits the cash/bank account specified in `cash_bank_account`
4. Credits the supplier account (Accounts Payable)
5. Creates General Ledger entries automatically on submission
6. Sets `outstanding_amount` to 0 (or remaining amount if partial payment)

**Important Notes:**
- `cash_bank_account` must be a valid Cash or Bank account in the company
- `paid_amount` defaults to `grand_total` if not specified
- Payment GL entries are created when the invoice is submitted
- For partial payments, set `paid_amount` to the actual amount paid

---

### Update Purchase Invoice

Update an existing Purchase Invoice. Only works for draft invoices.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.update_purchase_invoice`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Purchase Invoice name/ID |
| `items` | array | No | Updated list of items |
| `posting_date` | string | No | Updated posting date |
| `bill_no` | string | No | Updated bill number |
| `bill_date` | string | No | Updated bill date |
| `taxes` | array | No | Updated tax entries |
| `prevent_etims_submission` | boolean | No | Update eTIMS submission flag |

**Request Example:**

```json
{
  "name": "PI-00001",
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 15,
      "rate": 100.00
    }
  ],
  "bill_no": "BILL-002"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Invoice updated successfully",
  "name": "PI-00001"
}
```

---

### Get Purchase Invoice

Retrieve details of a specific Purchase Invoice.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.get_purchase_invoice`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Purchase Invoice name/ID |

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "PI-00001",
    "supplier": "Supplier Name",
    "supplier_name": "Supplier Name",
    "company": "Company Name",
    "posting_date": "2024-01-15",
    "bill_no": "BILL-001",
    "bill_date": "2024-01-15",
    "grand_total": 1160.00,
    "total_taxes_and_charges": 160.00,
    "outstanding_amount": 1160.00,
    "status": "Unpaid",
    "docstatus": 1,
    "has_etims": true,
    "prevent_etims_submission": false,
    "custom_slade_id": "SLADE-12345",
    "items": [
      {
        "item_code": "ITEM-001",
        "item_name": "Item Name",
        "qty": 10,
        "rate": 100.00,
        "amount": 1000.00,
        "warehouse": "Warehouse - Company"
      }
    ]
  }
}
```

---

### List Purchase Invoices

List Purchase Invoices with optional filters.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.list_purchase_invoices`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supplier` | string | No | Filter by supplier |
| `company` | string | No | Filter by company |
| `from_date` | string | No | Filter from date (YYYY-MM-DD) |
| `to_date` | string | No | Filter to date (YYYY-MM-DD) |
| `status` | string | No | Filter by status (Draft, Unpaid, Paid, Overdue, etc.) |
| `limit` | integer | No | Number of records to return (default: 20) |
| `offset` | integer | No | Offset for pagination (default: 0) |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.apis.list_purchase_invoices?company=Company%20Name&from_date=2024-01-01&to_date=2024-01-31&limit=50
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "PI-00001",
      "supplier": "Supplier Name",
      "supplier_name": "Supplier Name",
      "company": "Company Name",
      "posting_date": "2024-01-15",
      "bill_no": "BILL-001",
      "grand_total": 1160.00,
      "status": "Unpaid",
      "docstatus": 1
    }
  ],
  "count": 1
}
```

---

### Submit Purchase Invoice to eTIMS

Submit a Purchase Invoice to eTIMS. Only works if eTIMS is registered for the company.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.submit_purchase_invoice_to_etims`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Purchase Invoice name/ID |
| `settings_name` | string | No | Specific eTIMS settings name (optional) |

**Request Example:**

```json
{
  "name": "PI-00001"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Invoice submitted to eTIMS successfully",
  "name": "PI-00001"
}
```

**Error Response (No eTIMS Registration):**

```json
{
  "success": false,
  "message": "eTIMS is not registered for this company",
  "has_etims": false
}
```

---

### Cancel Purchase Invoice

Cancel a Purchase Invoice.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.cancel_purchase_invoice`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Purchase Invoice name/ID |

**Request Example:**

```json
{
  "name": "PI-00001"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Invoice cancelled successfully",
  "name": "PI-00001"
}
```

---

## Registered Purchases (eTIMS)

### Fetch Registered Purchases

Fetch registered purchases from eTIMS. Only works if eTIMS is registered.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.fetch_registered_purchases`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Company name (defaults to user's default company) |
| `from_date` | string | No | Start date for search (YYYY-MM-DD) |
| `to_date` | string | No | End date for search (YYYY-MM-DD) |
| `supplier_pin` | string | No | Supplier PIN to filter |
| `settings_name` | string | No | Specific eTIMS settings name (optional) |

**Request Example:**

```json
{
  "company": "Company Name",
  "from_date": "2024-01-01",
  "to_date": "2024-01-31",
  "supplier_pin": "P123456789A"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Fetching registered purchases from eTIMS. This may take a few moments."
}
```

**Note:** This is an asynchronous operation. The registered purchases will be created as documents in the system. Use `list_registered_purchases` to retrieve them.

---

### List Registered Purchases

List Registered Purchases from eTIMS.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.list_registered_purchases`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Filter by company |
| `supplier_name` | string | No | Filter by supplier name (partial match) |
| `from_date` | string | No | Filter from date (YYYY-MM-DD) |
| `to_date` | string | No | Filter to date (YYYY-MM-DD) |
| `limit` | integer | No | Number of records to return (default: 20) |
| `offset` | integer | No | Offset for pagination (default: 0) |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.apis.list_registered_purchases?company=Company%20Name&from_date=2024-01-01&limit=50
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "RP-00001",
      "supplier_name": "Supplier Name",
      "supplier_pin": "P123456789A",
      "supplier_invoice_number": "INV-001",
      "sales_date": "2024-01-15",
      "total_amount": 1160.00,
      "total_tax_amount": 160.00,
      "workflow_state": "Approved",
      "can_send_to_etims": true
    }
  ],
  "count": 1
}
```

---

### Create Purchase Invoice from Registered Purchase

Create a Purchase Invoice from a Registered Purchase document.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice_from_registered_purchase`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `registered_purchase_name` | string | Yes | Registered Purchase document name |
| `company` | string | No | Company name (defaults to registered purchase company) |
| `warehouse` | string | No | Warehouse for items |

**Request Example:**

```json
{
  "registered_purchase_name": "RP-00001",
  "warehouse": "Warehouse - Company"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Invoice created from Registered Purchase successfully"
}
```

---

## Purchase Returns

### Create Purchase Return

Create a Purchase Return (Credit Note) against an existing Purchase Invoice.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_return`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `return_against` | string | Yes | Original Purchase Invoice name/ID |
| `items` | array | Yes | List of items to return (see Item Object below) |
| `posting_date` | string | No | Posting date (YYYY-MM-DD) |
| `company` | string | No | Company name (defaults to original invoice company) |

**Item Object (for Returns):**

```json
{
  "item_code": "ITEM-001",
  "qty": 2,
  "rate": 100.00,
  "warehouse": "Warehouse - Company"
}
```

**Request Example:**

```json
{
  "return_against": "PI-00001",
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 2,
      "rate": 100.00,
      "warehouse": "Warehouse - Company"
    }
  ],
  "posting_date": "2024-01-20"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Purchase Return created successfully",
  "name": "PI-00002",
  "return_against": "PI-00001"
}
```

---

## Bulk Operations

### Bulk Submit Purchase Invoices to eTIMS

Submit multiple Purchase Invoices to eTIMS in a single request.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.bulk_submit_purchase_invoices`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `purchase_invoice_names` | array | Yes | List of Purchase Invoice names/IDs |
| `settings_name` | string | No | Specific eTIMS settings name (optional) |

**Request Example:**

```json
{
  "purchase_invoice_names": [
    "PI-00001",
    "PI-00002",
    "PI-00003"
  ]
}
```

**Response Example:**

```json
{
  "success": true,
  "submitted": ["PI-00001", "PI-00002"],
  "failed": [
    {
      "name": "PI-00003",
      "error": "eTIMS is not registered for this company"
    }
  ],
  "total": 3,
  "submitted_count": 2,
  "failed_count": 1
}
```

---

## Bank and Account Management

Bank and Account management endpoints allow you to create and manage Cash/Bank accounts and Bank Account records. These are essential for processing cash payments in purchase invoices.

### Account Types

In ERPNext, accounts can be:
- **Cash**: Physical cash accounts
- **Bank**: Bank accounts for electronic payments

### Create Cash or Bank Account

Create a new Cash or Bank account for a company.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_cash_or_bank_account`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_name` | string | Yes | Name of the account |
| `company` | string | Yes | Company name |
| `account_type` | string | Yes | Account type ("Cash" or "Bank") |
| `parent_account` | string | No | Parent account name (auto-detected if not provided) |
| `account_number` | string | No | Account number |
| `account_currency` | string | No | Currency code (defaults to company currency) |
| `is_group` | boolean | No | Whether this is a group account (default: false) |

**Request Example:**

```json
{
  "account_name": "Main Cash Account",
  "company": "Company Name",
  "account_type": "Cash",
  "account_number": "CASH-001"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Cash account created successfully",
  "name": "Main Cash Account - Company",
  "account_name": "Main Cash Account",
  "account_type": "Cash",
  "company": "Company Name"
}
```

---

### List Cash and Bank Accounts

List all Cash and Bank accounts for a company.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.list_cash_and_bank_accounts`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Filter by company (defaults to user's default company) |
| `account_type` | string | No | Filter by account type ("Cash" or "Bank") |
| `include_disabled` | boolean | No | Include disabled accounts (default: false) |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.apis.list_cash_and_bank_accounts?company=Company%20Name&account_type=Cash
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Main Cash Account - Company",
      "account_name": "Main Cash Account",
      "account_type": "Cash",
      "account_number": "CASH-001",
      "account_currency": "KES",
      "parent_account": "Cash In Hand - Company",
      "disabled": 0,
      "company": "Company Name"
    }
  ],
  "count": 1
}
```

---

### Get Account Details

Get detailed information about a specific account, including balance.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.get_account_details`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Account name/ID |

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "Main Cash Account - Company",
    "account_name": "Main Cash Account",
    "account_type": "Cash",
    "account_number": "CASH-001",
    "account_currency": "KES",
    "company": "Company Name",
    "parent_account": "Cash In Hand - Company",
    "is_group": 0,
    "disabled": 0,
    "root_type": "Asset",
    "report_type": "Balance Sheet",
    "balance": 50000.00
  }
}
```

---

### Create Bank Master

Create a Bank master record.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_bank`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bank_name` | string | Yes | Name of the bank |
| `swift_number` | string | No | SWIFT/BIC code |

**Request Example:**

```json
{
  "bank_name": "Equity Bank",
  "swift_number": "EQBLKENA"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Bank created successfully",
  "name": "Equity Bank",
  "bank_name": "Equity Bank"
}
```

---

### List Banks

List all bank master records.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.list_banks`

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Equity Bank",
      "bank_name": "Equity Bank",
      "swift_number": "EQBLKENA"
    }
  ],
  "count": 1
}
```

---

### Create Bank Account

Create a Bank Account record that links a Bank to an Account. This is useful for bank reconciliation and detailed bank account management.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.create_bank_account`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_name` | string | Yes | Name for the bank account record |
| `bank` | string | Yes | Bank name/ID |
| `company` | string | Yes | Company name |
| `account` | string | No | Company Account name/ID (will create if not provided) |
| `account_type` | string | No | Bank Account Type |
| `account_subtype` | string | No | Bank Account Subtype |
| `bank_account_no` | string | No | Bank account number |
| `iban` | string | No | IBAN |
| `branch_code` | string | No | Branch code |
| `is_company_account` | boolean | No | Whether this is a company account (default: true) |
| `is_default` | boolean | No | Whether this is the default account (default: false) |

**Request Example:**

```json
{
  "account_name": "Equity Bank Main Account",
  "bank": "Equity Bank",
  "company": "Company Name",
  "bank_account_no": "1234567890",
  "iban": "KE1234567890123456789012",
  "branch_code": "001",
  "is_company_account": true,
  "is_default": true
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Bank Account created successfully",
  "name": "Equity Bank Main Account",
  "account_name": "Equity Bank Main Account",
  "bank": "Equity Bank",
  "account": "Equity Bank Main Account - Company",
  "company": "Company Name"
}
```

---

### List Bank Accounts

List all Bank Account records.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.list_bank_accounts`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Filter by company |
| `bank` | string | No | Filter by bank |
| `is_company_account` | boolean | No | Filter by company account flag |

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Equity Bank Main Account",
      "account_name": "Equity Bank Main Account",
      "bank": "Equity Bank",
      "account": "Equity Bank Main Account - Company",
      "company": "Company Name",
      "bank_account_no": "1234567890",
      "iban": "KE1234567890123456789012",
      "branch_code": "001",
      "is_company_account": 1,
      "is_default": 1,
      "disabled": 0
    }
  ],
  "count": 1
}
```

---

### Get Bank Account Details

Get detailed information about a specific Bank Account.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.get_bank_account_details`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Bank Account name/ID |

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "Equity Bank Main Account",
    "account_name": "Equity Bank Main Account",
    "bank": "Equity Bank",
    "account": "Equity Bank Main Account - Company",
    "company": "Company Name",
    "bank_account_no": "1234567890",
    "iban": "KE1234567890123456789012",
    "branch_code": "001",
    "account_type": null,
    "account_subtype": null,
    "is_company_account": 1,
    "is_default": 1,
    "disabled": 0,
    "account_details": {
      "name": "Equity Bank Main Account - Company",
      "account_name": "Equity Bank Main Account",
      "account_type": "Bank",
      "balance": 100000.00
    }
  }
}
```

---

### Update Account

Update an existing account.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.apis.update_account`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Account name/ID |
| `account_name` | string | No | Updated account name |
| `account_number` | string | No | Updated account number |
| `disabled` | boolean | No | Update disabled status |

**Request Example:**

```json
{
  "name": "Main Cash Account - Company",
  "account_name": "Updated Cash Account Name",
  "disabled": false
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Account updated successfully",
  "name": "Main Cash Account - Company"
}
```

---

## Supplier Management

Supplier management endpoints allow you to create, list, update, and manage suppliers. These are essential for purchase invoice creation and supplier relationship management.

### Get Suppliers

Get a list of suppliers with optional filters. Supports both GET (query parameters) and POST (JSON payload) requests.

**Endpoint:** 
- `GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_suppliers`
- `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_suppliers`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Company name (optional, filters suppliers that have transactions with this company) |
| `supplier_group` | string | No | Filter by supplier group |
| `disabled` | boolean | No | Include disabled suppliers (default: false) |
| `limit` | integer | No | Number of records to return (default: 20) |
| `offset` | integer | No | Offset for pagination (default: 0) |
| `search_term` | string | No | Search term for supplier name or ID |
| `filter_by_company_transactions` | boolean | No | If True and company is provided, only return suppliers with transactions for that company (default: false) |

**Company Filtering:**
- By default, all suppliers are returned regardless of company transactions (`filter_by_company_transactions=False`)
- When `company` is provided and `filter_by_company_transactions=True`, the endpoint returns only suppliers that have Purchase Invoices or Purchase Orders for that company
- If no suppliers have transactions for the specified company when filtering is enabled, an empty list is returned

**Example Use Cases:**
- No `company` parameter or `filter_by_company_transactions=False` (default) → Returns all suppliers matching other filters
- `company="Company A"` + `filter_by_company_transactions=True` → Returns only suppliers used in Company A
- `company="Company A"` + `filter_by_company_transactions=False` → Returns all suppliers (company parameter ignored)

**Request Example (GET with query parameters):**

```
GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_suppliers?company=Company%20Name&limit=50&search_term=ABC&filter_by_company_transactions=true
```

**Request Example (POST with JSON payload):**

```json
{
  "company": "Company Name",
  "supplier_group": "All Supplier Groups",
  "limit": 50,
  "offset": 0,
  "search_term": "ABC",
  "filter_by_company_transactions": true,
  "disabled": false
}
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "SUP-00001",
      "supplier_name": "ABC Suppliers Ltd",
      "supplier_type": "Company",
      "supplier_group": "All Supplier Groups",
      "tax_id": "P123456789A",
      "disabled": 0,
      "is_internal_supplier": 0,
      "country": "Kenya",
      "default_currency": "KES"
    }
  ],
  "count": 1
}
```

---

### Get Supplier Details

Get detailed information about a specific supplier, including outstanding amounts and purchase statistics.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_details`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Supplier name/ID |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_details?name=SUP-00001
```

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "SUP-00001",
    "supplier_name": "ABC Suppliers Ltd",
    "supplier_type": "Company",
    "supplier_group": "All Supplier Groups",
    "tax_id": "P123456789A",
    "disabled": 0,
    "is_internal_supplier": 0,
    "country": "Kenya",
    "default_currency": "KES",
    "outstanding_amount": 50000.00,
    "total_purchase": 500000.00
  }
}
```

---

### Create Supplier

Create a new supplier.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.create_supplier`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supplier_name` | string | Yes | Name of the supplier |
| `supplier_group` | string | No | Supplier group (defaults to first available group) |
| `tax_id` | string | No | Tax ID/PIN |
| `country` | string | No | Country |
| `default_currency` | string | No | Default currency |
| `supplier_type` | string | No | Supplier type - "Company" or "Individual" (default: "Company") |
| `is_internal_supplier` | boolean | No | Whether this is an internal supplier (default: false) |

**Request Example:**

```json
{
  "supplier_name": "ABC Suppliers Ltd",
  "supplier_group": "All Supplier Groups",
  "tax_id": "P123456789A",
  "country": "Kenya",
  "default_currency": "KES",
  "supplier_type": "Company"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Supplier created successfully",
  "name": "SUP-00001",
  "supplier_name": "ABC Suppliers Ltd"
}
```

**Error Response (Permission Denied):**

```json
{
  "success": false,
  "message": "Permission denied: You do not have permission to create Supplier documents. Please contact your administrator to grant you the necessary role permissions.",
  "error_type": "permission_error",
  "required_permission": "Supplier: Create"
}
```

**Note:** If you receive a permission error, ensure your user role has the "Supplier: Create" permission. See the [Permissions](#permissions) section below for details.

---

### Update Supplier

Update an existing supplier.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.update_supplier`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Supplier name/ID |
| `supplier_name` | string | No | Updated supplier name |
| `supplier_group` | string | No | Updated supplier group |
| `tax_id` | string | No | Updated tax ID |
| `country` | string | No | Updated country |
| `default_currency` | string | No | Updated default currency |
| `disabled` | boolean | No | Update disabled status |

**Request Example:**

```json
{
  "name": "SUP-00001",
  "supplier_name": "ABC Suppliers Ltd - Updated",
  "tax_id": "P987654321B",
  "disabled": false
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Supplier updated successfully",
  "name": "SUP-00001"
}
```

---

### Get Supplier Groups

Get a list of all supplier groups with optional filters.

**Endpoint:** 
- `GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_groups`
- `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_groups`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_group` | boolean | No | Filter by is_group flag (true for groups, false for leaf nodes) |
| `parent_supplier_group` | string | No | Filter by parent supplier group |
| `limit` | integer | No | Number of records to return (default: 100) |
| `offset` | integer | No | Offset for pagination (default: 0) |

**Request Example (GET):**

```
GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_groups?is_group=false&limit=50
```

**Request Example (POST with JSON payload):**

```json
{
  "is_group": false,
  "parent_supplier_group": "All Supplier Groups",
  "limit": 50,
  "offset": 0
}
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "All Supplier Groups",
      "supplier_group_name": "All Supplier Groups",
      "is_group": 1,
      "parent_supplier_group": null
    },
    {
      "name": "Local Suppliers",
      "supplier_group_name": "Local Suppliers",
      "is_group": 0,
      "parent_supplier_group": "All Supplier Groups"
    }
  ],
  "count": 2
}
```

---

### Create Supplier Group

Create a new supplier group.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.create_supplier_group`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `supplier_group_name` | string | Yes | Name of the supplier group (must be unique) |
| `parent_supplier_group` | string | No | Parent supplier group name (defaults to root group) |
| `is_group` | boolean | No | Whether this is a group (default: false) |
| `payment_terms` | string | No | Default payment terms template (optional) |

**Request Example:**

```json
{
  "supplier_group_name": "Local Suppliers",
  "parent_supplier_group": "All Supplier Groups",
  "is_group": false,
  "payment_terms": "Net 30"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Supplier Group created successfully",
  "name": "Local Suppliers",
  "supplier_group_name": "Local Suppliers",
  "is_group": 0,
  "parent_supplier_group": "All Supplier Groups"
}
```

**Error Response (Permission Denied):**

```json
{
  "success": false,
  "message": "Permission denied: You do not have permission to create Supplier Group documents. Please contact your administrator to grant you the necessary role permissions.",
  "error_type": "permission_error",
  "required_permission": "Supplier Group: Create"
}
```

---

### Update Supplier Group

Update an existing supplier group.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.supplier_api.update_supplier_group`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Supplier Group name/ID |
| `supplier_group_name` | string | No | Updated supplier group name |
| `parent_supplier_group` | string | No | Updated parent supplier group |
| `is_group` | boolean | No | Update is_group flag |
| `payment_terms` | string | No | Updated payment terms |

**Request Example:**

```json
{
  "name": "Local Suppliers",
  "supplier_group_name": "Local Suppliers - Updated",
  "payment_terms": "Net 45"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Supplier Group updated successfully",
  "name": "Local Suppliers"
}
```

---

### Get Supplier Group Details

Get detailed information about a specific supplier group, including supplier count.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_group_details`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Supplier Group name/ID |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_group_details?name=Local%20Suppliers
```

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "Local Suppliers",
    "supplier_group_name": "Local Suppliers",
    "is_group": 0,
    "parent_supplier_group": "All Supplier Groups",
    "payment_terms": "Net 30",
    "supplier_count": 15
  }
}
```

---

## Warehouse Management

Warehouse management endpoints allow you to create, manage, and assign warehouses to staff members. The system supports two main types of warehouses:

1. **Regional Depot**: A regional distribution center that can serve multiple companies
2. **Company Warehouses/Shops**: Regular warehouses or shops belonging to a specific company
   - A company can have multiple warehouses/shops
   - A company can optionally have one main depot

**Key Features:**
- **Default Warehouse Assignment**: Each company can have a default warehouse that is automatically used when no warehouse is explicitly specified in transactions
- **Staff Assignment**: Staff members can be assigned to specific warehouses, which restricts their access to data within those warehouses only
- **Hierarchical Structure**: Warehouses can be organized in a hierarchical structure using parent warehouses

---

### Create Warehouse

Create a new warehouse with optional address and contact information.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.create_warehouse`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `warehouse_name` | string | Yes | Name of the warehouse |
| `company` | string | Yes | Company name |
| `warehouse_type` | string | No | Type: "Regional Depot", "Company Warehouse", "Shop", or "Main Depot" |
| `parent_warehouse` | string | No | Parent warehouse name (for hierarchical structure) |
| `is_group` | boolean | No | Whether this is a group warehouse (default: false) |
| `is_main_depot` | boolean | No | Whether this is the main depot for the company (default: false) |
| `set_as_default` | boolean | No | Whether to set this warehouse as the default warehouse for the company (default: false) |
| `account` | string | No | Warehouse account |
| `address_line_1` | string | No | Address line 1 |
| `address_line_2` | string | No | Address line 2 |
| `city` | string | No | City |
| `state` | string | No | State/Province |
| `pin` | string | No | PIN code |
| `phone_no` | string | No | Phone number |
| `mobile_no` | string | No | Mobile number |
| `email_id` | string | No | Email address |

**Request Example:**

```json
{
  "warehouse_name": "Nairobi Main Depot",
  "company": "Company Name",
  "warehouse_type": "Main Depot",
  "is_main_depot": true,
  "set_as_default": true,
  "address_line_1": "123 Main Street",
  "city": "Nairobi",
  "state": "Nairobi",
  "pin": "00100",
  "phone_no": "+254 20 1234567",
  "mobile_no": "+254 712 345678",
  "email_id": "warehouse@company.com"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Warehouse created successfully",
  "name": "Nairobi Main Depot - COM",
  "warehouse_name": "Nairobi Main Depot",
  "company": "Company Name",
  "warehouse_type": "Main Depot",
  "is_group": 0,
  "is_main_depot": true,
  "set_as_default": true,
  "parent_warehouse": null
}
```

---

### List Warehouses

Get a list of warehouses with optional filters.

**Endpoint:** 
- `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.list_warehouses`
- `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.list_warehouses`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Filter by company |
| `warehouse_type` | string | No | Filter by warehouse type |
| `is_group` | boolean | No | Filter by is_group flag |
| `is_main_depot` | boolean | No | Filter by main depot flag |
| `parent_warehouse` | string | No | Filter by parent warehouse |
| `limit` | integer | No | Number of records to return (default: 100) |
| `offset` | integer | No | Offset for pagination (default: 0) |

**Request Example (GET):**

```
GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.list_warehouses?company=Company%20Name&is_main_depot=false&limit=50
```

**Request Example (POST):**

```json
{
  "company": "Company Name",
  "warehouse_type": "Shop",
  "is_main_depot": false,
  "limit": 50,
  "offset": 0
}
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Nairobi Main Depot - COM",
      "warehouse_name": "Nairobi Main Depot",
      "company": "Company Name",
      "warehouse_type": "Main Depot",
      "is_group": 0,
      "is_main_depot": true,
      "is_default": true,
      "parent_warehouse": null,
      "disabled": 0,
      "address_line_1": "123 Main Street",
      "city": "Nairobi",
      "state": "Nairobi"
    },
    {
      "name": "Westlands Shop - COM",
      "warehouse_name": "Westlands Shop",
      "company": "Company Name",
      "warehouse_type": "Shop",
      "is_group": 0,
      "is_main_depot": false,
      "is_default": false,
      "parent_warehouse": null,
      "disabled": 0,
      "address_line_1": "456 Park Road",
      "city": "Nairobi",
      "state": "Nairobi"
    }
  ],
  "count": 2
}
```

**Note:** The `is_default` field indicates whether the warehouse is set as the default warehouse for its company. This field is automatically included in the response to help identify which warehouse is used as the default when no warehouse is explicitly specified in transactions.

---

### Get Warehouse Details

Get detailed information about a specific warehouse.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_warehouse_details`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Warehouse name/ID |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_warehouse_details?name=Nairobi%20Main%20Depot%20-%20COM
```

**Response Example:**

```json
{
  "success": true,
  "data": {
    "name": "Nairobi Main Depot - COM",
    "warehouse_name": "Nairobi Main Depot",
    "company": "Company Name",
    "warehouse_type": "Main Depot",
    "warehouse_type_description": "Warehouse type: Main Depot",
    "is_group": 0,
    "is_main_depot": true,
    "parent_warehouse": null,
    "account": "Stock In Hand - COM",
    "disabled": 0,
    "address_line_1": "123 Main Street",
    "address_line_2": null,
    "city": "Nairobi",
    "state": "Nairobi",
    "pin": "00100",
    "phone_no": "+254 20 1234567",
    "mobile_no": "+254 712 345678",
    "email_id": "warehouse@company.com"
  }
}
```

---

### Update Warehouse

Update an existing warehouse.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.update_warehouse`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Warehouse name/ID |
| `warehouse_name` | string | No | Updated warehouse name |
| `warehouse_type` | string | No | Updated warehouse type |
| `parent_warehouse` | string | No | Updated parent warehouse |
| `is_group` | boolean | No | Update is_group flag |
| `is_main_depot` | boolean | No | Update main depot flag |
| `account` | string | No | Updated account |
| `disabled` | boolean | No | Update disabled status |
| `address_line_1` | string | No | Updated address line 1 |
| `address_line_2` | string | No | Updated address line 2 |
| `city` | string | No | Updated city |
| `state` | string | No | Updated state |
| `pin` | string | No | Updated PIN |
| `phone_no` | string | No | Updated phone number |
| `mobile_no` | string | No | Updated mobile number |
| `email_id` | string | No | Updated email |

**Request Example:**

```json
{
  "name": "Nairobi Main Depot - COM",
  "warehouse_name": "Nairobi Main Depot - Updated",
  "phone_no": "+254 20 9876543",
  "disabled": false
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Warehouse updated successfully",
  "name": "Nairobi Main Depot - COM"
}
```

---

### Assign Warehouses to Staff

Assign one or more warehouses to a staff member. This restricts the staff member's access to only the assigned warehouses.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.assign_warehouses_to_staff`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_email` | string | Yes | Staff user email |
| `warehouses` | array | Yes | List of warehouse names/IDs to assign |
| `replace_existing` | boolean | No | Whether to replace existing assignments (default: true) |

**Request Example:**

```json
{
  "user_email": "staff@company.com",
  "warehouses": [
    "Nairobi Main Depot - COM",
    "Westlands Shop - COM"
  ],
  "replace_existing": true
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Successfully assigned 2 warehouse(s) to user",
  "user": "staff@company.com",
  "warehouses": [
    "Nairobi Main Depot - COM",
    "Westlands Shop - COM"
  ],
  "count": 2
}
```

**Note:** When warehouses are assigned to a staff member, they will only be able to access data (stock, transactions, etc.) related to those warehouses. If no warehouses are assigned, the staff member has access to all warehouses (subject to other permissions).

---

### Get Staff Warehouses

Get list of warehouses assigned to a staff member. If `user_email` is not provided, returns warehouses for the current user.

**Endpoint:** 
- `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_staff_warehouses`
- `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_staff_warehouses`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_email` | string | No | Staff user email (defaults to current user) |

**Request Example (GET):**

```
GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_staff_warehouses?user_email=staff@company.com
```

**Request Example (POST):**

```json
{
  "user_email": "staff@company.com"
}
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Nairobi Main Depot - COM",
      "warehouse_name": "Nairobi Main Depot",
      "company": "Company Name",
      "warehouse_type": "Main Depot",
      "is_group": 0,
      "is_main_depot": true,
      "parent_warehouse": null,
      "disabled": 0
    },
    {
      "name": "Westlands Shop - COM",
      "warehouse_name": "Westlands Shop",
      "company": "Company Name",
      "warehouse_type": "Shop",
      "is_group": 0,
      "is_main_depot": false,
      "parent_warehouse": null,
      "disabled": 0
    }
  ],
  "count": 2,
  "user": "staff@company.com"
}
```

**Response Example (No Warehouses Assigned):**

```json
{
  "success": true,
  "data": [],
  "count": 0,
  "message": "No warehouses assigned to this user. User has access to all warehouses.",
  "user": "staff@company.com"
}
```

---

### Get Warehouse Staff

Get list of staff members assigned to a specific warehouse.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_warehouse_staff`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `warehouse` | string | Yes | Warehouse name/ID |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_warehouse_staff?warehouse=Nairobi%20Main%20Depot%20-%20COM
```

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "staff@company.com",
      "email": "staff@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "enabled": 1
    }
  ],
  "count": 1,
  "warehouse": "Nairobi Main Depot - COM"
}
```

---

### Remove Warehouse from Staff

Remove a warehouse assignment from a staff member.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.remove_warehouse_from_staff`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_email` | string | Yes | Staff user email |
| `warehouse` | string | Yes | Warehouse name/ID to remove |

**Request Example:**

```json
{
  "user_email": "staff@company.com",
  "warehouse": "Westlands Shop - COM"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Successfully removed warehouse 'Westlands Shop - COM' from user 'staff@company.com'"
}
```

---

### Set Default Warehouse

Set a warehouse as the default warehouse for a company. The default warehouse is used when no warehouse is explicitly specified in transactions.

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.set_default_warehouse`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | Yes | Company name |
| `warehouse` | string | Yes | Warehouse name/ID to set as default |

**Request Example:**

```json
{
  "company": "Company Name",
  "warehouse": "Nairobi Main Depot - COM"
}
```

**Response Example:**

```json
{
  "success": true,
  "message": "Default warehouse set successfully for company 'Company Name'",
  "company": "Company Name",
  "warehouse": "Nairobi Main Depot - COM"
}
```

**Error Response (Warehouse doesn't belong to company):**

```json
{
  "success": false,
  "message": "Warehouse 'Nairobi Main Depot - COM' does not belong to company 'Company Name'"
}
```

---

### Get Default Warehouse

Get the default warehouse for a company.

**Endpoint:** 
- `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_default_warehouse`
- `POST /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_default_warehouse`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | Yes | Company name |

**Request Example (GET):**

```
GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_default_warehouse?company=Company%20Name
```

**Request Example (POST):**

```json
{
  "company": "Company Name"
}
```

**Response Example (Default warehouse set):**

```json
{
  "success": true,
  "data": {
    "name": "Nairobi Main Depot - COM",
    "warehouse_name": "Nairobi Main Depot",
    "company": "Company Name",
    "warehouse_type": "Main Depot",
    "is_group": 0,
    "parent_warehouse": null
  }
}
```

**Response Example (No default warehouse set):**

```json
{
  "success": true,
  "data": null,
  "message": "No default warehouse set for company 'Company Name'"
}
```

**Note:** The default warehouse feature allows you to assign a default warehouse for each company. When creating warehouses, you can use the `set_as_default` parameter to automatically set the warehouse as the default during creation. Alternatively, you can use the `set_default_warehouse` endpoint to set an existing warehouse as the default. The default warehouse is used by other APIs (like inventory APIs) when no warehouse is explicitly provided.

---

### List Warehouse Types

Get list of all warehouse types.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.warehouse_api.list_warehouse_types`

**Response Example:**

```json
{
  "success": true,
  "data": [
    {
      "name": "Regional Depot",
      "description": "Warehouse type: Regional Depot"
    },
    {
      "name": "Company Warehouse",
      "description": "Warehouse type: Company Warehouse"
    },
    {
      "name": "Shop",
      "description": "Warehouse type: Shop"
    },
    {
      "name": "Main Depot",
      "description": "Warehouse type: Main Depot"
    }
  ],
  "count": 4
}
```

---

## Utility Endpoints

### Check eTIMS Registration Status

Check if eTIMS is registered for a company.

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.apis.check_etims_registration_status`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Company name (defaults to user's default company) |

**Request Example:**

```
GET /api/method/savanna_pos.savanna_pos.apis.apis.check_etims_registration_status?company=Company%20Name
```

**Response Example (eTIMS Registered):**

```json
{
  "success": true,
  "company": "Company Name",
  "has_etims": true,
  "settings_name": "Settings-001",
  "is_active": true
}
```

**Response Example (Not Registered):**

```json
{
  "success": true,
  "company": "Company Name",
  "has_etims": false,
  "settings_name": null,
  "is_active": false
}
```

---

## Error Handling

All endpoints return a consistent error format:

```json
{
  "success": false,
  "message": "Error description",
  "error_type": "error_category"  // Optional: permission_error, validation_error, general_error
}
```

### Common Error Scenarios

1. **Permission Denied**
   ```json
   {
     "success": false,
     "message": "Permission denied: You do not have permission to create Supplier documents. Please contact your administrator to grant you the necessary role permissions.",
     "error_type": "permission_error",
     "required_permission": "Supplier: Create"
   }
   ```
   **Solution:** Grant the required permissions to the user's role (see [Permissions](#permissions) section).

2. **eTIMS Not Registered**
   ```json
   {
     "success": false,
     "message": "eTIMS is not registered for this company",
     "has_etims": false
   }
   ```

3. **Document Not Found**
   ```json
   {
     "success": false,
     "message": "Purchase Invoice PI-00001 not found"
   }
   ```

4. **Invalid State**
   ```json
   {
     "success": false,
     "message": "Purchase Invoice must be submitted before sending to eTIMS"
   }
   ```

5. **Validation Error**
   ```json
   {
     "success": false,
     "message": "Supplier is required",
     "error_type": "validation_error"
   }
   ```

---

## Examples

### Example 1: Create Purchase Invoice (Non-eTIMS User)

```python
import requests

url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice"
headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

data = {
    "supplier": "Supplier Name",
    "company": "Company Name",
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 10,
            "rate": 100.00,
            "warehouse": "Warehouse - Company"
        }
    ],
    "posting_date": "2024-01-15",
    "bill_no": "BILL-001",
    "update_stock": True
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Example 2: Create Purchase Invoice (eTIMS User)

```python
import requests

url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice"
headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

data = {
    "supplier": "Supplier Name",
    "company": "Company Name",
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 10,
            "rate": 100.00,
            "warehouse": "Warehouse - Company",
            "custom_item_classification": "Classification Code",
            "custom_packaging_unit": "Packaging Unit",
            "custom_unit_of_quantity": "Unit of Quantity",
            "custom_taxation_type": "Taxation Type"
        }
    ],
    "posting_date": "2024-01-15",
    "bill_no": "BILL-001",
    "update_stock": True
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

if result.get("has_etims"):
    # Submit to eTIMS after creation
    submit_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.submit_purchase_invoice_to_etims"
    submit_data = {"name": result["name"]}
    submit_response = requests.post(submit_url, json=submit_data, headers=headers)
    print(submit_response.json())
```

### Example 3: Fetch and Create Purchase Invoice from eTIMS

```python
import requests
import time

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Fetch registered purchases
fetch_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.fetch_registered_purchases"
fetch_data = {
    "company": "Company Name",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31"
}
fetch_response = requests.post(fetch_url, json=fetch_data, headers=headers)
print("Fetch initiated:", fetch_response.json())

# Step 2: Wait a moment for processing
time.sleep(5)

# Step 3: List registered purchases
list_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.list_registered_purchases"
list_params = {
    "company": "Company Name",
    "from_date": "2024-01-01",
    "limit": 10
}
list_response = requests.get(list_url, params=list_params, headers=headers)
registered_purchases = list_response.json()

# Step 4: Create purchase invoice from first registered purchase
if registered_purchases.get("data"):
    first_purchase = registered_purchases["data"][0]
    create_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice_from_registered_purchase"
    create_data = {
        "registered_purchase_name": first_purchase["name"],
        "warehouse": "Warehouse - Company"
    }
    create_response = requests.post(create_url, json=create_data, headers=headers)
    print("Purchase Invoice created:", create_response.json())
```

### Example 4: Check eTIMS Status Before Operations

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# Check eTIMS status
status_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.check_etims_registration_status"
status_params = {"company": "Company Name"}
status_response = requests.get(status_url, params=status_params, headers=headers)
status = status_response.json()

if status.get("has_etims"):
    print(f"eTIMS is registered. Settings: {status['settings_name']}")
    # Proceed with eTIMS-enabled operations
else:
    print("eTIMS is not registered. Using standard purchase operations.")
    # Proceed with standard operations
```

### Example 5: Create Cash Account and Use for Purchase Payment

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Create a Cash account
create_account_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_cash_or_bank_account"
account_data = {
    "account_name": "Main Cash Account",
    "company": "Company Name",
    "account_type": "Cash",
    "account_number": "CASH-001"
}
account_response = requests.post(create_account_url, json=account_data, headers=headers)
account_result = account_response.json()

if account_result.get("success"):
    cash_account = account_result["name"]
    print(f"Cash account created: {cash_account}")
    
    # Step 2: Create purchase invoice with cash payment
    purchase_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice"
    purchase_data = {
        "supplier": "Supplier Name",
        "company": "Company Name",
        "items": [
            {
                "item_code": "ITEM-001",
                "qty": 10,
                "rate": 100.00,
                "warehouse": "Warehouse - Company"
            }
        ],
        "is_paid": True,
        "paid_amount": 1160.00,
        "cash_bank_account": cash_account,
        "mode_of_payment": "Cash",
        "update_stock": True
    }
    purchase_response = requests.post(purchase_url, json=purchase_data, headers=headers)
    print("Purchase invoice created:", purchase_response.json())
```

### Example 6: Create Bank and Bank Account

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Create Bank master
create_bank_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_bank"
bank_data = {
    "bank_name": "Equity Bank",
    "swift_number": "EQBLKENA"
}
bank_response = requests.post(create_bank_url, json=bank_data, headers=headers)
bank_result = bank_response.json()

if bank_result.get("success"):
    bank_name = bank_result["name"]
    print(f"Bank created: {bank_name}")
    
    # Step 2: Create Bank Account
    create_bank_account_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_bank_account"
    bank_account_data = {
        "account_name": "Equity Bank Main Account",
        "bank": bank_name,
        "company": "Company Name",
        "bank_account_no": "1234567890",
        "iban": "KE1234567890123456789012",
        "branch_code": "001",
        "is_company_account": True,
        "is_default": True
    }
    bank_account_response = requests.post(create_bank_account_url, json=bank_account_data, headers=headers)
    print("Bank Account created:", bank_account_response.json())
```

### Example 7: List Available Cash/Bank Accounts for Payment

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# List all cash and bank accounts
list_accounts_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.list_cash_and_bank_accounts"
params = {
    "company": "Company Name",
    "account_type": "Cash"  # or "Bank" for bank accounts
}
response = requests.get(list_accounts_url, params=params, headers=headers)
accounts = response.json()

if accounts.get("success"):
    print("Available accounts:")
    for account in accounts["data"]:
        print(f"- {account['account_name']} ({account['account_type']}): {account['name']}")
        # Use account['name'] as cash_bank_account in purchase invoice
```

### Example 8: Create Supplier and Use in Purchase Invoice

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Create a supplier
create_supplier_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.create_supplier"
supplier_data = {
    "supplier_name": "ABC Suppliers Ltd",
    "supplier_group": "All Supplier Groups",
    "tax_id": "P123456789A",
    "country": "Kenya",
    "default_currency": "KES",
    "supplier_type": "Company"
}
supplier_response = requests.post(create_supplier_url, json=supplier_data, headers=headers)
supplier_result = supplier_response.json()

if supplier_result.get("success"):
    supplier_name = supplier_result["name"]
    print(f"Supplier created: {supplier_name}")
    
    # Step 2: Create purchase invoice with the new supplier
    purchase_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice"
    purchase_data = {
        "supplier": supplier_name,
        "company": "Company Name",
        "items": [
            {
                "item_code": "ITEM-001",
                "qty": 10,
                "rate": 100.00,
                "warehouse": "Warehouse - Company"
            }
        ],
        "posting_date": "2024-01-15",
        "bill_no": "BILL-001",
        "update_stock": True
    }
    purchase_response = requests.post(purchase_url, json=purchase_data, headers=headers)
    print("Purchase invoice created:", purchase_response.json())
```

### Example 9: Search and List Suppliers

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# Example 1: Get all suppliers (no company filter)
get_suppliers_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.get_suppliers"
params = {
    "search_term": "ABC",
    "limit": 50
}
response = requests.get(get_suppliers_url, params=params, headers=headers)
suppliers = response.json()

if suppliers.get("success"):
    print(f"Found {suppliers['count']} suppliers:")
    for supplier in suppliers["data"]:
        print(f"- {supplier['supplier_name']} ({supplier['name']})")

# Example 2: Get suppliers filtered by company (using GET)
params = {
    "company": "Company Name",
    "filter_by_company_transactions": True,
    "limit": 50
}
response = requests.get(get_suppliers_url, params=params, headers=headers)
suppliers = response.json()

# Example 3: Get suppliers filtered by company (using POST with JSON payload)
headers["Content-Type"] = "application/json"
payload = {
    "company": "Company Name",
    "supplier_group": "All Supplier Groups",
    "limit": 50,
    "offset": 0,
    "search_term": "ABC",
    "filter_by_company_transactions": True,
    "disabled": False
}
response = requests.post(get_suppliers_url, json=payload, headers=headers)
suppliers = response.json()

if suppliers.get("success"):
    print(f"Found {suppliers['count']} suppliers for Company Name:")
    for supplier in suppliers["data"]:
        print(f"- {supplier['supplier_name']} ({supplier['name']})")
        if supplier.get("tax_id"):
            print(f"  Tax ID: {supplier['tax_id']}")
```

### Example 10: Get Supplier Details and Outstanding Amount

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# Get supplier details
get_details_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_details"
params = {"name": "SUP-00001"}
response = requests.get(get_details_url, params=params, headers=headers)
supplier = response.json()

if supplier.get("success"):
    data = supplier["data"]
    print(f"Supplier: {data['supplier_name']}")
    print(f"Outstanding Amount: {data['outstanding_amount']}")
    print(f"Total Purchases: {data['total_purchase']}")
    print(f"Tax ID: {data.get('tax_id', 'N/A')}")
```

### Example 11: Create Supplier Group and Use It

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Create a supplier group
create_group_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.create_supplier_group"
group_data = {
    "supplier_group_name": "Local Suppliers",
    "parent_supplier_group": "All Supplier Groups",
    "is_group": False,
    "payment_terms": "Net 30"
}
group_response = requests.post(create_group_url, json=group_data, headers=headers)
group_result = group_response.json()

if group_result.get("success"):
    group_name = group_result["name"]
    print(f"Supplier Group created: {group_name}")
    
    # Step 2: Create a supplier with the new group
    create_supplier_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.create_supplier"
    supplier_data = {
        "supplier_name": "ABC Suppliers Ltd",
        "supplier_group": group_name,
        "tax_id": "P123456789A",
        "country": "Kenya"
    }
    supplier_response = requests.post(create_supplier_url, json=supplier_data, headers=headers)
    print("Supplier created:", supplier_response.json())
```

### Example 12: List and Filter Supplier Groups

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# Get all supplier groups (leaf nodes only)
get_groups_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.supplier_api.get_supplier_groups"
params = {
    "is_group": False,  # Get only leaf nodes (not groups)
    "limit": 100
}
response = requests.get(get_groups_url, params=params, headers=headers)
groups = response.json()

if groups.get("success"):
    print(f"Found {groups['count']} supplier groups:")
    for group in groups["data"]:
        print(f"- {group['supplier_group_name']} ({group['name']})")
        if group.get("parent_supplier_group"):
            print(f"  Parent: {group['parent_supplier_group']}")

# Get groups under a specific parent
params = {
    "parent_supplier_group": "All Supplier Groups",
    "limit": 50
}
response = requests.get(get_groups_url, params=params, headers=headers)
child_groups = response.json()
print(f"\nFound {child_groups['count']} groups under 'All Supplier Groups'")
```

### Example 13: Create Warehouse and Assign to Staff

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

# Step 1: Create a main depot
create_warehouse_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.warehouse_api.create_warehouse"
warehouse_data = {
    "warehouse_name": "Nairobi Main Depot",
    "company": "Company Name",
    "warehouse_type": "Main Depot",
    "is_main_depot": True,
    "address_line_1": "123 Main Street",
    "city": "Nairobi",
    "state": "Nairobi",
    "pin": "00100",
    "phone_no": "+254 20 1234567"
}
warehouse_response = requests.post(create_warehouse_url, json=warehouse_data, headers=headers)
warehouse_result = warehouse_response.json()

if warehouse_result.get("success"):
    warehouse_name = warehouse_result["name"]
    print(f"Warehouse created: {warehouse_name}")
    
    # Step 2: Create a shop
    shop_data = {
        "warehouse_name": "Westlands Shop",
        "company": "Company Name",
        "warehouse_type": "Shop",
        "is_main_depot": False,
        "address_line_1": "456 Park Road",
        "city": "Nairobi"
    }
    shop_response = requests.post(create_warehouse_url, json=shop_data, headers=headers)
    shop_result = shop_response.json()
    
    if shop_result.get("success"):
        shop_name = shop_result["name"]
        print(f"Shop created: {shop_name}")
        
        # Step 3: Assign warehouses to staff
        assign_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.warehouse_api.assign_warehouses_to_staff"
        assign_data = {
            "user_email": "staff@company.com",
            "warehouses": [warehouse_name, shop_name],
            "replace_existing": True
        }
        assign_response = requests.post(assign_url, json=assign_data, headers=headers)
        print("Warehouses assigned:", assign_response.json())
```

### Example 14: List Warehouses and Get Staff Assignments

```python
import requests

headers = {
    "Authorization": "token api_key:api_secret"
}

# List all warehouses for a company
list_warehouses_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.warehouse_api.list_warehouses"
params = {
    "company": "Company Name",
    "limit": 100
}
response = requests.get(list_warehouses_url, params=params, headers=headers)
warehouses = response.json()

if warehouses.get("success"):
    print(f"Found {warehouses['count']} warehouses:")
    for warehouse in warehouses["data"]:
        print(f"- {warehouse['warehouse_name']} ({warehouse['name']})")
        if warehouse.get("is_main_depot"):
            print("  (Main Depot)")
        
        # Get staff assigned to this warehouse
        staff_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_warehouse_staff"
        staff_params = {"warehouse": warehouse["name"]}
        staff_response = requests.get(staff_url, params=staff_params, headers=headers)
        staff_result = staff_response.json()
        
        if staff_result.get("success") and staff_result.get("count", 0) > 0:
            print(f"  Assigned staff: {', '.join([s['full_name'] for s in staff_result['data']])}")

# Get warehouses assigned to a specific staff member
staff_warehouses_url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.warehouse_api.get_staff_warehouses"
staff_params = {"user_email": "staff@company.com"}
staff_warehouses_response = requests.get(staff_warehouses_url, params=staff_params, headers=headers)
staff_warehouses = staff_warehouses_response.json()

if staff_warehouses.get("success"):
    if staff_warehouses.get("count", 0) > 0:
        print(f"\nStaff member has access to {staff_warehouses['count']} warehouse(s):")
        for warehouse in staff_warehouses["data"]:
            print(f"- {warehouse['warehouse_name']}")
    else:
        print("\nStaff member has access to all warehouses (no restrictions)")
```

---

## Cash Payment Handling

### How Cash Payments Work

Cash payments for purchases are handled through the Purchase Invoice's payment fields:

1. **Payment Fields:**
   - `is_paid`: Boolean flag to mark invoice as paid
   - `paid_amount`: Amount paid (can be partial or full)
   - `cash_bank_account`: The cash or bank account to debit
   - `mode_of_payment`: Payment method (e.g., "Cash", "Bank Transfer")

2. **General Ledger Entries:**
   When a purchase invoice is marked as paid and submitted, ERPNext automatically creates GL entries:
   - **Debit**: Supplier Account (Accounts Payable) - reduces liability
   - **Credit**: Cash/Bank Account - reduces cash/bank balance

3. **Payment Flow:**
   ```
   Purchase Invoice Created → is_paid=True → Invoice Submitted → GL Entries Created
   ```

4. **Current Implementation:**
   - In `create_purchase_invoice_from_request()` (line 843), cash payments are hardcoded with `custom_payment_type = "CASH"` for eTIMS purposes
   - The actual payment accounting is handled by ERPNext's standard `make_payment_gl_entries()` method
   - Payment GL entries are created only when `is_paid=1`, `cash_bank_account` is set, and invoice is submitted

5. **For eTIMS Users:**
   - The `custom_payment_type` field stores the payment type code for eTIMS submission
   - This is separate from the actual accounting payment handling
   - Payment type codes must match eTIMS payment type definitions

### Example: Creating Purchase Invoice with Cash Payment

```python
import requests

url = "https://your-instance.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice"
headers = {
    "Authorization": "token api_key:api_secret",
    "Content-Type": "application/json"
}

data = {
    "supplier": "Supplier Name",
    "company": "Company Name",
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 10,
            "rate": 100.00,
            "warehouse": "Warehouse - Company"
        }
    ],
    "posting_date": "2024-01-15",
    "bill_no": "BILL-001",
    "is_paid": True,
    "paid_amount": 1160.00,  # Including VAT
    "cash_bank_account": "Cash - Company",  # Must be a valid Cash account
    "mode_of_payment": "Cash",
    "update_stock": True
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

# Submit the invoice to create GL entries
if result.get("success"):
    submit_url = f"https://your-instance.com/api/resource/Purchase Invoice/{result['name']}/submit"
    submit_response = requests.post(submit_url, headers=headers)
    print("Invoice submitted with payment:", submit_response.json())
```

## Permissions

### Required Permissions

Different endpoints require different permissions. Ensure users have the appropriate role permissions:

#### Purchase Invoice Management
- **Purchase Invoice: Read** - Required to list and view purchase invoices
- **Purchase Invoice: Create** - Required to create purchase invoices
- **Purchase Invoice: Write** - Required to update purchase invoices
- **Purchase Invoice: Submit** - Required to submit purchase invoices
- **Purchase Invoice: Cancel** - Required to cancel purchase invoices

#### Supplier Management
- **Supplier: Read** - Required to list and view suppliers
- **Supplier: Create** - Required to create new suppliers
- **Supplier: Write** - Required to update existing suppliers
- **Supplier Group: Read** - Required to list supplier groups
- **Supplier Group: Create** - Required to create new supplier groups
- **Supplier Group: Write** - Required to update supplier groups

#### Warehouse Management
- **Warehouse: Read** - Required to list and view warehouses
- **Warehouse: Create** - Required to create new warehouses
- **Warehouse: Write** - Required to update warehouses
- **User Permission: Write** - Required to assign warehouses to staff (typically requires System Manager or Administrator role)

#### Account Management
- **Account: Read** - Required to list and view accounts
- **Account: Create** - Required to create accounts
- **Account: Write** - Required to update accounts

#### Bank Account Management
- **Bank Account: Read** - Required to list and view bank accounts
- **Bank Account: Create** - Required to create bank accounts
- **Bank: Read** - Required to list banks

### Granting Permissions

To grant permissions to a user:

1. **Via Role Permission Manager:**
   - Go to **Role Permission Manager** (search in the search bar)
   - Select the role (e.g., "Purchase User", "Accounts User")
   - Find the doctype (e.g., "Supplier", "Purchase Invoice")
   - Check the required permissions (Read, Write, Create, Submit, Cancel, etc.)
   - Click **Save**

2. **Via User Permissions:**
   - Go to **User** doctype
   - Select the user
   - Go to **Permissions** section
   - Add role permissions or user permissions as needed

### Common Roles

**Purchase Management Roles:**
- **Purchase Manager** - Full access to purchase operations
- **Purchase User** - Can create and manage purchase invoices
- **Purchase Viewer** - Read-only access

**Account Management Roles:**
- **Accounts Manager** - Full access to accounts and financial operations
- **Accounts User** - Can create and manage accounts
- **Accounts Viewer** - Read-only access

**System Administrator:**
- **System Manager** - Full access to all operations (use with caution)

---

## Notes

1. **eTIMS Registration**: Endpoints automatically detect eTIMS registration status. If eTIMS is not registered, operations proceed normally without eTIMS submission.

2. **Asynchronous Operations**: Some operations (like fetching registered purchases) are asynchronous. Use the list endpoints to check for results.

3. **Document States**: Purchase Invoices must be in "Submitted" state (docstatus=1) before they can be sent to eTIMS.

4. **Item Registration**: For eTIMS users, items should be registered with eTIMS before creating purchase invoices. Use the item registration endpoints for this.

5. **Error Logging**: All errors are logged in Frappe's error log for debugging purposes.

6. **Permissions**: Ensure users have appropriate permissions for Purchase Invoice and related doctypes.

   **Required Permissions for Supplier Management:**
   - **Supplier: Read** - Required to list and view suppliers
   - **Supplier: Create** - Required to create new suppliers
   - **Supplier: Write** - Required to update existing suppliers
   - **Supplier Group: Read** - Required to list supplier groups
   
   To grant permissions:
   1. Go to **Role Permission Manager** or **User Permissions**
   2. Select the user's role (e.g., "Purchase User", "Accounts User")
   3. Grant the required permissions for the Supplier doctype
   4. Save the role permissions
   
   **Common Roles with Supplier Permissions:**
   - Purchase Manager
   - Purchase User
   - Accounts Manager
   - Accounts User

7. **Cash Payment Requirements**: 
   - `cash_bank_account` must be a valid Cash or Bank account
   - Account must belong to the same company
   - Payment GL entries are created on invoice submission
   - For partial payments, set `paid_amount` to the actual amount paid
   - Use `list_cash_and_bank_accounts` to get available accounts for payments

8. **Bank Account Management**:
   - Create Cash/Bank accounts using `create_cash_or_bank_account`
   - Create Bank master records using `create_bank`
   - Link Bank to Account using `create_bank_account`
   - Bank Account records are useful for bank reconciliation and detailed tracking

9. **Supplier Management**:
   - Use `get_suppliers` to list and search suppliers
   - Filter suppliers by company to see only suppliers with transactions for that company
   - Use `get_supplier_details` to get outstanding amounts and purchase statistics
   - Create suppliers before creating purchase invoices
   - Supplier groups help organize suppliers by category

---

## Support

For issues or questions:
- Check Frappe error logs for detailed error messages
- Verify eTIMS settings configuration
- Ensure all required fields are provided
- Check user permissions

---

**Last Updated:** 2024-01-15
**Version:** 1.0.0

