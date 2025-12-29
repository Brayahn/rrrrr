# Account Provisioning - Quick Start Guide

## Problem

You're encountering this error:
```json
{
    "success": false,
    "message": "Provisional accounting is enabled for company 'WEE', but 'Default Provisional Account' is not set...",
    "error_type": "missing_provisional_account",
    "company": "WEE"
}
```

## Quick Solution

### Option 1: Auto-Configure (Recommended)

The easiest way to fix this is to use the auto-configure function which will:
- Find an existing suitable account, OR
- Create a new account if none exists
- Set it as the default provisional account
- Enable provisional accounting

```python
import frappe

result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)

if result["success"]:
    print("✓ Fixed! Provisional account configured.")
    print(f"Account: {result['data']['account']}")
```

### Option 2: Set Specific Account

If you want to use a specific existing account:

```python
import frappe

# First, list available accounts
accounts = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company="WEE"
)

# Select an account (preferably one marked as recommended)
account_name = accounts["data"][0]["name"]

# Set it as default
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
    company="WEE",
    account=account_name,
    auto_enable_provisional_accounting=True
)
```

## Check Status

To check the current status:

```python
import frappe

status = frappe.call(
    "savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status",
    company="WEE"
)

print(f"Enabled: {status['data']['enable_provisional_accounting']}")
print(f"Account: {status['data']['default_provisional_account']}")
print(f"Valid: {status['data']['is_valid']}")
```

## Validate Setup

To get detailed validation results:

```python
import frappe

validation = frappe.call(
    "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
    company="WEE"
)

if not validation["data"]["is_valid"]:
    print("Issues found:")
    for issue in validation["data"]["issues"]:
        print(f"  - {issue}")
    
    print("\nRecommendations:")
    for rec in validation["data"]["recommendations"]:
        print(f"  - {rec}")
```

## Available APIs

1. **`get_provisional_accounting_status`** - Get current configuration
2. **`set_default_provisional_account`** - Set/update default account
3. **`list_available_provisional_accounts`** - List suitable accounts
4. **`auto_configure_provisional_account`** - Auto-configure (recommended for quick fix)
5. **`validate_provisional_accounting_setup`** - Validate with detailed feedback

## Documentation

For detailed documentation, see: [ACCOUNT_PROVISIONING_API_DOCUMENTATION.md](./ACCOUNT_PROVISIONING_API_DOCUMENTATION.md)

## Integration

The error handling is now integrated into the `create_purchase_receipt` API. The API will automatically validate provisional accounting and return a helpful error if configuration is missing.
