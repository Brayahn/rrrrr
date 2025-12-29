# Customer Credit Limit Management API Documentation

## Overview

This document provides complete API documentation for **managing customer credit limits** in the SavvyPOS system. These APIs allow frontend applications to set, update, view, and track customer credit limits, monitor credit utilization, and view credit history.

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

## Credit Limit Hierarchy

Credit limits are determined in the following order of precedence:

1. **Customer Level** - Specific credit limit set for the customer
2. **Customer Group Level** - Credit limit set for the customer's group
3. **Company Level** - Default credit limit set at company level

If no credit limit is set at any level, the customer has unlimited credit (0 = unlimited).

---

## API Endpoints

### 1. Set Customer Credit Limit

Set or update credit limit for a customer for a specific company.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.set_customer_credit_limit`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer name/ID (e.g., `CUST-00001`) |
| `company` | string | Yes | Company name |
| `credit_limit` | number | Yes | Credit limit amount (must be >= 0, 0 = unlimited) |
| `bypass_credit_limit_check` | boolean | No | Bypass credit limit check at Sales Order level (default: `false`) |

**Response (Success):**

```json
{
  "success": true,
  "message": "Credit limit updated successfully",
  "data": {
    "customer": "CUST-00001",
    "company": "My Company",
    "credit_limit": 50000.0,
    "bypass_credit_limit_check": false,
    "effective_credit_limit": 50000.0,
    "outstanding_amount": 15000.0,
    "available_credit": 35000.0,
    "credit_utilization_percent": 30.0
  }
}
```

**Response Fields:**

- `credit_limit` (number): Credit limit set for the customer
- `effective_credit_limit` (number): Effective credit limit (may inherit from group/company)
- `outstanding_amount` (number): Current outstanding amount
- `available_credit` (number): Available credit (limit - outstanding)
- `credit_utilization_percent` (number): Percentage of credit limit used

**Error Responses:**

```json
// Customer not found
{
  "success": false,
  "message": "Customer CUST-00001 not found",
  "error_type": "not_found"
}

// Negative credit limit
{
  "success": false,
  "message": "Credit limit cannot be negative",
  "error_type": "validation_error"
}
```

**Example Request:**

```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.set_customer_credit_limit" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUST-00001",
    "company": "My Company",
    "credit_limit": 50000.0,
    "bypass_credit_limit_check": false
  }'
```

---

### 2. Get Customer Credit Limit

Get credit limit information for a customer. If company is provided, returns credit limit for that company. If not provided, returns credit limits for all companies.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer name/ID |
| `company` | string | No | Company name (optional, if not provided returns all companies) |

**Response (Success - Single Company):**

```json
{
  "success": true,
  "data": {
    "customer": "CUST-00001",
    "customer_name": "John Doe",
    "credit_limits": {
      "company": "My Company",
      "credit_limit": 50000.0,
      "effective_credit_limit": 50000.0,
      "outstanding_amount": 15000.0,
      "available_credit": 35000.0,
      "credit_utilization_percent": 30.0,
      "limit_source": "Customer",
      "bypass_credit_limit_check": false,
      "is_over_limit": false
    }
  }
}
```

**Response (Success - All Companies):**

```json
{
  "success": true,
  "data": {
    "customer": "CUST-00001",
    "customer_name": "John Doe",
    "credit_limits": [
      {
        "company": "My Company",
        "credit_limit": 50000.0,
        "effective_credit_limit": 50000.0,
        "outstanding_amount": 15000.0,
        "available_credit": 35000.0,
        "credit_utilization_percent": 30.0,
        "limit_source": "Customer",
        "bypass_credit_limit_check": false,
        "is_over_limit": false
      },
      {
        "company": "Another Company",
        "credit_limit": 0.0,
        "effective_credit_limit": 100000.0,
        "outstanding_amount": 25000.0,
        "available_credit": 75000.0,
        "credit_utilization_percent": 25.0,
        "limit_source": "Company",
        "bypass_credit_limit_check": false,
        "is_over_limit": false
      }
    ]
  }
}
```

**Response Fields:**

- `credit_limit` (number): Credit limit set at customer level (null if inherited)
- `effective_credit_limit` (number): Effective credit limit (from customer/group/company)
- `outstanding_amount` (number): Current outstanding amount
- `available_credit` (number): Available credit remaining
- `credit_utilization_percent` (number): Percentage of credit used
- `limit_source` (string): Source of credit limit (`Customer`, `Customer Group`, or `Company`)
- `is_over_limit` (boolean): Whether customer has exceeded credit limit

**Example Request:**

```bash
# Get credit limit for specific company
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUST-00001",
    "company": "My Company"
  }'

# Get credit limits for all companies
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit?customer=CUST-00001" \
  -H "Authorization: Bearer <access_token>"
```

---

### 3. Get Customer Credit History

Get credit history (transactions) for a customer showing all transactions that affect the customer's credit balance.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_history`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer name/ID |
| `company` | string | No | Company name (optional, filters by company) |
| `from_date` | string | No | Start date in `YYYY-MM-DD` format (optional) |
| `to_date` | string | No | End date in `YYYY-MM-DD` format (optional) |
| `limit` | number | No | Number of records to return (default: 50) |
| `offset` | number | No | Offset for pagination (default: 0) |

**Response (Success):**

```json
{
  "success": true,
  "data": {
    "customer": "CUST-00001",
    "transactions": [
      {
        "voucher_no": "SINV-00005",
        "voucher_type": "Sales Invoice",
        "posting_date": "2024-01-15",
        "amount": 5000.0,
        "outstanding_amount": 0.0,
        "status": "Paid",
        "company": "My Company"
      },
      {
        "voucher_no": "ACC-PAY-00003",
        "voucher_type": "Payment Entry",
        "posting_date": "2024-01-14",
        "amount": -2000.0,
        "outstanding_amount": 0.0,
        "status": "Submitted",
        "company": "My Company"
      },
      {
        "voucher_no": "SINV-00004",
        "voucher_type": "Sales Invoice",
        "posting_date": "2024-01-10",
        "amount": 10000.0,
        "outstanding_amount": 5000.0,
        "status": "Partly Paid",
        "company": "My Company"
      }
    ],
    "total_count": 15,
    "credit_summary": {
      "company": "My Company",
      "credit_limit": 50000.0,
      "outstanding_amount": 15000.0,
      "available_credit": 35000.0
    }
  }
}
```

**Response Fields:**

- `transactions` (array): List of transactions affecting credit
  - `voucher_no` (string): Document number
  - `voucher_type` (string): Document type (`Sales Invoice`, `Payment Entry`, `Credit Note`)
  - `posting_date` (string): Transaction date
  - `amount` (number): Transaction amount (positive for invoices, negative for payments/credit notes)
  - `outstanding_amount` (number): Outstanding amount for invoices
  - `status` (string): Document status
- `total_count` (number): Total number of transactions
- `credit_summary` (object): Current credit summary (only if company is provided)

**Example Request:**

```bash
# Get all credit history
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_history" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUST-00001",
    "company": "My Company",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "limit": 50,
    "offset": 0
  }'
```

---

### 4. Remove Customer Credit Limit

Remove credit limit for a customer for a specific company. After removal, credit limit will fall back to customer group or company default.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.remove_customer_credit_limit`

**Method:** `POST`

**Parameters (JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer name/ID |
| `company` | string | Yes | Company name |

**Response (Success):**

```json
{
  "success": true,
  "message": "Credit limit removed successfully",
  "data": {
    "customer": "CUST-00001",
    "company": "My Company",
    "effective_credit_limit": 100000.0,
    "outstanding_amount": 15000.0,
    "available_credit": 85000.0
  }
}
```

**Example Request:**

```bash
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.customer_api.remove_customer_credit_limit" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUST-00001",
    "company": "My Company"
  }'
```

---

### 5. List Customers (Updated)

The existing `list_customers` endpoint has been enhanced to include credit limit information when a company is provided.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.list_customers`

**Method:** `GET` or `POST`

**Parameters:** Same as before, but now when `company` is provided, credit limit fields are included.

**Response (Enhanced):**

```json
{
  "success": true,
  "data": [
    {
      "name": "CUST-00001",
      "customer_name": "John Doe",
      "customer_type": "Individual",
      "customer_group": "All Customer Groups",
      "territory": "All Territories",
      "tax_id": null,
      "mobile_no": "+254712345678",
      "email_id": "john@example.com",
      "disabled": false,
      "default_currency": "KES",
      "default_price_list": "Standard Selling",
      "credit_limit": 50000.0,
      "outstanding_amount": 15000.0,
      "available_credit": 35000.0,
      "credit_utilization_percent": 30.0,
      "is_over_limit": false
    }
  ],
  "count": 1
}
```

**New Fields (when company is provided):**

- `credit_limit` (number): Effective credit limit
- `outstanding_amount` (number): Current outstanding amount
- `available_credit` (number): Available credit remaining
- `credit_utilization_percent` (number): Percentage of credit used
- `is_over_limit` (boolean): Whether customer has exceeded credit limit

---

### 6. Get Customer (Updated)

The existing `get_customer` endpoint has been enhanced to include credit limit information for all companies.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.customer_api.get_customer`

**Response (Enhanced):**

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
    "email_id": "john@example.com",
    "disabled": false,
    "default_currency": "KES",
    "default_price_list": "Standard Selling",
    "accounts": [...],
    "outstanding_amount": 15000.0,
    "total_sales": 50000.0,
    "credit_limits": [
      {
        "company": "My Company",
        "credit_limit": 50000.0,
        "effective_credit_limit": 50000.0,
        "outstanding_amount": 15000.0,
        "available_credit": 35000.0,
        "credit_utilization_percent": 30.0,
        "limit_source": "Customer",
        "bypass_credit_limit_check": false,
        "is_over_limit": false
      }
    ]
  }
}
```

**New Field:**

- `credit_limits` (array): Credit limit information for all companies associated with the customer

---

## React Integration Examples

### 1. Credit Limit Management Component

```tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CreditLimitProps {
  customer: string;
  company: string;
  onUpdate?: () => void;
}

const CreditLimitManagement: React.FC<CreditLimitProps> = ({ 
  customer, 
  company,
  onUpdate 
}) => {
  const [creditInfo, setCreditInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    credit_limit: '',
    bypass_credit_limit_check: false,
  });

  useEffect(() => {
    fetchCreditLimit();
  }, [customer, company]);

  const fetchCreditLimit = async () => {
    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit',
        { customer, company },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        setCreditInfo(response.data.data.credit_limits);
        setFormData({
          credit_limit: response.data.data.credit_limits.credit_limit || '',
          bypass_credit_limit_check: response.data.data.credit_limits.bypass_credit_limit_check || false,
        });
      }
    } catch (error) {
      console.error('Error fetching credit limit:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.set_customer_credit_limit',
        {
          customer,
          company,
          credit_limit: parseFloat(formData.credit_limit),
          bypass_credit_limit_check: formData.bypass_credit_limit_check,
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        alert('Credit limit updated successfully!');
        fetchCreditLimit();
        if (onUpdate) onUpdate();
      } else {
        alert(`Error: ${response.data.message}`);
      }
    } catch (error: any) {
      alert(error.response?.data?.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm('Are you sure you want to remove the credit limit?')) return;

    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.remove_customer_credit_limit',
        { customer, company },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        alert('Credit limit removed successfully!');
        fetchCreditLimit();
        if (onUpdate) onUpdate();
      }
    } catch (error: any) {
      alert(error.response?.data?.message || 'An error occurred');
    }
  };

  if (!creditInfo) return <div>Loading...</div>;

  const utilizationColor = creditInfo.credit_utilization_percent > 80 
    ? 'red' 
    : creditInfo.credit_utilization_percent > 50 
    ? 'orange' 
    : 'green';

  return (
    <div className="credit-limit-management">
      <h3>Credit Limit Management</h3>

      {/* Credit Summary */}
      <div className="credit-summary">
        <div className="summary-item">
          <label>Credit Limit:</label>
          <span>{creditInfo.effective_credit_limit.toLocaleString()}</span>
        </div>
        <div className="summary-item">
          <label>Outstanding:</label>
          <span>{creditInfo.outstanding_amount.toLocaleString()}</span>
        </div>
        <div className="summary-item">
          <label>Available Credit:</label>
          <span className={creditInfo.available_credit < 0 ? 'negative' : ''}>
            {creditInfo.available_credit.toLocaleString()}
          </span>
        </div>
        <div className="summary-item">
          <label>Utilization:</label>
          <span style={{ color: utilizationColor }}>
            {creditInfo.credit_utilization_percent.toFixed(1)}%
          </span>
        </div>
        {creditInfo.is_over_limit && (
          <div className="alert alert-danger">
            ⚠️ Credit limit exceeded!
          </div>
        )}
      </div>

      {/* Credit Limit Form */}
      <form onSubmit={handleSubmit} className="credit-limit-form">
        <div className="form-group">
          <label>Credit Limit</label>
          <input
            type="number"
            step="0.01"
            value={formData.credit_limit}
            onChange={(e) => setFormData({ ...formData, credit_limit: e.target.value })}
            placeholder="0 = Unlimited"
            required
          />
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={formData.bypass_credit_limit_check}
              onChange={(e) => setFormData({ 
                ...formData, 
                bypass_credit_limit_check: e.target.checked 
              })}
            />
            Bypass credit limit check at Sales Order
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Updating...' : 'Update Credit Limit'}
          </button>
          {creditInfo.limit_source === 'Customer' && (
            <button type="button" onClick={handleRemove} className="btn-danger">
              Remove Credit Limit
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default CreditLimitManagement;
```

### 2. Credit History Component

```tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CreditHistoryProps {
  customer: string;
  company?: string;
}

const CreditHistory: React.FC<CreditHistoryProps> = ({ customer, company }) => {
  const [history, setHistory] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    from_date: '',
    to_date: '',
  });

  useEffect(() => {
    fetchHistory();
  }, [customer, company]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_history',
        {
          customer,
          company,
          ...filters,
          limit: 50,
          offset: 0,
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        setHistory(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching credit history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case 'Sales Invoice': return 'blue';
      case 'Payment Entry': return 'green';
      case 'Credit Note': return 'orange';
      default: return 'gray';
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!history) return null;

  return (
    <div className="credit-history">
      <h3>Credit History</h3>

      {/* Filters */}
      <div className="filters">
        <input
          type="date"
          value={filters.from_date}
          onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
          placeholder="From Date"
        />
        <input
          type="date"
          value={filters.to_date}
          onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
          placeholder="To Date"
        />
        <button onClick={fetchHistory}>Filter</button>
      </div>

      {/* Credit Summary */}
      {history.credit_summary && (
        <div className="credit-summary">
          <div>
            <label>Credit Limit:</label>
            <span>{history.credit_summary.credit_limit.toLocaleString()}</span>
          </div>
          <div>
            <label>Outstanding:</label>
            <span>{history.credit_summary.outstanding_amount.toLocaleString()}</span>
          </div>
          <div>
            <label>Available:</label>
            <span>{history.credit_summary.available_credit.toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <table className="transactions-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Document</th>
            <th>Amount</th>
            <th>Outstanding</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {history.transactions.map((txn: any) => (
            <tr key={`${txn.voucher_type}-${txn.voucher_no}`}>
              <td>{new Date(txn.posting_date).toLocaleDateString()}</td>
              <td>
                <span 
                  className="badge" 
                  style={{ backgroundColor: getTransactionTypeColor(txn.voucher_type) }}
                >
                  {txn.voucher_type}
                </span>
              </td>
              <td>{txn.voucher_no}</td>
              <td className={txn.amount < 0 ? 'negative' : 'positive'}>
                {txn.amount.toLocaleString()}
              </td>
              <td>{txn.outstanding_amount.toLocaleString()}</td>
              <td>{txn.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination-info">
        Showing {history.transactions.length} of {history.total_count} transactions
      </div>
    </div>
  );
};

export default CreditHistory;
```

### 3. Customer List with Credit Limits

```tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CustomerListProps {
  company: string;
}

const CustomerListWithCredit: React.FC<CustomerListProps> = ({ company }) => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCustomers();
  }, [company]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.list_customers',
        { company, limit: 50 },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.data.success) {
        setCustomers(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUtilizationColor = (percent: number) => {
    if (percent > 100) return '#dc3545'; // Red - over limit
    if (percent > 80) return '#fd7e14'; // Orange - high utilization
    if (percent > 50) return '#ffc107'; // Yellow - medium
    return '#28a745'; // Green - low
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="customer-list">
      <h2>Customers with Credit Limits</h2>
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            <th>Credit Limit</th>
            <th>Outstanding</th>
            <th>Available</th>
            <th>Utilization</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={customer.name}>
              <td>{customer.customer_name}</td>
              <td>{customer.credit_limit?.toLocaleString() || 'Unlimited'}</td>
              <td>{customer.outstanding_amount?.toLocaleString() || 0}</td>
              <td className={customer.available_credit < 0 ? 'negative' : ''}>
                {customer.available_credit?.toLocaleString() || 0}
              </td>
              <td>
                <div className="utilization-bar">
                  <div
                    className="utilization-fill"
                    style={{
                      width: `${Math.min(customer.credit_utilization_percent || 0, 100)}%`,
                      backgroundColor: getUtilizationColor(customer.credit_utilization_percent || 0),
                    }}
                  />
                  <span className="utilization-text">
                    {(customer.credit_utilization_percent || 0).toFixed(1)}%
                  </span>
                </div>
              </td>
              <td>
                {customer.is_over_limit ? (
                  <span className="badge badge-danger">Over Limit</span>
                ) : (
                  <span className="badge badge-success">OK</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CustomerListWithCredit;
```

---

## Best Practices

1. **Monitor Credit Utilization**: Regularly check `credit_utilization_percent` to identify customers approaching their limits
2. **Set Appropriate Limits**: Use customer history and risk assessment to set credit limits
3. **Handle Over-Limit Cases**: Check `is_over_limit` before allowing new credit sales
4. **Track Credit History**: Use credit history to understand customer payment patterns
5. **Company-Specific Limits**: Set different credit limits for different companies if needed
6. **Bypass with Caution**: Only use `bypass_credit_limit_check` for trusted customers or special circumstances
7. **Regular Reviews**: Periodically review and adjust credit limits based on customer behavior

---

## Credit Limit Calculation

The outstanding amount includes:
- **Sales Invoices**: Unpaid and partially paid invoices
- **Sales Orders**: Unbilled sales orders (if not bypassed)
- **Delivery Notes**: Outstanding delivery notes

Available credit = Credit Limit - Outstanding Amount

---

## Error Handling

### Common Errors

| Error Type | Description | Solution |
|------------|-------------|----------|
| `not_found` | Customer or company not found | Verify customer/company exists |
| `validation_error` | Invalid data (e.g., negative limit) | Check input values |
| `server_error` | Unexpected server error | Check error logs, retry request |

---

## Notes

- Credit limit of `0` means unlimited credit
- Credit limits can be set at customer, customer group, or company level
- The system automatically uses the most specific limit available
- Outstanding amount is calculated in real-time from GL Entries and transactions
- Credit history includes Sales Invoices, Payment Entries, and Credit Notes
- Payment entries reduce outstanding amount (negative in history)
- Credit notes reduce outstanding amount (negative in history)

---

## Support

For issues or questions:
- Check error logs in Frappe
- Review Customer Credit Limit child table in Customer document
- Verify company and customer group credit limit settings
- Check Accounts Settings for credit controller configuration






















