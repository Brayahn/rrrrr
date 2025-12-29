# Dashboard Metrics API Documentation

## Overview

This document provides complete API documentation for **Dashboard Metrics** in the SavvyPOS system. The API provides comprehensive business metrics including sales, purchases, financials, and inventory data with filtering capabilities by staff (user) and warehouse.

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

## API Endpoint

### Get Dashboard Metrics

Get comprehensive dashboard metrics with filtering by staff and warehouse.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company` | string | No | Company name (defaults to user's default company) |
| `warehouse` | string | No | Warehouse name to filter by |
| `staff` | string | No | User/Staff name (owner) to filter by |
| `from_date` | string | No | Start date for custom period (`YYYY-MM-DD`) |
| `to_date` | string | No | End date for custom period (`YYYY-MM-DD`) |
| `period` | string | No | Time period: `"30days"`, `"month"`, `"year"`, or `"custom"` (default: `"30days"`) |

**Response:**

```json
{
  "success": true,
  "data": {
    "stats": {
      "totalSales": 125430.0,
      "netSales": 118158.0,
      "salesReturns": 7272.0,
      "salesReturnsCount": 45,
      "totalPurchases": 89450.0,
      "netPurchases": 84520.0,
      "purchaseReturns": 4930.0,
      "purchaseReturnsCount": 28,
      "invoicesDue": 23450.0,
      "invoicesDueCount": 18,
      "totalExpense": 56780.0,
      "profitMargin": 28.5,
      "averageTransaction": 145.20
    },
    "salesLast30Days": [
      {
        "date": "2024-01-01",
        "sales": 4200.0,
        "returns": 320.0
      },
      {
        "date": "2024-01-02",
        "sales": 3800.0,
        "returns": 280.0
      }
    ],
    "monthlySales": [
      {
        "month": "Jan",
        "sales": 125430.0,
        "returns": 8720.0,
        "net": 116710.0
      },
      {
        "month": "Feb",
        "sales": 118500.0,
        "returns": 7940.0,
        "net": 110560.0
      }
    ],
    "salesDue": [
      {
        "id": "SINV-00001",
        "customer": "John Doe",
        "amount": 5200.0,
        "dueDate": "2024-02-15",
        "status": "Overdue"
      }
    ],
    "purchasesDue": [
      {
        "id": "PINV-00001",
        "supplier": "ABC Suppliers",
        "amount": 3200.0,
        "dueDate": "2024-02-18",
        "status": "Due Soon"
      }
    ],
    "stockAlerts": [
      {
        "id": "ITEM-001",
        "product": "Laptop Pro",
        "currentStock": 3.0,
        "minStock": 5.0,
        "status": "Low"
      }
    ],
    "pendingShipments": [
      {
        "id": "DN-00001",
        "orderId": "DN-00001",
        "customer": "John Doe",
        "items": 3,
        "status": "Processing",
        "estDelivery": "2024-02-18"
      }
    ]
  },
  "filters": {
    "company": "My Company",
    "warehouse": null,
    "staff": null,
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "period": "30days"
  }
}
```

**Response Fields:**

### Stats Object

- `totalSales` (number): Total gross sales amount
- `netSales` (number): Net sales after returns
- `salesReturns` (number): Total sales returns amount
- `salesReturnsCount` (number): Number of sales return invoices
- `totalPurchases` (number): Total gross purchases amount
- `netPurchases` (number): Net purchases after returns
- `purchaseReturns` (number): Total purchase returns amount
- `purchaseReturnsCount` (number): Number of purchase return invoices
- `invoicesDue` (number): Total outstanding sales invoices amount
- `invoicesDueCount` (number): Number of outstanding sales invoices
- `totalExpense` (number): Total expenses (from Journal Entries)
- `profitMargin` (number): Profit margin percentage
- `averageTransaction` (number): Average transaction value

### Time Series Data

- `salesLast30Days` (array): Daily sales and returns for last 30 days
- `monthlySales` (array): Monthly sales, returns, and net sales

### Detailed Lists

- `salesDue` (array): Outstanding sales invoices (up to 20)
- `purchasesDue` (array): Outstanding purchase invoices (up to 20)
- `stockAlerts` (array): Items with low stock (up to 20)
- `pendingShipments` (array): Pending delivery notes (up to 20)

**Example Requests:**

```bash
# Get dashboard metrics for last 30 days
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?period=30days" \
  -H "Authorization: Bearer <access_token>"

# Get metrics filtered by warehouse
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?warehouse=Main%20Warehouse&period=month" \
  -H "Authorization: Bearer <access_token>"

# Get metrics filtered by staff
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?staff=user@example.com&period=30days" \
  -H "Authorization: Bearer <access_token>"

# Get metrics with both warehouse and staff filters
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?warehouse=Main%20Warehouse&staff=user@example.com&period=month" \
  -H "Authorization: Bearer <access_token>"

# Custom date range
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?from_date=2024-01-01&to_date=2024-01-31&period=custom" \
  -H "Authorization: Bearer <access_token>"
```

**HTTP Status Code:** `200 OK`

---

## Frontend Integration

### React Hook Example

```javascript
import { useState, useEffect } from 'react';

function useDashboardMetrics(filters = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboardData() {
      setLoading(true);
      setError(null);
      
      try {
        const params = new URLSearchParams({
          period: filters.period || '30days',
          ...(filters.warehouse && { warehouse: filters.warehouse }),
          ...(filters.staff && { staff: filters.staff }),
          ...(filters.from_date && { from_date: filters.from_date }),
          ...(filters.to_date && { to_date: filters.to_date }),
        });

        const response = await fetch(
          `/api/method/savanna_pos.savanna_pos.apis.dashboard_api.get_dashboard_metrics?${params}`,
          {
            headers: {
              'Authorization': `Bearer ${accessToken}`
            }
          }
        );

        const result = await response.json();
        
        if (result.success) {
          setData(result.data);
        } else {
          setError(result.message);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [filters.period, filters.warehouse, filters.staff, filters.from_date, filters.to_date]);

  return { data, loading, error };
}
```

### Updated Dashboard Component

```javascript
import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  useTheme
} from '@mui/material';
import { useDashboardMetrics } from './hooks/useDashboardMetrics';

const Dashboard = () => {
  const [filters, setFilters] = useState({
    period: '30days',
    warehouse: '',
    staff: ''
  });

  const { data, loading, error } = useDashboardMetrics(filters);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  return (
    <Box sx={{ p: 3 }}>
      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Period</InputLabel>
          <Select
            value={filters.period}
            label="Period"
            onChange={(e) => setFilters({ ...filters, period: e.target.value })}
          >
            <MenuItem value="30days">Last 30 Days</MenuItem>
            <MenuItem value="month">This Month</MenuItem>
            <MenuItem value="year">This Year</MenuItem>
            <MenuItem value="custom">Custom</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Warehouse</InputLabel>
          <Select
            value={filters.warehouse}
            label="Warehouse"
            onChange={(e) => setFilters({ ...filters, warehouse: e.target.value })}
          >
            <MenuItem value="">All Warehouses</MenuItem>
            {/* Populate from warehouse list */}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Staff</InputLabel>
          <Select
            value={filters.staff}
            label="Staff"
            onChange={(e) => setFilters({ ...filters, staff: e.target.value })}
          >
            <MenuItem value="">All Staff</MenuItem>
            {/* Populate from staff list */}
          </Select>
        </FormControl>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Sales"
            value={data.stats.totalSales}
            subtitle={`Net: $${data.stats.netSales?.toLocaleString()}`}
            secondaryValue={`${data.stats.profitMargin}% Margin`}
            secondaryLabel="Profit Margin"
            icon={<TrendingUp />}
            color="#2196f3"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Sales Returns"
            value={data.stats.salesReturns}
            subtitle={`${data.stats.salesReturnsCount} returns`}
            secondaryValue={`$${data.stats.averageTransaction} Avg. Transaction`}
            secondaryLabel="Average"
            icon={<AssignmentReturn />}
            color="#ff9800"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Purchases"
            value={data.stats.totalPurchases}
            subtitle={`Net: $${data.stats.netPurchases?.toLocaleString()}`}
            icon={<Inventory />}
            color="#4caf50"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Purchase Returns"
            value={data.stats.purchaseReturns}
            subtitle={`${data.stats.purchaseReturnsCount} returns`}
            icon={<TrendingDown />}
            color="#f44336"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Invoices Due"
            value={data.stats.invoicesDue}
            subtitle={`${data.stats.invoicesDueCount} invoices`}
            icon={<Receipt />}
            color="#9c27b0"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Expense"
            value={data.stats.totalExpense}
            icon={<AccountBalance />}
            color="#607d8b"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Net Revenue"
            value={data.stats.netSales - data.stats.totalExpense}
            subtitle="Sales - Expenses"
            icon={<TrendingUp />}
            color="#00bcd4"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Shipments"
            value={data.pendingShipments.reduce((acc, s) => acc + s.items, 0)}
            subtitle={`${data.pendingShipments.length} orders`}
            icon={<LocalShipping />}
            color="#ff5722"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sales Performance - Last 30 Days
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data.salesLast30Days}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(v) => new Date(v).getDate()} />
                <YAxis />
                <Tooltip formatter={(v) => `$${v?.toLocaleString()}`} />
                <Legend />
                <Line type="monotone" dataKey="sales" stroke="#2196f3" name="Daily Sales" />
                <Line type="monotone" dataKey="returns" stroke="#ff9800" name="Returns" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Monthly Sales Overview
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.monthlySales}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(v) => `$${v?.toLocaleString()}`} />
                <Legend />
                <Bar dataKey="sales" fill="#4caf50" name="Total Sales" />
                <Bar dataKey="returns" fill="#ff9800" name="Returns" />
                <Bar dataKey="net" fill="#2196f3" name="Net Sales" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Tables for sales due, purchases due, stock alerts, pending shipments */}
      {/* Use data.salesDue, data.purchasesDue, data.stockAlerts, data.pendingShipments */}
    </Box>
  );
};

export default Dashboard;
```

---

## Filtering Behavior

### Warehouse Filter

When `warehouse` is provided:
- Sales and purchase metrics are filtered to only include transactions involving items from that warehouse
- Stock alerts are filtered to show only items in that warehouse
- Other metrics (financials, outstanding invoices) are not affected by warehouse filter

### Staff Filter

When `staff` is provided:
- All metrics are filtered to only include transactions created by that user
- This includes sales, purchases, returns, and outstanding invoices
- Stock alerts are not affected by staff filter

### Combined Filters

You can combine filters:
- `warehouse` + `staff`: Shows metrics for a specific staff member's transactions in a specific warehouse
- `warehouse` + `period`: Shows metrics for a specific warehouse over a time period
- All filters can be combined for precise reporting

---

## Period Options

### 30 Days (Default)

- `period=30days` or omit parameter
- Automatically sets `from_date` to 30 days ago and `to_date` to today

### Month

- `period=month`
- Automatically sets `from_date` to first day of current month and `to_date` to last day

### Year

- `period=year`
- Automatically sets `from_date` to first day of current year and `to_date` to last day

### Custom

- `period=custom`
- Requires both `from_date` and `to_date` parameters
- Use format: `YYYY-MM-DD`

---

## Status Values

### Sales/Purchases Due Status

- `"Overdue"`: Due date has passed
- `"Due Soon"`: Due date is in the future

### Stock Alert Status

- `"Critical"`: Stock is 0 or below 50% of minimum
- `"Low"`: Stock is below minimum but above 50%
- `"Warning"`: Stock is at or slightly above minimum

### Pending Shipments Status

- `"Processing"`: Delivery note status is "To Deliver" or "To Bill"
- `"Shipped"`: Delivery note status is "Completed"

---

## Performance Considerations

1. **Caching**: Consider caching dashboard data on the frontend for 5-10 minutes
2. **Pagination**: Detailed lists (sales due, etc.) are limited to 20 items
3. **Date Ranges**: Very large date ranges may be slower; consider using monthly/yearly periods
4. **Warehouse Filtering**: Warehouse filtering requires joins and may be slightly slower

---

## Error Handling

```json
{
  "success": false,
  "message": "Error getting dashboard metrics: <error details>"
}
```

Common errors:
- Invalid date format
- Non-existent warehouse
- Non-existent staff/user
- Missing company configuration

---

## Best Practices

1. **Use appropriate periods**: Use `30days` for daily views, `month` for monthly views
2. **Cache results**: Dashboard data doesn't need real-time updates
3. **Filter wisely**: Only apply filters when needed to improve performance
4. **Handle loading states**: Show loading indicators while fetching data
5. **Error boundaries**: Implement error boundaries in React components
6. **Refresh strategy**: Consider auto-refresh every 5-10 minutes for live dashboards

---

## Support and Feedback

For API support, feature requests, or to report issues:

- **Email**: api-support@savvypos.com
- **Documentation**: https://docs.savvypos.com/api
- **Status Page**: https://status.savvypos.com

---

## Changelog

### Version 1.0 (2025-01-20)

- Initial release of Dashboard Metrics API
- Support for sales, purchases, financials, and inventory metrics
- Filtering by warehouse and staff
- Time period filtering (30 days, month, year, custom)
- Daily and monthly time series data
- Outstanding invoices tracking
- Stock alerts
- Pending shipments tracking
