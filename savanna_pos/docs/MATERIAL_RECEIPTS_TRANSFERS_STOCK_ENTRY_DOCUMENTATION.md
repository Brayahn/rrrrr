# Material Receipts, Material Transfers, and Stock Entry Documentation

## Overview

This document provides comprehensive documentation for **Material Receipts**, **Material Transfers**, and **Stock Entry** operations in the SavvyPOS system, including their relationships to **Purchases** and **Inventory Management**.

---

## Table of Contents

1. [Concepts Overview](#concepts-overview)
2. [Stock Entry - The Foundation](#stock-entry---the-foundation)
3. [Material Receipts](#material-receipts)
4. [Material Transfers](#material-transfers)
5. [Relationship to Purchases](#relationship-to-purchases)
6. [Relationship to Inventory](#relationship-to-inventory)
7. [API Endpoints](#api-endpoints)
8. [Workflows and Use Cases](#workflows-and-use-cases)
9. [Best Practices](#best-practices)

---

## Concepts Overview

### What is Stock Entry?

**Stock Entry** is a versatile ERPNext document type that handles various types of stock movements. It's the primary mechanism for:
- Receiving stock into warehouses
- Issuing stock from warehouses
- Transferring stock between warehouses
- Manufacturing operations
- Stock adjustments

### Stock Entry Types

| Type | Purpose | Source Warehouse | Target Warehouse |
|------|---------|------------------|------------------|
| **Material Receipt** | Stock coming into warehouse | None | Required |
| **Material Issue** | Stock going out of warehouse | Required | None |
| **Material Transfer** | Moving stock between warehouses | Required | Required |
| **Manufacture** | Converting raw materials to finished goods | Required (raw materials) | Required (finished goods) |
| **Repack** | Repacking items | Required | Required |
| **Opening Stock** | Initial stock setup | None | Required |

---

## Stock Entry - The Foundation

### What is Stock Entry?

**Stock Entry** is a unified document type in ERPNext that records all stock movements. It creates:
- **Stock Ledger Entries (SLE)** - Permanent record of stock transactions
- **Bin Updates** - Updates current stock balance
- **General Ledger Entries** - Accounting entries for stock value changes

### Key Characteristics

- **Single Document Type**: All stock movements use the same `Stock Entry` doctype
- **Purpose-Based**: Differentiated by `purpose` field (Material Receipt, Material Transfer, etc.)
- **Automatic Inventory Updates**: On submission, automatically updates Bin and creates SLE
- **Accounting Integration**: Creates GL entries for stock value changes

### Stock Entry Structure

```json
{
  "name": "MAT-STE-00001",
  "stock_entry_type": "Material Receipt",
  "purpose": "Material Receipt",
  "company": "My Company",
  "posting_date": "2024-01-15",
  "posting_time": "10:30:00",
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 100,
      "s_warehouse": null,  // Source warehouse (null for Material Receipt)
      "t_warehouse": "Main Warehouse",  // Target warehouse
      "basic_rate": 50.00,
      "amount": 5000.00,
      "valuation_rate": 50.00
    }
  ],
  "total_incoming_value": 5000.00,
  "total_outgoing_value": 0.00,
  "total_amount": 5000.00
}
```

---

## Material Receipts

### What is a Material Receipt?

A **Material Receipt** is a Stock Entry with `purpose = "Material Receipt"` that records stock **coming into** a warehouse. It's used when:
- Receiving goods from suppliers (alternative to Purchase Receipt)
- Receiving returned goods from customers
- Adding stock that wasn't purchased (gifts, samples, found stock)
- Initial stock setup (Opening Stock)

### Key Features

- **Increases Stock**: Creates positive Stock Ledger Entries
- **No Source Warehouse**: Stock comes from outside the system
- **Target Warehouse Required**: Must specify where stock is received
- **Valuation**: Can specify `basic_rate` for stock valuation
- **Accounting**: Creates GL entries (Debit: Stock, Credit: Expense/Asset account)

### When to Use Material Receipt vs Purchase Receipt

| Scenario | Use Material Receipt | Use Purchase Receipt |
|----------|---------------------|---------------------|
| Goods from supplier with invoice | ❌ | ✅ |
| Goods from supplier without invoice | ✅ | ❌ |
| Customer returns | ✅ | ❌ |
| Found stock / Stock adjustment | ✅ | ❌ |
| Opening stock | ✅ | ❌ |
| Gifts / Samples | ✅ | ❌ |
| Need to track supplier billing | ❌ | ✅ |

### Material Receipt Process Flow

```
1. Create Material Receipt
   ↓
2. Add items with quantities
   ↓
3. Specify target warehouse
   ↓
4. Set basic_rate (valuation)
   ↓
5. Submit document
   ↓
6. System creates:
   - Stock Ledger Entry (positive qty)
   - Updates Bin (increases actual_qty)
   - General Ledger Entry (Debit: Stock, Credit: Expense)
   ↓
7. Stock balance increases in warehouse
```

### Inventory Impact

- **Stock Ledger Entry**: Creates positive `actual_qty` entry
- **Bin Update**: Increases `actual_qty` in target warehouse
- **Stock Value**: Increases `stock_value` based on `valuation_rate`
- **Valuation Rate**: Updates average cost per unit

---

## Material Transfers

### What is a Material Transfer?

A **Material Transfer** is a Stock Entry with `purpose = "Material Transfer"` that records stock **moving between** warehouses. It's used when:
- Transferring stock from one warehouse to another
- Moving stock between locations
- Rebalancing inventory across warehouses
- Internal stock movements

### Key Features

- **Dual Warehouse Operation**: Requires both source and target warehouses
- **Stock Balance Neutral**: Total stock remains same, just moves location
- **Two SLE Entries**: Creates one negative entry (source) and one positive entry (target)
- **No Accounting Impact**: Typically no GL entries (unless valuation differs)
- **Validation**: Source and target warehouses must be different

### Material Transfer Process Flow

```
1. Create Material Transfer
   ↓
2. Add items with quantities
   ↓
3. Specify source warehouse (s_warehouse)
   ↓
4. Specify target warehouse (t_warehouse)
   ↓
5. Submit document
   ↓
6. System creates:
   - Stock Ledger Entry (negative qty) for source warehouse
   - Stock Ledger Entry (positive qty) for target warehouse
   - Updates Bin (decreases source, increases target)
   ↓
7. Stock moves from source to target warehouse
```

### Inventory Impact

- **Source Warehouse**: 
  - Stock Ledger Entry with negative `actual_qty`
  - Bin `actual_qty` decreases
  - `stock_value` decreases
  
- **Target Warehouse**:
  - Stock Ledger Entry with positive `actual_qty`
  - Bin `actual_qty` increases
  - `stock_value` increases

- **Total Stock**: Remains unchanged (only location changes)

---

## Relationship to Purchases

### Purchase Receipt vs Material Receipt

#### Purchase Receipt

**What it is:**
- Document that records goods received from suppliers
- Part of the purchase cycle (Purchase Order → Purchase Receipt → Purchase Invoice)
- Tracks supplier information, billing, and stock receipt together

**When to use:**
- Goods received from a supplier
- Need to track supplier billing
- Want to link to Purchase Order
- Need to create Purchase Invoice later

**Stock Impact:**
- When submitted, creates Stock Ledger Entries (if `update_stock = 1`)
- Increases stock in warehouse
- Updates Bin `actual_qty`

**Example Flow:**
```
Purchase Order (PO-00001)
    ↓
Purchase Receipt (PR-00001) - Receives goods
    ↓
Purchase Invoice (PI-00001) - Bills supplier
```

#### Material Receipt

**What it is:**
- Stock Entry that records stock coming into warehouse
- Standalone stock operation (not linked to purchase cycle)
- Used for non-purchase stock receipts

**When to use:**
- Stock received without supplier invoice
- Customer returns
- Found stock / adjustments
- Opening stock
- Gifts or samples

**Stock Impact:**
- Always creates Stock Ledger Entries
- Increases stock in warehouse
- Updates Bin `actual_qty`

### Purchase Invoice with Stock Update

**Purchase Invoice** can also update stock directly when `update_stock = 1`:

**When `update_stock = 1`:**
- Creates Stock Ledger Entries (positive)
- Updates Bin (increases `actual_qty`)
- Acts as both billing and stock receipt document
- **Cannot** be used if Purchase Receipt already exists for the items

**When `update_stock = 0`:**
- Only handles billing/accounting
- No stock impact
- Stock must be received via Purchase Receipt or Material Receipt separately

### Comparison Table

| Feature | Purchase Receipt | Material Receipt | Purchase Invoice (update_stock=1) |
|---------|-----------------|------------------|-----------------------------------|
| **Supplier Tracking** | ✅ Yes | ❌ No | ✅ Yes |
| **Billing Integration** | ✅ Links to PI | ❌ No | ✅ Yes (is the invoice) |
| **Purchase Order Link** | ✅ Yes | ❌ No | ✅ Yes |
| **Stock Update** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Accounting** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Use Case** | Supplier goods | Non-supplier stock | Direct purchase with stock |

### Workflow Examples

#### Example 1: Standard Purchase Flow

```
1. Create Purchase Order (PO-00001)
   - Items: ITEM-001, qty: 100
   - Status: Ordered
   
2. Goods arrive → Create Purchase Receipt (PR-00001)
   - Links to PO-00001
   - Receives ITEM-001, qty: 100
   - Stock increases in warehouse
   - Status: Received
   
3. Supplier invoice arrives → Create Purchase Invoice (PI-00001)
   - Links to PR-00001
   - Bills for ITEM-001, qty: 100
   - No stock impact (already received)
   - Status: Billed
```

#### Example 2: Direct Purchase Invoice (Stock Update)

```
1. Create Purchase Invoice (PI-00001) with update_stock=1
   - Supplier: ABC Suppliers
   - Items: ITEM-001, qty: 100
   - Stock increases immediately
   - Billing and stock receipt in one step
```

#### Example 3: Material Receipt for Non-Purchase Stock

```
1. Customer returns goods → Create Material Receipt
   - Items: ITEM-001, qty: 5
   - Target warehouse: Main Warehouse
   - Stock increases
   - No supplier/billing involved
```

---

## Relationship to Inventory

### How Stock Entries Update Inventory

All Stock Entry types (Material Receipt, Material Transfer, Material Issue) update inventory through the same mechanism:

#### 1. Stock Ledger Entry (SLE) Creation

**What it is:**
- Permanent, immutable record of every stock transaction
- Single source of truth for stock history
- Cannot be deleted, only cancelled

**Fields:**
- `item_code`: Item being tracked
- `warehouse`: Warehouse location
- `actual_qty`: Change in quantity (+ for receipts, - for issues/transfers out)
- `qty_after_transaction`: Running balance after this transaction
- `valuation_rate`: Cost per unit
- `stock_value`: Total stock value
- `voucher_type`: "Stock Entry"
- `voucher_no`: Stock Entry name

**Example SLE for Material Receipt:**
```json
{
  "item_code": "ITEM-001",
  "warehouse": "Main Warehouse",
  "actual_qty": 100.0,  // Positive for receipt
  "qty_after_transaction": 150.0,  // Previous: 50, Now: 150
  "valuation_rate": 50.00,
  "stock_value": 7500.00,
  "voucher_type": "Stock Entry",
  "voucher_no": "MAT-STE-00001"
}
```

#### 2. Bin Update

**What it is:**
- Cached/aggregated view of current stock state
- One Bin per item-warehouse combination
- Automatically updated when SLE is created

**Fields Updated:**
- `actual_qty`: Current physical quantity
- `stock_value`: Total value of stock
- `valuation_rate`: Average cost per unit
- `reserved_qty`: Quantity reserved for sales
- `ordered_qty`: Quantity on purchase orders
- `projected_qty`: Available quantity = actual_qty + ordered_qty - reserved_qty

**Example Bin Update:**
```
Before Material Receipt:
  actual_qty: 50
  stock_value: 2500.00
  valuation_rate: 50.00

After Material Receipt (qty: 100, rate: 50):
  actual_qty: 150  // 50 + 100
  stock_value: 7500.00  // 2500 + 5000
  valuation_rate: 50.00  // (2500 + 5000) / 150
```

#### 3. General Ledger Entry (GL Entry)

**What it is:**
- Accounting entries for stock value changes
- Ensures accounting books match inventory value

**For Material Receipt:**
```
Debit: Stock Account (Asset) - Increases
Credit: Expense Account / Asset Account - Source of stock
```

**For Material Transfer:**
```
Source Warehouse:
  Debit: Stock Account (Source) - Decreases
  Credit: Stock Account (Target) - Increases

Target Warehouse:
  Debit: Stock Account (Target) - Increases
  Credit: Stock Account (Source) - Decreases

Net Effect: Usually zero (unless valuation differs)
```

### Inventory Calculation

#### Stock Balance Formula

```
Current Stock Balance = Sum of all SLE actual_qty for item-warehouse
```

**Example:**
```
SLE 1: actual_qty = +100 (Material Receipt)
SLE 2: actual_qty = -20 (Material Issue)
SLE 3: actual_qty = +50 (Material Receipt)
SLE 4: actual_qty = -30 (Sales Invoice)

Current Balance = 100 - 20 + 50 - 30 = 100 units
```

#### Valuation Rate Calculation

```
Valuation Rate = Total Stock Value / Total Quantity

Example:
  Receipt 1: 100 units @ 50.00 = 5,000.00
  Receipt 2: 50 units @ 60.00 = 3,000.00
  
  Total Value: 8,000.00
  Total Quantity: 150 units
  Valuation Rate: 8,000 / 150 = 53.33 per unit
```

### Inventory Tracking Components

```
┌─────────────────────────────────────────────────┐
│           Stock Entry (Material Receipt)        │
│                  MAT-STE-00001                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ├──► Stock Ledger Entry (SLE)
                   │    - Permanent record
                   │    - actual_qty: +100
                   │    - qty_after_transaction: 150
                   │
                   ├──► Bin Update
                   │    - actual_qty: 50 → 150
                   │    - stock_value: 2,500 → 7,500
                   │    - valuation_rate: 50.00
                   │
                   └──► General Ledger Entry
                        - Debit: Stock Account
                        - Credit: Expense Account
```

---

## API Endpoints

### 1. Create Material Receipt

Create a material receipt stock entry (stock coming into warehouse).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array or JSON string | Yes | List of items with `item_code` and `qty` |
| `target_warehouse` | string | Yes | Warehouse where stock will be received |
| `posting_date` | string | No | Posting date (`YYYY-MM-DD`, defaults to today) |
| `company` | string | No | Company name (uses default if not provided) |
| `do_not_submit` | boolean | No | If `true`, saves as draft only (default: `false`) |

**Item Object:**
```json
{
  "item_code": "ITEM-001",
  "qty": 100,
  "basic_rate": 50.00,  // Optional: Valuation rate
  "serial_no": "SN001,SN002",  // Optional: For serialized items
  "batch_no": "BATCH-001",  // Optional: For batched items
  "expense_account": "Stock Received - Company",  // Optional
  "cost_center": "Main - Company"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Stock entry created successfully",
  "data": {
    "name": "MAT-STE-00001",
    "stock_entry_type": "Material Receipt",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 1
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 100,
        "basic_rate": 50.00
      }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-15"
  }'
```

---

### 2. Create Material Transfer

Create a material transfer stock entry (stock moving between warehouses).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array or JSON string | Yes | List of items with `item_code` and `qty` |
| `source_warehouse` | string | Yes | Source warehouse (stock coming from) |
| `target_warehouse` | string | Yes | Target warehouse (stock going to) |
| `posting_date` | string | No | Posting date (`YYYY-MM-DD`, defaults to today) |
| `company` | string | No | Company name (uses default if not provided) |
| `do_not_submit` | boolean | No | If `true`, saves as draft only (default: `false`) |

**Item Object:**
```json
{
  "item_code": "ITEM-001",
  "qty": 50,
  "s_warehouse": "Store A",  // Optional: Override document-level source
  "t_warehouse": "Store B",  // Optional: Override document-level target
  "basic_rate": 50.00,  // Optional: Valuation rate
  "serial_no": "SN001,SN002",  // Optional
  "batch_no": "BATCH-001"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Stock entry created successfully",
  "data": {
    "name": "MAT-STE-00002",
    "stock_entry_type": "Material Transfer",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 1
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 50
      }
    ],
    "source_warehouse": "Store A",
    "target_warehouse": "Store B",
    "posting_date": "2024-01-15"
  }'
```

---

### 3. Create Stock Entry (Generic)

Create any type of stock entry (Material Receipt, Material Issue, Material Transfer, etc.).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.create_stock_entry`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_type` | string | Yes | Type: `"Material Receipt"`, `"Material Issue"`, `"Material Transfer"`, etc. |
| `items` | array or JSON string | Yes | List of items |
| `posting_date` | string | No | Posting date (`YYYY-MM-DD`) |
| `posting_time` | string | No | Posting time (`HH:MM:SS`) |
| `company` | string | No | Company name |
| `purpose` | string | No | Purpose (auto-determined if not provided) |
| `from_warehouse` | string | No | Document-level source warehouse |
| `to_warehouse` | string | No | Document-level target warehouse |
| `do_not_save` | boolean | No | If `true`, don't save (default: `false`) |
| `do_not_submit` | boolean | No | If `true`, save as draft (default: `false`) |

**Example Request (Material Receipt):**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_stock_entry" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_type": "Material Receipt",
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 100,
        "t_warehouse": "Main Warehouse"
      }
    ],
    "company": "My Company"
  }'
```

---

### 4. List Material Receipts

List all material receipt stock entries with filtering.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.list_material_receipts`

**Method:** `GET` or `POST`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Company name |
| `warehouse` | string | No | Filter by target warehouse |
| `item_code` | string | No | Filter by item code |
| `from_date` | string | No | Start date (`YYYY-MM-DD`) |
| `to_date` | string | No | End date (`YYYY-MM-DD`) |
| `docstatus` | number | No | Document status: `0`=Draft, `1`=Submitted, `2`=Cancelled (default: `1`) |
| `page` | number | No | Page number (default: `1`) |
| `page_size` | number | No | Items per page (default: `20`) |

**Response:**
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "name": "MAT-STE-00001",
        "stock_entry_type": "Material Receipt",
        "purpose": "Material Receipt",
        "company": "My Company",
        "posting_date": "2024-01-15",
        "posting_time": "10:30:00",
        "docstatus": 1,
        "total_incoming_value": 5000.00,
        "total_amount": 5000.00,
        "items": [
          {
            "item_code": "ITEM-001",
            "qty": 100,
            "s_warehouse": null,
            "t_warehouse": "Main Warehouse",
            "basic_rate": 50.00,
            "amount": 5000.00
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

---

### 5. List Material Transfers

List all material transfer stock entries with filtering.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.list_material_transfers`

**Method:** `GET` or `POST`

**Parameters:** Same as List Material Receipts

**Response:** Same structure as List Material Receipts, but with `stock_entry_type: "Material Transfer"`

---

### 6. List Stock Entries (All Types)

List all stock entries (any type) with filtering.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.list_stock_entries`

**Method:** `GET` or `POST`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_type` | string | No | Filter by type: `"Material Receipt"`, `"Material Transfer"`, etc. |
| `company` | string | No | Company name |
| `warehouse` | string | No | Filter by warehouse (source or target) |
| `item_code` | string | No | Filter by item code |
| `from_date` | string | No | Start date |
| `to_date` | string | No | End date |
| `docstatus` | number | No | Document status |
| `page` | number | No | Page number |
| `page_size` | number | No | Items per page |

---

### 7. Get Stock Entry Details

Get detailed information about a specific stock entry.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.get_stock_entry_details`

**Method:** `GET` or `POST`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Stock Entry name (e.g., `MAT-STE-00001`) |

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "MAT-STE-00001",
    "stock_entry_type": "Material Receipt",
    "purpose": "Material Receipt",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "posting_time": "10:30:00",
    "docstatus": 1,
    "total_outgoing_value": 0.00,
    "total_incoming_value": 5000.00,
    "total_additional_costs": 0.00,
    "total_amount": 5000.00,
    "items": [
      {
        "item_code": "ITEM-001",
        "item_name": "Product A",
        "qty": 100,
        "s_warehouse": null,
        "t_warehouse": "Main Warehouse",
        "basic_rate": 50.00,
        "amount": 5000.00,
        "valuation_rate": 50.00,
        "serial_no": null,
        "batch_no": null,
        "expense_account": "Stock Received - Company",
        "cost_center": "Main - Company"
      }
    ],
    "items_count": 1
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_stock_entry_details" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_name": "MAT-STE-00001"
  }'
```

---

### 8. Update Stock Entry

Update an existing draft stock entry (only works for draft entries, docstatus=0).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to update |
| `items` | array or JSON string | No | Updated list of items |
| `posting_date` | string | No | Updated posting date (`YYYY-MM-DD`) |
| `posting_time` | string | No | Updated posting time (`HH:MM:SS`) |
| `from_warehouse` | string | No | Updated source warehouse |
| `to_warehouse` | string | No | Updated target warehouse |
| `do_not_submit` | boolean | No | If `true`, don't submit after update (default: `false`) |

**Response:**
```json
{
  "success": true,
  "message": "Stock entry updated successfully",
  "data": {
    "name": "MAT-STE-00001",
    "stock_entry_type": "Material Receipt",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 2
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_name": "MAT-STE-00001",
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 150,
        "basic_rate": 50.00,
        "t_warehouse": "Main Warehouse"
      },
      {
        "item_code": "ITEM-002",
        "qty": 75,
        "basic_rate": 30.00,
        "t_warehouse": "Main Warehouse"
      }
    ],
    "posting_date": "2024-01-16"
  }'
```

---

### 9. Submit Stock Entry

Submit a draft stock entry (only works for draft entries, docstatus=0).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to submit |

**Response:**
```json
{
  "success": true,
  "message": "Stock entry submitted successfully",
  "data": {
    "name": "MAT-STE-00001",
    "stock_entry_type": "Material Receipt",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 1
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_name": "MAT-STE-00001"
  }'
```

---

### 10. Cancel Stock Entry

Cancel a submitted stock entry (only works for submitted entries, docstatus=1).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to cancel |
| `reason` | string | No | Reason for cancellation |

**Response:**
```json
{
  "success": true,
  "message": "Stock entry cancelled successfully",
  "data": {
    "name": "MAT-STE-00001",
    "docstatus": 2,
    "cancelled_at": "2024-01-16 14:30:00"
  }
}
```

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_name": "MAT-STE-00001",
    "reason": "Incorrect quantity entered"
  }'
```

---

### 11. List Material Issues

List all material issue stock entries (stock going out of warehouse).

**Endpoint:**  
`savanna_pos.savanna_pos.apis.inventory_api.list_material_issues`

**Method:** `GET` or `POST`

**Parameters:** Same as List Material Receipts

**Response:** Same structure as List Material Receipts, but with `stock_entry_type: "Material Issue"`

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_issues" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "My Company",
    "warehouse": "Main Warehouse",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "page": 1,
    "page_size": 20
  }'
```

---

## Workflows and Use Cases

### Use Case 1: Receiving Stock from Supplier (Without Invoice)

**Scenario:** Goods arrive from supplier, but invoice will come later.

**Solution:** Use Material Receipt

#### Step 1: Receive Goods (Material Receipt)

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 100,
        "basic_rate": 50.00
      }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-15",
    "company": "My Company"
  }'
```

**JavaScript (Fetch API):**
```javascript
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        basic_rate: 50.00
      }
    ],
    target_warehouse: 'Main Warehouse',
    posting_date: '2024-01-15',
    company: 'My Company'
  })
});

const result = await response.json();
console.log('Material Receipt Created:', result.data.name);
// Result: Stock increases, no billing yet
```

**Python:**
```python
import requests

url = "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt"
headers = {
    "Authorization": "Bearer <access_token>",
    "Content-Type": "application/json"
}
data = {
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 100,
            "basic_rate": 50.00
        }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-15",
    "company": "My Company"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(f"Material Receipt Created: {result['data']['name']}")
# Result: Stock increases, no billing yet
```

#### Step 2: Create Purchase Invoice (When Invoice Arrives)

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier": "ABC Suppliers",
    "company": "My Company",
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 100,
        "rate": 50.00
      }
    ],
    "posting_date": "2024-01-15",
    "update_stock": false
  }'
```

**JavaScript:**
```javascript
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    supplier: 'ABC Suppliers',
    company: 'My Company',
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        rate: 50.00
      }
    ],
    posting_date: '2024-01-15',
    update_stock: false  // Stock already received
  })
});

const result = await response.json();
console.log('Purchase Invoice Created:', result.name);
```

---

### Use Case 2: Transferring Stock Between Warehouses

**Scenario:** Moving stock from Store A to Store B.

**Solution:** Use Material Transfer

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 50
      }
    ],
    "source_warehouse": "Store A",
    "target_warehouse": "Store B",
    "posting_date": "2024-01-15",
    "company": "My Company"
  }'
```

**JavaScript:**
```javascript
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [
      {
        item_code: 'ITEM-001',
        qty: 50
      }
    ],
    source_warehouse: 'Store A',
    target_warehouse: 'Store B',
    posting_date: '2024-01-15',
    company: 'My Company'
  })
});

const result = await response.json();
console.log('Material Transfer Created:', result.data.name);
// Result:
// - Store A: Stock decreases by 50
// - Store B: Stock increases by 50
// - Total stock: Unchanged
```

**Python:**
```python
import requests

url = "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer"
headers = {
    "Authorization": "Bearer <access_token>",
    "Content-Type": "application/json"
}
data = {
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 50
        }
    ],
    "source_warehouse": "Store A",
    "target_warehouse": "Store B",
    "posting_date": "2024-01-15",
    "company": "My Company"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(f"Material Transfer Created: {result['data']['name']}")
# Result: Stock moves from Store A to Store B
```

---

### Use Case 3: Customer Returns

**Scenario:** Customer returns goods that were previously sold.

**Solution:** Use Material Receipt + Sales Return

#### Step 1: Receive Returned Stock (Material Receipt)

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 5,
        "basic_rate": 50.00
      }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-15",
    "company": "My Company"
  }'
```

**JavaScript:**
```javascript
// Step 1: Receive returned stock
const receiptResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [
      {
        item_code: 'ITEM-001',
        qty: 5,
        basic_rate: 50.00  // Use original cost
      }
    ],
    target_warehouse: 'Main Warehouse',
    posting_date: '2024-01-15',
    company: 'My Company'
  })
});

const receiptResult = await receiptResponse.json();
console.log('Returned Stock Received:', receiptResult.data.name);

// Step 2: Create Sales Return (Credit Note) for accounting
// ... (use sales_api.create_sales_return endpoint)
```

---

### Use Case 4: Opening Stock Setup

**Scenario:** Setting initial stock when starting the system.

**Solution:** Use Material Receipt or Stock Reconciliation

#### Option 1: Material Receipt (Single Item)

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 200,
        "basic_rate": 50.00
      }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-01",
    "company": "My Company"
  }'
```

#### Option 2: Stock Reconciliation (Bulk Setup)

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_stock_reconciliation" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 200,
        "valuation_rate": 50.00
      },
      {
        "item_code": "ITEM-002",
        "qty": 150,
        "valuation_rate": 30.00
      }
    ],
    "warehouse": "Main Warehouse",
    "purpose": "Opening Stock",
    "expense_account": "Opening Stock - Company",
    "posting_date": "2024-01-01",
    "company": "My Company"
  }'
```

**JavaScript:**
```javascript
// Bulk opening stock setup
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_stock_reconciliation', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [
      { item_code: 'ITEM-001', qty: 200, valuation_rate: 50.00 },
      { item_code: 'ITEM-002', qty: 150, valuation_rate: 30.00 },
      { item_code: 'ITEM-003', qty: 100, valuation_rate: 25.00 }
    ],
    warehouse: 'Main Warehouse',
    purpose: 'Opening Stock',
    expense_account: 'Opening Stock - Company',
    posting_date: '2024-01-01',
    company: 'My Company'
  })
});

const result = await response.json();
console.log('Opening Stock Setup Complete:', result.data.name);
```

---

### Use Case 5: Purchase Flow with Stock Receipt

**Scenario:** Complete purchase cycle with stock tracking.

**Solution:** Purchase Receipt → Purchase Invoice

#### Step 1: Goods Arrive → Create Purchase Receipt

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_receipt" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier": "ABC Suppliers",
    "company": "My Company",
    "items": [
      {
        "item_code": "ITEM-001",
        "qty": 100,
        "rate": 50.00,
        "warehouse": "Main Warehouse"
      }
    ],
    "posting_date": "2024-01-15"
  }'
```

**JavaScript:**
```javascript
// Step 1: Goods arrive → Create Purchase Receipt
const prResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_receipt', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    supplier: 'ABC Suppliers',
    company: 'My Company',
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        rate: 50.00,
        warehouse: 'Main Warehouse'
      }
    ],
    posting_date: '2024-01-15'
  })
});

const prResult = await prResponse.json();
console.log('Purchase Receipt Created:', prResult.name);
// Result: Stock increases, Purchase Receipt created

// Step 2: Invoice arrives → Create Purchase Invoice
const piResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.apis.create_purchase_invoice', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    supplier: 'ABC Suppliers',
    company: 'My Company',
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        rate: 50.00,
        purchase_receipt: prResult.name,  // Link to receipt
        purchase_receipt_item: 'PR-ITEM-001'
      }
    ],
    update_stock: false  // Stock already received via PR
  })
});

const piResult = await piResponse.json();
console.log('Purchase Invoice Created:', piResult.name);
// Result: Billing complete, stock already updated
```

---

### Use Case 6: Draft, Update, and Submit Workflow

**Scenario:** Create a draft stock entry, update it, then submit it.

**Solution:** Create with `do_not_submit=true`, then update, then submit

**JavaScript:**
```javascript
// Step 1: Create draft Material Receipt
const createResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        basic_rate: 50.00
      }
    ],
    target_warehouse: 'Main Warehouse',
    posting_date: '2024-01-15',
    company: 'My Company',
    do_not_submit: true  // Save as draft
  })
});

const createResult = await createResponse.json();
const stockEntryName = createResult.data.name;
console.log('Draft Created:', stockEntryName);

// Step 2: Update the draft (add more items)
const updateResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stock_entry_name: stockEntryName,
    items: [
      {
        item_code: 'ITEM-001',
        qty: 100,
        basic_rate: 50.00,
        t_warehouse: 'Main Warehouse'
      },
      {
        item_code: 'ITEM-002',
        qty: 50,
        basic_rate: 30.00,
        t_warehouse: 'Main Warehouse'
      }
    ],
    do_not_submit: true  // Keep as draft
  })
});

const updateResult = await updateResponse.json();
console.log('Draft Updated:', updateResult.data.name);

// Step 3: Submit the draft
const submitResponse = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stock_entry_name: stockEntryName
  })
});

const submitResult = await submitResponse.json();
console.log('Stock Entry Submitted:', submitResult.data.name);
// Result: Stock entry is now submitted and stock is updated
```

**Python:**
```python
import requests

base_url = "https://your-domain.com/api/method"
headers = {
    "Authorization": "Bearer <access_token>",
    "Content-Type": "application/json"
}

# Step 1: Create draft
create_data = {
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 100,
            "basic_rate": 50.00
        }
    ],
    "target_warehouse": "Main Warehouse",
    "posting_date": "2024-01-15",
    "company": "My Company",
    "do_not_submit": True
}

response = requests.post(
    f"{base_url}/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt",
    headers=headers,
    json=create_data
)
create_result = response.json()
stock_entry_name = create_result['data']['name']
print(f"Draft Created: {stock_entry_name}")

# Step 2: Update draft
update_data = {
    "stock_entry_name": stock_entry_name,
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 100,
            "basic_rate": 50.00,
            "t_warehouse": "Main Warehouse"
        },
        {
            "item_code": "ITEM-002",
            "qty": 50,
            "basic_rate": 30.00,
            "t_warehouse": "Main Warehouse"
        }
    ],
    "do_not_submit": True
}

response = requests.post(
    f"{base_url}/savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry",
    headers=headers,
    json=update_data
)
update_result = response.json()
print(f"Draft Updated: {update_result['data']['name']}")

# Step 3: Submit
submit_data = {
    "stock_entry_name": stock_entry_name
}

response = requests.post(
    f"{base_url}/savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry",
    headers=headers,
    json=submit_data
)
submit_result = response.json()
print(f"Stock Entry Submitted: {submit_result['data']['name']}")
```

---

### Use Case 7: Cancel Incorrect Stock Entry

**Scenario:** A stock entry was submitted incorrectly and needs to be cancelled.

**Solution:** Use Cancel Stock Entry endpoint

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_name": "MAT-STE-00001",
    "reason": "Incorrect quantity entered - should be 50 instead of 100"
  }'
```

**JavaScript:**
```javascript
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stock_entry_name: 'MAT-STE-00001',
    reason: 'Incorrect quantity entered - should be 50 instead of 100'
  })
});

const result = await response.json();
console.log('Stock Entry Cancelled:', result.data.name);
// Result: Stock entry is cancelled and stock is reversed
```

---

### Use Case 8: Query Stock Entries with Filters

**Scenario:** Get all material receipts for a specific warehouse in a date range.

**Solution:** Use List Material Receipts with filters

**cURL:**
```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_receipts" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "My Company",
    "warehouse": "Main Warehouse",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "docstatus": 1,
    "page": 1,
    "page_size": 20
  }'
```

**JavaScript:**
```javascript
const response = await fetch('https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_receipts', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <access_token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    company: 'My Company',
    warehouse: 'Main Warehouse',
    from_date: '2024-01-01',
    to_date: '2024-01-31',
    docstatus: 1,  // Only submitted entries
    page: 1,
    page_size: 20
  })
});

const result = await response.json();
console.log(`Found ${result.data.pagination.total} material receipts`);
result.data.entries.forEach(entry => {
  console.log(`${entry.name}: ${entry.posting_date} - ${entry.total_amount}`);
});
```

---

## Relationship Diagrams

### Material Receipt Flow

```
┌─────────────────────────────────────────────────────────┐
│              Material Receipt (Stock Entry)             │
│                   MAT-STE-00001                         │
│  Purpose: Material Receipt                              │
│  Target Warehouse: Main Warehouse                       │
│  Items: ITEM-001, qty: 100                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├──► Stock Ledger Entry
                     │    ┌──────────────────────────────┐
                     │    │ item_code: ITEM-001           │
                     │    │ warehouse: Main Warehouse     │
                     │    │ actual_qty: +100              │
                     │    │ qty_after_transaction: 150   │
                     │    │ valuation_rate: 50.00         │
                     │    │ stock_value: 7500.00          │
                     │    └──────────────────────────────┘
                     │
                     ├──► Bin Update
                     │    ┌──────────────────────────────┐
                     │    │ actual_qty: 50 → 150         │
                     │    │ stock_value: 2500 → 7500     │
                     │    │ valuation_rate: 50.00         │
                     │    └──────────────────────────────┘
                     │
                     └──► General Ledger Entry
                          ┌──────────────────────────────┐
                          │ Debit: Stock Account          │
                          │   Amount: 5000.00             │
                          │ Credit: Expense Account       │
                          │   Amount: 5000.00             │
                          └──────────────────────────────┘
```

### Material Transfer Flow

```
┌─────────────────────────────────────────────────────────┐
│            Material Transfer (Stock Entry)              │
│                   MAT-STE-00002                         │
│  Purpose: Material Transfer                             │
│  Source: Store A  →  Target: Store B                   │
│  Items: ITEM-001, qty: 50                               │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               │                      │
    ┌──────────▼──────────┐  ┌────────▼──────────┐
    │ Source Warehouse    │  │ Target Warehouse  │
    │ (Store A)           │  │ (Store B)         │
    └──────────┬──────────┘  └────────┬──────────┘
               │                      │
               │                      │
    ┌──────────▼──────────┐  ┌────────▼──────────┐
    │ SLE (Negative)      │  │ SLE (Positive)   │
    │ actual_qty: -50     │  │ actual_qty: +50   │
    │ qty_after: 50       │  │ qty_after: 50     │
    └─────────────────────┘  └──────────────────┘
               │                      │
               │                      │
    ┌──────────▼──────────┐  ┌────────▼──────────┐
    │ Bin Update          │  │ Bin Update        │
    │ actual_qty: 100→50  │  │ actual_qty: 0→50  │
    │ stock_value: ↓     │  │ stock_value: ↑    │
    └─────────────────────┘  └──────────────────┘
```

### Purchase Receipt vs Material Receipt

```
┌─────────────────────────────────────────────────────────┐
│                    Purchase Receipt                      │
│                      PR-00001                            │
│  Supplier: ABC Suppliers                                 │
│  Links to: Purchase Order                                │
│  Stock Update: Yes                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├──► Creates Stock Ledger Entry
                     │    (Same as Material Receipt)
                     │
                     ├──► Updates Bin
                     │    (Same as Material Receipt)
                     │
                     ├──► Creates GL Entry
                     │    (Same as Material Receipt)
                     │
                     └──► Links to Purchase Invoice
                          (Billing document)

┌─────────────────────────────────────────────────────────┐
│                    Material Receipt                      │
│                    MAT-STE-00001                         │
│  Supplier: None (or not tracked)                        │
│  Links to: None                                          │
│  Stock Update: Yes                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├──► Creates Stock Ledger Entry
                     │    (Same as Purchase Receipt)
                     │
                     ├──► Updates Bin
                     │    (Same as Purchase Receipt)
                     │
                     └──► Creates GL Entry
                         (Same as Purchase Receipt)
                         
Note: Both create identical inventory impact,
      but Purchase Receipt includes supplier/billing tracking
```

---

## Best Practices

### 1. When to Use Each Method

**Use Purchase Receipt when:**
- ✅ Goods come from a supplier
- ✅ You need to track supplier billing
- ✅ You want to link to Purchase Order
- ✅ You'll create Purchase Invoice later

**Use Material Receipt when:**
- ✅ Stock received without supplier invoice
- ✅ Customer returns
- ✅ Found stock / adjustments
- ✅ Opening stock setup
- ✅ Gifts, samples, or non-purchase stock

**Use Material Transfer when:**
- ✅ Moving stock between warehouses
- ✅ Rebalancing inventory
- ✅ Internal stock movements
- ✅ Transferring to different locations

### 2. Stock Valuation

- **Always specify `basic_rate`** for Material Receipts to ensure accurate stock valuation
- **Use consistent valuation** across receipts for the same item
- **For transfers**, system uses current valuation rate automatically

### 3. Warehouse Management

- **Validate warehouses exist** before creating stock entries
- **Ensure warehouses belong to the same company** for transfers
- **Use warehouse hierarchy** for better organization

### 4. Serial and Batch Tracking

- **For serialized items**: Provide `serial_no` in item object
- **For batched items**: Provide `batch_no` in item object
- **Format**: Serial numbers as comma-separated string: `"SN001,SN002,SN003"`

### 5. Error Handling

- **Check stock availability** before Material Transfer (source must have stock)
- **Validate quantities** are positive
- **Ensure warehouses are different** for Material Transfer
- **Handle negative stock** - enable `allow_negative_stock` on Item if needed

### 6. Integration with Purchases

- **Don't mix Purchase Receipt and Material Receipt** for the same goods
- **Use Purchase Receipt** for supplier goods with invoices
- **Use Material Receipt** only for non-supplier stock
- **Purchase Invoice with `update_stock=1`** cannot be used if Purchase Receipt exists

---

## Common Scenarios

### Scenario 1: Supplier Goods Arrive Before Invoice

```
1. Goods arrive → Create Material Receipt
   - Stock increases immediately
   - No billing yet
   
2. Invoice arrives later → Create Purchase Invoice
   - Link to Material Receipt (optional)
   - update_stock = false (already received)
   - Handles billing only
```

### Scenario 2: Direct Purchase with Stock Update

```
1. Create Purchase Invoice with update_stock=1
   - Stock increases immediately
   - Billing happens simultaneously
   - One-step process
```

### Scenario 3: Standard Purchase Cycle

```
1. Purchase Order → Order placed
2. Purchase Receipt → Goods received, stock increases
3. Purchase Invoice → Supplier billed, links to PR
```

### Scenario 4: Inter-Warehouse Transfer

```
1. Create Material Transfer
   - Source: Store A (stock decreases)
   - Target: Store B (stock increases)
   - Total stock unchanged
```

---

## Inventory Impact Summary

| Operation | Stock Ledger Entry | Bin Update | GL Entry | Total Stock |
|-----------|-------------------|------------|----------|-------------|
| **Material Receipt** | +qty | Increases | Debit Stock, Credit Expense | Increases |
| **Material Transfer** | -qty (source), +qty (target) | Decreases source, Increases target | Usually zero | Unchanged |
| **Purchase Receipt** | +qty | Increases | Debit Stock, Credit Expense | Increases |
| **Purchase Invoice (update_stock=1)** | +qty | Increases | Debit Stock, Credit Payable | Increases |

---

## API Response Examples

### Material Receipt Response

```json
{
  "success": true,
  "message": "Stock entry created successfully",
  "data": {
    "name": "MAT-STE-00001",
    "stock_entry_type": "Material Receipt",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 1
  }
}
```

### Material Transfer Response

```json
{
  "success": true,
  "message": "Stock entry created successfully",
  "data": {
    "name": "MAT-STE-00002",
    "stock_entry_type": "Material Transfer",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "docstatus": 1,
    "items_count": 1
  }
}
```

---

## Error Handling

### Common Errors

**1. Warehouse Not Found**
```json
{
  "success": false,
  "message": "Source warehouse 'Store A' does not exist"
}
```

**2. Insufficient Stock (Material Transfer)**
```json
{
  "success": false,
  "message": "Validation error: Insufficient stock in source warehouse"
}
```

**3. Same Source and Target Warehouse**
```json
{
  "success": false,
  "message": "Validation error: Source and Target Warehouse cannot be the same for Material Transfer"
}
```

**4. Item Not Found**
```json
{
  "success": false,
  "message": "Item 'ITEM-001' does not exist"
}
```

---

## Integration with eTIMS

For eTIMS-registered users, Stock Entries are automatically submitted to eTIMS:

1. **Material Receipt** → Submitted as `StockOperationSaveReq`
2. **Material Transfer** → Submitted as `StockOperationSaveReq`
3. **Stock Items** → Submitted as `StockOperationLineReq`

The system automatically:
- Detects eTIMS registration status
- Submits stock operations to eTIMS
- Updates submission status
- Handles errors and retries

---

## Support and Feedback

For API support, feature requests, or to report issues:

- **Email**: api-support@savvypos.com
- **Documentation**: https://docs.savvypos.com/api
- **Status Page**: https://status.savvypos.com

---

## Complete Endpoint Reference

### Quick Reference Table

| # | Endpoint | Method | Purpose | Works on Draft | Works on Submitted |
|---|----------|--------|---------|----------------|-------------------|
| 1 | `create_material_receipt` | POST | Create material receipt | N/A | N/A |
| 2 | `create_material_transfer` | POST | Create material transfer | N/A | N/A |
| 3 | `create_material_issue` | POST | Create material issue | N/A | N/A |
| 4 | `create_stock_entry` | POST | Create any stock entry type | N/A | N/A |
| 5 | `list_material_receipts` | GET/POST | List material receipts | ✅ | ✅ |
| 6 | `list_material_transfers` | GET/POST | List material transfers | ✅ | ✅ |
| 7 | `list_material_issues` | GET/POST | List material issues | ✅ | ✅ |
| 8 | `list_stock_entries` | GET/POST | List all stock entries | ✅ | ✅ |
| 9 | `get_stock_entry_details` | GET/POST | Get stock entry details | ✅ | ✅ |
| 10 | `update_stock_entry` | POST | Update draft stock entry | ✅ | ❌ |
| 11 | `submit_stock_entry` | POST | Submit draft stock entry | ✅ | ❌ |
| 12 | `cancel_stock_entry` | POST | Cancel submitted stock entry | ❌ | ✅ |

### Endpoint URLs

All endpoints use the base URL pattern:
```
https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.inventory_api.{endpoint_name}
```

### Document Status Reference

- **docstatus = 0**: Draft (can be updated, submitted, or deleted)
- **docstatus = 1**: Submitted (can be cancelled, cannot be updated)
- **docstatus = 2**: Cancelled (read-only, cannot be modified)

### Common Response Structure

**Success Response:**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Endpoint-specific data
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "error_type": "validation_error"  // Optional
}
```

---

## Changelog

### Version 1.1 (2025-01-20)

- Added `update_stock_entry` endpoint for updating draft entries
- Added `submit_stock_entry` endpoint for submitting draft entries
- Added `cancel_stock_entry` endpoint for cancelling submitted entries
- Added `list_material_issues` endpoint documentation
- Added complete example implementations in cURL, JavaScript, and Python
- Added 8 comprehensive use case scenarios with full code examples
- Added quick reference table for all endpoints
- Enhanced workflow documentation with step-by-step examples

### Version 1.0 (2025-01-20)

- Initial release of Material Receipts, Material Transfers, and Stock Entry documentation
- Complete API endpoint documentation
- Relationship explanations with Purchases and Inventory
- Workflow examples and best practices
- Integration details with eTIMS
