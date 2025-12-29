# Account Provisioning API - React Integration Guide

Complete TypeScript/React documentation for consuming the Account Provisioning APIs in your React application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [TypeScript Types](#typescript-types)
3. [API Client](#api-client)
4. [React Hooks](#react-hooks)
5. [API Reference](#api-reference)
6. [Error Handling](#error-handling)
7. [Complete Examples](#complete-examples)

---

## Quick Start

### Installation

```bash
# Install dependencies (if not already installed)
npm install axios
# or
yarn add axios
```

### Basic Usage

```typescript
import { useAccountProvisioning } from './hooks/useAccountProvisioning';

function CompanySettings() {
  const { status, loading, error, autoConfigure } = useAccountProvisioning('WEE');

  const handleAutoConfigure = async () => {
    const result = await autoConfigure({ createAccountIfMissing: true });
    if (result.success) {
      console.log('Account configured:', result.data.account);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <p>Status: {status?.is_valid ? 'Valid' : 'Invalid'}</p>
      <button onClick={handleAutoConfigure}>Auto-Configure</button>
    </div>
  );
}
```

---

## TypeScript Types

### Core Types

```typescript
// types/accountProvisioning.ts

/**
 * Base API response structure
 */
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error_type?: string;
  warnings?: string[];
}

/**
 * Provisional accounting status
 */
export interface ProvisionalAccountingStatus {
  company: string;
  enable_provisional_accounting: boolean;
  default_provisional_account: string | null;
  account_details: AccountDetails | null;
  is_valid: boolean;
  validation_message: string | null;
}

/**
 * Account details
 */
export interface AccountDetails {
  account_name: string;
  account_type: string;
  root_type: string;
  parent_account?: string;
  is_group?: boolean;
  disabled?: boolean;
  company?: string;
}

/**
 * Available account for selection
 */
export interface AvailableAccount {
  name: string;
  account_name: string;
  account_type: string;
  root_type: string;
  parent_account: string;
  is_recommended: boolean;
}

/**
 * List accounts response
 */
export interface ListAccountsResponse {
  data: AvailableAccount[];
  count: number;
  recommended_types: string[];
}

/**
 * Set account response
 */
export interface SetAccountResponse {
  company: string;
  account: string;
  account_name: string;
  account_type: string;
  root_type: string;
  provisional_accounting_enabled: boolean;
}

/**
 * Auto-configure response
 */
export interface AutoConfigureResponse {
  company: string;
  account: string;
  account_name: string;
  account_type: string;
  root_type: string;
  provisional_accounting_enabled: boolean;
}

/**
 * Validation results
 */
export interface ValidationResults {
  company: string;
  enable_provisional_accounting: boolean;
  default_provisional_account: string | null;
  is_valid: boolean;
  issues: string[];
  recommendations: string[];
  warnings: string[];
  account_details?: AccountDetails;
}

/**
 * Error types
 */
export type ErrorType =
  | 'company_not_found'
  | 'account_not_found'
  | 'account_company_mismatch'
  | 'group_account_error'
  | 'disabled_account_error'
  | 'missing_provisional_account'
  | 'invalid_provisional_account'
  | 'parent_account_not_found'
  | 'validation_error'
  | 'general_error';

/**
 * API error
 */
export interface ApiError {
  success: false;
  message: string;
  error_type: ErrorType;
  company?: string;
}
```

---

## API Client

### Base API Client

```typescript
// api/accountProvisioningClient.ts

import axios, { AxiosInstance } from 'axios';
import type {
  ApiResponse,
  ProvisionalAccountingStatus,
  ListAccountsResponse,
  SetAccountResponse,
  AutoConfigureResponse,
  ValidationResults,
  AvailableAccount,
} from '../types/accountProvisioning';

const API_BASE = '/api/method/savanna_pos.savanna_pos.apis.account_provisioning_api';

class AccountProvisioningClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '', token?: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) {
      this.client.defaults.headers.common['X-Frappe-CSRF-Token'] = csrfToken;
    }
  }

  /**
   * Get provisional accounting status for a company
   */
  async getStatus(company: string): Promise<ApiResponse<ProvisionalAccountingStatus>> {
    const response = await this.client.get(`${API_BASE}.get_provisional_accounting_status`, {
      params: { company },
    });
    return response.data.message || response.data;
  }

  /**
   * Set default provisional account
   */
  async setDefaultAccount(
    company: string,
    account: string,
    options?: { autoEnable?: boolean }
  ): Promise<ApiResponse<SetAccountResponse>> {
    const response = await this.client.post(`${API_BASE}.set_default_provisional_account`, {
      company,
      account,
      auto_enable_provisional_accounting: options?.autoEnable ?? false,
    });
    return response.data.message || response.data;
  }

  /**
   * List available provisional accounts
   */
  async listAccounts(
    company: string,
    options?: {
      accountType?: string;
      searchTerm?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<ApiResponse<ListAccountsResponse>> {
    const response = await this.client.get(`${API_BASE}.list_available_provisional_accounts`, {
      params: {
        company,
        account_type: options?.accountType,
        search_term: options?.searchTerm,
        limit: options?.limit ?? 50,
        offset: options?.offset ?? 0,
      },
    });
    return response.data.message || response.data;
  }

  /**
   * Auto-configure provisional account (Autoprovisioning)
   */
  async autoConfigure(
    company: string,
    options?: {
      createAccountIfMissing?: boolean;
      accountName?: string;
    }
  ): Promise<ApiResponse<AutoConfigureResponse>> {
    const response = await this.client.post(`${API_BASE}.auto_configure_provisional_account`, {
      company,
      create_account_if_missing: options?.createAccountIfMissing ?? false,
      account_name: options?.accountName,
    });
    return response.data.message || response.data;
  }

  /**
   * Validate provisional accounting setup
   */
  async validate(company: string): Promise<ApiResponse<ValidationResults>> {
    const response = await this.client.get(`${API_BASE}.validate_provisional_accounting_setup`, {
      params: { company },
    });
    return response.data.message || response.data;
  }
}

// Export singleton instance
export const accountProvisioningClient = new AccountProvisioningClient();

// Export class for custom instances
export { AccountProvisioningClient };
```

---

## React Hooks

### Main Hook

```typescript
// hooks/useAccountProvisioning.ts

import { useState, useEffect, useCallback } from 'react';
import { accountProvisioningClient } from '../api/accountProvisioningClient';
import type {
  ApiResponse,
  ProvisionalAccountingStatus,
  SetAccountResponse,
  AutoConfigureResponse,
  ValidationResults,
  AvailableAccount,
  ListAccountsResponse,
} from '../types/accountProvisioning';

interface UseAccountProvisioningOptions {
  autoFetch?: boolean;
  onError?: (error: Error) => void;
}

export function useAccountProvisioning(
  company: string | null,
  options: UseAccountProvisioningOptions = {}
) {
  const { autoFetch = true, onError } = options;

  const [status, setStatus] = useState<ProvisionalAccountingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Fetch status
  const fetchStatus = useCallback(async () => {
    if (!company) return;

    setLoading(true);
    setError(null);

    try {
      const response = await accountProvisioningClient.getStatus(company);
      if (response.success && response.data) {
        setStatus(response.data);
      } else {
        throw new Error(response.message || 'Failed to fetch status');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [company, onError]);

  // Auto-configure
  const autoConfigure = useCallback(
    async (options?: { createAccountIfMissing?: boolean; accountName?: string }) => {
      if (!company) throw new Error('Company is required');

      setLoading(true);
      setError(null);

      try {
        const response = await accountProvisioningClient.autoConfigure(company, options);
        if (response.success) {
          // Refresh status after configuration
          await fetchStatus();
          return response;
        } else {
          throw new Error(response.message || 'Auto-configuration failed');
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [company, fetchStatus, onError]
  );

  // Set default account
  const setDefaultAccount = useCallback(
    async (account: string, autoEnable?: boolean) => {
      if (!company) throw new Error('Company is required');

      setLoading(true);
      setError(null);

      try {
        const response = await accountProvisioningClient.setDefaultAccount(company, account, {
          autoEnable,
        });
        if (response.success) {
          await fetchStatus();
          return response;
        } else {
          throw new Error(response.message || 'Failed to set account');
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [company, fetchStatus, onError]
  );

  // Validate setup
  const validate = useCallback(async () => {
    if (!company) throw new Error('Company is required');

    setLoading(true);
    setError(null);

    try {
      const response = await accountProvisioningClient.validate(company);
      if (response.success && response.data) {
        return response.data;
      } else {
        throw new Error(response.message || 'Validation failed');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [company, onError]);

  useEffect(() => {
    if (autoFetch && company) {
      fetchStatus();
    }
  }, [autoFetch, company, fetchStatus]);

  return {
    status,
    loading,
    error,
    refetch: fetchStatus,
    autoConfigure,
    setDefaultAccount,
    validate,
  };
}
```

### Accounts List Hook

```typescript
// hooks/useAvailableAccounts.ts

import { useState, useEffect, useCallback } from 'react';
import { accountProvisioningClient } from '../api/accountProvisioningClient';
import type { AvailableAccount, ApiResponse, ListAccountsResponse } from '../types/accountProvisioning';

interface UseAvailableAccountsOptions {
  accountType?: string;
  searchTerm?: string;
  limit?: number;
  autoFetch?: boolean;
}

export function useAvailableAccounts(
  company: string | null,
  options: UseAvailableAccountsOptions = {}
) {
  const { accountType, searchTerm, limit = 50, autoFetch = false } = options;

  const [accounts, setAccounts] = useState<AvailableAccount[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAccounts = useCallback(async () => {
    if (!company) return;

    setLoading(true);
    setError(null);

    try {
      const response = await accountProvisioningClient.listAccounts(company, {
        accountType,
        searchTerm,
        limit,
      });

      if (response.success && response.data) {
        setAccounts(response.data.data || []);
        setCount(response.data.count || 0);
      } else {
        throw new Error(response.message || 'Failed to fetch accounts');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [company, accountType, searchTerm, limit]);

  useEffect(() => {
    if (autoFetch && company) {
      fetchAccounts();
    }
  }, [autoFetch, company, fetchAccounts]);

  return {
    accounts,
    count,
    loading,
    error,
    refetch: fetchAccounts,
  };
}
```

---

## API Reference

### 1. Get Provisional Accounting Status

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.account_provisioning_api.get_provisional_accounting_status`

**Parameters:**
```typescript
{
  company: string; // Required
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    company: string;
    enable_provisional_accounting: boolean;
    default_provisional_account: string | null;
    account_details: AccountDetails | null;
    is_valid: boolean;
    validation_message: string | null;
  }
}
```

**Example:**
```typescript
const response = await accountProvisioningClient.getStatus('WEE');
if (response.success) {
  console.log('Status:', response.data);
}
```

---

### 2. Set Default Provisional Account

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.account_provisioning_api.set_default_provisional_account`

**Parameters:**
```typescript
{
  company: string; // Required
  account: string; // Required
  auto_enable_provisional_accounting?: boolean; // Default: false
}
```

**Response:**
```typescript
{
  success: true,
  message: string;
  data: {
    company: string;
    account: string;
    account_name: string;
    account_type: string;
    root_type: string;
    provisional_accounting_enabled: boolean;
  };
  warnings?: string[];
}
```

**Example:**
```typescript
const response = await accountProvisioningClient.setDefaultAccount(
  'WEE',
  'Service Received But Not Billed - WEE',
  { autoEnable: true }
);
```

---

### 3. List Available Provisional Accounts

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.account_provisioning_api.list_available_provisional_accounts`

**Parameters:**
```typescript
{
  company: string; // Required
  account_type?: string; // Optional filter
  search_term?: string; // Optional search
  limit?: number; // Default: 50
  offset?: number; // Default: 0
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    data: AvailableAccount[];
    count: number;
    recommended_types: string[];
  }
}
```

**Example:**
```typescript
const response = await accountProvisioningClient.listAccounts('WEE', {
  searchTerm: 'Service',
  limit: 20,
});
```

---

### 4. Auto-Configure Provisional Account (Autoprovisioning)

**Endpoint:** `POST /api/method/savanna_pos.savanna_pos.apis.account_provisioning_api.auto_configure_provisional_account`

**Parameters:**
```typescript
{
  company: string; // Required
  create_account_if_missing?: boolean; // Default: false
  account_name?: string; // Optional custom name
}
```

**Response:**
```typescript
{
  success: true,
  message: string;
  auto_configured?: boolean;
  account_created?: boolean;
  already_configured?: boolean;
  data: {
    company: string;
    account: string;
    account_name: string;
    account_type: string;
    root_type: string;
    provisional_accounting_enabled: boolean;
  };
}
```

**Example:**
```typescript
const response = await accountProvisioningClient.autoConfigure('WEE', {
  createAccountIfMissing: true,
  accountName: 'Custom Provisional Account - WEE',
});
```

---

### 5. Validate Provisional Accounting Setup

**Endpoint:** `GET /api/method/savanna_pos.savanna_pos.apis.account_provisioning_api.validate_provisional_accounting_setup`

**Parameters:**
```typescript
{
  company: string; // Required
}
```

**Response:**
```typescript
{
  success: true,
  data: {
    company: string;
    enable_provisional_accounting: boolean;
    default_provisional_account: string | null;
    is_valid: boolean;
    issues: string[];
    recommendations: string[];
    warnings: string[];
    account_details?: AccountDetails;
  }
}
```

**Example:**
```typescript
const validation = await accountProvisioningClient.validate('WEE');
if (!validation.is_valid) {
  console.log('Issues:', validation.issues);
  console.log('Recommendations:', validation.recommendations);
}
```

---

## Error Handling

### Error Types

```typescript
type ErrorType =
  | 'company_not_found'
  | 'account_not_found'
  | 'account_company_mismatch'
  | 'group_account_error'
  | 'disabled_account_error'
  | 'missing_provisional_account'
  | 'invalid_provisional_account'
  | 'parent_account_not_found'
  | 'validation_error'
  | 'general_error';
```

### Error Handler Utility

```typescript
// utils/errorHandler.ts

import type { ApiError, ErrorType } from '../types/accountProvisioning';

export function handleAccountProvisioningError(error: ApiError): {
  message: string;
  severity: 'error' | 'warning' | 'info';
  action?: string;
} {
  const errorMessages: Record<ErrorType, { message: string; severity: 'error' | 'warning' | 'info'; action?: string }> = {
    company_not_found: {
      message: `Company not found. Please check the company name.`,
      severity: 'error',
    },
    account_not_found: {
      message: `Account not found. Please select a different account.`,
      severity: 'error',
      action: 'Select Account',
    },
    account_company_mismatch: {
      message: `The selected account belongs to a different company.`,
      severity: 'error',
      action: 'Select Account',
    },
    group_account_error: {
      message: `Group accounts cannot be used. Please select a ledger account.`,
      severity: 'error',
      action: 'Select Account',
    },
    disabled_account_error: {
      message: `The selected account is disabled. Please select an active account.`,
      severity: 'error',
      action: 'Select Account',
    },
    missing_provisional_account: {
      message: `Provisional accounting is enabled but no default account is set.`,
      severity: 'warning',
      action: 'Auto-Configure',
    },
    invalid_provisional_account: {
      message: `The default provisional account no longer exists.`,
      severity: 'error',
      action: 'Set Account',
    },
    parent_account_not_found: {
      message: `Could not find a suitable parent account for creating the provisional account.`,
      severity: 'error',
    },
    validation_error: {
      message: `Validation error: ${error.message}`,
      severity: 'error',
    },
    general_error: {
      message: error.message || 'An unexpected error occurred.',
      severity: 'error',
    },
  };

  return errorMessages[error.error_type] || errorMessages.general_error;
}
```

### Error Handling in Components

```typescript
import { handleAccountProvisioningError } from '../utils/errorHandler';

function MyComponent() {
  const { autoConfigure, error } = useAccountProvisioning('WEE');

  const handleError = (err: any) => {
    if (err.response?.data?.message) {
      const errorInfo = handleAccountProvisioningError(err.response.data.message);
      
      // Show toast notification
      toast[errorInfo.severity](errorInfo.message);
      
      // Show action button if available
      if (errorInfo.action) {
        // Show action button
      }
    }
  };

  // Use error handler
  useEffect(() => {
    if (error) {
      handleError(error);
    }
  }, [error]);
}
```

---

## Complete Examples

### Example 1: Company Settings Component

```typescript
// components/CompanyProvisioningSettings.tsx

import React, { useState } from 'react';
import { useAccountProvisioning } from '../hooks/useAccountProvisioning';
import { useAvailableAccounts } from '../hooks/useAvailableAccounts';
import { handleAccountProvisioningError } from '../utils/errorHandler';

interface Props {
  company: string;
}

export function CompanyProvisioningSettings({ company }: Props) {
  const { status, loading, error, autoConfigure, setDefaultAccount, validate } =
    useAccountProvisioning(company);
  const { accounts, loading: accountsLoading, refetch: refetchAccounts } =
    useAvailableAccounts(company, { autoFetch: false });

  const [showAccountSelector, setShowAccountSelector] = useState(false);
  const [validating, setValidating] = useState(false);

  const handleAutoConfigure = async () => {
    try {
      const result = await autoConfigure({ createAccountIfMissing: true });
      if (result.success) {
        alert(`Successfully configured: ${result.data?.account_name}`);
      }
    } catch (err) {
      console.error('Auto-configure failed:', err);
    }
  };

  const handleSelectAccount = async (accountName: string) => {
    try {
      const result = await setDefaultAccount(accountName, true);
      if (result.success) {
        setShowAccountSelector(false);
        alert('Account set successfully');
      }
    } catch (err) {
      console.error('Set account failed:', err);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      const validation = await validate();
      if (validation.is_valid) {
        alert('✓ Setup is valid');
      } else {
        alert(`Issues found:\n${validation.issues.join('\n')}`);
      }
    } catch (err) {
      console.error('Validation failed:', err);
    } finally {
      setValidating(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="provisioning-settings">
      <h3>Provisional Accounting Settings</h3>

      {status && (
        <div className="status">
          <p>
            <strong>Status:</strong>{' '}
            {status.is_valid ? (
              <span className="valid">✓ Valid</span>
            ) : (
              <span className="invalid">✗ Invalid</span>
            )}
          </p>
          <p>
            <strong>Enabled:</strong> {status.enable_provisional_accounting ? 'Yes' : 'No'}
          </p>
          {status.default_provisional_account && (
            <p>
              <strong>Account:</strong> {status.account_details?.account_name}
            </p>
          )}
          {status.validation_message && (
            <p className="warning">{status.validation_message}</p>
          )}
        </div>
      )}

      <div className="actions">
        <button onClick={handleAutoConfigure} disabled={loading}>
          Auto-Configure
        </button>
        <button onClick={() => {
          setShowAccountSelector(true);
          refetchAccounts();
        }}>
          Select Account
        </button>
        <button onClick={handleValidate} disabled={validating}>
          Validate Setup
        </button>
      </div>

      {showAccountSelector && (
        <div className="account-selector">
          <h4>Select Account</h4>
          {accountsLoading ? (
            <div>Loading accounts...</div>
          ) : (
            <ul>
              {accounts.map((account) => (
                <li key={account.name}>
                  <button onClick={() => handleSelectAccount(account.name)}>
                    {account.account_name}
                    {account.is_recommended && <span className="badge">Recommended</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <button onClick={() => setShowAccountSelector(false)}>Cancel</button>
        </div>
      )}

      {error && (
        <div className="error">
          {handleAccountProvisioningError(error as any).message}
        </div>
      )}
    </div>
  );
}
```

### Example 2: Autoprovisioning on Error

```typescript
// components/PurchaseReceiptForm.tsx

import React, { useEffect } from 'react';
import { useAccountProvisioning } from '../hooks/useAccountProvisioning';

interface Props {
  company: string;
  onSubmit: (data: any) => void;
}

export function PurchaseReceiptForm({ company, onSubmit }: Props) {
  const { status, autoConfigure, loading } = useAccountProvisioning(company, {
    autoFetch: true,
  });

  // Auto-provision if needed
  useEffect(() => {
    if (status && !status.is_valid && status.enable_provisional_accounting) {
      // Automatically configure if invalid
      autoConfigure({ createAccountIfMissing: true }).catch(console.error);
    }
  }, [status, autoConfigure]);

  const handleSubmit = async (formData: any) => {
    // Ensure provisioning is valid before submitting
    if (status && !status.is_valid) {
      alert('Please configure provisional accounting first');
      return;
    }

    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={loading || (status && !status.is_valid)}>
        Submit
      </button>
    </form>
  );
}
```

### Example 3: Account Selector Component

```typescript
// components/AccountSelector.tsx

import React, { useState } from 'react';
import { useAvailableAccounts } from '../hooks/useAvailableAccounts';

interface Props {
  company: string;
  onSelect: (accountName: string) => void;
  onCancel?: () => void;
}

export function AccountSelector({ company, onSelect, onCancel }: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const { accounts, loading, refetch } = useAvailableAccounts(company, {
    searchTerm,
    autoFetch: true,
  });

  return (
    <div className="account-selector">
      <input
        type="text"
        placeholder="Search accounts..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {loading ? (
        <div>Loading...</div>
      ) : (
        <ul>
          {accounts.map((account) => (
            <li key={account.name}>
              <button onClick={() => onSelect(account.name)}>
                <div>
                  <strong>{account.account_name}</strong>
                  {account.is_recommended && (
                    <span className="badge">Recommended</span>
                  )}
                </div>
                <small>{account.account_type}</small>
              </button>
            </li>
          ))}
        </ul>
      )}

      {onCancel && <button onClick={onCancel}>Cancel</button>}
    </div>
  );
}
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```typescript
try {
  const result = await autoConfigure({ createAccountIfMissing: true });
  // Handle success
} catch (error) {
  // Log error
  console.error('Auto-configure failed:', error);
  
  // Show user-friendly message
  const errorInfo = handleAccountProvisioningError(error);
  toast.error(errorInfo.message);
}
```

### 2. Loading States

Always show loading states:

```typescript
const { loading, status } = useAccountProvisioning(company);

if (loading) {
  return <Spinner />;
}
```

### 3. Validation Before Actions

Validate setup before critical operations:

```typescript
const { status, validate } = useAccountProvisioning(company);

const handleCriticalAction = async () => {
  const validation = await validate();
  if (!validation.is_valid) {
    alert('Please fix configuration issues first');
    return;
  }
  // Proceed with action
};
```

### 4. Autoprovisioning Strategy

Use autoprovisioning strategically:

```typescript
// For user-facing features: allow opt-in
const [autoProvision, setAutoProvision] = useState(false);
const { autoConfigure } = useAccountProvisioning(company);

// For background processes: enable by default
const { autoConfigure } = useAccountProvisioning(company);
useEffect(() => {
  if (needsProvisioning) {
    autoConfigure({ createAccountIfMissing: true });
  }
}, [needsProvisioning]);
```

---

## Summary

This documentation provides:

- ✅ Complete TypeScript types
- ✅ React hooks for all endpoints
- ✅ API client with error handling
- ✅ Real-world component examples
- ✅ Best practices and patterns

**Quick Links:**
- [TypeScript Types](#typescript-types)
- [React Hooks](#react-hooks)
- [API Reference](#api-reference)
- [Complete Examples](#complete-examples)

For backend documentation, see [ACCOUNT_PROVISIONING_API_DOCUMENTATION.md](./ACCOUNT_PROVISIONING_API_DOCUMENTATION.md).
