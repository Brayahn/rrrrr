# Global Products Seeding Guide

## Overview

This guide explains how to seed global products (products available to all industries) into your POS system. Global products have `custom_pos_industry = NULL`, making them visible to users regardless of their selected industry.

## Important Notes

- **Products are per-company**: Each product is created for a specific company (multi-tenant isolation)
- **Global means all industries**: Products with no industry assignment are visible to all industries within a company
- **Company is required**: Products cannot exist without a company assignment

## Methods to Seed Products

### Method 1: Using API Endpoint (Recommended)

The easiest way to seed products is through the API endpoint.

#### Endpoint

**URL**: `/api/method/savanna_pos.savanna_pos.apis.product_api.seed_global_products`

**Method**: `POST`

**Authentication**: Required (System Manager role)

#### Parameters

- `company` (optional): Company name. If not provided, seeds for all companies
- `products_data` (optional): Array of product objects. If not provided, uses default products

#### Example 1: Seed Default Products for All Companies

```javascript
const response = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.seed_global_products',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({})
  }
);

const result = await response.json();
console.log(result);
// {
//   "success": true,
//   "message": "Seeded 10 products, skipped 0 products",
//   "created": 10,
//   "skipped": 0,
//   "created_products": [...],
//   "skipped_products": [...]
// }
```

#### Example 2: Seed for Specific Company

```javascript
const response = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.seed_global_products',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      company: "Your Company Name"
    })
  }
);
```

#### Example 3: Seed Custom Products

```javascript
const customProducts = [
  {
    "item_code": "MY-PROD-001",
    "item_name": "My Custom Product",
    "item_group": "Products",
    "stock_uom": "Nos",
    "standard_rate": 100.0,
    "description": "My custom product description",
    "is_stock_item": true,
    "is_sales_item": true,
    "is_purchase_item": false,
    "brand": "My Brand"
  }
];

const response = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.seed_global_products',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      company: "Your Company Name",
      products_data: customProducts
    })
  }
);
```

### Method 2: Using Python Console/Command

You can also seed products directly from the Python console or a custom script.

#### Via Bench Console

```bash
bench --site [your-site] console
```

Then in the console:

```python
import frappe
from savanna_pos.savanna_pos.setup.seed_global_products import seed_global_products

# Seed for all companies with default products
result = seed_global_products()
print(result)

# Seed for specific company
result = seed_global_products(company="Your Company Name")
print(result)

# Seed custom products
custom_products = [
    {
        "item_code": "CUSTOM-001",
        "item_name": "Custom Product",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 100.0,
        "is_stock_item": True,
        "is_sales_item": True,
        "is_purchase_item": False
    }
]
result = seed_global_products(company="Your Company Name", products_data=custom_products)
print(result)
```

#### Via Custom Script

Create a Python script and run it:

```python
# seed_products.py
import frappe

def seed():
    frappe.connect(site="your-site")
    frappe.set_user("Administrator")
    
    from savanna_pos.savanna_pos.setup.seed_global_products import seed_global_products
    
    result = seed_global_products(company="Your Company Name")
    print(f"Created: {result['created']}, Skipped: {result['skipped']}")
    
    frappe.db.commit()
    frappe.destroy()

if __name__ == "__main__":
    seed()
```

Run with:
```bash
bench --site [your-site] execute seed_products.seed
```

### Method 3: Using Individual Product Creation API

You can create products one by one using the `create_product` API, ensuring `custom_pos_industry` is not set:

```javascript
const response = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.create_product',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      item_code: "GLOBAL-PEN-001",
      item_name: "Ballpoint Pen",
      item_group: "Stationery",
      stock_uom: "Nos",
      standard_rate: 20.0,
      description: "Standard ballpoint pen",
      is_stock_item: true,
      is_sales_item: true,
      company: "Your Company Name"
      // Note: custom_pos_industry is automatically NULL for global products
    })
  }
);
```

## Default Products Included

The seeding script includes 10 default global products:

1. **Ballpoint Pen** - Stationery item
2. **Notebook A4** - Stationery item
3. **File Folder** - Stationery item
4. **Shopping Bag** - Packaging item
5. **Thermal Receipt Paper** - Consumable for POS
6. **Packaging Tape** - Packaging item
7. **Cardboard Box Small** - Packaging item
8. **Water Bottle 500ml** - Beverage
9. **Candy Pack** - Food item
10. **Service Charge** - Service item (non-stock)

## Product Data Structure

Each product in the `products_data` array should have:

### Required Fields

- `item_code`: Unique item code (string)
- `item_name`: Display name (string)

### Optional Fields

- `item_group`: Item group name (default: "All Item Groups")
- `stock_uom`: Unit of measure (default: "Nos")
- `standard_rate`: Default selling price (default: 0.0)
- `description`: Product description
- `is_stock_item`: Whether item is tracked in stock (default: true)
- `is_sales_item`: Whether item can be sold (default: true)
- `is_purchase_item`: Whether item can be purchased (default: false)
- `brand`: Brand name
- `barcode`: Barcode string
- `image`: Image URL or file path

### Example Product Object

```json
{
  "item_code": "GLOBAL-PEN-001",
  "item_name": "Ballpoint Pen",
  "item_group": "Stationery",
  "stock_uom": "Nos",
  "standard_rate": 20.0,
  "description": "Standard ballpoint pen - blue ink",
  "is_stock_item": true,
  "is_sales_item": true,
  "is_purchase_item": false,
  "brand": "Generic",
  "barcode": "1234567890123"
}
```

## Verifying Seeded Products

After seeding, you can verify the products were created correctly:

```javascript
// Get products for your company
const response = await fetch(
  '/api/method/savanna_pos.savanna_pos.apis.product_api.get_products?company=Your%20Company%20Name',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

const { products } = await response.json();
console.log(products);
```

## Updating Existing Products to Global

If you have existing products and want to make them global (available to all industries):

```bash
bench --site [your-site] console
```

```python
import frappe

# Get all products for a company
company = "Your Company Name"
items = frappe.get_all("Item", filters={"custom_company": company}, fields=["name"])

# Set custom_pos_industry to NULL for all
for item in items:
    frappe.db.set_value("Item", item.name, "custom_pos_industry", None)

frappe.db.commit()
print(f"Updated {len(items)} products to global")
```

## Best Practices

1. **Seed after company creation**: Ensure companies exist before seeding products
2. **Use meaningful item codes**: Use a prefix like "GLOBAL-" to identify global products
3. **Group related products**: Use appropriate item groups for organization
4. **Set appropriate prices**: Update standard_rate based on your market
5. **Review before production**: Test seeding in a development environment first

## Troubleshooting

### Error: "No companies found"

**Solution**: Create a company first before seeding products.

### Error: "Company does not exist"

**Solution**: Check the company name spelling and ensure it exists in the system.

### Products not showing up

**Check**:
1. Products are created for the correct company
2. User's company matches the product's company
3. Products have `custom_pos_industry = NULL` (verify in database)
4. Products are not disabled

### Permission Denied

**Solution**: Ensure the user has "System Manager" role to use the seeding endpoint.

## Customizing Default Products

To customize the default products, edit the `get_default_global_products()` function in:
```
savanna_pos/savanna_pos/setup/seed_global_products.py
```

Or use the `products_data` parameter to provide your own list of products.

