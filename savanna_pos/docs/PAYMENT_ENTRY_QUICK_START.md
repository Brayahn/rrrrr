# Payment Entry API - Quick Start Guide

## Overview

The Payment Entry API allows you to record payments against Sales Invoices, automatically updating the invoice status from "Unpaid" or "Partly Paid" to "Paid" when fully paid.

## Quick Example

### Record Full Payment

```javascript
// React/JavaScript Example
const recordPayment = async (invoiceId) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sales_invoice: invoiceId,
        mode_of_payment: 'Cash',
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    console.log('Payment recorded!', data.data);
    // Invoice status automatically updated to "Paid"
  }
};
```

### Record Partial Payment

```javascript
const recordPartialPayment = async (invoiceId, amount) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sales_invoice: invoiceId,
        paid_amount: amount,
        mode_of_payment: 'Bank Transfer',
        bank_account: 'Bank Account - MC',
        reference_no: 'TXN-123456',
        remarks: 'Partial payment received',
      }),
    }
  );
  
  const data = await response.json();
  // Invoice status will be "Partly Paid" if amount < outstanding_amount
};
```

### Check Payment Status

```javascript
const checkPaymentStatus = async (invoiceId) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sales_invoice: invoiceId,
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    const { sales_invoice, payment_summary } = data.data;
    console.log('Status:', sales_invoice.status);
    console.log('Outstanding:', sales_invoice.outstanding_amount);
    console.log('Is Fully Paid:', payment_summary.is_fully_paid);
  }
};
```

## API Endpoints

### 1. Create Payment Entry
- **Endpoint:** `savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice`
- **Method:** POST
- **Required:** `sales_invoice`
- **Optional:** `paid_amount`, `mode_of_payment`, `bank_account`, `posting_date`, `reference_no`, `remarks`, `submit`

### 2. Get Payment Status
- **Endpoint:** `savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status`
- **Method:** GET or POST
- **Required:** `sales_invoice`

## Status Flow

```
Unpaid → [First Payment] → Partly Paid → [Final Payment] → Paid
```

## Key Points

1. **Automatic Status Update**: Invoice status updates automatically when payment is submitted
2. **Partial Payments**: You can make multiple payments against the same invoice
3. **Full Payment**: Omit `paid_amount` to pay the full outstanding amount
4. **Validation**: API validates that payment amount doesn't exceed outstanding amount
5. **Payment History**: Use `get_invoice_payment_status` to see all payments

## Common Use Cases

### Use Case 1: Customer Pays Full Amount
```javascript
{
  sales_invoice: "SINV-00001",
  mode_of_payment: "Cash"
  // paid_amount omitted = full payment
}
```

### Use Case 2: Customer Makes Partial Payment
```javascript
{
  sales_invoice: "SINV-00001",
  paid_amount: 2000.0,
  mode_of_payment: "Bank Transfer",
  reference_no: "TXN-123456"
}
```

### Use Case 3: Multiple Payments Over Time
```javascript
// First payment
await recordPayment("SINV-00001", 1000, "Cash");

// Second payment
await recordPayment("SINV-00001", 500, "Bank Transfer");

// Final payment (remaining amount)
await recordPayment("SINV-00001", null, "Cash");
```

## Error Handling

```javascript
try {
  const response = await fetch(apiUrl, options);
  const data = await response.json();
  
  if (!data.success) {
    switch (data.error_type) {
      case 'not_found':
        console.error('Invoice not found');
        break;
      case 'validation_error':
        console.error('Validation error:', data.message);
        break;
      default:
        console.error('Error:', data.message);
    }
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Full Documentation

See [PAYMENT_ENTRY_API_DOCUMENTATION.md](./PAYMENT_ENTRY_API_DOCUMENTATION.md) for complete API documentation with React examples.

