# Account Provisioning API Documentation

## Overview

The Account Provisioning API provides comprehensive functionality for managing provisional accounting setup and default provisional accounts for companies. This API helps resolve errors related to missing provisional accounts and automates the configuration process.

### Key Features

- **Status Checking**: Check current provisional accounting configuration
- **Account Management**: Set, list, and manage provisional accounts
- **Autoprovisioning**: Automatically configure missing setups (find existing or create new accounts)
- **Validation**: Comprehensive validation with detailed recommendations
- **Error Resolution**: Tools to resolve common configuration errors

### Quick Start: Autoprovisioning

The fastest way to configure provisional accounting:

```python
import frappe

# Auto-configure (finds existing account or creates new one)
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)

if result["success"]:
    print(f"✓ Configured: {result['data']['account']}")
```

Or use autoprovisioning in your APIs:

```python
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account

is_valid, error, account = validate_and_get_provisional_account(
    company="WEE",
    auto_fix=True  # Automatically provisions if missing
)
```

## Table of Contents

1. [Introduction](#introduction)
2. [Error Resolution](#error-resolution)
3. [Autoprovisioning Guide](#autoprovisioning-guide)
   - [What is Autoprovisioning?](#what-is-autoprovisioning)
   - [Autoprovisioning Methods](#autoprovisioning-methods)
   - [When to Use Autoprovisioning](#when-to-use-autoprovisioning)
4. [API Endpoints](#api-endpoints)
   - [Get Provisional Accounting Status](#get-provisional-accounting-status)
   - [Set Default Provisional Account](#set-default-provisional-account)
   - [List Available Provisional Accounts](#list-available-provisional-accounts)
   - [Auto-Configure Provisional Account](#auto-configure-provisional-account)
   - [Validate Provisional Accounting Setup](#validate-provisional-accounting-setup)
5. [Helper Functions](#helper-functions)
6. [Usage Examples](#usage-examples)
7. [Error Scenarios and Solutions](#error-scenarios-and-solutions)
8. [Best Practices](#best-practices)

---

## Introduction

Provisional accounting is a feature in ERPNext that allows companies to handle non-stock items (services) that are received but not yet billed. When provisional accounting is enabled for a company, a default provisional account must be set to properly account for these transactions.

### Common Error

When provisional accounting is enabled but no default provisional account is set, you may encounter this error:

```json
{
    "message": {
        "success": false,
        "message": "Provisional accounting is enabled for company 'WEE', but 'Default Provisional Account' is not set. Please set it in Company settings (Company > WEE > Default Provisional Account).",
        "error_type": "missing_provisional_account",
        "company": "WEE"
    }
}
```

This API provides tools to resolve this error and manage provisional accounting configuration programmatically.

---

## Autoprovisioning Guide

### What is Autoprovisioning?

Autoprovisioning is the automatic configuration of provisional accounting accounts when they are missing. Instead of requiring manual setup, the system can:

1. **Find existing suitable accounts** - Search for accounts that can be used as provisional accounts
2. **Create new accounts** - Automatically create a provisional account if none exists
3. **Configure the company** - Set the account as default and enable provisional accounting

This eliminates the need for manual intervention when provisional accounting is required but not yet configured.

### Autoprovisioning Methods

There are two main ways to enable autoprovisioning:

#### Method 1: Direct API Call (`auto_configure_provisional_account`)

Use this method when you want explicit control over the provisioning process:

```python
import frappe

# Auto-configure with account creation enabled
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True,  # Creates account if none found
    account_name="Custom Name - WEE"  # Optional: custom account name
)

if result["success"]:
    if result.get("account_created"):
        print(f"✓ New account created: {result['data']['account']}")
    else:
        print(f"✓ Using existing account: {result['data']['account']}")
```

**Workflow:**
1. Checks if already configured → returns immediately if yes
2. Searches for existing accounts with preferred types
3. Creates account if `create_account_if_missing=True` and none found
4. Sets account as default and enables provisional accounting

#### Method 2: Helper Function with Auto-Fix (`validate_and_get_provisional_account`)

Use this method when integrating autoprovisioning into other APIs:

```python
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account

# Enable autoprovisioning via auto_fix parameter
is_valid, error_dict, account = validate_and_get_provisional_account(
    company="WEE",
    auto_fix=True  # Automatically provisions if missing
)

if is_valid:
    if account:
        print(f"Provisional account ready: {account}")
    else:
        print("Provisional accounting not enabled (not an error)")
else:
    print(f"Error: {error_dict['message']}")
```

**Behavior:**
- If provisional accounting is enabled but account missing → calls `auto_configure_provisional_account` with `create_account_if_missing=True`
- If provisional accounting not enabled → returns `(True, None, None)` (no error)
- If account exists → returns `(True, None, account_name)`

### When to Use Autoprovisioning

**✅ Use autoprovisioning when:**
- Building user-facing APIs where seamless experience is important
- Automating setup processes or migrations
- Batch operations that need to handle missing configurations gracefully
- Development/testing environments where automatic setup is acceptable
- You want to reduce manual configuration overhead

**❌ Don't use autoprovisioning when:**
- You need explicit user approval before creating accounts
- Compliance/audit requirements mandate manual account setup
- You want to surface configuration issues to users for awareness
- The API should fail fast on missing configuration
- Account naming/structure requires business-specific decisions

**Example: User-Controlled Autoprovisioning**
```python
@frappe.whitelist()
def create_purchase_receipt_with_autoprovision(
    company: str,
    supplier: str,
    auto_provision: bool = False  # User can opt-in
):
    """Create purchase receipt with optional autoprovisioning."""
    from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account
    
    # Validate with optional autoprovisioning
    is_valid, error_dict, provisional_account = validate_and_get_provisional_account(
        company=company,
        auto_fix=auto_provision
    )
    
    if not is_valid:
        if auto_provision:
            return {
                "success": False,
                "message": "Autoprovisioning failed. Please configure manually.",
                "error": error_dict
            }
        else:
            return {
                "success": False,
                "message": error_dict["message"],
                "suggestion": "Set auto_provision=True to automatically configure"
            }
    
    # Continue with purchase receipt creation
    # ... your logic here
```

---

## Error Resolution

### Quick Fix

The fastest way to resolve the missing provisional account error is to use the auto-configure function:

```python
import frappe

# Auto-configure provisional account for company
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)

if result.get("success"):
    print("Provisional account configured successfully!")
    print(f"Account: {result['data']['account']}")
else:
    print(f"Error: {result['message']}")
```

### Manual Configuration

If you prefer to set a specific account:

```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
    company="WEE",
    account="Service Received But Not Billed - WEE",
    auto_enable_provisional_accounting=True
)
```

---

## API Endpoints

### Get Provisional Accounting Status

Get the current provisional accounting status and configuration for a company.

**Endpoint:** `savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status`

**Parameters:**
- `company` (str, required): Company name/ID

**Returns:**
```json
{
    "success": true,
    "data": {
        "company": "WEE",
        "enable_provisional_accounting": true,
        "default_provisional_account": "Service Received But Not Billed - WEE",
        "account_details": {
            "account_name": "Service Received But Not Billed - WEE",
            "account_type": "Service Received But Not Billed",
            "root_type": "Asset",
            "parent_account": "Current Assets - WEE"
        },
        "is_valid": true,
        "validation_message": null
    }
}
```

**Example:**
```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status",
    company="WEE"
)

if result["success"]:
    status = result["data"]
    print(f"Provisional accounting enabled: {status['enable_provisional_accounting']}")
    print(f"Default account: {status['default_provisional_account']}")
    print(f"Is valid: {status['is_valid']}")
```

---

### Set Default Provisional Account

Set or update the default provisional account for a company.

**Endpoint:** `savanna_pos.apis.account_provisioning_api.set_default_provisional_account`

**Parameters:**
- `company` (str, required): Company name/ID
- `account` (str, required): Account name/ID to set as default provisional account
- `auto_enable_provisional_accounting` (bool, optional): If True, enables provisional accounting if not already enabled (default: False)

**Returns:**
```json
{
    "success": true,
    "message": "Default provisional account set successfully",
    "data": {
        "company": "WEE",
        "account": "Service Received But Not Billed - WEE",
        "account_name": "Service Received But Not Billed - WEE",
        "account_type": "Service Received But Not Billed",
        "root_type": "Asset",
        "provisional_accounting_enabled": true
    },
    "warnings": []
}
```

**Example:**
```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
    company="WEE",
    account="Service Received But Not Billed - WEE",
    auto_enable_provisional_accounting=True
)

if result["success"]:
    print(f"Account set: {result['data']['account']}")
    if result.get("warnings"):
        print("Warnings:", result["warnings"])
```

**Error Responses:**

- **Company not found:**
```json
{
    "success": false,
    "message": "Company 'WEE' not found",
    "error_type": "company_not_found"
}
```

- **Account not found:**
```json
{
    "success": false,
    "message": "Account 'Invalid Account' not found",
    "error_type": "account_not_found"
}
```

- **Account company mismatch:**
```json
{
    "success": false,
    "message": "Account 'Account Name' does not belong to company 'WEE'",
    "error_type": "account_company_mismatch"
}
```

- **Group account error:**
```json
{
    "success": false,
    "message": "Account 'Account Name' is a group account. Please select a ledger account.",
    "error_type": "group_account_error"
}
```

---

### List Available Provisional Accounts

List available accounts that can be used as provisional accounts for a company.

**Endpoint:** `savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts`

**Parameters:**
- `company` (str, required): Company name/ID
- `account_type` (str, optional): Filter by account type (e.g., "Service Received But Not Billed")
- `search_term` (str, optional): Search term for account name
- `limit` (int, optional): Number of records to return (default: 50)
- `offset` (int, optional): Offset for pagination (default: 0)

**Returns:**
```json
{
    "success": true,
    "data": [
        {
            "name": "Service Received But Not Billed - WEE",
            "account_name": "Service Received But Not Billed - WEE",
            "account_type": "Service Received But Not Billed",
            "root_type": "Asset",
            "parent_account": "Current Assets - WEE",
            "is_recommended": true
        },
        {
            "name": "Asset Received But Not Billed - WEE",
            "account_name": "Asset Received But Not Billed - WEE",
            "account_type": "Asset Received But Not Billed",
            "root_type": "Asset",
            "parent_account": "Current Assets - WEE",
            "is_recommended": true
        }
    ],
    "count": 2,
    "recommended_types": [
        "Service Received But Not Billed",
        "Asset Received But Not Billed",
        "Expense Account",
        "Indirect Expense",
        "Direct Expense"
    ]
}
```

**Example:**
```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company="WEE",
    search_term="Service",
    limit=10
)

if result["success"]:
    accounts = result["data"]
    print(f"Found {result['count']} accounts")
    for account in accounts:
        recommended = "✓ Recommended" if account.get("is_recommended") else ""
        print(f"- {account['account_name']} ({account['account_type']}) {recommended}")
```

---

### Auto-Configure Provisional Account

Automatically configure provisional account for a company. This function will:
1. Look for existing suitable accounts
2. Optionally create a new account if none found
3. Set it as the default provisional account
4. Enable provisional accounting

**Endpoint:** `savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account`

**Parameters:**
- `company` (str, required): Company name/ID
- `create_account_if_missing` (bool, optional): If True, creates a new account if no suitable one exists (default: False)
- `account_name` (str, optional): Name for the new account if creating (optional, uses default if not provided)

**Returns:**
```json
{
    "success": true,
    "message": "Provisional account auto-configured successfully",
    "auto_configured": true,
    "account_created": true,
    "data": {
        "company": "WEE",
        "account": "Service Received But Not Billed - WEE",
        "account_name": "Service Received But Not Billed - WEE",
        "account_type": "Service Received But Not Billed",
        "root_type": "Asset",
        "provisional_accounting_enabled": true
    }
}
```

**Example:**
```python
# Auto-configure with account creation
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)

if result["success"]:
    print("✓ Provisional accounting configured")
    if result.get("account_created"):
        print(f"✓ Account created: {result['data']['account']}")
    else:
        print(f"✓ Using existing account: {result['data']['account']}")
```

**Note:** If the company already has provisional accounting configured, the function will return early with a success message indicating it's already configured.

#### Autoprovisioning Workflow

The `auto_configure_provisional_account` function follows this workflow:

1. **Check Existing Configuration**
   - If provisional accounting is already enabled and a default account is set, returns immediately with success

2. **Search for Existing Accounts**
   - Searches for accounts with preferred types in this order:
     - `Service Received But Not Billed` (highest priority)
     - `Asset Received But Not Billed`
   - Only considers active, non-group ledger accounts belonging to the company

3. **Create Account (if requested)**
   - If `create_account_if_missing=True` and no suitable account found:
     - Determines parent account (looks for "Current Assets - {company_abbr}" or any Current Asset group)
     - Creates account with type "Service Received But Not Billed"
     - Uses provided `account_name` or defaults to "Service Received But Not Billed - {company_abbr}"

4. **Configure and Enable**
   - Sets the found/created account as default provisional account
   - Enables provisional accounting for the company
   - Returns configuration details

**Example with Full Workflow:**
```python
# Step 1: Check if already configured
status = frappe.call(
    "savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status",
    company="WEE"
)

if not status["data"]["is_valid"]:
    # Step 2: Auto-configure (will find existing or create new)
    result = frappe.call(
        "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
        company="WEE",
        create_account_if_missing=True,
        account_name="Custom Provisional Account - WEE"  # Optional custom name
    )
    
    if result["success"]:
        if result.get("account_created"):
            print(f"✓ New account created: {result['data']['account']}")
        else:
            print(f"✓ Using existing account: {result['data']['account']}")
```

---

### Autoprovisioning in Helper Functions

The `validate_and_get_provisional_account` helper function supports autoprovisioning through the `auto_fix` parameter. This is useful when integrating provisional account validation into other APIs.

#### Using Auto-Fix

When `auto_fix=True`, the helper function will automatically attempt to configure a missing provisional account:

```python
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account

# With auto-fix enabled
is_valid, error_dict, account = validate_and_get_provisional_account(
    company="WEE",
    auto_fix=True  # Automatically configures if missing
)

if is_valid:
    print(f"Provisional account ready: {account}")
    # Use account in your transaction
else:
    print(f"Error: {error_dict['message']}")
    # Handle error (auto-fix failed or provisional accounting not enabled)
```

#### Autoprovisioning Behavior

When `auto_fix=True`:
- **If provisional accounting is enabled but account is missing:**
  - Calls `auto_configure_provisional_account` with `create_account_if_missing=True`
  - If successful, returns the newly configured account
  - If failed, returns error dictionary

- **If provisional accounting is not enabled:**
  - Returns `(True, None, None)` - no error, no account needed

- **If account exists and is valid:**
  - Returns `(True, None, account_name)` - ready to use

#### Integration Example

Here's how to integrate autoprovisioning into your own API:

```python
@frappe.whitelist()
def my_custom_api(company: str, enable_autoprovisioning: bool = False):
    """
    Custom API that requires provisional account.
    
    Args:
        company: Company name
        enable_autoprovisioning: If True, automatically provisions account if missing
    """
    from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account
    
    # Validate with optional auto-fix
    is_valid, error_dict, provisional_account = validate_and_get_provisional_account(
        company=company,
        auto_fix=enable_autoprovisioning
    )
    
    if not is_valid:
        # Return error if autoprovisioning is disabled or failed
        return error_dict
    
    # Check if provisional accounting is needed
    if provisional_account:
        # Provisional accounting is enabled and account is available
        print(f"Using provisional account: {provisional_account}")
        # Continue with your logic using the account
    else:
        # Provisional accounting not enabled (not an error)
        print("Provisional accounting not enabled for this company")
        # Continue with your logic
    
    # Your API logic here
    return {"success": True, "provisional_account": provisional_account}
```

#### When to Use Autoprovisioning

**Use autoprovisioning (`auto_fix=True`) when:**
- Building user-facing APIs where seamless experience is important
- Automating setup processes
- Batch operations that need to handle missing configurations gracefully
- Development/testing environments where automatic setup is acceptable

**Don't use autoprovisioning when:**
- You need explicit user approval before creating accounts
- Compliance requires manual account setup
- You want to surface configuration issues to users
- The API should fail fast on missing configuration

**Example: Conditional Autoprovisioning**
```python
# Allow users to opt-in to autoprovisioning
@frappe.whitelist()
def create_transaction(company: str, auto_provision: bool = False):
    is_valid, error_dict, account = validate_and_get_provisional_account(
        company=company,
        auto_fix=auto_provision  # User-controlled
    )
    
    if not is_valid:
        if auto_provision:
            # Autoprovisioning was attempted but failed
            return {
                "success": False,
                "message": "Autoprovisioning failed. Please configure manually.",
                "error": error_dict
            }
        else:
            # Suggest enabling autoprovisioning
            return {
                "success": False,
                "message": error_dict["message"],
                "suggestion": "Set auto_provision=True to automatically configure"
            }
```

---

### Validate Provisional Accounting Setup

Validate the provisional accounting setup for a company and get detailed validation results with recommendations.

**Endpoint:** `savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup`

**Parameters:**
- `company` (str, required): Company name/ID

**Returns:**
```json
{
    "success": true,
    "data": {
        "company": "WEE",
        "enable_provisional_accounting": true,
        "default_provisional_account": "Service Received But Not Billed - WEE",
        "is_valid": true,
        "issues": [],
        "recommendations": [],
        "warnings": [],
        "account_details": {
            "account_name": "Service Received But Not Billed - WEE",
            "account_type": "Service Received But Not Billed",
            "root_type": "Asset",
            "is_group": false,
            "disabled": false,
            "company": "WEE"
        }
    }
}
```

**Example with Issues:**
```json
{
    "success": true,
    "data": {
        "company": "WEE",
        "enable_provisional_accounting": true,
        "default_provisional_account": null,
        "is_valid": false,
        "issues": [
            "Provisional accounting is enabled but 'Default Provisional Account' is not set."
        ],
        "recommendations": [
            "Use 'set_default_provisional_account' API to set a default account, or use 'auto_configure_provisional_account' to auto-configure."
        ],
        "warnings": []
    }
}
```

**Example:**
```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
    company="WEE"
)

if result["success"]:
    validation = result["data"]
    
    if validation["is_valid"]:
        print("✓ Provisional accounting setup is valid")
    else:
        print("✗ Issues found:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
        
        if validation["recommendations"]:
            print("\nRecommendations:")
            for rec in validation["recommendations"]:
                print(f"  - {rec}")
        
        if validation["warnings"]:
            print("\nWarnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
```

---

## Helper Functions

### validate_and_get_provisional_account

This helper function is used internally by other APIs (like `create_purchase_receipt`) to validate provisional accounting setup. It can also be used directly if needed.

**Function Signature:**
```python
validate_and_get_provisional_account(company: str, auto_fix: bool = False) -> tuple[bool, Optional[Dict], Optional[str]]
```

**Parameters:**
- `company` (str): Company name/ID
- `auto_fix` (bool): If True, attempts to auto-configure if missing (default: False)

**Returns:**
- `tuple[bool, Optional[Dict], Optional[str]]`: 
  - `is_valid`: Whether the setup is valid
  - `error_dict`: Error dictionary if invalid, None if valid
  - `account_name`: Account name if valid, None if invalid

**Example Usage:**
```python
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account

is_valid, error_dict, account = validate_and_get_provisional_account(
    company="WEE",
    auto_fix=True
)

if not is_valid:
    print(f"Error: {error_dict['message']}")
else:
    print(f"Provisional account: {account}")
```

---

## Usage Examples

### Example 1: Resolve Missing Provisional Account Error

When you encounter the missing provisional account error, use auto-configure:

```python
import frappe

def resolve_provisional_account_error(company):
    """Resolve missing provisional account error for a company."""
    # First, check current status
    status = frappe.call(
        "savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status",
        company=company
    )
    
    if not status["data"]["is_valid"]:
        # Auto-configure if invalid
        result = frappe.call(
            "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
            company=company,
            create_account_if_missing=True
        )
        
        if result["success"]:
            print(f"✓ Resolved: {result['message']}")
            return result
        else:
            print(f"✗ Failed: {result['message']}")
            return result
    else:
        print("✓ Provisional accounting is already properly configured")
        return status

# Usage
resolve_provisional_account_error("WEE")
```

### Example 2: Set Up Provisional Accounting for Multiple Companies

```python
def setup_provisional_accounting_for_companies(companies):
    """Set up provisional accounting for multiple companies."""
    results = {}
    
    for company in companies:
        print(f"\nProcessing company: {company}")
        
        # Validate setup
        validation = frappe.call(
            "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
            company=company
        )
        
        if not validation["data"]["is_valid"]:
            # List available accounts
            accounts = frappe.call(
                "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
                company=company
            )
            
            if accounts["success"] and accounts["data"]:
                # Use first recommended account
                recommended_account = next(
                    (acc for acc in accounts["data"] if acc.get("is_recommended")),
                    accounts["data"][0]
                )
                
                # Set default account
                result = frappe.call(
                    "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
                    company=company,
                    account=recommended_account["name"],
                    auto_enable_provisional_accounting=True
                )
                
                results[company] = result
            else:
                # Auto-create account
                result = frappe.call(
                    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
                    company=company,
                    create_account_if_missing=True
                )
                results[company] = result
        else:
            results[company] = {"success": True, "message": "Already configured"}
    
    return results

# Usage
companies = ["WEE", "Company 2", "Company 3"]
results = setup_provisional_accounting_for_companies(companies)

for company, result in results.items():
    status = "✓" if result.get("success") else "✗"
    print(f"{status} {company}: {result.get('message', 'Unknown')}")
```

### Example 3: Validate All Companies

```python
def validate_all_companies_provisional_accounting():
    """Validate provisional accounting setup for all companies."""
    companies = frappe.get_all("Company", fields=["name"])
    
    validation_results = []
    
    for company in companies:
        company_name = company["name"]
        
        result = frappe.call(
            "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
            company=company_name
        )
        
        validation_results.append({
            "company": company_name,
            **result["data"]
        })
    
    # Print summary
    valid_count = sum(1 for v in validation_results if v["is_valid"])
    invalid_count = len(validation_results) - valid_count
    
    print(f"\nValidation Summary:")
    print(f"Total companies: {len(validation_results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")
    
    if invalid_count > 0:
        print("\nInvalid companies:")
        for v in validation_results:
            if not v["is_valid"]:
                print(f"\n  {v['company']}:")
                for issue in v["issues"]:
                    print(f"    - {issue}")
    
    return validation_results

# Usage
validation_results = validate_all_companies_provisional_accounting()
```

---

## Error Scenarios and Solutions

### Scenario 1: Missing Provisional Account

**Error:**
```json
{
    "error_type": "missing_provisional_account",
    "message": "Provisional accounting is enabled for company 'WEE', but 'Default Provisional Account' is not set..."
}
```

**Solution:**
```python
result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)
```

### Scenario 2: Invalid Account Type

**Error:** Account type is not appropriate for provisional accounting

**Solution:**
```python
# List recommended accounts
accounts = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company="WEE"
)

# Use a recommended account
recommended = next(acc for acc in accounts["data"] if acc.get("is_recommended"))

result = frappe.call(
    "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
    company="WEE",
    account=recommended["name"]
)
```

### Scenario 3: Disabled Account

**Error:** Default provisional account is disabled

**Solution:**
```python
# Validate to see the issue
validation = frappe.call(
    "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
    company="WEE"
)

# Find a new account
accounts = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company="WEE"
)

# Set a new active account
if accounts["data"]:
    new_account = accounts["data"][0]["name"]
    frappe.call(
        "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
        company="WEE",
        account=new_account
    )
```

### Scenario 4: Account Belongs to Different Company

**Error:** Account does not belong to the specified company

**Solution:**
```python
# Use list_available_provisional_accounts to ensure company match
accounts = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company="WEE"
)

# Accounts returned are guaranteed to belong to the company
if accounts["data"]:
    account = accounts["data"][0]["name"]
    frappe.call(
        "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
        company="WEE",
        account=account
    )
```

---

## Best Practices

### 1. Always Validate Before Operations

Before performing operations that require provisional accounting, validate the setup:

```python
validation = frappe.call(
    "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
    company=company
)

if not validation["data"]["is_valid"]:
    # Fix issues before proceeding
    auto_configure_result = frappe.call(
        "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
        company=company,
        create_account_if_missing=True
    )
```

### 2. Use Recommended Account Types

When selecting accounts, prefer recommended types:
- `Service Received But Not Billed` (most common)
- `Asset Received But Not Billed`

```python
accounts = frappe.call(
    "savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts",
    company=company
)

# Filter for recommended accounts
recommended = [acc for acc in accounts["data"] if acc.get("is_recommended")]
```

### 3. Enable Auto-Fix in Production APIs

When using the helper function in your APIs, consider enabling auto-fix for a better user experience:

```python
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account

# In your API function
is_valid, error_dict, account = validate_and_get_provisional_account(
    company=company,
    auto_fix=True  # Automatically fixes if possible
)
```

### 4. Monitor Configuration Status

Regularly validate all companies' provisional accounting setup:

```python
# Schedule this as a background job
companies = frappe.get_all("Company", fields=["name"])

for company in companies:
    validation = frappe.call(
        "savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup",
        company=company["name"]
    )
    
    if not validation["data"]["is_valid"]:
        # Log or send notification
        frappe.log_error(
            f"Invalid provisional accounting setup for {company['name']}",
            "Provisional Accounting Validation"
        )
```

### 5. Handle Errors Gracefully

Always handle errors appropriately in your code:

```python
try:
    result = frappe.call(
        "savanna_pos.apis.account_provisioning_api.set_default_provisional_account",
        company=company,
        account=account
    )
    
    if not result["success"]:
        error_type = result.get("error_type")
        
        if error_type == "account_not_found":
            # Try to list available accounts
            pass
        elif error_type == "group_account_error":
            # User selected a group account, suggest a ledger account
            pass
        else:
            # General error handling
            pass
except Exception as e:
    frappe.log_error(f"Error: {str(e)}", "Account Provisioning Error")
```

---

## Integration with Existing APIs

The account provisioning validation is now integrated into the `create_purchase_receipt` API. When you call this API, it will automatically validate provisional accounting setup and return a helpful error if configuration is missing:

```python
# This will now automatically validate provisional accounting
result = frappe.call(
    "savanna_pos.apis.apis.create_purchase_receipt",
    supplier="Supplier 1",
    company="WEE",
    items=[{"item_code": "Item 1", "qty": 1, "rate": 100}]
)

# If provisional account is missing, you'll get a clear error:
# {
#     "success": false,
#     "error_type": "missing_provisional_account",
#     "message": "...",
#     "company": "WEE"
# }
```

---

## Summary

The Account Provisioning API provides:

1. **Status Checking**: Check current provisional accounting configuration
2. **Account Management**: Set, list, and manage provisional accounts
3. **Autoprovisioning**: Automatically configure missing setups (find existing accounts or create new ones)
4. **Validation**: Comprehensive validation with detailed recommendations
5. **Error Resolution**: Tools to resolve common configuration errors

### Autoprovisioning Highlights

**Two Methods Available:**

1. **Direct API Call** - `auto_configure_provisional_account`:
   - Finds existing suitable accounts or creates new ones
   - Fully configures the company automatically
   - Best for one-time setup or explicit provisioning

2. **Helper Function** - `validate_and_get_provisional_account` with `auto_fix=True`:
   - Integrates seamlessly into other APIs
   - Automatically provisions when validation fails
   - Best for production APIs requiring seamless user experience

**Quick Example:**
```python
# Method 1: Direct provisioning
frappe.call(
    "savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account",
    company="WEE",
    create_account_if_missing=True
)

# Method 2: Integrated autoprovisioning
from savanna_pos.apis.account_provisioning_api import validate_and_get_provisional_account
is_valid, error, account = validate_and_get_provisional_account(
    company="WEE",
    auto_fix=True
)
```

Use these APIs to ensure your provisional accounting setup is always properly configured and to resolve errors proactively. Autoprovisioning eliminates manual configuration overhead while maintaining flexibility for compliance-sensitive environments.

---

## Support

For issues or questions related to account provisioning APIs, please refer to:
- ERPNext Documentation: [Provisional Accounting](https://docs.erpnext.com/docs/user/manual/en/accounts/provisional-accounting)
- Company Settings: Company > [Company Name] > Default Provisional Account

---

**Last Updated:** 2024
**Version:** 1.0.0
