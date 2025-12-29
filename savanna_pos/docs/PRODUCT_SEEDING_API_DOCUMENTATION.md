# Product Seeding API Documentation

## Overview

This document provides complete API documentation for **POS Industry Product Seeding** in the SavvyPOS system. These APIs allow frontend applications to retrieve industries, fetch products for specific industries, and bulk upload product templates.

---

## Base URL

```
https://your-domain.com/api/method/
```

## Authentication

Most endpoints support **guest access** (`allow_guest=True`), meaning they can be called without authentication. However, **`create_seed_item` requires authentication** as it creates items scoped to the user's company.

### Guest Access Endpoints (No Auth Required)
- `get_pos_industries`
- `seed_products`
- `bulk_upload_products`

### Authenticated Endpoints (Auth Required)
- `create_seed_item` - Requires user authentication to scope items to user's company

### Authentication Methods

1. **OAuth Bearer Token** (Required for `create_seed_item`, Optional for others)
   ```
   Authorization: Bearer <access_token>
   ```

2. **API Key/Secret** (Required for `create_seed_item`, Optional for others)
   ```
   Authorization: token <api_key>:<api_secret>
   ```

---

## API Endpoints

### 1. Get POS Industries

Retrieve a list of all POS industries with their details.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.product_seeding.get_pos_industries`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `is_active` | boolean | No | `true` | Filter by active status. Set to `false` to include inactive industries |

**Response:**

```json
{
  "success": true,
  "industries": [
    {
      "name": "REST",
      "industry_code": "REST",
      "industry_name": "Restaurant & Food Service",
      "description": "Full-service restaurants, cafes, bars, food trucks, and other food service establishments",
      "serving_location": "Physical restaurant, cafe, or food service location",
      "is_active": 1,
      "sort_order": 1
    },
    {
      "name": "RETAIL",
      "industry_code": "RETAIL",
      "industry_name": "Retail Store",
      "description": "General retail stores selling various consumer products",
      "serving_location": "Physical retail store location",
      "is_active": 1,
      "sort_order": 2
    }
  ],
  "count": 2,
  "message": "Industries retrieved successfully"
}
```

**Response Fields:**

- `success` (boolean): Indicates if the request was successful
- `industries` (array): List of industry objects
  - `name` (string): Industry identifier (used as reference in other APIs)
  - `industry_code` (string): Unique industry code
  - `industry_name` (string): Display name
  - `description` (string): Detailed description
  - `serving_location` (string): Where the industry serves customers
  - `is_active` (number): `1` if active, `0` if inactive
  - `sort_order` (number): Display order
- `count` (number): Total number of industries returned
- `message` (string): Success message

**Error Response:**

```json
{
  "success": false,
  "message": "Error retrieving industries: <error_details>"
}
```

---

### 2. Get Products for Industry

Retrieve all products (templates) available for a specific industry.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.product_seeding.seed_products`

**Method:** `GET` or `POST`

**Parameters (Query string or JSON body):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `industry` | string | Yes | Industry identifier (use `name` field from industries list, e.g., `"REST"`, `"RETAIL"`) |

**Response (Success):**

```json
{
  "status": "success",
  "industry": "REST",
  "total_products": 20,
  "products": [
    {
      "sku": "REST-001",
      "name": "Veg Burger",
      "status": "available"
    },
    {
      "sku": "REST-002",
      "name": "Chicken Burger",
      "status": "available"
    }
  ]
}
```

**Response Fields:**

- `status` (string): `"success"` or `"error"`
- `industry` (string): The industry identifier that was queried
- `total_products` (number): Total number of products found
- `products` (array): List of product objects
  - `sku` (string): Product SKU/item code
  - `name` (string): Product name
  - `status` (string): Always `"available"` for now

**Error Responses:**

```json
// Missing industry parameter
{
  "status": "error",
  "message": "Industry is required",
  "total_products": 0
}

// Industry doesn't exist
{
  "status": "error",
  "message": "Industry 'INVALID' does not exist",
  "total_products": 0
}

// No products found
{
  "status": "error",
  "message": "No products found for industry 'REST'",
  "total_products": 0
}
```

---

### 3. Bulk Upload Products

Bulk upload products from the seed data file into the Industry Product Template. This endpoint reads from a predefined JSON file and creates product templates for each industry.

**Endpoint:**  
`savanna_pos.savanna_pos.apis.product_seeding.bulk_upload_products`

**Method:** `POST` only

**Parameters:**  
None (reads from internal seed data file)

**Response (Success):**

```json
{
  "status": "success",
  "created": 45,
  "skipped": 15,
  "failed": 0,
  "ignored_industries": [],
  "failed_items": [],
  "total_processed": 60
}
```

**Response Fields:**

- `status` (string): `"success"`, `"partial_success"`, `"no_op"`, or `"error"`
  - `"success"`: All items processed successfully
  - `"partial_success"`: Some items failed but others succeeded
  - `"no_op"`: No items were created or skipped (all failed or already exist)
  - `"error"`: Request failed completely
- `created` (number): Number of new product templates created
- `skipped` (number): Number of products that already existed (skipped)
- `failed` (number): Number of items that failed to create
- `ignored_industries` (array): List of industry names from the JSON file that don't exist in the system
- `failed_items` (array): List of items that failed with error details
  - Each item contains: `industry`, `item`, and `error` or `reason`
- `total_processed` (number): Total products processed (created + skipped + failed)

**Error Responses:**

```json
// Seed file not found
{
  "status": "error",
  "message": "Seed data file not found at <file_path>"
}

// Invalid JSON
{
  "status": "error",
  "message": "Invalid JSON in seed data file"
}

// Empty file
{
  "status": "error",
  "message": "Seed data file is empty"
}

// Unexpected error
{
  "status": "error",
  "message": "Unexpected error: <error_details>"
}
```

---

### 4. Create Seed Items

Create actual Item master records, Item Price records (selling and/or buying), and optionally update inventory quantities from seed data. This endpoint creates sellable products in the system scoped to the authenticated user's company.

**🔒 Authentication Required:** This endpoint requires user authentication. Items will be automatically scoped to the user's company for multi-tenant isolation.

**✨ New Features:**
- ✅ Supports buying price lists and buying prices
- ✅ Can create Material Receipt Stock Entry to add inventory quantities
- ✅ Supports warehouse assignment and inventory valuation

**Endpoint:**  
`savanna_pos.savanna_pos.apis.product_seeding.create_seed_item`

**Method:** `POST` only

**Authentication:** Required (Bearer token or API key)

**Request Body:**

```json
{
  "price_list": "Standard Selling",
  "buying_price_list": "Standard Buying",
  "company": "Your Company Name",
  "industry": "REST",
  "warehouse": "Main Warehouse",
  "items": [
    {
      "item_code": "BURG001",
      "item_name": "Cheese Burger",
      "item_price": 5.99,
      "buying_price": 3.50,
      "item_group": "All Item Groups",
      "uom": "Nos",
      "qty": 100,
      "warehouse": "Main Warehouse",
      "basic_rate": 3.50
    },
    {
      "item_code": "BURG002",
      "item_name": "Veg Burger",
      "item_price": 4.99,
      "buying_price": 2.75,
      "item_group": "Consumable",
      "uom": "Nos",
      "qty": 50,
      "warehouse": "Store Warehouse",
      "basic_rate": 2.75
    }
  ]
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `price_list` | string | Yes | Name of the selling price list (e.g., "Standard Selling") |
| `buying_price_list` | string | No | Name of the buying price list (e.g., "Standard Buying"). Required if `buying_price` is provided in items |
| `company` | string | No | Company name. If not provided, uses user's default company |
| `industry` | string | No | POS Industry code (e.g., "REST", "RETAIL"). If not provided, uses user's industry or NULL for global products |
| `warehouse` | string | No | Default warehouse for all items. Can be overridden per item. Required if `qty` is provided |
| `items` | array | Yes | Array of item objects to create |
| `items[].item_code` | string | Yes | Unique item code (scoped per company) |
| `items[].item_name` | string | Yes | Display name for the item |
| `items[].item_price` | number | Yes | Selling price (must be >= 0) |
| `items[].buying_price` | number | No | Buying/cost price (must be >= 0). Requires `buying_price_list` at payload level |
| `items[].item_group` | string | No | Item group (default: "All Item Groups") |
| `items[].uom` | string | No | Unit of measure (default: "Nos") |
| `items[].qty` | number | No | Quantity to add to inventory. If provided, requires `warehouse` (payload-level or item-level). Creates Material Receipt Stock Entry |
| `items[].warehouse` | string | No | Warehouse for this item (overrides payload-level `warehouse`). Required if `qty` is provided for this item |
| `items[].basic_rate` | number | No | Cost per unit for inventory valuation. Used in Stock Entry. Defaults to `buying_price` if not provided, otherwise 0 |

**Industry Scoping Logic:**

1. If `industry` is provided in payload → Items are scoped to that industry
2. If `industry` is not provided → Uses user's industry (if user has one assigned)
3. If neither → Creates global products (NULL industry, available to all industries)

**Response (Success):**

```json
{
  "status": "success",
  "company": "Your Company Name",
  "industry": "REST",
  "created": 2,
  "skipped": 0,
  "failed": [],
  "total_received": 2,
  "stock_entry_created": true,
  "stock_entry_name": "MAT-STE-00001",
  "inventory_items_count": 2
}
```

**Response Fields:**

- `status` (string): `"success"`, `"partial_success"`, or `"failed"`
  - `"success"`: All items created successfully
  - `"partial_success"`: Some items created, some failed or skipped
  - `"failed"`: No items were created
- `company` (string): Company name that items were created for
- `industry` (string or null): POS Industry code that items were scoped to, or `null` for global products
- `created` (number): Number of items successfully created
- `skipped` (number): Number of items that already existed for this company (skipped)
- `failed` (array): List of items that failed to create
  - Each item contains: `item_code` and `error` message
- `total_received` (number): Total number of items in the request
- `stock_entry_created` (boolean): `true` if Material Receipt Stock Entry was created, `false` otherwise
- `stock_entry_name` (string or null): Name of the created Stock Entry document, or `null` if no stock entry was created
- `inventory_items_count` (number): Number of items that were added to inventory via Stock Entry

**Error Responses:**

```json
// Authentication required
{
  "exc_type": "AuthenticationError",
  "exc_message": "Please log in to create items. Your session has expired or you are not authenticated."
}

// Missing price list
{
  "exc_type": "ValidationError",
  "exc_message": "Price List is required"
}

// Missing items
{
  "exc_type": "ValidationError",
  "exc_message": "Items must be a non-empty list"
}

// Company not found or not set
{
  "exc_type": "ValidationError",
  "exc_message": "Company is required. Please set a default company in your profile settings or provide the company parameter when creating items."
}

// Invalid industry
{
  "exc_type": "ValidationError",
  "exc_message": "The industry 'INVALID' does not exist or is not active. Please provide a valid industry code."
}

// Invalid item price
{
  "exc_type": "ValidationError",
  "exc_message": "Item Price must be >= 0"
}

// Invalid buying price
{
  "exc_type": "ValueError",
  "exc_message": "Buying Price must be >= 0"
}

// Buying price list required
{
  "exc_type": "ValueError",
  "exc_message": "Buying Price List is required when providing buying_price"
}

// Invalid buying price list
{
  "exc_type": "ValidationError",
  "exc_message": "Price List 'INVALID' is not a buying price list"
}

// Warehouse required for inventory
{
  "exc_type": "ValueError",
  "exc_message": "Warehouse is required when providing qty for item 'BURG001'"
}

// Invalid quantity
{
  "exc_type": "ValueError",
  "exc_message": "Quantity must be greater than 0 for item 'BURG001'"
}

// Missing required fields
{
  "exc_type": "ValueError",
  "exc_message": "Item Code and Item Name are required"
}
```

**What This Endpoint Does:**

1. **Validates Authentication** - Ensures user is logged in
2. **Company Scoping** - Automatically scopes items to user's company (or provided company)
3. **Industry Scoping** - Sets `custom_pos_industry` based on:
   - Industry from payload (if provided)
   - User's industry (if user has one and no industry in payload)
   - NULL (global products available to all industries)
4. Creates `Item` master records with:
   - `item_code`, `item_name`, `item_group`, `stock_uom`
   - Sets `is_stock_item = 1`
   - Sets `custom_company` for multi-tenant isolation
   - Sets `custom_pos_industry` for industry filtering
   - Sets `custom_prevent_etims_registration = 1` by default
   
5. Creates **Selling** `Item Price` records with:
   - `item_code`, `price_list`, `price_list_rate`
   - Links the price to the specified selling price list
   - Sets company if Item Price supports it

6. Creates **Buying** `Item Price` records (if `buying_price_list` and `buying_price` are provided):
   - `item_code`, `price_list`, `price_list_rate`
   - Links the price to the specified buying price list
   - Sets company if Item Price supports it

7. Creates **Material Receipt Stock Entry** (if `qty` and `warehouse` are provided):
   - Creates a Stock Entry of type "Material Receipt"
   - Adds items with specified quantities to warehouses
   - Uses `basic_rate` for inventory valuation (defaults to `buying_price` or 0)
   - Automatically submits the Stock Entry to update inventory
   - Updates Bin and creates Stock Ledger Entries

8. **Duplicate Checking** - Checks for existing items by `item_code` + `company` (allows same code across different companies)

**Example Use Cases:**

#### Example 1: Seeding Items for User's Industry

```javascript
// Items will be scoped to user's company and industry automatically
const response = await apiRequest(
  'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
  'POST',
  {
    price_list: "Standard Selling",
    items: [
      { item_code: "BURG001", item_name: "Cheese Burger", item_price: 5.99 }
    ]
  },
  {
    'Authorization': `Bearer ${accessToken}`  // Required!
  }
);
```

#### Example 2: Seeding Items with Buying Prices

```javascript
// Create items with both selling and buying prices
const response = await apiRequest(
  'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
  'POST',
  {
    price_list: "Standard Selling",
    buying_price_list: "Standard Buying",
    items: [
      {
        item_code: "BURG001",
        item_name: "Cheese Burger",
        item_price: 5.99,      // Selling price
        buying_price: 3.50     // Buying/cost price
      }
    ]
  },
  {
    'Authorization': `Bearer ${accessToken}`  // Required!
  }
);
```

#### Example 3: Seeding Items with Inventory

```javascript
// Create items and add inventory in one call
const response = await apiRequest(
  'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
  'POST',
  {
    price_list: "Standard Selling",
    buying_price_list: "Standard Buying",
    warehouse: "Main Warehouse",  // Default warehouse
    items: [
      {
        item_code: "BURG001",
        item_name: "Cheese Burger",
        item_price: 5.99,
        buying_price: 3.50,
        qty: 100,                 // Add 100 units to inventory
        basic_rate: 3.50         // Valuation rate
      },
      {
        item_code: "BURG002",
        item_name: "Veg Burger",
        item_price: 4.99,
        buying_price: 2.75,
        qty: 50,
        warehouse: "Store Warehouse",  // Different warehouse per item
        basic_rate: 2.75
      }
    ]
  },
  {
    'Authorization': `Bearer ${accessToken}`  // Required!
  }
);

// Response includes stock entry information:
// {
//   "status": "success",
//   "created": 2,
//   "stock_entry_created": true,
//   "stock_entry_name": "MAT-STE-00001",
//   "inventory_items_count": 2
// }
```

#### Example 4: Seeding Items for Specific Industry

```javascript
// Seed items for REST industry, even if user's industry is different
const response = await apiRequest(
  'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
  'POST',
  {
    price_list: "Standard Selling",
    industry: "REST",  // Specify industry
    items: [
      { item_code: "REST-001", item_name: "Veg Burger", item_price: 4.99 }
    ]
  },
  {
    'Authorization': `Bearer ${accessToken}`  // Required!
  }
);
```

#### Example 5: Creating Global Products

```javascript
// Create products available to all industries
const response = await apiRequest(
  'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
  'POST',
  {
    price_list: "Standard Selling",
    industry: null,  // Explicitly set to null for global
    items: [
      { item_code: "GLOBAL-001", item_name: "Service Charge", item_price: 0 }
    ]
  },
  {
    'Authorization': `Bearer ${accessToken}`  // Required!
  }
);
```

**Note:** You can still add stock separately using the Stock Entry API if you prefer to create items first and add inventory later. However, the `create_seed_item` endpoint now supports adding inventory in the same call for convenience.

---

## React.js Implementation Examples

### Setup: API Configuration

Create an API utility file for making requests:

```javascript
// utils/api.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://your-domain.com/api/method/';

/**
 * Make API request to Frappe endpoint
 * @param {string} endpoint - API endpoint (e.g., 'savanna_pos.savanna_pos.apis.product_seeding.get_pos_industries')
 * @param {string} method - HTTP method ('GET' or 'POST')
 * @param {object} params - Request parameters
 * @param {object} headers - Additional headers
 * @returns {Promise<object>} API response
 */
export const apiRequest = async (endpoint, method = 'GET', params = {}, headers = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  // Add authentication token if available
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  // Add parameters
  if (method === 'GET') {
    const queryParams = new URLSearchParams(params).toString();
    const fullUrl = queryParams ? `${url}?${queryParams}` : url;
    const response = await fetch(fullUrl, config);
    return response.json();
  } else {
    config.body = JSON.stringify(params);
    const response = await fetch(url, config);
    return response.json();
  }
};
```

### Example 1: Fetch Industries

```javascript
// hooks/useIndustries.js
import { useState, useEffect } from 'react';
import { apiRequest } from '../utils/api';

export const useIndustries = (isActive = true) => {
  const [industries, setIndustries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchIndustries = async () => {
      try {
        setLoading(true);
        const response = await apiRequest(
          'savanna_pos.savanna_pos.apis.product_seeding.get_pos_industries',
          'GET',
          { is_active: isActive }
        );

        if (response.success) {
          setIndustries(response.industries);
          setError(null);
        } else {
          setError(response.message || 'Failed to fetch industries');
        }
      } catch (err) {
        setError(err.message || 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchIndustries();
  }, [isActive]);

  return { industries, loading, error };
};

// Component usage
import React from 'react';
import { useIndustries } from './hooks/useIndustries';

const IndustriesList = () => {
  const { industries, loading, error } = useIndustries();

  if (loading) return <div>Loading industries...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>POS Industries ({industries.length})</h2>
      <ul>
        {industries.map((industry) => (
          <li key={industry.name}>
            <strong>{industry.industry_name}</strong> ({industry.industry_code})
            <p>{industry.description}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default IndustriesList;
```

### Example 2: Fetch Products for Industry

```javascript
// hooks/useIndustryProducts.js
import { useState, useEffect } from 'react';
import { apiRequest } from '../utils/api';

export const useIndustryProducts = (industry) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totalProducts, setTotalProducts] = useState(0);

  useEffect(() => {
    if (!industry) {
      setProducts([]);
      return;
    }

    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await apiRequest(
          'savanna_pos.savanna_pos.apis.product_seeding.seed_products',
          'POST',
          { industry }
        );

        if (response.status === 'success') {
          setProducts(response.products);
          setTotalProducts(response.total_products);
        } else {
          setError(response.message || 'Failed to fetch products');
          setProducts([]);
          setTotalProducts(0);
        }
      } catch (err) {
        setError(err.message || 'An error occurred');
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [industry]);

  return { products, loading, error, totalProducts };
};

// Component usage
import React, { useState } from 'react';
import { useIndustries } from './hooks/useIndustries';
import { useIndustryProducts } from './hooks/useIndustryProducts';

const ProductSeeding = () => {
  const { industries } = useIndustries();
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const { products, loading, error, totalProducts } = useIndustryProducts(selectedIndustry);

  return (
    <div>
      <h2>Product Seeding</h2>
      
      <div>
        <label>Select Industry:</label>
        <select 
          value={selectedIndustry} 
          onChange={(e) => setSelectedIndustry(e.target.value)}
        >
          <option value="">-- Select Industry --</option>
          {industries.map((industry) => (
            <option key={industry.name} value={industry.name}>
              {industry.industry_name}
            </option>
          ))}
        </select>
      </div>

      {loading && <div>Loading products...</div>}
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      
      {selectedIndustry && !loading && !error && (
        <div>
          <h3>Products ({totalProducts})</h3>
          <ul>
            {products.map((product) => (
              <li key={product.sku}>
                <strong>{product.name}</strong> - SKU: {product.sku}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProductSeeding;
```

### Example 3: Bulk Upload Products

```javascript
// hooks/useBulkUpload.js
import { useState } from 'react';
import { apiRequest } from '../utils/api';

export const useBulkUpload = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const uploadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await apiRequest(
        'savanna_pos.savanna_pos.apis.product_seeding.bulk_upload_products',
        'POST'
      );

      if (response.status === 'success') {
        setResult(response);
      } else {
        setError(response.message || 'Upload failed');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return { uploadProducts, loading, result, error };
};

// Component usage
import React from 'react';
import { useBulkUpload } from './hooks/useBulkUpload';

const BulkUploadProducts = () => {
  const { uploadProducts, loading, result, error } = useBulkUpload();

  const handleUpload = () => {
    if (window.confirm('Are you sure you want to bulk upload products? This will create product templates from the seed data file.')) {
      uploadProducts();
    }
  };

  return (
    <div>
      <h2>Bulk Upload Products</h2>
      <button onClick={handleUpload} disabled={loading}>
        {loading ? 'Uploading...' : 'Upload Products'}
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          Error: {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '10px' }}>
          <h3>Upload Results:</h3>
          <ul>
            <li>Created: {result.created}</li>
            <li>Skipped: {result.skipped}</li>
            <li>Total Processed: {result.total_processed}</li>
            {result.ignored_industries && result.ignored_industries.length > 0 && (
              <li>
                Ignored Industries: {result.ignored_industries.join(', ')}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default BulkUploadProducts;
```

### Example 4: Create Seed Items

```javascript
// hooks/useCreateSeedItems.js
import { useState } from 'react';
import { apiRequest } from '../utils/api';

export const useCreateSeedItems = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const createItems = async (
    priceList, 
    items, 
    company = null, 
    industry = null,
    buyingPriceList = null,
    warehouse = null
  ) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      // Get authentication token
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required. Please log in.');
        return;
      }

      const payload = {
        price_list: priceList,
        items: items
      };

      // Add optional fields
      if (company) payload.company = company;
      if (industry !== undefined) payload.industry = industry;  // Can be null for global
      if (buyingPriceList) payload.buying_price_list = buyingPriceList;
      if (warehouse) payload.warehouse = warehouse;

      const response = await apiRequest(
        'savanna_pos.savanna_pos.apis.product_seeding.create_seed_item',
        'POST',
        payload,
        {
          'Authorization': `Bearer ${token}`  // Required!
        }
      );

      // Frappe returns errors in exc_message format
      if (response.exc_type) {
        setError(response.exc_message || 'Failed to create items');
      } else {
        setResult(response);
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return { createItems, loading, result, error };
};

// Component usage
import React, { useState } from 'react';
import { useCreateSeedItems } from './hooks/useCreateSeedItems';

const CreateSeedItems = () => {
  const { createItems, loading, result, error } = useCreateSeedItems();
  const [priceList, setPriceList] = useState('Standard Selling');
  const [buyingPriceList, setBuyingPriceList] = useState('');  // Optional
  const [company, setCompany] = useState('');  // Optional - defaults to user's company
  const [industry, setIndustry] = useState('');  // Optional - defaults to user's industry
  const [warehouse, setWarehouse] = useState('');  // Optional - default warehouse
  const [items, setItems] = useState([
    { 
      item_code: '', 
      item_name: '', 
      item_price: 0, 
      buying_price: null,
      item_group: 'All Item Groups', 
      uom: 'Nos',
      qty: null,
      warehouse: '',
      basic_rate: null
    }
  ]);

  const handleAddItem = () => {
    setItems([...items, { 
      item_code: '', 
      item_name: '', 
      item_price: 0, 
      buying_price: null,
      item_group: 'All Item Groups', 
      uom: 'Nos',
      qty: null,
      warehouse: '',
      basic_rate: null
    }]);
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const handleSubmit = () => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in to create items');
      return;
    }

    // Validate required fields
    const validItems = items.filter(item => {
      if (!item.item_code || !item.item_name || item.item_price < 0) {
        return false;
      }
      // If buying_price is provided, buying_price_list must be set
      if (item.buying_price && item.buying_price > 0 && !buyingPriceList) {
        alert(`Buying Price List is required for item ${item.item_code || 'with buying price'}`);
        return false;
      }
      // If qty is provided, warehouse must be set (item-level or default)
      if (item.qty && item.qty > 0 && !item.warehouse && !warehouse) {
        alert(`Warehouse is required for item ${item.item_code || 'with quantity'}`);
        return false;
      }
      return true;
    });

    if (validItems.length === 0) {
      alert('Please add at least one valid item');
      return;
    }

    if (!priceList) {
      alert('Price list is required');
      return;
    }

    if (window.confirm(`Create ${validItems.length} items for your company?`)) {
      // Pass company, industry, buying price list, and warehouse (can be empty strings, will use defaults)
      createItems(
        priceList, 
        validItems, 
        company || null,  // null if empty
        industry || null,  // null if empty (will use user's industry or global)
        buyingPriceList || null,  // null if empty
        warehouse || null  // null if empty
      );
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Create Seed Items</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <label>Price List (Selling) *: </label>
        <input
          type="text"
          value={priceList}
          onChange={(e) => setPriceList(e.target.value)}
          placeholder="Standard Selling"
          style={{ padding: '8px', fontSize: '16px', minWidth: '200px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Buying Price List (optional): </label>
        <input
          type="text"
          value={buyingPriceList}
          onChange={(e) => setBuyingPriceList(e.target.value)}
          placeholder="Standard Buying"
          style={{ padding: '8px', fontSize: '16px', minWidth: '200px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Required if you provide buying_price for items
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Company (optional): </label>
        <input
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Defaults to your company"
          style={{ padding: '8px', fontSize: '16px', minWidth: '200px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Leave empty to use your default company
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Industry (optional): </label>
        <input
          type="text"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          placeholder="REST, RETAIL, etc. (defaults to your industry)"
          style={{ padding: '8px', fontSize: '16px', minWidth: '200px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Leave empty to use your industry, or enter industry code (e.g., "REST")
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>Default Warehouse (optional): </label>
        <input
          type="text"
          value={warehouse}
          onChange={(e) => setWarehouse(e.target.value)}
          placeholder="Main Warehouse"
          style={{ padding: '8px', fontSize: '16px', minWidth: '200px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Default warehouse for all items. Can be overridden per item. Required if adding inventory (qty)
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Items</h3>
        {items.map((item, index) => (
          <div key={index} style={{ 
            border: '1px solid #ddd', 
            padding: '15px', 
            marginBottom: '10px',
            borderRadius: '4px'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label>Item Code *</label>
                <input
                  type="text"
                  value={item.item_code}
                  onChange={(e) => handleItemChange(index, 'item_code', e.target.value)}
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>Item Name *</label>
                <input
                  type="text"
                  value={item.item_name}
                  onChange={(e) => handleItemChange(index, 'item_name', e.target.value)}
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>Selling Price *</label>
                <input
                  type="number"
                  value={item.item_price}
                  onChange={(e) => handleItemChange(index, 'item_price', parseFloat(e.target.value) || 0)}
                  min="0"
                  step="0.01"
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>Buying Price (optional)</label>
                <input
                  type="number"
                  value={item.buying_price || ''}
                  onChange={(e) => handleItemChange(index, 'buying_price', e.target.value ? parseFloat(e.target.value) : null)}
                  min="0"
                  step="0.01"
                  placeholder="Cost price"
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>Item Group</label>
                <input
                  type="text"
                  value={item.item_group}
                  onChange={(e) => handleItemChange(index, 'item_group', e.target.value)}
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>UOM</label>
                <input
                  type="text"
                  value={item.uom}
                  onChange={(e) => handleItemChange(index, 'uom', e.target.value)}
                  placeholder="Nos"
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
              <div>
                <label>Quantity (optional)</label>
                <input
                  type="number"
                  value={item.qty || ''}
                  onChange={(e) => handleItemChange(index, 'qty', e.target.value ? parseFloat(e.target.value) : null)}
                  min="0"
                  step="1"
                  placeholder="Add to inventory"
                  style={{ width: '100%', padding: '8px' }}
                />
                <small style={{ display: 'block', color: '#666', marginTop: '2px' }}>
                  Requires warehouse
                </small>
              </div>
              <div>
                <label>Warehouse (optional)</label>
                <input
                  type="text"
                  value={item.warehouse}
                  onChange={(e) => handleItemChange(index, 'warehouse', e.target.value)}
                  placeholder="Overrides default"
                  style={{ width: '100%', padding: '8px' }}
                />
                <small style={{ display: 'block', color: '#666', marginTop: '2px' }}>
                  Required if qty provided
                </small>
              </div>
              <div>
                <label>Basic Rate (optional)</label>
                <input
                  type="number"
                  value={item.basic_rate || ''}
                  onChange={(e) => handleItemChange(index, 'basic_rate', e.target.value ? parseFloat(e.target.value) : null)}
                  min="0"
                  step="0.01"
                  placeholder="Valuation rate"
                  style={{ width: '100%', padding: '8px' }}
                />
                <small style={{ display: 'block', color: '#666', marginTop: '2px' }}>
                  Defaults to buying_price
                </small>
              </div>
            </div>
          </div>
        ))}
        <button onClick={handleAddItem} style={{ marginTop: '10px' }}>
          + Add Item
        </button>
      </div>

      <button 
        onClick={handleSubmit} 
        disabled={loading}
        style={{ 
          padding: '12px 24px', 
          fontSize: '16px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Creating...' : 'Create Items'}
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '15px', padding: '10px', background: '#ffe6e6' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: '15px', padding: '15px', background: '#e6f7e6', borderRadius: '4px' }}>
          <h3>Results:</h3>
          <p><strong>Company:</strong> {result.company}</p>
          <p><strong>Industry:</strong> {result.industry || 'Global (all industries)'}</p>
          <p>✅ <strong>Created:</strong> {result.created}</p>
          <p>⏭️ <strong>Skipped:</strong> {result.skipped}</p>
          <p>📊 <strong>Total Received:</strong> {result.total_received}</p>
          {result.stock_entry_created && (
            <div style={{ marginTop: '10px', padding: '10px', background: '#d4edda', borderRadius: '4px' }}>
              <p>📦 <strong>Stock Entry Created:</strong> {result.stock_entry_name}</p>
              <p>📈 <strong>Inventory Items:</strong> {result.inventory_items_count}</p>
            </div>
          )}
          {result.failed && result.failed.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <strong>❌ Failed Items:</strong>
              <ul>
                {result.failed.map((item, index) => (
                  <li key={index}>
                    {item.item_code}: {item.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CreateSeedItems;
```

### Example 5: Complete Product Seeding Dashboard

```javascript
// components/ProductSeedingDashboard.jsx
import React, { useState } from 'react';
import { useIndustries } from '../hooks/useIndustries';
import { useIndustryProducts } from '../hooks/useIndustryProducts';
import { useBulkUpload } from '../hooks/useBulkUpload';

const ProductSeedingDashboard = () => {
  const { industries, loading: industriesLoading } = useIndustries();
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const { products, loading: productsLoading, error, totalProducts } = 
    useIndustryProducts(selectedIndustry);
  const { uploadProducts, loading: uploadLoading, result, error: uploadError } = 
    useBulkUpload();

  const handleBulkUpload = () => {
    if (window.confirm('Upload products from seed data file?')) {
      uploadProducts();
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Product Seeding Dashboard</h1>

      {/* Bulk Upload Section */}
      <section style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd' }}>
        <h2>Bulk Upload</h2>
        <button 
          onClick={handleBulkUpload} 
          disabled={uploadLoading}
          style={{ padding: '10px 20px', fontSize: '16px' }}
        >
          {uploadLoading ? 'Uploading...' : 'Upload Products from Seed File'}
        </button>
        
        {uploadError && (
          <div style={{ color: 'red', marginTop: '10px' }}>{uploadError}</div>
        )}
        
        {result && (
          <div style={{ marginTop: '15px', padding: '10px', background: '#f0f0f0' }}>
            <h3>Upload Results:</h3>
            <p>✅ Created: {result.created}</p>
            <p>⏭️ Skipped: {result.skipped}</p>
            <p>📊 Total Processed: {result.total_processed}</p>
            {result.ignored_industries?.length > 0 && (
              <p>⚠️ Ignored Industries: {result.ignored_industries.join(', ')}</p>
            )}
          </div>
        )}
      </section>

      {/* Industry Selection */}
      <section style={{ marginBottom: '30px' }}>
        <h2>Select Industry</h2>
        {industriesLoading ? (
          <div>Loading industries...</div>
        ) : (
          <select
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            style={{ padding: '10px', fontSize: '16px', minWidth: '300px' }}
          >
            <option value="">-- Select an Industry --</option>
            {industries.map((industry) => (
              <option key={industry.name} value={industry.name}>
                {industry.industry_name} ({industry.industry_code})
              </option>
            ))}
          </select>
        )}
      </section>

      {/* Products Display */}
      {selectedIndustry && (
        <section>
          <h2>Products for Selected Industry</h2>
          {productsLoading ? (
            <div>Loading products...</div>
          ) : error ? (
            <div style={{ color: 'red' }}>Error: {error}</div>
          ) : (
            <div>
              <p><strong>Total Products:</strong> {totalProducts}</p>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                gap: '10px',
                marginTop: '15px'
              }}>
                {products.map((product) => (
                  <div 
                    key={product.sku}
                    style={{ 
                      padding: '15px', 
                      border: '1px solid #ddd', 
                      borderRadius: '5px',
                      background: '#f9f9f9'
                    }}
                  >
                    <div style={{ fontWeight: 'bold' }}>{product.name}</div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      SKU: {product.sku}
                    </div>
                    <div style={{ 
                      fontSize: '11px', 
                      color: '#28a745', 
                      marginTop: '5px' 
                    }}>
                      {product.status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default ProductSeedingDashboard;
```

---

## Error Handling Best Practices

### 1. Network Errors

```javascript
try {
  const response = await apiRequest(endpoint, 'GET', params);
  // Handle response
} catch (error) {
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    // Network error
    console.error('Network error - check your connection');
  } else {
    // Other errors
    console.error('Error:', error);
  }
}
```

### 2. API Error Responses

```javascript
const handleApiResponse = (response) => {
  if (response.status === 'error' || !response.success) {
    // Show user-friendly error message
    const errorMessage = response.message || 'An unexpected error occurred';
    alert(errorMessage);
    return false;
  }
  return true;
};
```

### 3. Loading States

Always show loading indicators during API calls:

```javascript
const [loading, setLoading] = useState(false);

// In your component
{loading && <Spinner />}
{!loading && <Content />}
```

---

## TypeScript Types (Optional)

If you're using TypeScript, here are type definitions:

```typescript
// types/productSeeding.ts

export interface Industry {
  name: string;
  industry_code: string;
  industry_name: string;
  description: string;
  serving_location: string;
  is_active: number;
  sort_order: number;
}

export interface Product {
  sku: string;
  name: string;
  status: 'available';
}

export interface IndustriesResponse {
  success: boolean;
  industries: Industry[];
  count: number;
  message: string;
}

export interface ProductsResponse {
  status: 'success' | 'error';
  industry?: string;
  total_products: number;
  products?: Product[];
  message?: string;
}

export interface BulkUploadResponse {
  status: 'success' | 'partial_success' | 'no_op' | 'error';
  created?: number;
  skipped?: number;
  failed?: number;
  ignored_industries?: string[];
  failed_items?: Array<{
    industry: string;
    item: any;
    error?: string;
    reason?: string;
  }>;
  total_processed?: number;
  message?: string;
}

export interface CreateSeedItemResponse {
  status: 'success' | 'partial_success' | 'failed';
  company: string;
  industry: string | null;
  created: number;
  skipped: number;
  failed: Array<{
    item_code: string;
    error: string;
  }>;
  total_received: number;
}
```

---

## Notes

1. **Authentication**: 
   - Most endpoints support guest access (`get_pos_industries`, `seed_products`, `bulk_upload_products`)
   - **`create_seed_item` requires authentication** - items are scoped to the authenticated user's company

2. **Company Scoping**: 
   - Items created via `create_seed_item` are automatically scoped to the user's company
   - Same item codes can exist across different companies (multi-tenant isolation)
   - Duplicate checking is done by `item_code` + `company` combination

3. **Industry Scoping**:
   - Items can be scoped to a specific industry, user's industry, or global (NULL)
   - Global products (`custom_pos_industry = NULL`) are available to all industries
   - Industry-specific products are only visible to users with that industry

4. **Industry Identifier**: When calling `seed_products`, use the `name` field from the industries list (e.g., `"REST"`, `"RETAIL"`), not the `industry_name` or `industry_code`.

5. **Bulk Upload**: The `bulk_upload_products` endpoint reads from an internal seed data file. It will skip products that already exist and ignore industries that don't exist in the system.

6. **Error Messages**: All error messages are internationalized and may vary based on the system's language settings.

7. **Rate Limiting**: Consider implementing rate limiting on the frontend to prevent excessive API calls.

---

## Testing

### Using cURL

```bash
# Get industries
curl -X GET "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.product_seeding.get_pos_industries?is_active=true"

# Get products for industry
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.product_seeding.seed_products" \
  -H "Content-Type: application/json" \
  -d '{"industry": "REST"}'

# Bulk upload
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.product_seeding.bulk_upload_products" \
  -H "Content-Type: application/json"

# Create seed items (requires authentication)
curl -X POST "https://your-domain.com/api/method/savanna_pos.savanna_pos.apis.product_seeding.create_seed_item" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "price_list": "Standard Selling",
    "industry": "REST",
    "items": [
      {
        "item_code": "BURG001",
        "item_name": "Cheese Burger",
        "item_price": 5.99,
        "item_group": "Consumable",
        "uom": "Nos"
      }
    ]
  }'
```

### Using Postman

1. Create a new request
2. Set method to `GET` or `POST`
3. Enter the full endpoint URL
4. Add parameters in Query Params (GET) or Body (POST)
5. Send request

---

## Support

For issues or questions, please contact the development team or refer to the main SavvyPOS documentation.
