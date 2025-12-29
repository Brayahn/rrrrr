# Role Management API Documentation

Complete API documentation for role management endpoints, designed for React.js frontend consumption.

## Base URL

All endpoints are relative to your Frappe backend API:
```
/api/method/savanna_pos.savanna_pos.apis.role_api.<endpoint_name>
```

## Authentication

All endpoints require authentication. Include the session cookie or API key in your requests.

```javascript
// Using fetch with session cookie (automatic)
fetch('/api/method/savanna_pos.savanna_pos.apis.role_api.list_roles', {
  credentials: 'include'
})

// Using API key
fetch('/api/method/savanna_pos.savanna_pos.apis.role_api.list_roles', {
  headers: {
    'Authorization': 'token <api_key>:<api_secret>'
  }
})
```

---

## Endpoints

### 1. Create Role

Creates a new role in the system.

**Endpoint:** `create_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.create_role`

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `role_name` | string | Yes | - | Unique name for the role |
| `desk_access` | boolean | No | `true` | Whether role has desk access |
| `two_factor_auth` | boolean | No | `false` | Whether role requires 2FA |
| `restrict_to_domain` | string | No | `null` | Domain to restrict role to |
| `home_page` | string | No | `null` | Home page route (e.g., "/app") |
| `is_custom` | boolean | No | `true` | Whether this is a custom role |

#### Request Example

```javascript
const createRole = async (roleData) => {
  const formData = new FormData();
  formData.append('role_name', roleData.roleName);
  formData.append('desk_access', roleData.deskAccess ?? true);
  formData.append('two_factor_auth', roleData.twoFactorAuth ?? false);
  if (roleData.restrictToDomain) {
    formData.append('restrict_to_domain', roleData.restrictToDomain);
  }
  if (roleData.homePage) {
    formData.append('home_page', roleData.homePage);
  }
  formData.append('is_custom', roleData.isCustom ?? true);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.create_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const newRole = await createRole({
  roleName: 'Inventory Manager',
  deskAccess: true,
  twoFactorAuth: false
});
```

#### Response Example

**Success (201):**
```json
{
  "message": {
    "success": true,
    "message": "Role created successfully",
    "data": {
      "name": "Inventory Manager",
      "role_name": "Inventory Manager",
      "desk_access": 1,
      "two_factor_auth": 0,
      "is_custom": 1,
      "restrict_to_domain": null,
      "home_page": null,
      "disabled": 0
    }
  }
}
```

**Error (417):**
```json
{
  "message": {
    "success": false,
    "message": "Role 'Inventory Manager' already exists"
  }
}
```

---

### 2. Update Role

Updates an existing role's properties.

**Endpoint:** `update_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.update_role`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role to update |
| `desk_access` | boolean | No | Update desk access |
| `two_factor_auth` | boolean | No | Update 2FA requirement |
| `restrict_to_domain` | string | No | Update domain (empty string to remove) |
| `home_page` | string | No | Update home page (empty string to remove) |
| `disabled` | boolean | No | Update disabled status |

#### Request Example

```javascript
const updateRole = async (roleName, updates) => {
  const formData = new FormData();
  formData.append('role_name', roleName);
  
  if (updates.deskAccess !== undefined) {
    formData.append('desk_access', updates.deskAccess);
  }
  if (updates.twoFactorAuth !== undefined) {
    formData.append('two_factor_auth', updates.twoFactorAuth);
  }
  if (updates.restrictToDomain !== undefined) {
    formData.append('restrict_to_domain', updates.restrictToDomain || '');
  }
  if (updates.homePage !== undefined) {
    formData.append('home_page', updates.homePage || '');
  }
  if (updates.disabled !== undefined) {
    formData.append('disabled', updates.disabled);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.update_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await updateRole('Inventory Manager', {
  deskAccess: false,
  twoFactorAuth: true
});
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Role updated successfully",
    "data": {
      "name": "Inventory Manager",
      "role_name": "Inventory Manager",
      "desk_access": 0,
      "two_factor_auth": 1,
      "is_custom": 1,
      "restrict_to_domain": null,
      "home_page": null,
      "disabled": 0
    }
  }
}
```

---

### 3. Delete Role

Deletes a role. Only works if the role is not assigned to any users.

**Endpoint:** `delete_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.delete_role`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role to delete |

#### Request Example

```javascript
const deleteRole = async (roleName) => {
  const formData = new FormData();
  formData.append('role_name', roleName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.delete_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await deleteRole('Inventory Manager');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Role deleted successfully"
  }
}
```

**Error (417):**
```json
{
  "message": {
    "success": false,
    "message": "Cannot delete role 'Inventory Manager' because it is assigned to one or more users. Please remove the role from all users first."
  }
}
```

---

### 4. Disable Role

Disables a role, which removes it from all users.

**Endpoint:** `disable_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.disable_role`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role to disable |

#### Request Example

```javascript
const disableRole = async (roleName) => {
  const formData = new FormData();
  formData.append('role_name', roleName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.disable_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await disableRole('Inventory Manager');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Role disabled successfully. The role has been removed from all users.",
    "data": {
      "name": "Inventory Manager",
      "role_name": "Inventory Manager",
      "disabled": 1
    }
  }
}
```

---

### 5. Enable Role

Enables a previously disabled role.

**Endpoint:** `enable_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.enable_role`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role to enable |

#### Request Example

```javascript
const enableRole = async (roleName) => {
  const formData = new FormData();
  formData.append('role_name', roleName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.enable_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await enableRole('Inventory Manager');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Role enabled successfully",
    "data": {
      "name": "Inventory Manager",
      "role_name": "Inventory Manager",
      "disabled": 0
    }
  }
}
```

---

### 6. Assign Permissions to Role

Assigns permissions to a role for a specific doctype.

**Endpoint:** `assign_permissions_to_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.assign_permissions_to_role`

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `role_name` | string | Yes | - | Name of the role |
| `doctype` | string | Yes | - | DocType to assign permissions for |
| `permissions` | object | Yes | - | Permission flags object (see below) |
| `permlevel` | number | No | `0` | Permission level |
| `if_owner` | boolean | No | `false` | Apply only if user is owner |

#### Permissions Object

The `permissions` parameter accepts an object with the following boolean flags:

```typescript
{
  read: boolean;      // Read access
  write: boolean;     // Write access
  create: boolean;    // Create access
  delete: boolean;    // Delete access
  submit: boolean;    // Submit access
  cancel: boolean;    // Cancel access
  amend: boolean;     // Amend access
  print: boolean;     // Print access
  email: boolean;     // Email access
  export: boolean;    // Export access
  import: boolean;    // Import access
  report: boolean;    // Report access
  share: boolean;     // Share access
  select: boolean;    // Select access
}
```

#### Request Example

```javascript
const assignPermissions = async (roleName, doctype, permissions, options = {}) => {
  const formData = new FormData();
  formData.append('role_name', roleName);
  formData.append('doctype', doctype);
  formData.append('permissions', JSON.stringify(permissions));
  formData.append('permlevel', options.permlevel ?? 0);
  formData.append('if_owner', options.ifOwner ?? false);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.assign_permissions_to_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await assignPermissions(
  'Inventory Manager',
  'Item',
  {
    read: true,
    write: true,
    create: true,
    delete: false,
    submit: false,
    cancel: false,
    amend: false,
    print: true,
    email: false,
    export: true,
    import: false,
    report: true,
    share: false,
    select: true
  }
);
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Permissions assigned successfully",
    "data": {
      "role": "Inventory Manager",
      "doctype": "Item",
      "permlevel": 0,
      "if_owner": false,
      "permissions": {
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "print": 1,
        "email": 0,
        "export": 1,
        "import": 0,
        "report": 1,
        "share": 0,
        "select": 1
      }
    }
  }
}
```

---

### 7. Get Role Permissions

Retrieves all permissions for a role, optionally filtered by doctype.

**Endpoint:** `get_role_permissions`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.get_role_permissions`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role |
| `doctype` | string | No | Filter by specific doctype |

#### Request Example

```javascript
const getRolePermissions = async (roleName, doctype = null) => {
  const formData = new FormData();
  formData.append('role_name', roleName);
  if (doctype) {
    formData.append('doctype', doctype);
  }

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.get_role_permissions',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Get all permissions for a role
const allPerms = await getRolePermissions('Inventory Manager');

// Get permissions for a specific doctype
const itemPerms = await getRolePermissions('Inventory Manager', 'Item');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "data": {
      "role": "Inventory Manager",
      "permissions": [
        {
          "doctype": "Item",
          "role": "Inventory Manager",
          "permlevel": 0,
          "if_owner": false,
          "permissions": {
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 0,
            "submit": 0,
            "cancel": 0,
            "amend": 0,
            "print": 1,
            "email": 0,
            "export": 1,
            "import": 0,
            "report": 1,
            "share": 0,
            "select": 1
          }
        },
        {
          "doctype": "Stock Entry",
          "role": "Inventory Manager",
          "permlevel": 0,
          "if_owner": false,
          "permissions": {
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "submit": 1,
            "cancel": 1,
            "amend": 0,
            "print": 1,
            "email": 0,
            "export": 1,
            "import": 0,
            "report": 1,
            "share": 0,
            "select": 1
          }
        }
      ],
      "count": 2
    }
  }
}
```

---

### 8. Remove Permissions from Role

Removes permissions from a role for a specific doctype.

**Endpoint:** `remove_permissions_from_role`  
**Method:** `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.remove_permissions_from_role`

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `role_name` | string | Yes | - | Name of the role |
| `doctype` | string | Yes | - | DocType to remove permissions for |
| `permlevel` | number | No | `0` | Permission level |
| `if_owner` | boolean | No | `false` | If owner permission to remove |

#### Request Example

```javascript
const removePermissions = async (roleName, doctype, options = {}) => {
  const formData = new FormData();
  formData.append('role_name', roleName);
  formData.append('doctype', doctype);
  formData.append('permlevel', options.permlevel ?? 0);
  formData.append('if_owner', options.ifOwner ?? false);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.remove_permissions_from_role',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
await removePermissions('Inventory Manager', 'Item');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "message": "Permissions removed successfully"
  }
}
```

---

### 9. List Roles

Lists all roles with optional filters and pagination.

**Endpoint:** `list_roles`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.list_roles`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `disabled` | boolean | No | Filter by disabled status |
| `is_custom` | boolean | No | Filter by custom role |
| `desk_access` | boolean | No | Filter by desk access |
| `restrict_to_domain` | string | No | Filter by domain |
| `page` | number | No | Page number (default: 1) |
| `page_size` | number | No | Items per page (default: 20) |

#### Request Example

```javascript
const listRoles = async (filters = {}, pagination = {}) => {
  const formData = new FormData();
  
  if (filters.disabled !== undefined) {
    formData.append('disabled', filters.disabled);
  }
  if (filters.isCustom !== undefined) {
    formData.append('is_custom', filters.isCustom);
  }
  if (filters.deskAccess !== undefined) {
    formData.append('desk_access', filters.deskAccess);
  }
  if (filters.restrictToDomain) {
    formData.append('restrict_to_domain', filters.restrictToDomain);
  }
  formData.append('page', pagination.page ?? 1);
  formData.append('page_size', pagination.pageSize ?? 20);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.list_roles',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const roles = await listRoles(
  { disabled: false, isCustom: true },
  { page: 1, pageSize: 20 }
);
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "data": {
      "roles": [
        {
          "name": "Inventory Manager",
          "role_name": "Inventory Manager",
          "disabled": 0,
          "is_custom": 1,
          "desk_access": 1,
          "two_factor_auth": 0,
          "restrict_to_domain": null,
          "home_page": null,
          "user_count": 5
        },
        {
          "name": "Sales User",
          "role_name": "Sales User",
          "disabled": 0,
          "is_custom": 0,
          "desk_access": 1,
          "two_factor_auth": 0,
          "restrict_to_domain": null,
          "home_page": null,
          "user_count": 12
        }
      ],
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 2,
        "total_pages": 1
      }
    }
  }
}
```

---

### 10. Get Role Details

Retrieves detailed information about a specific role.

**Endpoint:** `get_role_details`  
**Method:** `GET` or `POST`  
**URL:** `/api/method/savanna_pos.savanna_pos.apis.role_api.get_role_details`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_name` | string | Yes | Name of the role |

#### Request Example

```javascript
const getRoleDetails = async (roleName) => {
  const formData = new FormData();
  formData.append('role_name', roleName);

  const response = await fetch(
    '/api/method/savanna_pos.savanna_pos.apis.role_api.get_role_details',
    {
      method: 'POST',
      credentials: 'include',
      body: formData
    }
  );

  const data = await response.json();
  return data;
};

// Usage
const roleDetails = await getRoleDetails('Inventory Manager');
```

#### Response Example

**Success (200):**
```json
{
  "message": {
    "success": true,
    "data": {
      "name": "Inventory Manager",
      "role_name": "Inventory Manager",
      "disabled": 0,
      "is_custom": 1,
      "desk_access": 1,
      "two_factor_auth": 0,
      "restrict_to_domain": null,
      "home_page": null,
      "user_count": 5,
      "permission_count": 8,
      "doctypes_with_permissions": [
        "Item",
        "Stock Entry",
        "Stock Reconciliation",
        "Warehouse"
      ],
      "is_automatic": false
    }
  }
}
```

---

## React Hook Example

Here's a complete React hook for managing roles:

```javascript
import { useState, useCallback } from 'react';

const useRoleManagement = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = useCallback(async (endpoint, data = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          if (typeof value === 'object' && !(value instanceof File)) {
            formData.append(key, JSON.stringify(value));
          } else {
            formData.append(key, value);
          }
        }
      });

      const response = await fetch(
        `/api/method/savanna_pos.savanna_pos.apis.role_api.${endpoint}`,
        {
          method: 'POST',
          credentials: 'include',
          body: formData
        }
      );

      const result = await response.json();
      
      if (result.message?.success) {
        return result.message;
      } else {
        throw new Error(result.message?.message || 'An error occurred');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createRole = useCallback((roleData) => 
    apiCall('create_role', roleData), [apiCall]);

  const updateRole = useCallback((roleName, updates) => 
    apiCall('update_role', { role_name: roleName, ...updates }), [apiCall]);

  const deleteRole = useCallback((roleName) => 
    apiCall('delete_role', { role_name: roleName }), [apiCall]);

  const disableRole = useCallback((roleName) => 
    apiCall('disable_role', { role_name: roleName }), [apiCall]);

  const enableRole = useCallback((roleName) => 
    apiCall('enable_role', { role_name: roleName }), [apiCall]);

  const assignPermissions = useCallback((roleName, doctype, permissions, options) => 
    apiCall('assign_permissions_to_role', {
      role_name: roleName,
      doctype,
      permissions,
      ...options
    }), [apiCall]);

  const getRolePermissions = useCallback((roleName, doctype = null) => 
    apiCall('get_role_permissions', {
      role_name: roleName,
      ...(doctype && { doctype })
    }), [apiCall]);

  const removePermissions = useCallback((roleName, doctype, options) => 
    apiCall('remove_permissions_from_role', {
      role_name: roleName,
      doctype,
      ...options
    }), [apiCall]);

  const listRoles = useCallback((filters = {}, pagination = {}) => 
    apiCall('list_roles', { ...filters, ...pagination }), [apiCall]);

  const getRoleDetails = useCallback((roleName) => 
    apiCall('get_role_details', { role_name: roleName }), [apiCall]);

  return {
    loading,
    error,
    createRole,
    updateRole,
    deleteRole,
    disableRole,
    enableRole,
    assignPermissions,
    getRolePermissions,
    removePermissions,
    listRoles,
    getRoleDetails
  };
};

export default useRoleManagement;
```

## Usage in React Component

```javascript
import React, { useState, useEffect } from 'react';
import useRoleManagement from './hooks/useRoleManagement';

const RoleManagement = () => {
  const {
    loading,
    error,
    createRole,
    listRoles,
    assignPermissions,
    getRolePermissions
  } = useRoleManagement();

  const [roles, setRoles] = useState([]);
  const [newRoleName, setNewRoleName] = useState('');

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = async () => {
    try {
      const result = await listRoles({ disabled: false });
      setRoles(result.data.roles);
    } catch (err) {
      console.error('Failed to load roles:', err);
    }
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    try {
      await createRole({
        role_name: newRoleName,
        desk_access: true
      });
      setNewRoleName('');
      loadRoles();
    } catch (err) {
      console.error('Failed to create role:', err);
    }
  };

  const handleAssignPermissions = async (roleName, doctype) => {
    try {
      await assignPermissions(roleName, doctype, {
        read: true,
        write: true,
        create: true,
        delete: false,
        print: true
      });
      alert('Permissions assigned successfully!');
    } catch (err) {
      console.error('Failed to assign permissions:', err);
    }
  };

  return (
    <div>
      <h1>Role Management</h1>
      
      {error && <div className="error">{error}</div>}
      
      <form onSubmit={handleCreateRole}>
        <input
          type="text"
          value={newRoleName}
          onChange={(e) => setNewRoleName(e.target.value)}
          placeholder="Role name"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Role'}
        </button>
      </form>

      <div>
        <h2>Roles</h2>
        {roles.map(role => (
          <div key={role.name}>
            <h3>{role.role_name}</h3>
            <p>Users: {role.user_count}</p>
            <button onClick={() => handleAssignPermissions(role.name, 'Item')}>
              Assign Item Permissions
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RoleManagement;
```

## TypeScript Types

For TypeScript projects, here are the type definitions:

```typescript
interface Role {
  name: string;
  role_name: string;
  disabled: number;
  is_custom: number;
  desk_access: number;
  two_factor_auth: number;
  restrict_to_domain: string | null;
  home_page: string | null;
  user_count?: number;
}

interface Permissions {
  read: boolean;
  write: boolean;
  create: boolean;
  delete: boolean;
  submit: boolean;
  cancel: boolean;
  amend: boolean;
  print: boolean;
  email: boolean;
  export: boolean;
  import: boolean;
  report: boolean;
  share: boolean;
  select: boolean;
}

interface RolePermission {
  doctype: string;
  role: string;
  permlevel: number;
  if_owner: boolean;
  permissions: Permissions;
}

interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "message": {
    "success": false,
    "message": "Error description here"
  }
}
```

Common HTTP status codes:
- **200**: Success
- **201**: Created successfully
- **417**: Validation error
- **401**: Authentication required
- **403**: Permission denied

## Notes

1. **Automatic Roles**: Some roles (like "Administrator", "Guest", "All", "Desk User") are automatic and cannot be modified or deleted.

2. **Permission Levels**: The `permlevel` parameter allows you to set different permission levels (0, 1, 2, etc.) for field-level access control.

3. **If Owner**: The `if_owner` flag restricts permissions to documents owned by the user.

4. **Custom vs Standard Permissions**: Custom permissions (Custom DocPerm) override standard permissions (DocPerm) for the same role and doctype.

5. **Disabled Roles**: When a role is disabled, it's automatically removed from all users. Re-enabling it doesn't automatically reassign it to users.

6. **FormData**: All POST requests use FormData format, which is required by Frappe's API.
