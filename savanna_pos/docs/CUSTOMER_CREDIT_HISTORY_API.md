# Customer Credit & Sale History API Documentation

## Overview

This document provides complete API documentation for **tracing customer credit and sale history** in the SavvyPOS system. These APIs allow frontend applications to retrieve customer credit balances, outstanding amounts, invoice history, and payment statuses.

---

## Base URL

```
https://your-domain.com/api/method/
```

## Authentication

All endpoints require authentication:

1. **OAuth Bearer Token** (Recommended)
   ```
   Authorization: Bearer <access_token>
   ```

2. **API Key/Secret**
   ```
   Authorization: token <api_key>:<api_secret>
   ```

---

## API Endpoints

### 1. Get Customer Credit Summary

Get a customer's credit summary including total outstanding amount and total sales.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.get_customer`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Customer name/ID (e.g., `CUST-00001`) |

**Response:**

```json
{
  "success": true,
  "data": {
    "name": "CUST-00001",
    "customer_name": "John Doe",
    "customer_type": "Individual",
    "customer_group": "All Customer Groups",
    "territory": "All Territories",
    "tax_id": null,
    "mobile_no": "+254712345678",
    "email_id": "john.doe@example.com",
    "disabled": false,
    "default_currency": "KES",
    "default_price_list": "Standard Selling",
    "accounts": [
      {
        "company": "My Company",
        "account": "Debtors - MC"
      }
    ],
    "outstanding_amount": 5000.0,
    "total_sales": 25000.0
  }
}
```

**Response Fields:**

- `outstanding_amount` (number): **Total credit balance** - Sum of all unpaid/partially paid invoices
- `total_sales` (number): **Total sales amount** - Sum of all submitted sales invoices (paid + unpaid)
- `accounts` (array): Customer accounts per company

**Example Request:**

```bash
# GET request
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer?name=CUST-00001" \
  -H "Authorization: Bearer <access_token>"

# POST request
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CUST-00001"
  }'
```

**Error Response (Not Found):**

```json
{
  "success": false,
  "message": "Customer CUST-00001 not found",
  "error_type": "not_found"
}
```

**HTTP Status Code:** `200 OK` (success) or `404 Not Found` (customer not found)

---

### 2. List Customer Sales Invoices (Credit History)

List all sales invoices for a customer with detailed credit information. This is the primary endpoint for tracing credit history.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer name/ID to filter invoices |
| `from_date` | string | No | Filter by posting date start (`YYYY-MM-DD`) |
| `to_date` | string | No | Filter by posting date end (`YYYY-MM-DD`) |
| `company` | string | No | Company name (defaults to current user's company) |
| `status` | string | No | Filter by status: `"Draft"`, `"Unpaid"`, `"Partly Paid"`, `"Paid"`, `"Overdue"`, `"Cancelled"` |
| `is_pos` | boolean | No | Filter POS invoices (`true`) or regular invoices (`false`) |
| `limit_start` | number | No | Pagination offset (default: `0`) |
| `limit_page_length` | number | No | Number of records per page (default: `20`) |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "name": "SINV-00005",
      "customer": "CUST-00001",
      "posting_date": "2024-01-25",
      "company": "My Company",
      "grand_total": 3000.0,
      "rounded_total": 3000.0,
      "outstanding_amount": 3000.0,
      "status": "Unpaid",
      "is_pos": false,
      "docstatus": 1
    },
    {
      "name": "SINV-00002",
      "customer": "CUST-00001",
      "posting_date": "2024-01-20",
      "company": "My Company",
      "grand_total": 2000.0,
      "rounded_total": 2000.0,
      "outstanding_amount": 500.0,
      "status": "Partly Paid",
      "is_pos": false,
      "docstatus": 1
    },
    {
      "name": "SINV-00001",
      "customer": "CUST-00001",
      "posting_date": "2024-01-15",
      "company": "My Company",
      "grand_total": 1500.0,
      "rounded_total": 1500.0,
      "outstanding_amount": 0.0,
      "status": "Paid",
      "is_pos": false,
      "docstatus": 1
    }
  ],
  "count": 3
}
```

**Response Fields:**

- `name` (string): Invoice number (e.g., `SINV-00001`)
- `customer` (string): Customer ID
- `posting_date` (string): Invoice date (`YYYY-MM-DD`)
- `grand_total` (number): Total invoice amount
- `outstanding_amount` (number): **Credit balance** - Amount still owed (0 if fully paid)
- `status` (string): Payment status:
  - `"Unpaid"` - No payment received
  - `"Partly Paid"` - Partial payment received
  - `"Paid"` - Fully paid
  - `"Overdue"` - Payment past due date
  - `"Draft"` - Not yet submitted
  - `"Cancelled"` - Invoice cancelled
- `is_pos` (boolean): Whether this is a POS invoice (`true`) or regular credit sale (`false`)
- `docstatus` (number): Document status (`0` = Draft, `1` = Submitted, `2` = Cancelled)

**Example Requests:**

```bash
# Get all invoices for a customer
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=CUST-00001" \
  -H "Authorization: Bearer <access_token>"

# Get only unpaid invoices (credit sales)
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=CUST-00001&status=Unpaid" \
  -H "Authorization: Bearer <access_token>"

# Get invoices within date range
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=CUST-00001&from_date=2024-01-01&to_date=2024-01-31" \
  -H "Authorization: Bearer <access_token>"

# Get overdue invoices
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=CUST-00001&status=Overdue" \
  -H "Authorization: Bearer <access_token>"

# Pagination example
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=CUST-00001&limit_start=0&limit_page_length=50" \
  -H "Authorization: Bearer <access_token>"
```

**HTTP Status Code:** `200 OK`

---

### 3. Get Individual Invoice Details

Get complete details of a specific sales invoice including items, payments, and credit information.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.sales_api.get_sales_invoice`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Invoice name (e.g., `SINV-00001`) |

**Response:**

```json
{
  "success": true,
  "data": {
    "name": "SINV-00001",
    "customer": "CUST-00001",
    "customer_name": "John Doe",
    "company": "My Company",
    "posting_date": "2024-01-15",
    "due_date": "2024-01-30",
    "grand_total": 1500.0,
    "rounded_total": 1500.0,
    "outstanding_amount": 1500.0,
    "paid_amount": 0.0,
    "status": "Unpaid",
    "is_pos": false,
    "docstatus": 1,
    "items": [
      {
        "item_code": "ITEM-001",
        "item_name": "Product A",
        "qty": 2,
        "rate": 500,
        "amount": 1000
      }
    ],
    "payments": [],
    "payment_terms_template": null,
    "remarks": null
  }
}
```

**Key Credit-Related Fields:**

- `outstanding_amount` (number): Amount still owed
- `paid_amount` (number): Amount already paid
- `due_date` (string): Payment due date (`YYYY-MM-DD`)
- `status` (string): Current payment status
- `payments` (array): Payment entries (empty for credit sales)
- `payment_terms_template` (string): Payment terms if applicable

**Example Request:**

```bash
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.get_sales_invoice?name=SINV-00001" \
  -H "Authorization: Bearer <access_token>"
```

**Error Response (Not Found):**

```json
{
  "success": false,
  "message": "Sales Invoice SINV-00001 does not exist"
}
```

**HTTP Status Code:** `200 OK` (success) or `404 Not Found` (invoice not found)

---

### 4. List Sales Returns (Credit Notes)

List credit notes/returns for a customer. These represent refunds or adjustments to invoices.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.sales_api.list_sales_returns`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | No | Filter by customer |
| `from_date` | string | No | Filter by posting date start (`YYYY-MM-DD`) |
| `to_date` | string | No | Filter by posting date end (`YYYY-MM-DD`) |
| `company` | string | No | Company name |
| `return_against` | string | No | Filter by original invoice name |
| `status` | string | No | Filter by status |
| `limit_start` | number | No | Pagination offset (default: `0`) |
| `limit_page_length` | number | No | Records per page (default: `20`) |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "name": "CN-00001",
      "customer": "CUST-00001",
      "return_against": "SINV-00001",
      "posting_date": "2024-01-22",
      "company": "My Company",
      "grand_total": -500.0,
      "rounded_total": -500.0,
      "outstanding_amount": -500.0,
      "status": "Unpaid",
      "docstatus": 1
    }
  ],
  "count": 1
}
```

**Note:** Credit notes have negative amounts. The `outstanding_amount` is negative, representing credit to the customer.

**Example Request:**

```bash
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_returns?customer=CUST-00001" \
  -H "Authorization: Bearer <access_token>"
```

**HTTP Status Code:** `200 OK`

---

## Frontend Integration Guide

### Common Use Cases

#### 1. Display Customer Credit Summary

Show total outstanding amount and total sales on customer profile page:

```javascript
// Fetch customer credit summary
async function getCustomerCreditSummary(customerId) {
  const response = await fetch(
    `/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer?name=${customerId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    return {
      outstandingAmount: data.data.outstanding_amount,
      totalSales: data.data.total_sales,
      customerName: data.data.customer_name
    };
  }
  
  throw new Error(data.message);
}
```

#### 2. Display Credit History Table

Show all invoices with credit balances in a table:

```javascript
// Fetch customer credit history
async function getCustomerCreditHistory(customerId, filters = {}) {
  const params = new URLSearchParams({
    customer: customerId,
    ...filters
  });
  
  const response = await fetch(
    `/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    return data.data.map(invoice => ({
      invoiceNumber: invoice.name,
      date: invoice.posting_date,
      total: invoice.grand_total,
      outstanding: invoice.outstanding_amount,
      status: invoice.status,
      isCredit: invoice.outstanding_amount > 0
    }));
  }
  
  throw new Error(data.message);
}
```

#### 3. Filter Unpaid/Overdue Invoices

Get only invoices that need payment:

```javascript
// Get unpaid invoices
const unpaidInvoices = await getCustomerCreditHistory(customerId, {
  status: 'Unpaid'
});

// Get overdue invoices
const overdueInvoices = await getCustomerCreditHistory(customerId, {
  status: 'Overdue'
});

// Get all credit sales (unpaid + partly paid)
const creditSales = await getCustomerCreditHistory(customerId, {
  status: ['Unpaid', 'Partly Paid'] // Note: API may need to support array
});
```

#### 4. Date Range Filtering

Get invoices within a specific period:

```javascript
// Get invoices for current month
const currentMonth = new Date();
const firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
const lastDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);

const monthlyInvoices = await getCustomerCreditHistory(customerId, {
  from_date: firstDay.toISOString().split('T')[0],
  to_date: lastDay.toISOString().split('T')[0]
});
```

#### 5. Pagination Implementation

Handle large lists with pagination:

```javascript
async function getCustomerInvoicesPaginated(customerId, page = 1, pageSize = 20) {
  const response = await fetch(
    `/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?customer=${customerId}&limit_start=${(page - 1) * pageSize}&limit_page_length=${pageSize}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  
  return {
    invoices: data.data,
    totalCount: data.count,
    hasMore: data.count === pageSize
  };
}
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function CustomerCreditHistory({ customerId }) {
  const [summary, setSummary] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: 'Unpaid', // Default: show only unpaid
    from_date: null,
    to_date: null
  });

  useEffect(() => {
    loadCustomerData();
  }, [customerId, filters]);

  async function loadCustomerData() {
    setLoading(true);
    try {
      // Load summary
      const summaryRes = await fetch(
        `/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer?name=${customerId}`,
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        }
      );
      const summaryData = await summaryRes.json();
      if (summaryData.success) {
        setSummary(summaryData.data);
      }

      // Load invoices
      const params = new URLSearchParams({
        customer: customerId,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== null)
        )
      });
      
      const invoicesRes = await fetch(
        `/api/method/savanna_pos.savanna_pos.apis.sales_api.list_sales_invoices?${params}`,
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        }
      );
      const invoicesData = await invoicesRes.json();
      if (invoicesData.success) {
        setInvoices(invoicesData.data);
      }
    } catch (error) {
      console.error('Error loading customer data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {/* Credit Summary Card */}
      {summary && (
        <div className="credit-summary">
          <h3>Credit Summary</h3>
          <p>Total Outstanding: {summary.outstanding_amount.toLocaleString()} {summary.default_currency}</p>
          <p>Total Sales: {summary.total_sales.toLocaleString()} {summary.default_currency}</p>
        </div>
      )}

      {/* Invoice History Table */}
      <table>
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Date</th>
            <th>Total</th>
            <th>Outstanding</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map(invoice => (
            <tr key={invoice.name}>
              <td>{invoice.name}</td>
              <td>{invoice.posting_date}</td>
              <td>{invoice.grand_total.toLocaleString()}</td>
              <td className={invoice.outstanding_amount > 0 ? 'outstanding' : 'paid'}>
                {invoice.outstanding_amount.toLocaleString()}
              </td>
              <td>
                <span className={`status-${invoice.status.toLowerCase().replace(' ', '-')}`}>
                  {invoice.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default CustomerCreditHistory;
```

---

## Status Values Reference

### Invoice Status

| Status | Description | Outstanding Amount |
|--------|-------------|-------------------|
| `Draft` | Invoice not yet submitted | Equal to grand_total |
| `Unpaid` | No payment received, not overdue | > 0 |
| `Partly Paid` | Partial payment received | > 0 and < grand_total |
| `Paid` | Fully paid | 0 |
| `Overdue` | Payment past due date | > 0 |
| `Cancelled` | Invoice cancelled | 0 |

### Document Status (docstatus)

| Value | Description |
|-------|-------------|
| `0` | Draft - Not submitted |
| `1` | Submitted - Active invoice |
| `2` | Cancelled - Invoice cancelled |

---

## Error Handling

All endpoints return structured error responses:

### Not Found Error

```json
{
  "success": false,
  "message": "Customer CUST-00001 not found",
  "error_type": "not_found"
}
```

### Validation Error

```json
{
  "success": false,
  "message": "Validation error: Invalid customer",
  "error_type": "validation_error"
}
```

### General Error

```json
{
  "success": false,
  "message": "Error fetching customer: <error details>"
}
```

---

## HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Validation error or invalid parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Best Practices

1. **Always check `success` field** in responses before processing data
2. **Handle pagination** for large customer histories using `limit_start` and `limit_page_length`
3. **Use date filters** to limit data retrieval to relevant periods
4. **Cache customer summary** data to reduce API calls
5. **Filter by status** to show only relevant invoices (e.g., unpaid for credit management)
6. **Display outstanding amounts prominently** for credit management
7. **Use `is_pos` flag** to distinguish between POS cash sales and credit sales
8. **Handle negative outstanding amounts** for credit notes (returns)
9. **Implement error boundaries** in frontend to handle API failures gracefully
10. **Show loading states** while fetching data

---

## Credit Sales vs Cash Sales

### Credit Sales (Regular Sales Invoices)

- `is_pos = false` or not set
- Can have `outstanding_amount > 0`
- Payment not required at creation
- Status can be: `Unpaid`, `Partly Paid`, `Paid`, `Overdue`

### Cash Sales (POS Invoices)

- `is_pos = true` or `doctype = "POS Invoice"`
- Usually `outstanding_amount = 0` (unless partial payment allowed)
- Payment required at creation
- Status usually: `Paid`

---

## Support and Feedback

For API support, feature requests, or to report issues:

- **Email**: api-support@savvypos.com
- **Documentation**: https://docs.savvypos.com/api
- **Status Page**: https://status.savvypos.com

---

## Changelog

### Version 1.0 (2025-01-20)

- Initial release of Customer Credit & Sale History API documentation
- Support for customer credit summary
- Support for listing customer invoices with credit information
- Support for individual invoice details
- Support for credit notes/returns
- Comprehensive filtering and pagination options
