# Inventory Discount API Documentation

Complete API reference for managing inventory-level discounts in Savanna POS. Discounts can be applied to single items, batches, or item groups (categories) and are automatically applied during invoice creation.

## Base URL

All endpoints are exposed as whitelisted methods under:
```
/api/method/savanna_pos.savanna_pos.apis.inventory_api.<method>
```

## Authentication

All endpoints require authentication. Include session cookies or use Frappe's authentication headers in your requests.

## TypeScript Type Definitions

```typescript
// Discount Rule Types
type RuleType = "Batch" | "Item" | "Item Group";
type DiscountType = "Percentage" | "Amount";

// Inventory Discount Rule
interface InventoryDiscountRule {
  name: string;
  rule_type: RuleType;
  item_code?: string;
  batch_no?: string;
  item_group?: string;
  warehouse?: string;
  company: string;
  discount_type: DiscountType;
  discount_value: number;
  priority: number;
  is_active: number; // 0 or 1
  valid_from?: string; // ISO date string
  valid_upto?: string; // ISO date string
  description?: string;
}

// API Response Wrapper
interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
  error_type?: string;
}

// Pagination Info
interface PaginationInfo {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// Bulk Discount Item Request
interface BulkDiscountItem {
  item_code: string;
  batch_no?: string;
  warehouse?: string;
  item_group?: string;
}

// Bulk Discount Result
interface BulkDiscountResult {
  item_code: string;
  batch_no?: string;
  warehouse?: string;
  item_group?: string;
  rule: InventoryDiscountRule | null;
}
```

## Data Model

### Priority Order

Discount rules are applied with the following priority (most specific first):
1. **Batch** - Highest priority (most specific)
2. **Item** - Medium priority
3. **Item Group** - Lowest priority (least specific)

Within the same rule type, lower `priority` number wins (default is 10).

### Rule Fields

- **rule_type** (required): `Batch`, `Item`, or `Item Group`
- **company** (required): Company name
- **discount_type** (required): `Percentage` or `Amount`
- **discount_value** (required): Numeric value (0-100 for percentage, any positive number for amount)
- **priority** (optional): Integer, default 10 (lower = higher priority)
- **is_active** (optional): 0 or 1, default 1
- **warehouse** (optional): Warehouse name (leave empty for all warehouses)
- **valid_from** (optional): Start date (ISO format: YYYY-MM-DD)
- **valid_upto** (optional): End date (ISO format: YYYY-MM-DD)
- **description** (optional): Free text description

### Conditional Fields

Based on `rule_type`:
- If `rule_type = "Item"`: `item_code` is required
- If `rule_type = "Batch"`: `batch_no` is required
- If `rule_type = "Item Group"`: `item_group` is required

---

## API Endpoints

### 1. Create Inventory Discount Rule

Creates a new discount rule for items, batches, or item groups.

**Endpoint:** `create_inventory_discount_rule`  
**Method:** `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rule_type` | `RuleType` | Yes | `"Batch"`, `"Item"`, or `"Item Group"` |
| `company` | `string` | Yes | Company name |
| `discount_type` | `DiscountType` | Yes | `"Percentage"` or `"Amount"` |
| `discount_value` | `number` | Yes | Discount value (0-100 for percentage) |
| `item_code` | `string` | Conditional | Required if `rule_type = "Item"` |
| `batch_no` | `string` | Conditional | Required if `rule_type = "Batch"` |
| `item_group` | `string` | Conditional | Required if `rule_type = "Item Group"` |
| `warehouse` | `string` | No | Warehouse name (optional) |
| `priority` | `number` | No | Priority (default: 10) |
| `is_active` | `number` | No | 0 or 1 (default: 1) |
| `valid_from` | `string` | No | Start date (YYYY-MM-DD) |
| `valid_upto` | `string` | No | End date (YYYY-MM-DD) |
| `description` | `string` | No | Description text |

#### Response

```typescript
ApiResponse<InventoryDiscountRule>
```

#### Example

```typescript
// Create a 10% discount for all items in "Beverages" group
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.create_inventory_discount_rule",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include", // Include session cookies
    body: JSON.stringify({
      rule_type: "Item Group",
      item_group: "Beverages",
      company: "My Company",
      discount_type: "Percentage",
      discount_value: 10,
      priority: 5,
      is_active: 1,
      description: "10% off all beverages",
    }),
  }
);

const result: ApiResponse<InventoryDiscountRule> = await response.json();
if (result.success) {
  console.log("Rule created:", result.data);
} else {
  console.error("Error:", result.message);
}
```

---

### 2. Update Inventory Discount Rule

Updates an existing discount rule. All parameters except `name` are optional.

**Endpoint:** `update_inventory_discount_rule`  
**Method:** `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Rule name/ID to update |
| `rule_type` | `RuleType` | No | Rule type |
| `company` | `string` | No | Company name |
| `discount_type` | `DiscountType` | No | Discount type |
| `discount_value` | `number` | No | Discount value |
| `item_code` | `string` | No | Item code |
| `batch_no` | `string` | No | Batch number |
| `item_group` | `string` | No | Item group |
| `warehouse` | `string` | No | Warehouse name |
| `priority` | `number` | No | Priority |
| `is_active` | `number` | No | Active status (0 or 1) |
| `valid_from` | `string` | No | Start date |
| `valid_upto` | `string` | No | End date |
| `description` | `string` | No | Description |

#### Response

```typescript
ApiResponse<InventoryDiscountRule>
```

#### Example

```typescript
// Update discount value and priority
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.update_inventory_discount_rule",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      name: "INV-DISC-00001",
      discount_value: 15,
      priority: 3,
    }),
  }
);

const result: ApiResponse<InventoryDiscountRule> = await response.json();
```

---

### 3. Delete Inventory Discount Rule

Deletes a discount rule.

**Endpoint:** `delete_inventory_discount_rule`  
**Method:** `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Rule name/ID to delete |

#### Response

```typescript
ApiResponse<null>
```

#### Example

```typescript
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.delete_inventory_discount_rule",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      name: "INV-DISC-00001",
    }),
  }
);

const result: ApiResponse<null> = await response.json();
```

---

### 4. Get Inventory Discount Rule

Fetches a single discount rule by name.

**Endpoint:** `get_inventory_discount_rule`  
**Method:** `GET` or `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `string` | Yes | Rule name/ID |

#### Response

```typescript
ApiResponse<InventoryDiscountRule>
```

#### Example

```typescript
// GET request
const response = await fetch(
  `/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_inventory_discount_rule?name=INV-DISC-00001`,
  {
    method: "GET",
    credentials: "include",
  }
);

// POST request (alternative)
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_inventory_discount_rule",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ name: "INV-DISC-00001" }),
  }
);

const result: ApiResponse<InventoryDiscountRule> = await response.json();
```

---

### 5. List Inventory Discount Rules

Lists discount rules with filtering and pagination.

**Endpoint:** `list_inventory_discount_rules`  
**Method:** `GET` or `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rule_type` | `RuleType` | No | Filter by rule type |
| `company` | `string` | No | Filter by company |
| `item_code` | `string` | No | Filter by item code |
| `batch_no` | `string` | No | Filter by batch number |
| `item_group` | `string` | No | Filter by item group |
| `warehouse` | `string` | No | Filter by warehouse |
| `is_active` | `number` | No | Filter by active status (0 or 1) |
| `page` | `number` | No | Page number (default: 1) |
| `page_size` | `number` | No | Items per page (default: 20) |

#### Response

```typescript
ApiResponse<{
  rules: InventoryDiscountRule[];
  pagination: PaginationInfo;
}>
```

#### Example

```typescript
// List all active item group discounts for a company
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.list_inventory_discount_rules",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      rule_type: "Item Group",
      company: "My Company",
      is_active: 1,
      page: 1,
      page_size: 20,
    }),
  }
);

const result = await response.json();
if (result.success) {
  console.log("Rules:", result.data.rules);
  console.log("Total pages:", result.data.pagination.total_pages);
}
```

---

### 6. Get Inventory Discount for Item

Gets the applicable discount rule for a single item (returns best match: Batch > Item > Item Group).

**Endpoint:** `get_inventory_discount_for_item`  
**Method:** `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_code` | `string` | Yes | Item code |
| `company` | `string` | Yes | Company name |
| `warehouse` | `string` | No | Warehouse name |
| `batch_no` | `string` | No | Batch number |
| `item_group` | `string` | No | Item group (auto-fetched if not provided) |
| `posting_date` | `string` | No | Date for validation (YYYY-MM-DD) |

#### Response

```typescript
ApiResponse<InventoryDiscountRule | null>
```

#### Example

```typescript
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.get_inventory_discount_for_item",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      item_code: "ITEM-001",
      company: "My Company",
      warehouse: "Main Warehouse",
      batch_no: "BATCH-123",
    }),
  }
);

const result: ApiResponse<InventoryDiscountRule | null> = await response.json();
if (result.success && result.data) {
  console.log("Applicable discount:", result.data.discount_value, result.data.discount_type);
}
```

---

### 7. Bulk Get Inventory Discounts

Gets applicable discount rules for multiple items in one call. Useful for loading discounts for entire categories or product lists.

**Endpoint:** `bulk_get_inventory_discounts`  
**Method:** `POST`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | `BulkDiscountItem[]` or `string` | Yes | Array of items or JSON string |
| `company` | `string` | Yes | Company name |
| `warehouse` | `string` | No | Default warehouse (can be overridden per item) |
| `posting_date` | `string` | No | Date for validation (YYYY-MM-DD) |

#### Response

```typescript
ApiResponse<BulkDiscountResult[]>
```

#### Example

```typescript
const response = await fetch(
  "/api/method/savanna_pos.savanna_pos.apis.inventory_api.bulk_get_inventory_discounts",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      company: "My Company",
      warehouse: "Main Warehouse",
      items: [
        { item_code: "ITEM-001" },
        { item_code: "ITEM-002", item_group: "Beverages" },
        { item_code: "ITEM-003", batch_no: "BATCH-1", warehouse: "Secondary Warehouse" },
      ],
    }),
  }
);

const result = await response.json();
if (result.success) {
  result.data.forEach((item: BulkDiscountResult) => {
    if (item.rule) {
      console.log(`${item.item_code}: ${item.rule.discount_value}% discount`);
    }
  });
}
```

---

## React Usage Examples

### Custom Hook for Inventory Discounts

```typescript
import { useState, useEffect } from "react";

interface UseInventoryDiscountsOptions {
  company: string;
  warehouse?: string;
  items: BulkDiscountItem[];
  posting_date?: string;
}

export function useInventoryDiscounts(options: UseInventoryDiscountsOptions) {
  const [discounts, setDiscounts] = useState<BulkDiscountResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!options.company || !options.items.length) return;

    const fetchDiscounts = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          "/api/method/savanna_pos.savanna_pos.apis.inventory_api.bulk_get_inventory_discounts",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              company: options.company,
              warehouse: options.warehouse,
              items: options.items,
              posting_date: options.posting_date,
            }),
          }
        );

        const result: ApiResponse<BulkDiscountResult[]> = await response.json();
        if (result.success && result.data) {
          setDiscounts(result.data);
        } else {
          setError(result.message);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch discounts");
      } finally {
        setLoading(false);
      }
    };

    fetchDiscounts();
  }, [options.company, options.warehouse, JSON.stringify(options.items), options.posting_date]);

  return { discounts, loading, error };
}

// Usage in component
function ProductList({ company, warehouse }: { company: string; warehouse?: string }) {
  const items = [
    { item_code: "ITEM-001" },
    { item_code: "ITEM-002" },
    { item_code: "ITEM-003" },
  ];

  const { discounts, loading, error } = useInventoryDiscounts({
    company,
    warehouse,
    items,
  });

  if (loading) return <div>Loading discounts...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {discounts.map((item) => (
        <div key={item.item_code}>
          <span>{item.item_code}</span>
          {item.rule && (
            <span>
              {item.rule.discount_value}
              {item.rule.discount_type === "Percentage" ? "%" : " off"}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
```

### API Service Class

```typescript
class InventoryDiscountService {
  private baseUrl = "/api/method/savanna_pos.savanna_pos.apis.inventory_api";

  private async request<T>(
    method: string,
    data?: Record<string, any>
  ): Promise<ApiResponse<T>> {
    const options: RequestInit = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(`${this.baseUrl}.${method}`, options);
    return response.json();
  }

  async createRule(rule: Partial<InventoryDiscountRule>): Promise<ApiResponse<InventoryDiscountRule>> {
    return this.request<InventoryDiscountRule>("create_inventory_discount_rule", rule);
  }

  async updateRule(
    name: string,
    updates: Partial<InventoryDiscountRule>
  ): Promise<ApiResponse<InventoryDiscountRule>> {
    return this.request<InventoryDiscountRule>("update_inventory_discount_rule", {
      name,
      ...updates,
    });
  }

  async deleteRule(name: string): Promise<ApiResponse<null>> {
    return this.request<null>("delete_inventory_discount_rule", { name });
  }

  async getRule(name: string): Promise<ApiResponse<InventoryDiscountRule>> {
    return this.request<InventoryDiscountRule>("get_inventory_discount_rule", { name });
  }

  async listRules(filters: {
    rule_type?: RuleType;
    company?: string;
    item_code?: string;
    batch_no?: string;
    item_group?: string;
    warehouse?: string;
    is_active?: number;
    page?: number;
    page_size?: number;
  }): Promise<ApiResponse<{ rules: InventoryDiscountRule[]; pagination: PaginationInfo }>> {
    return this.request("list_inventory_discount_rules", filters);
  }

  async getDiscountForItem(params: {
    item_code: string;
    company: string;
    warehouse?: string;
    batch_no?: string;
    item_group?: string;
    posting_date?: string;
  }): Promise<ApiResponse<InventoryDiscountRule | null>> {
    return this.request<InventoryDiscountRule | null>("get_inventory_discount_for_item", params);
  }

  async getBulkDiscounts(params: {
    items: BulkDiscountItem[];
    company: string;
    warehouse?: string;
    posting_date?: string;
  }): Promise<ApiResponse<BulkDiscountResult[]>> {
    return this.request<BulkDiscountResult[]>("bulk_get_inventory_discounts", params);
  }
}

// Export singleton instance
export const inventoryDiscountService = new InventoryDiscountService();

// Usage
const result = await inventoryDiscountService.createRule({
  rule_type: "Item Group",
  item_group: "Beverages",
  company: "My Company",
  discount_type: "Percentage",
  discount_value: 10,
});
```

### Applying Discounts in Invoice Creation

```typescript
// When creating a POS invoice, discounts are automatically applied if not provided
async function createInvoice(customer: string, cartItems: CartItem[], company: string) {
  // Map cart items to invoice items (discounts optional - will be auto-applied)
  const items = cartItems.map((item) => ({
    item_code: item.item_code,
    qty: item.qty,
    rate: item.price,
    // discount_percentage and discount_amount are optional
    // If omitted, the backend will automatically apply Inventory Discount Rules
    discount_percentage: item.discount_percentage, // optional
    discount_amount: item.discount_amount, // optional
    warehouse: item.warehouse,
    batch_no: item.batch_no,
  }));

  const response = await fetch(
    "/api/method/savanna_pos.savanna_pos.apis.sales_api.create_pos_invoice",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        customer,
        items,
        company,
        warehouse: "Main Warehouse",
        is_pos: true,
      }),
    }
  );

  const result = await response.json();
  // Discounts have been automatically applied based on Inventory Discount Rules
  return result;
}
```

### Error Handling Utility

```typescript
async function handleApiCall<T>(
  apiCall: () => Promise<ApiResponse<T>>
): Promise<{ data: T | null; error: string | null }> {
  try {
    const result = await apiCall();
    if (result.success && result.data !== undefined) {
      return { data: result.data, error: null };
    } else {
      return { data: null, error: result.message || "Unknown error" };
    }
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : "Network error",
    };
  }
}

// Usage
const { data, error } = await handleApiCall(() =>
  inventoryDiscountService.getDiscountForItem({
    item_code: "ITEM-001",
    company: "My Company",
  })
);

if (error) {
  console.error("Failed to get discount:", error);
} else if (data) {
  console.log("Discount found:", data);
}
```

---

## How Discounts Apply in Sales Flows

When creating invoices via `create_sales_invoice` or `create_pos_invoice`:

1. **If discount fields are provided**: The provided discounts are used as-is
2. **If discount fields are omitted**: The system automatically looks up the best matching `Inventory Discount Rule` using the priority order (Batch > Item > Item Group) and applies it before calculating totals

This means you can:
- **Explicitly set discounts** for manual overrides
- **Omit discounts** to let the system automatically apply inventory discount rules
- **Combine both**: Set discounts for some items, let rules apply to others

---

## Priority and Matching Rules

1. **Rule Type Priority** (checked in order):
   - Batch rules (most specific)
   - Item rules
   - Item Group rules (least specific)

2. **Within same rule type**:
   - Lower `priority` number wins
   - If priorities are equal, most recently modified rule wins

3. **Filtering criteria**:
   - Must match `company`
   - Must be `is_active = 1`
   - Must pass date validation (`valid_from` and `valid_upto` if set)
   - Warehouse must match if specified in rule

4. **Warehouse matching**:
   - Rules with empty `warehouse` apply to all warehouses
   - Rules with specific `warehouse` only apply to that warehouse

---

## Best Practices

1. **Use Item Group rules** for category-wide promotions
2. **Use Item rules** for specific product discounts
3. **Use Batch rules** for batch-specific promotions (e.g., clearance items)
4. **Set appropriate priorities** to control which rules apply when multiple match
5. **Use date ranges** (`valid_from`, `valid_upto`) for time-limited promotions
6. **Use bulk_get_inventory_discounts** when loading discounts for multiple items to reduce API calls
7. **Handle errors gracefully** - always check `success` flag in API responses

---

## Common Use Cases

### 1. Category-wide Sale (10% off all Beverages)

```typescript
await inventoryDiscountService.createRule({
  rule_type: "Item Group",
  item_group: "Beverages",
  company: "My Company",
  discount_type: "Percentage",
  discount_value: 10,
  priority: 5,
  is_active: 1,
  description: "10% off all beverages",
});
```

### 2. Specific Item Discount ($5 off)

```typescript
await inventoryDiscountService.createRule({
  rule_type: "Item",
  item_code: "ITEM-001",
  company: "My Company",
  discount_type: "Amount",
  discount_value: 5,
  priority: 3,
  is_active: 1,
});
```

### 3. Time-limited Promotion

```typescript
await inventoryDiscountService.createRule({
  rule_type: "Item Group",
  item_group: "Electronics",
  company: "My Company",
  discount_type: "Percentage",
  discount_value: 15,
  priority: 1,
  valid_from: "2025-01-01",
  valid_upto: "2025-01-31",
  description: "January sale - 15% off electronics",
});
```

### 4. Warehouse-specific Discount

```typescript
await inventoryDiscountService.createRule({
  rule_type: "Item Group",
  item_group: "Clothing",
  company: "My Company",
  warehouse: "Outlet Store",
  discount_type: "Percentage",
  discount_value: 20,
  priority: 2,
  description: "20% off clothing at outlet store",
});
```
