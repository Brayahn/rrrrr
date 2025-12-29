# Dashboard React Integration Guide

## Overview

This guide shows how to integrate the Dashboard Metrics API with your React dashboard component.

## Quick Start

### 1. Create Custom Hook

Create `hooks/useDashboardMetrics.js`:

```javascript
import { useState, useEffect } from 'react';

export function useDashboardMetrics(filters = {}) {
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
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
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
  }, [
    filters.period, 
    filters.warehouse, 
    filters.staff, 
    filters.from_date, 
    filters.to_date
  ]);

  return { data, loading, error, refetch: () => fetchDashboardData() };
}
```

### 2. Update Your Dashboard Component

Replace the mock data in your Dashboard component:

```javascript
import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  TrendingUp,
  TrendingDown,
  Receipt,
  Inventory,
  LocalShipping,
  AccountBalance,
  AssignmentReturn
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useDashboardMetrics } from './hooks/useDashboardMetrics';

const StatCard = ({ title, value, subtitle, icon, color, secondaryValue, secondaryLabel }) => {
  return (
    <Card 
      sx={{ 
        background: `linear-gradient(135deg, ${color}25, ${color}15)`,
        border: `1px solid ${color}30`,
        borderRadius: 2,
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
        },
        height: '100%'
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography color="textSecondary" gutterBottom variant="overline" fontWeight="medium" fontSize="0.7rem">
              {title}
            </Typography>
            <Typography variant="h5" component="div" fontWeight="bold" color={color} gutterBottom>
              ${value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                {subtitle}
              </Typography>
            )}
            {secondaryValue && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  {secondaryLabel}:
                </Typography>
                <Typography variant="caption" fontWeight="medium" color={color}>
                  {secondaryValue}
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              padding: 1.5,
              borderRadius: 1.5,
              backgroundColor: `${color}20`,
              color: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const StatusChip = ({ status }) => {
  const getColor = (status) => {
    switch (status) {
      case 'Overdue': return 'error';
      case 'Due Soon': return 'warning';
      case 'Low': return 'warning';
      case 'Critical': return 'error';
      case 'Warning': return 'warning';
      case 'Processing': return 'info';
      case 'Shipped': return 'success';
      default: return 'default';
    }
  };

  return <Chip label={status} color={getColor(status)} size="small" />;
};

const Dashboard = () => {
  const [expanded, setExpanded] = useState(['panel1', 'panel2', 'panel3']);
  const [filters, setFilters] = useState({
    period: '30days',
    warehouse: '',
    staff: ''
  });

  const { data, loading, error } = useDashboardMetrics(filters);

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? [...expanded, panel] : expanded.filter(p => p !== panel));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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
            {/* TODO: Populate from warehouse API */}
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
            {/* TODO: Populate from staff API */}
          </Select>
        </FormControl>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Sales Cards */}
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

        {/* Purchases Cards */}
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

        {/* Financial Cards */}
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

        {/* Additional Metrics */}
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
            value={data.pendingShipments.reduce((acc, shipment) => acc + shipment.items, 0)}
            subtitle={`${data.pendingShipments.length} orders`}
            icon={<LocalShipping />}
            color="#ff5722"
          />
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, borderRadius: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Sales Performance - Last 30 Days
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data.salesLast30Days}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => new Date(value).getDate()}
                  stroke="#666"
                />
                <YAxis stroke="#666" />
                <Tooltip 
                  formatter={(value, name) => [
                    `$${value?.toLocaleString()}`,
                    name === 'sales' ? 'Sales' : 'Returns'
                  ]}
                  labelFormatter={(label) => `Date: ${new Date(label).toLocaleDateString()}`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="sales" 
                  stroke="#2196f3" 
                  strokeWidth={3}
                  dot={{ fill: '#2196f3', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#2196f3' }}
                  name="Daily Sales"
                />
                <Line 
                  type="monotone" 
                  dataKey="returns" 
                  stroke="#ff9800" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: '#ff9800', strokeWidth: 2, r: 3 }}
                  activeDot={{ r: 5, fill: '#ff9800' }}
                  name="Returns"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3, borderRadius: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
            <Typography variant="h6" gutterBottom fontWeight="bold">
              Monthly Sales Overview
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.monthlySales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  formatter={(value, name) => [
                    `$${value?.toLocaleString()}`,
                    name === 'sales' ? 'Total Sales' : 
                    name === 'returns' ? 'Returns' : 'Net Sales'
                  ]}
                />
                <Legend />
                <Bar 
                  dataKey="sales" 
                  fill="#4caf50" 
                  radius={[4, 4, 0, 0]}
                  name="Total Sales"
                />
                <Bar 
                  dataKey="returns" 
                  fill="#ff9800" 
                  radius={[4, 4, 0, 0]}
                  name="Returns"
                />
                <Bar 
                  dataKey="net" 
                  fill="#2196f3" 
                  radius={[4, 4, 0, 0]}
                  name="Net Sales"
                />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Accordion Sections */}
      <Box sx={{ mb: 4 }}>
        {/* Sales & Purchases Due */}
        <Accordion 
          expanded={expanded.includes('panel1')}
          onChange={handleAccordionChange('panel1')}
          sx={{ 
            mb: 2, 
            borderRadius: '8px !important',
            boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
          }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" fontWeight="bold">
              Outstanding Payments
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom fontWeight="medium" color="primary">
                  Sales Due (Total: ${data.salesDue.reduce((acc, item) => acc + item.amount, 0)?.toLocaleString()})
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Customer</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell>Due Date</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.salesDue.map((row) => (
                        <TableRow key={row.id} hover>
                          <TableCell>{row.customer}</TableCell>
                          <TableCell align="right">${row.amount?.toLocaleString()}</TableCell>
                          <TableCell>{row.dueDate ? new Date(row.dueDate).toLocaleDateString() : 'N/A'}</TableCell>
                          <TableCell>
                            <StatusChip status={row.status} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom fontWeight="medium" color="primary">
                  Purchases Due (Total: ${data.purchasesDue.reduce((acc, item) => acc + item.amount, 0)?.toLocaleString()})
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Supplier</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell>Due Date</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.purchasesDue.map((row) => (
                        <TableRow key={row.id} hover>
                          <TableCell>{row.supplier}</TableCell>
                          <TableCell align="right">${row.amount?.toLocaleString()}</TableCell>
                          <TableCell>{row.dueDate ? new Date(row.dueDate).toLocaleDateString() : 'N/A'}</TableCell>
                          <TableCell>
                            <StatusChip status={row.status} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Stock Alerts */}
        <Accordion 
          expanded={expanded.includes('panel2')}
          onChange={handleAccordionChange('panel2')}
          sx={{ 
            mb: 2, 
            borderRadius: '8px !important',
            boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
          }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" fontWeight="bold">
              Stock Alerts
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell align="right">Current Stock</TableCell>
                    <TableCell align="right">Minimum Stock</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.stockAlerts.map((row) => (
                    <TableRow key={row.id} hover>
                      <TableCell>{row.product}</TableCell>
                      <TableCell align="right">{row.currentStock}</TableCell>
                      <TableCell align="right">{row.minStock}</TableCell>
                      <TableCell>
                        <StatusChip status={row.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>

        {/* Pending Shipments */}
        <Accordion 
          expanded={expanded.includes('panel3')}
          onChange={handleAccordionChange('panel3')}
          sx={{ 
            borderRadius: '8px !important',
            boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
          }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" fontWeight="bold">
              Pending Shipments
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Order ID</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell align="right">Items</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Est. Delivery</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.pendingShipments.map((row) => (
                    <TableRow key={row.id} hover>
                      <TableCell>{row.orderId}</TableCell>
                      <TableCell>{row.customer}</TableCell>
                      <TableCell align="right">{row.items}</TableCell>
                      <TableCell>
                        <StatusChip status={row.status} />
                      </TableCell>
                      <TableCell>{row.estDelivery ? new Date(row.estDelivery).toLocaleDateString() : 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      </Box>
    </Box>
  );
};

export default Dashboard;
```

## Key Changes from Your Original Code

1. **Removed Mock Data**: Replaced `dashboardData` with API data from `useDashboardMetrics` hook
2. **Added Filters**: Added period, warehouse, and staff filter dropdowns
3. **Loading State**: Added loading spinner while fetching data
4. **Error Handling**: Added error alert display
5. **Data Mapping**: Mapped API response fields to your component structure

## Next Steps

1. **Populate Filter Dropdowns**: 
   - Fetch warehouses from warehouse API
   - Fetch staff/users from user/staff API

2. **Add Caching**: Implement caching to reduce API calls

3. **Add Refresh Button**: Allow manual refresh of dashboard data

4. **Add Date Picker**: For custom period selection

5. **Optimize Performance**: Consider pagination for large datasets
