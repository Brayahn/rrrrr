# POS Industry Implementation Guide

## Overview

This document describes the POS Industry feature that allows users to select their industry during registration and filters products based on the selected industry. This enables a global product catalog where products can be available to all industries or restricted to specific industries.

## Architecture

### Components

1. **POS Industry DocType** - Master data containing industry definitions
2. **User Custom Field** - `custom_pos_industry` field to store user's selected industry
3. **Item Custom Field** - `custom_pos_industry` field to link products to industries
4. **API Endpoints** - For listing industries, registration, and product filtering

## Features

### 1. Industry Master Data

The `POS Industry` DocType contains:
- `industry_code`: Unique code (e.g., "REST", "RETAIL")
- `industry_name`: Display name (e.g., "Restaurant & Food Service")
- `description`: Detailed description
- `serving_location`: Where the industry serves customers
- `is_active`: Whether the industry is available for selection
- `sort_order`: Display order

### 2. User Registration

During registration, users can now provide a `pos_industry` parameter:
- Can be provided as industry code, name (case-insensitive)
- Validates that the industry exists and is active
- Stores the industry in the user's profile

### 3. Product Filtering

Products are filtered based on user's industry:
- Products with `custom_pos_industry = NULL` are available to ALL industries (global products)
- Products with `custom_pos_industry` set are only available to users with that industry
- When a user queries products, they see:
  - Global products (no industry assigned)
  - Products assigned to their industry

## API Endpoints

### 1. Get POS Industries

**Endpoint**: `savanna_pos.savanna_pos.apis.industry_api.get_pos_industries`

**Method**: `GET` or `POST`

**Authentication**: Optional (public endpoint)

**Parameters**:
- `is_active` (bool, optional): Filter by active status (default: True)

**Response**:
```json
{
  "success": true,
  "industries": [
    {
      "name": "REST",
      "industry_code": "REST",
      "industry_name": "Restaurant & Food Service",
      "description": "Full-service restaurants, cafes, bars...",
      "serving_location": "Physical restaurant, cafe...",
      "is_active": 1,
      "sort_order": 1
    }
  ],
  "count": 15,
  "message": "Industries retrieved successfully"
}
```

### 2. Get User Industry

**Endpoint**: `savanna_pos.savanna_pos.apis.industry_api.get_user_industry`

**Method**: `GET` or `POST`

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "industry": {
    "name": "REST",
    "industry_code": "REST",
    "industry_name": "Restaurant & Food Service",
    "description": "...",
    "serving_location": "...",
    "is_active": 1
  },
  "message": "Industry retrieved successfully"
}
```

### 3. Register User (Updated)

**Endpoint**: `savanna_pos.savanna_pos.apis.auth_api.register_user`

**Method**: `POST`

**Authentication**: Not required (public endpoint)

**New Parameter**:
- `pos_industry` (string, optional): Industry code or name

**Example Request**:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "phone": "+254712345678",
  "pos_industry": "REST"
}
```

**Response** (includes industry info if provided):
```json
{
  "user": {...},
  "pos_industry": {
    "name": "REST",
    "industry_name": "Restaurant & Food Service"
  },
  ...
}
```

### 4. Get Products (Updated)

**Endpoint**: `savanna_pos.savanna_pos.apis.product_api.get_products`

**Method**: `GET`

**Authentication**: Required

**Automatic Filtering**:
- Automatically filters products based on user's industry
- Shows global products (no industry) + user's industry products

**Example**:
- User with industry "REST" will see:
  - All products with `custom_pos_industry = NULL`
  - All products with `custom_pos_industry = "REST"`

### 5. Get Current User (Updated)

**Endpoint**: `savanna_pos.savanna_pos.apis.auth_api.get_current_user`

**Method**: `GET`

**Authentication**: Required

**New Field in Response**:
```json
{
  "user": {...},
  "company": {...},
  "pos_profile": {...},
  "pos_industry": {
    "name": "REST",
    "industry_code": "REST",
    "industry_name": "Restaurant & Food Service",
    "description": "...",
    "serving_location": "..."
  }
}
```

## Setup Instructions

### 1. Migrate the Database

After adding the new DocType and custom fields, run:

```bash
bench migrate
```

This will:
- Create the `POS Industry` DocType
- Add `custom_pos_industry` field to User
- Add `custom_pos_industry` field to Item

### 2. Import Sample Industries

The fixture file `fixtures/pos_industry.json` contains 15 sample industries. To import them:

```bash
bench --site [your-site] import-doc /path/to/fixtures/pos_industry.json
```

Or they will be automatically imported during app installation/migration if configured in hooks.

### 3. Seed Global Products

To seed a list of global products (available to all industries), see the [Global Products Seeding Guide](./GLOBAL_PRODUCTS_SEEDING.md).

**Quick Start:**
```javascript
// Seed default global products for all companies
POST /api/method/savanna_pos.savanna_pos.apis.product_api.seed_global_products
```

When creating products manually:
- Leave `custom_pos_industry` field empty/null for global products
- Set `custom_pos_industry` to the appropriate industry for industry-specific products

## Usage Examples

### Frontend Registration Flow

```javascript
// 1. Get available industries
const industriesResponse = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.industry_api.get_pos_industries'
);
const { industries } = await industriesResponse.json();

// 2. Display industries to user for selection
// Show list with industry_name and description

// 3. Register user with selected industry
const registerResponse = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.auth_api.register_user',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'user@example.com',
      first_name: 'John',
      last_name: 'Doe',
      password: 'securepass123',
      pos_industry: 'REST' // or industry_code
    })
  }
);
```

### Product Management

```javascript
// Creating a global product (available to all industries)
const globalProduct = {
  item_code: 'GLOBAL-001',
  item_name: 'Universal Product',
  custom_company: 'Company Name',
  // custom_pos_industry: null (or omit the field)
};

// Creating an industry-specific product
const restaurantProduct = {
  item_code: 'REST-001',
  item_name: 'Menu Item',
  custom_company: 'Company Name',
  custom_pos_industry: 'REST'
};
```

### Querying Products

Products are automatically filtered when using `get_products` API:

```javascript
// This will automatically filter based on current user's industry
const productsResponse = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.get_products',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);
// Returns only relevant products for user's industry
```

## Sample Industries Included

The fixture includes 15 common POS industries:

1. Restaurant & Food Service
2. Retail Store
3. Grocery & Supermarket
4. Pharmacy & Health
5. Fashion & Apparel
6. Electronics & Technology
7. Beauty & Salon
8. Automotive
9. Fuel Station
10. Hotel & Hospitality
11. Bookstore & Stationery
12. Sports & Recreation
13. Jewelry & Accessories
14. Furniture & Home Decor
15. E-commerce & Online Retail
16. Other

You can add more industries as needed by creating new `POS Industry` records.

## Customization

### Adding New Industries

1. Go to Frappe Desk
2. Navigate to "POS Industry" list
3. Click "New"
4. Fill in:
   - Industry Code (unique identifier)
   - Industry Name
   - Description
   - Serving Location
   - Sort Order
5. Save

### Modifying Product-Industry Mapping

To change which products are available to which industries:
1. Edit the Item record
2. Modify the `POS Industry` field
3. Save

## Database Schema

### POS Industry Table
- `name`: Industry code (primary key)
- `industry_code`: Unique code
- `industry_name`: Display name
- `description`: Text description
- `serving_location`: Location description
- `is_active`: Boolean (0 or 1)
- `sort_order`: Integer

### User Custom Field
- `custom_pos_industry`: Link to POS Industry

### Item Custom Field
- `custom_pos_industry`: Link to POS Industry (nullable for global products)

## Notes

- Industry selection during registration is **optional** - users can register without selecting an industry
- Products without an industry assignment are **global** and visible to all users
- Users can see their industry via the `get_current_user` endpoint
- Product filtering happens automatically in the `get_products` API
- The system supports case-insensitive industry lookup during registration

