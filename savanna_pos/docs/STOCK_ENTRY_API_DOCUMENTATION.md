# Stock Entry API Documentation

Complete API documentation for stock entry management endpoints, designed for React.js frontend consumption.

## Base URL

All endpoints are relative to your Frappe backend API:
```
/api/method/savanna_pos.savanna_pos.apis.inventory_api.<endpoint_name>
```

## Authentication

All endpoints require authentication. Include the session cookie or API key in your requests.

```javascript
// Using fetch with session cookie (automatic)
fetch('/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt', {
  credentials: 'include'
})

// Using API key
fetch('/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt', {
  headers: {
    'Authorization': 'token <api_key>:<api_secret>'
  }
})
```

## Document Status

Stock entries have a `docstatus` field that indicates their state:
- **0** = Draft (can be edited, not yet submitted)
- **1** = Submitted (finalized, inventory updated, cannot be edited)
- **2** = Cancelled (reversed, inventory restored)

---

## Endpoints

### 1. Create Stock Entry (Generic)

Creates a stock entry for any type of stock movement.

**Endpoint:** `create_stock_entry`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_stock_entry`

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `stock_entry_type` | string | Yes | - | Type: "Material Receipt", "Material Issue", "Material Transfer", "Manufacture", "Repack", "Opening Stock" |
| `items` | array/string | Yes | - | List of items (see Item Object below) |
| `posting_date` | string | No | Today | Posting date (YYYY-MM-DD) |
| `posting_time` | string | No | Current time | Posting time (HH:MM:SS) |
| `company` | string | No | User default | Company name |
| `purpose` | string | No | Auto | Purpose of stock entry |
| `from_warehouse` | string | No | - | Default source warehouse (can override per item) |
| `to_warehouse` | string | No | - | Default target warehouse (can override per item) |
| `do_not_save` | boolean | No | `false` | If true, don't save (validation only) |
| `do_not_submit` | boolean | No | `false` | If true, save as draft |

#### Item Object

Each item in the `items` array should have:

```typescript
{
  item_code: string;           // Required: Item code
  qty: number;                 // Required: Quantity (must be > 0)
  s_warehouse?: string;        // Optional: Source warehouse (overrides default)
  t_warehouse?: string;        // Optional: Target warehouse (overrides default)
  basic_rate?: number;         // Optional: Cost per unit
  conversion_factor?: number;  // Optional: UOM conversion (default: 1.0)
  serial_no?: string;          // Optional: Serial number
  batch_no?: string;          // Optional: Batch number
  expense_account?: string;   // Optional: Expense account
  cost_center?: string;       // Optional: Cost center
}
```

#### Request Example

```javascript
const createStockEntry = async (entryData) => {
  const formData = new FormData();
  formData.append('stock_entry_type', entryData.stockEntryType);
  formData.append('items', JSON.stringify(entryData.items));
  if (entryData.postingDate) {
    formData.append('posting_date', entryData.postingDate);
  }
  if (entryData.postingTime) {
    formData.append('posting_time', entryData.postingTime);
  }
  if (entryData.company) {
    formData.append('company', entryData.company);
  }
  if (entryData.fromWarehouse) {
    formData.append('from_warehouse', entryData.fromWarehouse);
  }
  if (entryData.toWarehouse) {
    formData.append('to_warehouse', entryData.toWarehouse);
  }
  if (entryData.doNotSave) {
    formData.append('do_not_save', entryData.doNotSave);
  }
  if (entryData.doNotSubmit) {
    formData.append('do_not_submit', entryData.doNotSubmit);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_stock_entry',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const result = await createStockEntry({
  stockEntryType: 'Material Transfer',
  items: [
    {
      item_code: 'ITEM-001',
      qty: 50,
      basic_rate: 25.00
    }
  ],
  fromWarehouse: 'Warehouse A',
  toWarehouse: 'Warehouse B',
  company: 'My Company'
});
```

#### Response Example

**Success:**
```json
{
  "message": {
    "success": true,
    "message": "Stock entry created successfully",
    "data": {
      "name": "MAT-STE-00001",
      "stock_entry_type": "Material Transfer",
      "company": "My Company",
      "posting_date": "2024-01-15",
      "docstatus": 1,
      "items_count": 1
    }
  }
}
```

**Error:**
```json
{
  "message": {
    "success": false,
    "message": "Item 'ITEM-001' does not exist"
  }
}
```

---

### 2. Create Material Receipt

Convenience endpoint for creating material receipt (stock coming into warehouse).

**Endpoint:** `create_material_receipt`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array/string | Yes | List of items (see Item Object) |
| `target_warehouse` | string | Yes | Warehouse where stock will be received |
| `posting_date` | string | No | Posting date (YYYY-MM-DD, defaults to today) |
| `company` | string | No | Company name (uses default if not provided) |
| `do_not_submit` | boolean | No | If true, save as draft (default: false) |

#### Request Example

```javascript
const createMaterialReceipt = async (receiptData) => {
  const formData = new FormData();
  formData.append('items', JSON.stringify(receiptData.items));
  formData.append('target_warehouse', receiptData.targetWarehouse);
  if (receiptData.postingDate) {
    formData.append('posting_date', receiptData.postingDate);
  }
  if (receiptData.company) {
    formData.append('company', receiptData.company);
  }
  if (receiptData.doNotSubmit) {
    formData.append('do_not_submit', receiptData.doNotSubmit);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_receipt',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage - Receiving 100 units of ITEM-001 into Main Warehouse
await createMaterialReceipt({
  items: [
    {
      item_code: 'ITEM-001',
      qty: 100,
      basic_rate: 50.00
    }
  ],
  targetWarehouse: 'Main Warehouse',
  postingDate: '2024-01-15'
});
```

#### Response Example

**Success:**
```json
{
  "message": {
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
}
```

---

### 3. Create Material Issue

Convenience endpoint for creating material issue (stock going out of warehouse).

**Endpoint:** `create_material_issue`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_issue`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array/string | Yes | List of items (see Item Object) |
| `source_warehouse` | string | Yes | Warehouse where stock will be issued from |
| `posting_date` | string | No | Posting date (YYYY-MM-DD, defaults to today) |
| `company` | string | No | Company name (uses default if not provided) |
| `do_not_submit` | boolean | No | If true, save as draft (default: false) |

#### Request Example

```javascript
const createMaterialIssue = async (issueData) => {
  const formData = new FormData();
  formData.append('items', JSON.stringify(issueData.items));
  formData.append('source_warehouse', issueData.sourceWarehouse);
  if (issueData.postingDate) {
    formData.append('posting_date', issueData.postingDate);
  }
  if (issueData.company) {
    formData.append('company', issueData.company);
  }
  if (issueData.doNotSubmit) {
    formData.append('do_not_submit', issueData.doNotSubmit);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_issue',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage - Issuing 25 units of ITEM-001 from Main Warehouse
await createMaterialIssue({
  items: [
    {
      item_code: 'ITEM-001',
      qty: 25
    }
  ],
  sourceWarehouse: 'Main Warehouse'
});
```

---

### 4. Create Material Transfer

Convenience endpoint for creating material transfer (stock moving between warehouses).

**Endpoint:** `create_material_transfer`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array/string | Yes | List of items (see Item Object) |
| `source_warehouse` | string | Yes | Source warehouse |
| `target_warehouse` | string | Yes | Target warehouse |
| `posting_date` | string | No | Posting date (YYYY-MM-DD, defaults to today) |
| `company` | string | No | Company name (uses default if not provided) |
| `do_not_submit` | boolean | No | If true, save as draft (default: false) |

#### Request Example

```javascript
const createMaterialTransfer = async (transferData) => {
  const formData = new FormData();
  formData.append('items', JSON.stringify(transferData.items));
  formData.append('source_warehouse', transferData.sourceWarehouse);
  formData.append('target_warehouse', transferData.targetWarehouse);
  if (transferData.postingDate) {
    formData.append('posting_date', transferData.postingDate);
  }
  if (transferData.company) {
    formData.append('company', transferData.company);
  }
  if (transferData.doNotSubmit) {
    formData.append('do_not_submit', transferData.doNotSubmit);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_material_transfer',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage - Transferring 50 units from Warehouse A to Warehouse B
await createMaterialTransfer({
  items: [
    {
      item_code: 'ITEM-001',
      qty: 50
    }
  ],
  sourceWarehouse: 'Warehouse A',
  targetWarehouse: 'Warehouse B'
});
```

---

### 5. List Stock Entries

Lists stock entries with filters and pagination.

**Endpoint:** `list_stock_entries`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_stock_entries`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_type` | string | No | Filter by type (Material Receipt, Material Issue, Material Transfer, etc.) |
| `company` | string | No | Filter by company (uses default if not provided) |
| `warehouse` | string | No | Filter by warehouse (checks both source and target) |
| `item_code` | string | No | Filter by item code |
| `from_date` | string | No | Start date (YYYY-MM-DD) |
| `to_date` | string | No | End date (YYYY-MM-DD) |
| `docstatus` | number | No | Document status: 0=Draft, 1=Submitted, 2=Cancelled (default: 1) |
| `page` | number | No | Page number (default: 1) |
| `page_size` | number | No | Items per page (default: 20) |

#### Request Example

```javascript
const listStockEntries = async (filters = {}, pagination = {}) => {
  const formData = new FormData();
  
  if (filters.stockEntryType) {
    formData.append('stock_entry_type', filters.stockEntryType);
  }
  if (filters.company) {
    formData.append('company', filters.company);
  }
  if (filters.warehouse) {
    formData.append('warehouse', filters.warehouse);
  }
  if (filters.itemCode) {
    formData.append('item_code', filters.itemCode);
  }
  if (filters.fromDate) {
    formData.append('from_date', filters.fromDate);
  }
  if (filters.toDate) {
    formData.append('to_date', filters.toDate);
  }
  if (filters.docstatus !== undefined) {
    formData.append('docstatus', filters.docstatus);
  }
  formData.append('page', pagination.page ?? 1);
  formData.append('page_size', pagination.pageSize ?? 20);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_stock_entries',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const entries = await listStockEntries(
  {
    stockEntryType: 'Material Receipt',
    fromDate: '2024-01-01',
    toDate: '2024-01-31',
    docstatus: 1
  },
  { page: 1, pageSize: 20 }
);
```

#### Response Example

**Success:**
```json
{
  "message": {
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
          "total_outgoing_value": 0.0,
          "total_incoming_value": 5000.0,
          "total_additional_costs": 0.0,
          "total_amount": 5000.0,
          "items_count": 1,
          "items": [
            {
              "item_code": "ITEM-001",
              "qty": 100,
              "s_warehouse": null,
              "t_warehouse": "Main Warehouse",
              "basic_rate": 50.0,
              "amount": 5000.0
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
}
```

---

### 6. List Material Receipts

Convenience endpoint to list only material receipt entries.

**Endpoint:** `list_material_receipts`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_receipts`

#### Request Parameters

Same as `list_stock_entries`, but automatically filters by `stock_entry_type = "Material Receipt"`.

#### Request Example

```javascript
const listMaterialReceipts = async (filters = {}, pagination = {}) => {
  const formData = new FormData();
  
  if (filters.company) formData.append('company', filters.company);
  if (filters.warehouse) formData.append('warehouse', filters.warehouse);
  if (filters.itemCode) formData.append('item_code', filters.itemCode);
  if (filters.fromDate) formData.append('from_date', filters.fromDate);
  if (filters.toDate) formData.append('to_date', filters.toDate);
  if (filters.docstatus !== undefined) formData.append('docstatus', filters.docstatus);
  formData.append('page', pagination.page ?? 1);
  formData.append('page_size', pagination.pageSize ?? 20);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_receipts',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};
```

---

### 7. List Material Issues

Convenience endpoint to list only material issue entries.

**Endpoint:** `list_material_issues`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_issues`

Same parameters as `list_material_receipts`, but filters by `stock_entry_type = "Material Issue"`.

---

### 8. List Material Transfers

Convenience endpoint to list only material transfer entries.

**Endpoint:** `list_material_transfers`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_material_transfers`

Same parameters as `list_material_receipts`, but filters by `stock_entry_type = "Material Transfer"`.

---

### 9. Get Stock Entry Details

Retrieves detailed information about a specific stock entry.

**Endpoint:** `get_stock_entry_details`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_stock_entry_details`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry document |

#### Request Example

```javascript
const getStockEntryDetails = async (stockEntryName) => {
  const formData = new FormData();
  formData.append('stock_entry_name', stockEntryName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_stock_entry_details',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const details = await getStockEntryDetails('MAT-STE-00001');
```

#### Response Example

**Success:**
```json
{
  "message": {
    "success": true,
    "data": {
      "name": "MAT-STE-00001",
      "stock_entry_type": "Material Receipt",
      "purpose": "Material Receipt",
      "company": "My Company",
      "posting_date": "2024-01-15",
      "posting_time": "10:30:00",
      "docstatus": 1,
      "total_outgoing_value": 0.0,
      "total_incoming_value": 5000.0,
      "total_additional_costs": 0.0,
      "total_amount": 5000.0,
      "items": [
        {
          "item_code": "ITEM-001",
          "item_name": "Product Name",
          "qty": 100,
          "s_warehouse": null,
          "t_warehouse": "Main Warehouse",
          "basic_rate": 50.0,
          "amount": 5000.0,
          "valuation_rate": 50.0,
          "serial_no": null,
          "batch_no": null,
          "expense_account": "Stock Adjustment - MC",
          "cost_center": "Main - MC"
        }
      ],
      "items_count": 1
    }
  }
}
```

---

### 10. Update Stock Entry

Updates an existing draft stock entry (only works for `docstatus = 0`).

**Endpoint:** `update_stock_entry`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to update |
| `items` | array/string | No | Updated list of items (replaces all existing items) |
| `posting_date` | string | No | Updated posting date |
| `posting_time` | string | No | Updated posting time |
| `from_warehouse` | string | No | Updated source warehouse |
| `to_warehouse` | string | No | Updated target warehouse |
| `do_not_submit` | boolean | No | If true, don't submit after update (default: false) |

#### Request Example

```javascript
const updateStockEntry = async (stockEntryName, updates) => {
  const formData = new FormData();
  formData.append('stock_entry_name', stockEntryName);
  
  if (updates.items) {
    formData.append('items', JSON.stringify(updates.items));
  }
  if (updates.postingDate) {
    formData.append('posting_date', updates.postingDate);
  }
  if (updates.postingTime) {
    formData.append('posting_time', updates.postingTime);
  }
  if (updates.fromWarehouse) {
    formData.append('from_warehouse', updates.fromWarehouse);
  }
  if (updates.toWarehouse) {
    formData.append('to_warehouse', updates.toWarehouse);
  }
  if (updates.doNotSubmit) {
    formData.append('do_not_submit', updates.doNotSubmit);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.update_stock_entry',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage - Update items in a draft entry
await updateStockEntry('MAT-STE-00001', {
  items: [
    {
      item_code: 'ITEM-001',
      qty: 150,  // Changed from 100
      basic_rate: 50.00
    }
  ]
});
```

#### Response Example

**Success:**
```json
{
  "message": {
    "success": true,
    "message": "Stock entry updated successfully",
    "data": {
      "name": "MAT-STE-00001",
      "stock_entry_type": "Material Receipt",
      "company": "My Company",
      "posting_date": "2024-01-15",
      "docstatus": 1,
      "items_count": 1
    }
  }
}
```

**Error (if already submitted):**
```json
{
  "message": {
    "success": false,
    "message": "Stock Entry 'MAT-STE-00001' cannot be updated. Only draft entries (docstatus=0) can be updated. Current status: 1",
    "docstatus": 1
  }
}
```

---

### 11. Submit Stock Entry

Submits a draft stock entry (changes `docstatus` from 0 to 1).

**Endpoint:** `submit_stock_entry`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to submit |

#### Request Example

```javascript
const submitStockEntry = async (stockEntryName) => {
  const formData = new FormData();
  formData.append('stock_entry_name', stockEntryName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.submit_stock_entry',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await submitStockEntry('MAT-STE-00001');
```

#### Response Example

**Success:**
```json
{
  "message": {
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
}
```

**Error (if already submitted):**
```json
{
  "message": {
    "success": false,
    "message": "Stock Entry 'MAT-STE-00001' cannot be submitted. Only draft entries (docstatus=0) can be submitted. Current status: 1",
    "docstatus": 1
  }
}
```

---

### 12. Cancel Stock Entry

Cancels a submitted stock entry (reverses inventory changes, changes `docstatus` from 1 to 2).

**Endpoint:** `cancel_stock_entry`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stock_entry_name` | string | Yes | Name of the stock entry to cancel |
| `reason` | string | No | Reason for cancellation (optional) |

#### Request Example

```javascript
const cancelStockEntry = async (stockEntryName, reason = null) => {
  const formData = new FormData();
  formData.append('stock_entry_name', stockEntryName);
  if (reason) {
    formData.append('reason', reason);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.inventory_api.cancel_stock_entry',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await cancelStockEntry('MAT-STE-00001', 'Entry was created by mistake');
```

#### Response Example

**Success:**
```json
{
  "message": {
    "success": true,
    "message": "Stock entry cancelled successfully",
    "data": {
      "name": "MAT-STE-00001",
      "docstatus": 2,
      "cancelled_at": "2024-01-15 14:30:00"
    }
  }
}
```

**Error (if not submitted):**
```json
{
  "message": {
    "success": false,
    "message": "Stock Entry 'MAT-STE-00001' cannot be cancelled. Only submitted entries (docstatus=1) can be cancelled. Current status: 0",
    "docstatus": 0
  }
}
```

---

## React Hook Example

Here's a complete React hook for managing stock entries:

```javascript
import { useState, useCallback } from 'react';

const useStockEntry = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = useCallback(async (endpoint, data = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          if (typeof value === 'object' && !(value instanceof File)) {
            formData.append(key, JSON.stringify(value));
          } else {
            formData.append(key, value);
          }
        }
      });

      const response = await fetch(
        `/api/method/savanna_pos.savanna_pos.apis.inventory_api.${endpoint}`,
        {
          method: 'POST',
          credentials: 'include',
          body: formData
        }
      );

      const result = await response.json();
      
      if (result.message?.success) {
        return result.message;
      } else {
        throw new Error(result.message?.message || 'An error occurred');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createStockEntry = useCallback((entryData) => 
    apiCall('create_stock_entry', entryData), [apiCall]);

  const createMaterialReceipt = useCallback((receiptData) => 
    apiCall('create_material_receipt', receiptData), [apiCall]);

  const createMaterialIssue = useCallback((issueData) => 
    apiCall('create_material_issue', issueData), [apiCall]);

  const createMaterialTransfer = useCallback((transferData) => 
    apiCall('create_material_transfer', transferData), [apiCall]);

  const listStockEntries = useCallback((filters = {}, pagination = {}) => 
    apiCall('list_stock_entries', { ...filters, ...pagination }), [apiCall]);

  const listMaterialReceipts = useCallback((filters = {}, pagination = {}) => 
    apiCall('list_material_receipts', { ...filters, ...pagination }), [apiCall]);

  const listMaterialIssues = useCallback((filters = {}, pagination = {}) => 
    apiCall('list_material_issues', { ...filters, ...pagination }), [apiCall]);

  const listMaterialTransfers = useCallback((filters = {}, pagination = {}) => 
    apiCall('list_material_transfers', { ...filters, ...pagination }), [apiCall]);

  const getStockEntryDetails = useCallback((stockEntryName) => 
    apiCall('get_stock_entry_details', { stock_entry_name: stockEntryName }), [apiCall]);

  const updateStockEntry = useCallback((stockEntryName, updates) => 
    apiCall('update_stock_entry', { stock_entry_name: stockEntryName, ...updates }), [apiCall]);

  const submitStockEntry = useCallback((stockEntryName) => 
    apiCall('submit_stock_entry', { stock_entry_name: stockEntryName }), [apiCall]);

  const cancelStockEntry = useCallback((stockEntryName, reason) => 
    apiCall('cancel_stock_entry', { stock_entry_name: stockEntryName, reason }), [apiCall]);

  return {
    loading,
    error,
    createStockEntry,
    createMaterialReceipt,
    createMaterialIssue,
    createMaterialTransfer,
    listStockEntries,
    listMaterialReceipts,
    listMaterialIssues,
    listMaterialTransfers,
    getStockEntryDetails,
    updateStockEntry,
    submitStockEntry,
    cancelStockEntry
  };
};

export default useStockEntry;
```

## Usage in React Component

```javascript
import React, { useState, useEffect } from 'react';
import useStockEntry from './hooks/useStockEntry';

const StockEntryManagement = () => {
  const {
    loading,
    error,
    createMaterialReceipt,
    listMaterialReceipts,
    submitStockEntry,
    cancelStockEntry
  } = useStockEntry();

  const [receipts, setReceipts] = useState([]);
  const [formData, setFormData] = useState({
    items: [{ item_code: '', qty: 0, basic_rate: 0 }],
    targetWarehouse: ''
  });

  useEffect(() => {
    loadReceipts();
  }, []);

  const loadReceipts = async () => {
    try {
      const result = await listMaterialReceipts({ docstatus: 1 }, { page: 1, pageSize: 20 });
      setReceipts(result.data.entries);
    } catch (err) {
      console.error('Failed to load receipts:', err);
    }
  };

  const handleCreateReceipt = async (e) => {
    e.preventDefault();
    try {
      const result = await createMaterialReceipt({
        items: formData.items,
        targetWarehouse: formData.targetWarehouse,
        doNotSubmit: true  // Create as draft first
      });
      
      // Submit the draft entry
      await submitStockEntry(result.data.name);
      
      setFormData({
        items: [{ item_code: '', qty: 0, basic_rate: 0 }],
        targetWarehouse: ''
      });
      loadReceipts();
    } catch (err) {
      console.error('Failed to create receipt:', err);
    }
  };

  const handleCancel = async (entryName) => {
    if (window.confirm('Are you sure you want to cancel this entry?')) {
      try {
        await cancelStockEntry(entryName, 'Cancelled by user');
        loadReceipts();
      } catch (err) {
        console.error('Failed to cancel entry:', err);
      }
    }
  };

  return (
    <div>
      <h1>Stock Entry Management</h1>
      
      {error && <div className="error">{error}</div>}
      
      <form onSubmit={handleCreateReceipt}>
        <h2>Create Material Receipt</h2>
        <input
          type="text"
          value={formData.targetWarehouse}
          onChange={(e) => setFormData({ ...formData, targetWarehouse: e.target.value })}
          placeholder="Target Warehouse"
          required
        />
        {formData.items.map((item, idx) => (
          <div key={idx}>
            <input
              type="text"
              value={item.item_code}
              onChange={(e) => {
                const newItems = [...formData.items];
                newItems[idx].item_code = e.target.value;
                setFormData({ ...formData, items: newItems });
              }}
              placeholder="Item Code"
              required
            />
            <input
              type="number"
              value={item.qty}
              onChange={(e) => {
                const newItems = [...formData.items];
                newItems[idx].qty = parseFloat(e.target.value);
                setFormData({ ...formData, items: newItems });
              }}
              placeholder="Quantity"
              required
              min="0.01"
              step="0.01"
            />
            <input
              type="number"
              value={item.basic_rate}
              onChange={(e) => {
                const newItems = [...formData.items];
                newItems[idx].basic_rate = parseFloat(e.target.value);
                setFormData({ ...formData, items: newItems });
              }}
              placeholder="Rate"
              min="0"
              step="0.01"
            />
          </div>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Receipt'}
        </button>
      </form>

      <div>
        <h2>Material Receipts</h2>
        {receipts.map(entry => (
          <div key={entry.name}>
            <h3>{entry.name}</h3>
            <p>Date: {entry.posting_date}</p>
            <p>Status: {entry.docstatus === 0 ? 'Draft' : entry.docstatus === 1 ? 'Submitted' : 'Cancelled'}</p>
            <p>Total: {entry.total_amount}</p>
            {entry.docstatus === 1 && (
              <button onClick={() => handleCancel(entry.name)}>Cancel</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StockEntryManagement;
```

## TypeScript Types

For TypeScript projects, here are the type definitions:

```typescript
interface StockEntryItem {
  item_code: string;
  qty: number;
  s_warehouse?: string | null;
  t_warehouse?: string | null;
  basic_rate?: number;
  conversion_factor?: number;
  serial_no?: string | null;
  batch_no?: string | null;
  expense_account?: string;
  cost_center?: string;
}

interface StockEntry {
  name: string;
  stock_entry_type: string;
  purpose: string;
  company: string;
  posting_date: string;
  posting_time?: string;
  docstatus: 0 | 1 | 2;  // 0=Draft, 1=Submitted, 2=Cancelled
  total_outgoing_value: number;
  total_incoming_value: number;
  total_additional_costs: number;
  total_amount: number;
  items: StockEntryItem[];
  items_count: number;
}

interface StockEntryListItem {
  name: string;
  stock_entry_type: string;
  purpose: string;
  company: string;
  posting_date: string;
  posting_time?: string;
  docstatus: number;
  total_outgoing_value: number;
  total_incoming_value: number;
  total_additional_costs: number;
  total_amount: number;
  items_count: number;
  items?: StockEntryItem[];
}

interface StockEntryFilters {
  stock_entry_type?: string;
  company?: string;
  warehouse?: string;
  item_code?: string;
  from_date?: string;
  to_date?: string;
  docstatus?: number;
}

interface Pagination {
  page?: number;
  page_size?: number;
}

interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error_type?: string;
}

type StockEntryType = 
  | 'Material Receipt'
  | 'Material Issue'
  | 'Material Transfer'
  | 'Manufacture'
  | 'Repack'
  | 'Opening Stock';
```

## Common Workflows

### Workflow 1: Create and Submit Material Receipt

```javascript
// Step 1: Create as draft
const draft = await createMaterialReceipt({
  items: [{ item_code: 'ITEM-001', qty: 100, basic_rate: 50.00 }],
  targetWarehouse: 'Main Warehouse',
  doNotSubmit: true
});

// Step 2: Review/Edit if needed
// ... user reviews the draft ...

// Step 3: Submit
await submitStockEntry(draft.data.name);
```

### Workflow 2: Update Draft Entry

```javascript
// Get existing draft
const draft = await getStockEntryDetails('MAT-STE-00001');

// Update it
await updateStockEntry('MAT-STE-00001', {
  items: [
    {
      item_code: 'ITEM-001',
      qty: 150,  // Updated quantity
      basic_rate: 50.00
    }
  ]
});
```

### Workflow 3: Transfer Stock Between Warehouses

```javascript
await createMaterialTransfer({
  items: [
    { item_code: 'ITEM-001', qty: 50 },
    { item_code: 'ITEM-002', qty: 25 }
  ],
  sourceWarehouse: 'Warehouse A',
  targetWarehouse: 'Warehouse B',
  postingDate: '2024-01-15'
});
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "message": {
    "success": false,
    "message": "Error description here",
    "error_type": "validation_error"  // Optional
  }
}
```

Common HTTP status codes:
- **200**: Success
- **417**: Validation error
- **401**: Authentication required
- **403**: Permission denied

## Important Notes

1. **Document Status**: 
   - Draft (0): Can be edited, inventory not yet updated
   - Submitted (1): Finalized, inventory updated, cannot be edited
   - Cancelled (2): Reversed, inventory restored

2. **Submission Required**: Stock entries must be submitted (`docstatus = 1`) to update inventory. Draft entries don't affect stock balances.

3. **Cancellation**: Cancelling a submitted entry reverses all inventory changes and restores stock balances.

4. **Warehouse Requirements**:
   - Material Receipt: Requires `target_warehouse` only
   - Material Issue: Requires `source_warehouse` only
   - Material Transfer: Requires both `source_warehouse` and `target_warehouse`

5. **Item-Level Warehouses**: You can override document-level warehouses by specifying `s_warehouse` or `t_warehouse` in individual items.

6. **Batch and Serial Numbers**: For items with batch/serial tracking, include `batch_no` or `serial_no` in item objects.

7. **Valuation**: The `basic_rate` field sets the cost per unit for inventory valuation. If not provided, system uses standard cost or average cost.

8. **FormData Format**: All POST requests use FormData format, which is required by Frappe's API.
