# Payment Entry API Documentation

## Overview

This document provides complete API documentation for **creating payment entries against Sales Invoices** in the SavvyPOS system. These APIs allow frontend applications to record payments received from customers, moving invoices from "Unpaid" or "Partly Paid" status to "Paid" status when fully paid.

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

### 1. Create Payment Entry for Sales Invoice

Create a payment entry to record payment received against a Sales Invoice. This will update the invoice's outstanding amount and status automatically.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sales_invoice` | string | Yes | Sales Invoice name/ID (e.g., `SINV-00001`) |
| `paid_amount` | number | No | Amount to pay (defaults to outstanding_amount if not provided) |
| `mode_of_payment` | string | No | Mode of payment name (e.g., `Cash`, `Bank Transfer`). If not provided, uses company default or first available. |
| `bank_account` | string | No | Bank account name (required for bank payments) |
| `posting_date` | string | No | Posting date in `YYYY-MM-DD` format (defaults to today) |
| `reference_no` | string | No | Payment reference number (e.g., cheque number, transaction ID) |
| `reference_date` | string | No | Reference date in `YYYY-MM-DD` format |
| `remarks` | string | No | Additional remarks/notes |
| `submit` | boolean | No | Whether to submit the payment entry (default: `true`) |

**Response (Success):**

```json
{
  "success": true,
  "message": "Payment Entry created successfully",
  "data": {
    "payment_entry": {
      "name": "ACC-PAY-00001",
      "payment_type": "Receive",
      "party": "CUST-00001",
      "party_type": "Customer",
      "paid_amount": 5000.0,
      "received_amount": 5000.0,
      "posting_date": "2024-01-15",
      "mode_of_payment": "Cash",
      "docstatus": 1
    },
    "sales_invoice": {
      "name": "SINV-00001",
      "outstanding_amount": 0.0,
      "status": "Paid",
      "paid_amount": 5000.0
    }
  }
}
```

**Response Fields:**

- `payment_entry.name` (string): Payment Entry document name
- `payment_entry.payment_type` (string): Type of payment (`Receive` for customer payments)
- `payment_entry.paid_amount` (number): Amount paid
- `payment_entry.docstatus` (number): Document status (0=Draft, 1=Submitted, 2=Cancelled)
- `sales_invoice.outstanding_amount` (number): Remaining outstanding amount after payment
- `sales_invoice.status` (string): Updated invoice status (`Unpaid`, `Partly Paid`, `Paid`, `Overdue`)

**Error Responses:**

```json
// Invoice not found
{
  "success": false,
  "message": "Sales Invoice SINV-00001 not found",
  "error_type": "not_found"
}

// Invoice not submitted
{
  "success": false,
  "message": "Sales Invoice SINV-00001 must be submitted before receiving payment",
  "error_type": "validation_error"
}

// Already fully paid
{
  "success": false,
  "message": "Sales Invoice SINV-00001 is already fully paid",
  "error_type": "validation_error"
}

// Amount exceeds outstanding
{
  "success": false,
  "message": "Paid amount (6000.0) cannot be greater than outstanding amount (5000.0)",
  "error_type": "validation_error"
}
```

**Example Request (Full Payment):**

```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sales_invoice": "SINV-00001",
    "mode_of_payment": "Cash",
    "remarks": "Payment received in full"
  }'
```

**Example Request (Partial Payment):**

```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sales_invoice": "SINV-00001",
    "paid_amount": 2000.0,
    "mode_of_payment": "Bank Transfer",
    "bank_account": "Bank Account - MC",
    "reference_no": "TXN-123456",
    "posting_date": "2024-01-15",
    "remarks": "Partial payment via bank transfer"
  }'
```

**Example Request (Draft Payment Entry):**

```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sales_invoice": "SINV-00001",
    "paid_amount": 3000.0,
    "mode_of_payment": "Cash",
    "submit": false
  }'
```

---

### 2. Get Invoice Payment Status

Get the current payment status, outstanding amount, and payment history for a Sales Invoice.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sales_invoice` | string | Yes | Sales Invoice name/ID (e.g., `SINV-00001`) |

**Response (Success):**

```json
{
  "success": true,
  "data": {
    "sales_invoice": {
      "name": "SINV-00001",
      "customer": "CUST-00001",
      "grand_total": 5000.0,
      "outstanding_amount": 2000.0,
      "paid_amount": 3000.0,
      "status": "Partly Paid",
      "posting_date": "2024-01-10",
      "due_date": "2024-01-25"
    },
    "payment_summary": {
      "total_paid": 3000.0,
      "outstanding_amount": 2000.0,
      "is_fully_paid": false,
      "payment_count": 2
    },
    "payment_entries": [
      {
        "name": "ACC-PAY-00001",
        "posting_date": "2024-01-12",
        "paid_amount": 2000.0,
        "mode_of_payment": "Cash",
        "docstatus": 1,
        "status": "Submitted"
      },
      {
        "name": "ACC-PAY-00002",
        "posting_date": "2024-01-14",
        "paid_amount": 1000.0,
        "mode_of_payment": "Bank Transfer",
        "docstatus": 1,
        "status": "Submitted"
      }
    ]
  }
}
```

**Response Fields:**

- `sales_invoice.status` (string): Current invoice status
  - `"Unpaid"`: No payment received
  - `"Partly Paid"`: Partial payment received
  - `"Paid"`: Fully paid
  - `"Overdue"`: Past due date and unpaid
- `payment_summary.is_fully_paid` (boolean): Whether invoice is fully paid
- `payment_summary.payment_count` (number): Number of payment entries
- `payment_entries` (array): List of all payment entries against this invoice

**Example Request:**

```bash
# GET request
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status?sales_invoice=SINV-00001" \
  -H "Authorization: Bearer <access_token>"

# POST request
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sales_invoice": "SINV-00001"
  }'
```

---

## React Integration Examples

### 1. Create Payment Entry Component

```tsx
import React, { useState } from 'react';
import axios from 'axios';

interface PaymentEntryProps {
  salesInvoice: string;
  onPaymentSuccess?: () => void;
}

const CreatePaymentEntry: React.FC<PaymentEntryProps> = ({ 
  salesInvoice, 
  onPaymentSuccess 
}) => {
  const [formData, setFormData] = useState({
    paid_amount: '',
    mode_of_payment: '',
    bank_account: '',
    reference_no: '',
    remarks: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.sales_api.create_payment_entry_for_invoice',
        {
          sales_invoice: salesInvoice,
          ...formData,
          paid_amount: formData.paid_amount ? parseFloat(formData.paid_amount) : undefined,
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        alert('Payment recorded successfully!');
        if (onPaymentSuccess) {
          onPaymentSuccess();
        }
        // Reset form
        setFormData({
          paid_amount: '',
          mode_of_payment: '',
          bank_account: '',
          reference_no: '',
          remarks: '',
        });
      } else {
        setError(response.data.message || 'Failed to create payment entry');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="payment-entry-form">
      <h3>Record Payment</h3>
      
      {error && <div className="error">{error}</div>}
      
      <div className="form-group">
        <label>Amount to Pay</label>
        <input
          type="number"
          step="0.01"
          value={formData.paid_amount}
          onChange={(e) => setFormData({ ...formData, paid_amount: e.target.value })}
          placeholder="Leave empty for full payment"
        />
      </div>

      <div className="form-group">
        <label>Mode of Payment *</label>
        <select
          value={formData.mode_of_payment}
          onChange={(e) => setFormData({ ...formData, mode_of_payment: e.target.value })}
          required
        >
          <option value="">Select...</option>
          <option value="Cash">Cash</option>
          <option value="Bank Transfer">Bank Transfer</option>
          <option value="Cheque">Cheque</option>
        </select>
      </div>

      <div className="form-group">
        <label>Bank Account (if applicable)</label>
        <input
          type="text"
          value={formData.bank_account}
          onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
        />
      </div>

      <div className="form-group">
        <label>Reference Number</label>
        <input
          type="text"
          value={formData.reference_no}
          onChange={(e) => setFormData({ ...formData, reference_no: e.target.value })}
          placeholder="e.g., Transaction ID, Cheque Number"
        />
      </div>

      <div className="form-group">
        <label>Remarks</label>
        <textarea
          value={formData.remarks}
          onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
          rows={3}
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Record Payment'}
      </button>
    </form>
  );
};

export default CreatePaymentEntry;
```

### 2. Invoice Payment Status Component

```tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface PaymentStatusProps {
  salesInvoice: string;
}

interface PaymentStatusData {
  sales_invoice: {
    name: string;
    customer: string;
    grand_total: number;
    outstanding_amount: number;
    paid_amount: number;
    status: string;
    posting_date: string;
    due_date: string | null;
  };
  payment_summary: {
    total_paid: number;
    outstanding_amount: number;
    is_fully_paid: boolean;
    payment_count: number;
  };
  payment_entries: Array<{
    name: string;
    posting_date: string;
    paid_amount: number;
    mode_of_payment: string;
    docstatus: number;
    status: string;
  }>;
}

const InvoicePaymentStatus: React.FC<PaymentStatusProps> = ({ salesInvoice }) => {
  const [data, setData] = useState<PaymentStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPaymentStatus();
  }, [salesInvoice]);

  const fetchPaymentStatus = async () => {
    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.sales_api.get_invoice_payment_status',
        { sales_invoice: salesInvoice },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        setData(response.data.data);
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch payment status');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!data) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Paid': return 'green';
      case 'Partly Paid': return 'orange';
      case 'Unpaid': return 'red';
      case 'Overdue': return 'darkred';
      default: return 'gray';
    }
  };

  return (
    <div className="payment-status">
      <div className="invoice-summary">
        <h3>Invoice: {data.sales_invoice.name}</h3>
        <div className="status-badge" style={{ color: getStatusColor(data.sales_invoice.status) }}>
          {data.sales_invoice.status}
        </div>
        
        <div className="amounts">
          <div>
            <label>Grand Total:</label>
            <span>{data.sales_invoice.grand_total.toLocaleString()}</span>
          </div>
          <div>
            <label>Paid Amount:</label>
            <span>{data.sales_invoice.paid_amount.toLocaleString()}</span>
          </div>
          <div>
            <label>Outstanding:</label>
            <span className={data.sales_invoice.outstanding_amount > 0 ? 'outstanding' : 'paid'}>
              {data.sales_invoice.outstanding_amount.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="payment-history">
        <h4>Payment History ({data.payment_summary.payment_count} payments)</h4>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Mode</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.payment_entries.map((entry) => (
              <tr key={entry.name}>
                <td>{new Date(entry.posting_date).toLocaleDateString()}</td>
                <td>{entry.paid_amount.toLocaleString()}</td>
                <td>{entry.mode_of_payment}</td>
                <td>
                  <span className={entry.docstatus === 1 ? 'submitted' : 'draft'}>
                    {entry.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InvoicePaymentStatus;
```

### 3. Complete Payment Flow Example

```tsx
import React, { useState, useEffect } from 'react';
import CreatePaymentEntry from './CreatePaymentEntry';
import InvoicePaymentStatus from './InvoicePaymentStatus';

const InvoicePaymentPage: React.FC<{ invoiceId: string }> = ({ invoiceId }) => {
  const [refreshKey, setRefreshKey] = useState(0);

  const handlePaymentSuccess = () => {
    // Refresh payment status after successful payment
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="invoice-payment-page">
      <h2>Invoice Payment Management</h2>
      
      <div className="payment-status-section">
        <InvoicePaymentStatus 
          key={refreshKey}
          salesInvoice={invoiceId} 
        />
      </div>

      <div className="payment-entry-section">
        <CreatePaymentEntry 
          salesInvoice={invoiceId}
          onPaymentSuccess={handlePaymentSuccess}
        />
      </div>
    </div>
  );
};

export default InvoicePaymentPage;
```

---

## Status Flow

### Invoice Status Transitions

1. **Unpaid** → **Partly Paid**
   - When first partial payment is received
   - `outstanding_amount` > 0 and < `grand_total`

2. **Partly Paid** → **Paid**
   - When remaining outstanding amount is paid
   - `outstanding_amount` becomes 0 or negative

3. **Unpaid** → **Paid**
   - When full payment is received in one transaction
   - `outstanding_amount` becomes 0

4. **Unpaid/Partly Paid** → **Overdue**
   - When `due_date` has passed and `outstanding_amount` > 0
   - Status automatically updates based on due date

### Payment Entry Status

- **Draft (docstatus: 0)**: Payment entry created but not submitted
- **Submitted (docstatus: 1)**: Payment entry submitted and invoice updated
- **Cancelled (docstatus: 2)**: Payment entry cancelled (reverses invoice update)

---

## Best Practices

1. **Always check invoice status** before creating payment entry
2. **Validate outstanding amount** to prevent overpayment
3. **Use appropriate mode of payment** for different payment types
4. **Include reference numbers** for bank transfers and cheques
5. **Handle partial payments** by specifying `paid_amount`
6. **Refresh invoice status** after payment creation
7. **Display payment history** to users for transparency
8. **Handle errors gracefully** with user-friendly messages

---

## Error Handling

### Common Errors

| Error Type | Description | Solution |
|------------|-------------|----------|
| `not_found` | Invoice or mode of payment not found | Verify invoice/mode of payment exists |
| `validation_error` | Invalid data or business rule violation | Check error message and fix input |
| `server_error` | Unexpected server error | Check error logs, retry request |

### Error Response Format

```json
{
  "success": false,
  "message": "Error description",
  "error_type": "error_category"
}
```

---

## Testing

### Test Scenarios

1. **Full Payment**
   - Create payment entry without `paid_amount`
   - Verify invoice status changes to "Paid"
   - Verify `outstanding_amount` becomes 0

2. **Partial Payment**
   - Create payment entry with `paid_amount` < `outstanding_amount`
   - Verify invoice status changes to "Partly Paid"
   - Verify `outstanding_amount` is reduced correctly

3. **Multiple Payments**
   - Create multiple payment entries
   - Verify all payments are recorded
   - Verify final status when fully paid

4. **Error Cases**
   - Try to pay more than outstanding amount
   - Try to pay against non-existent invoice
   - Try to pay against draft invoice

---

## Notes

- Payment entries automatically update the Sales Invoice's `outstanding_amount` and `status` fields
- The invoice status is calculated based on `outstanding_amount`:
  - `outstanding_amount <= 0` → "Paid"
  - `0 < outstanding_amount < grand_total` → "Partly Paid"
  - `outstanding_amount > 0` and `due_date < today` → "Overdue"
  - `outstanding_amount > 0` and `due_date >= today` → "Unpaid"
- Payment entries create General Ledger entries automatically
- Payment entries can be cancelled, which reverses the invoice update

---

## Support

For issues or questions:
- Check error logs in Frappe
- Review Payment Entry document in ERPNext
- Verify Sales Invoice status and outstanding amount
- Check mode of payment configuration

