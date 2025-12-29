# Customer Credit Limit API - Quick Start Guide

## Overview

The Customer Credit Limit API allows you to manage customer credit limits, monitor credit utilization, and view credit history. Credit limits help control the amount of credit extended to customers.

## Quick Examples

### Set Credit Limit

```javascript
// React/JavaScript Example
const setCreditLimit = async (customerId, company, limit) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.customer_api.set_customer_credit_limit',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer: customerId,
        company: company,
        credit_limit: limit,
        bypass_credit_limit_check: false,
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    console.log('Credit limit set!', data.data);
    console.log('Available credit:', data.data.available_credit);
  }
};
```

### Get Credit Limit

```javascript
const getCreditLimit = async (customerId, company) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer: customerId,
        company: company,
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    const creditInfo = data.data.credit_limits;
    console.log('Credit Limit:', creditInfo.effective_credit_limit);
    console.log('Outstanding:', creditInfo.outstanding_amount);
    console.log('Available:', creditInfo.available_credit);
    console.log('Utilization:', creditInfo.credit_utilization_percent + '%');
    
    if (creditInfo.is_over_limit) {
      alert('Customer has exceeded credit limit!');
    }
  }
};
```

### Get Credit History

```javascript
const getCreditHistory = async (customerId, company) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_history',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer: customerId,
        company: company,
        from_date: '2024-01-01',
        to_date: '2024-01-31',
        limit: 50,
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    console.log('Transactions:', data.data.transactions);
    console.log('Total:', data.data.total_count);
  }
};
```

### List Customers with Credit Info

```javascript
const listCustomersWithCredit = async (company) => {
  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.customer_api.list_customers',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        company: company,
        limit: 50,
      }),
    }
  );
  
  const data = await response.json();
  if (data.success) {
    data.data.forEach(customer => {
      console.log(`${customer.customer_name}:`);
      console.log(`  Credit Limit: ${customer.credit_limit}`);
      console.log(`  Outstanding: ${customer.outstanding_amount}`);
      console.log(`  Available: ${customer.available_credit}`);
      console.log(`  Utilization: ${customer.credit_utilization_percent}%`);
      
      if (customer.is_over_limit) {
        console.log('  ⚠️ OVER LIMIT!');
      }
    });
  }
};
```

## API Endpoints

### 1. Set Credit Limit
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.set_customer_credit_limit`
- **Method:** POST
- **Required:** `customer`, `company`, `credit_limit`
- **Optional:** `bypass_credit_limit_check`

### 2. Get Credit Limit
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit`
- **Method:** GET or POST
- **Required:** `customer`
- **Optional:** `company` (if not provided, returns all companies)

### 3. Get Credit History
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_history`
- **Method:** GET or POST
- **Required:** `customer`
- **Optional:** `company`, `from_date`, `to_date`, `limit`, `offset`

### 4. Remove Credit Limit
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.remove_customer_credit_limit`
- **Method:** POST
- **Required:** `customer`, `company`

### 5. List Customers (Enhanced)
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.list_customers`
- **Method:** GET or POST
- **Note:** When `company` is provided, includes credit limit fields

### 6. Get Customer (Enhanced)
- **Endpoint:** `savanna_pos.savanna_pos.apis.customer_api.get_customer`
- **Method:** GET or POST
- **Note:** Now includes `credit_limits` array for all companies

## Credit Limit Hierarchy

Credit limits are determined in this order:

1. **Customer Level** - Specific limit for the customer
2. **Customer Group Level** - Limit for the customer's group
3. **Company Level** - Default company limit

If no limit is set at any level, credit is unlimited (0 = unlimited).

## Key Concepts

### Credit Utilization

```
Credit Utilization % = (Outstanding Amount / Credit Limit) × 100
Available Credit = Credit Limit - Outstanding Amount
```

### Status Indicators

- **Green (< 50%)**: Low utilization, safe
- **Yellow (50-80%)**: Medium utilization, monitor
- **Orange (80-100%)**: High utilization, caution
- **Red (> 100%)**: Over limit, blocked

### Outstanding Amount Includes

- Unpaid Sales Invoices
- Partially paid Sales Invoices
- Unbilled Sales Orders (if not bypassed)
- Outstanding Delivery Notes

## Common Use Cases

### Use Case 1: Set Initial Credit Limit

```javascript
await setCreditLimit("CUST-00001", "My Company", 50000);
```

### Use Case 2: Check Before Creating Invoice

```javascript
const creditInfo = await getCreditLimit("CUST-00001", "My Company");

if (creditInfo.is_over_limit) {
  alert('Cannot create invoice: Customer has exceeded credit limit');
  return;
}

const invoiceAmount = 5000;
if (creditInfo.available_credit < invoiceAmount) {
  alert(`Insufficient credit. Available: ${creditInfo.available_credit}`);
  return;
}

// Proceed with invoice creation
```

### Use Case 3: Monitor High Utilization Customers

```javascript
const customers = await listCustomersWithCredit("My Company");

const highUtilization = customers.filter(c => 
  c.credit_utilization_percent > 80 && !c.is_over_limit
);

console.log('Customers needing attention:', highUtilization);
```

### Use Case 4: Review Credit History

```javascript
const history = await getCreditHistory(
  "CUST-00001", 
  "My Company",
  "2024-01-01",
  "2024-01-31"
);

// Analyze payment patterns
const payments = history.transactions.filter(t => 
  t.voucher_type === 'Payment Entry'
);
const invoices = history.transactions.filter(t => 
  t.voucher_type === 'Sales Invoice'
);

console.log(`Total payments: ${payments.length}`);
console.log(`Total invoices: ${invoices.length}`);
```

### Use Case 5: Update Credit Limit Based on Performance

```javascript
// Get current credit info
const creditInfo = await getCreditLimit("CUST-00001", "My Company");

// Get credit history
const history = await getCreditHistory("CUST-00001", "My Company");

// Analyze: if customer pays on time, increase limit
const recentPayments = history.transactions
  .filter(t => t.voucher_type === 'Payment Entry')
  .slice(0, 10);

const onTimePayments = recentPayments.length; // Add your logic here

if (onTimePayments >= 8) {
  // Increase credit limit by 20%
  const newLimit = creditInfo.effective_credit_limit * 1.2;
  await setCreditLimit("CUST-00001", "My Company", newLimit);
}
```

## Error Handling

```javascript
try {
  const response = await fetch(apiUrl, options);
  const data = await response.json();
  
  if (!data.success) {
    switch (data.error_type) {
      case 'not_found':
        console.error('Customer or company not found');
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

## React Hook Example

```tsx
import { useState, useEffect } from 'react';

const useCustomerCreditLimit = (customer: string, company: string) => {
  const [creditInfo, setCreditInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCreditLimit();
  }, [customer, company]);

  const fetchCreditLimit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        '/api/method/savanna_pos.savanna_pos.apis.customer_api.get_customer_credit_limit',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ customer, company }),
        }
      );

      const data = await response.json();
      if (data.success) {
        setCreditInfo(data.data.credit_limits);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to fetch credit limit');
    } finally {
      setLoading(false);
    }
  };

  return { creditInfo, loading, error, refetch: fetchCreditLimit };
};

// Usage
const MyComponent = () => {
  const { creditInfo, loading, error } = useCustomerCreditLimit('CUST-00001', 'My Company');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!creditInfo) return null;

  return (
    <div>
      <p>Credit Limit: {creditInfo.effective_credit_limit}</p>
      <p>Outstanding: {creditInfo.outstanding_amount}</p>
      <p>Available: {creditInfo.available_credit}</p>
      {creditInfo.is_over_limit && <p>⚠️ Over Limit!</p>}
    </div>
  );
};
```

## Full Documentation

See [CUSTOMER_CREDIT_LIMIT_API_DOCUMENTATION.md](./CUSTOMER_CREDIT_LIMIT_API_DOCUMENTATION.md) for complete API documentation with detailed React examples.






















