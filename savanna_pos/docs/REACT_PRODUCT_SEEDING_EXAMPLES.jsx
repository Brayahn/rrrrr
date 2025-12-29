/**
 * React.js Examples for Product Seeding API
 * 
 * This file contains ready-to-use React components and hooks
 * for integrating with the Product Seeding API.
 * 
 * Usage:
 * 1. Copy the API utility function to your utils/api.js
 * 2. Copy the hooks to your hooks directory
 * 3. Import and use the components in your application
 */

// ============================================================================
// API UTILITY
// ============================================================================

/**
 * API Request Utility
 * Place this in: utils/api.js
 */
export const apiRequest = async (endpoint, method = 'GET', params = {}, headers = {}) => {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://your-domain.com/api/method/';
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
    const queryParams = new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        acc[key] = value === true ? '1' : value === false ? '0' : value;
        return acc;
      }, {})
    ).toString();
    const fullUrl = queryParams ? `${url}?${queryParams}` : url;
    const response = await fetch(fullUrl, config);
    return response.json();
  } else {
    config.body = JSON.stringify(params);
    const response = await fetch(url, config);
    return response.json();
  }
};

// ============================================================================
// CUSTOM HOOKS
// ============================================================================

/**
 * Hook: useIndustries
 * Place this in: hooks/useIndustries.js
 */
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

/**
 * Hook: useIndustryProducts
 * Place this in: hooks/useIndustryProducts.js
 */
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
      setTotalProducts(0);
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

/**
 * Hook: useBulkUpload
 * Place this in: hooks/useBulkUpload.js
 */
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

// ============================================================================
// REACT COMPONENTS
// ============================================================================

/**
 * Component: IndustriesList
 * Simple list of all industries
 */
import React from 'react';
import { useIndustries } from '../hooks/useIndustries';

const IndustriesList = () => {
  const { industries, loading, error } = useIndustries();

  if (loading) return <div>Loading industries...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

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

/**
 * Component: ProductSeeding
 * Select industry and view products
 */
import React, { useState } from 'react';
import { useIndustries } from '../hooks/useIndustries';
import { useIndustryProducts } from '../hooks/useIndustryProducts';

const ProductSeeding = () => {
  const { industries, loading: industriesLoading } = useIndustries();
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const { products, loading: productsLoading, error, totalProducts } = 
    useIndustryProducts(selectedIndustry);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Product Seeding</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <label>Select Industry: </label>
        {industriesLoading ? (
          <span>Loading...</span>
        ) : (
          <select 
            value={selectedIndustry} 
            onChange={(e) => setSelectedIndustry(e.target.value)}
            style={{ padding: '8px', fontSize: '16px', minWidth: '250px' }}
          >
            <option value="">-- Select Industry --</option>
            {industries.map((industry) => (
              <option key={industry.name} value={industry.name}>
                {industry.industry_name}
              </option>
            ))}
          </select>
        )}
      </div>

      {productsLoading && <div>Loading products...</div>}
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      
      {selectedIndustry && !productsLoading && !error && (
        <div>
          <h3>Products ({totalProducts})</h3>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '10px',
            marginTop: '15px'
          }}>
            {products.map((product) => (
              <div 
                key={product.sku}
                style={{ 
                  padding: '12px', 
                  border: '1px solid #ddd', 
                  borderRadius: '4px',
                  background: '#f9f9f9'
                }}
              >
                <div style={{ fontWeight: 'bold' }}>{product.name}</div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  SKU: {product.sku}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductSeeding;

/**
 * Component: BulkUploadProducts
 * Button to trigger bulk upload
 */
import React from 'react';
import { useBulkUpload } from '../hooks/useBulkUpload';

const BulkUploadProducts = () => {
  const { uploadProducts, loading, result, error } = useBulkUpload();

  const handleUpload = () => {
    if (window.confirm('Are you sure you want to bulk upload products? This will create product templates from the seed data file.')) {
      uploadProducts();
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Bulk Upload Products</h2>
      <button 
        onClick={handleUpload} 
        disabled={loading}
        style={{ 
          padding: '10px 20px', 
          fontSize: '16px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Uploading...' : 'Upload Products from Seed File'}
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '10px', padding: '10px', background: '#ffe6e6' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ 
          marginTop: '15px', 
          padding: '15px', 
          background: '#e6f7e6',
          borderRadius: '4px'
        }}>
          <h3>Upload Results:</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>✅ <strong>Created:</strong> {result.created}</li>
            <li>⏭️ <strong>Skipped:</strong> {result.skipped}</li>
            <li>📊 <strong>Total Processed:</strong> {result.total_processed}</li>
            {result.ignored_industries && result.ignored_industries.length > 0 && (
              <li>⚠️ <strong>Ignored Industries:</strong> {result.ignored_industries.join(', ')}</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default BulkUploadProducts;

/**
 * Hook: useCreateSeedItems
 * Place this in: hooks/useCreateSeedItems.js
 */
import { useState } from 'react';
import { apiRequest } from '../utils/api';

export const useCreateSeedItems = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const createItems = async (priceList, items, company = null, industry = null) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      // Check authentication
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required. Please log in to create items.');
        setLoading(false);
        return;
      }

      const payload = {
        price_list: priceList,
        items: items
      };

      // Add optional fields
      if (company) payload.company = company;
      if (industry !== undefined) payload.industry = industry;  // Can be null for global

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

/**
 * Component: CreateSeedItems
 * Form to create items and item prices
 */
import React, { useState } from 'react';
import { useCreateSeedItems } from '../hooks/useCreateSeedItems';

const CreateSeedItems = () => {
  const { createItems, loading, result, error } = useCreateSeedItems();
  const [priceList, setPriceList] = useState('Standard Selling');
  const [company, setCompany] = useState('');  // Optional - defaults to user's company
  const [industry, setIndustry] = useState('');  // Optional - defaults to user's industry
  const [items, setItems] = useState([
    { item_code: '', item_name: '', item_price: 0, item_group: 'All Item Groups', uom: 'Nos' }
  ]);

  const handleAddItem = () => {
    setItems([...items, { 
      item_code: '', 
      item_name: '', 
      item_price: 0, 
      item_group: 'All Item Groups', 
      uom: 'Nos' 
    }]);
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const handleRemoveItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Please log in to create items. Authentication is required.');
      return;
    }

    // Validate required fields
    const validItems = items.filter(item => 
      item.item_code && item.item_name && item.item_price >= 0
    );

    if (validItems.length === 0) {
      alert('Please add at least one valid item');
      return;
    }

    if (!priceList) {
      alert('Price list is required');
      return;
    }

    if (window.confirm(`Create ${validItems.length} items for your company?`)) {
      // Pass company and industry (can be empty strings, will use defaults)
      createItems(
        priceList, 
        validItems, 
        company || null,  // null if empty
        industry || null  // null if empty (will use user's industry or global)
      );
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Create Seed Items</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Create Item master records and Item Prices scoped to your company. 
        <strong> Authentication required.</strong> Note: This does NOT add inventory stock.
      </p>
      
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Price List *
        </label>
        <input
          type="text"
          value={priceList}
          onChange={(e) => setPriceList(e.target.value)}
          placeholder="Standard Selling"
          style={{ padding: '10px', fontSize: '16px', minWidth: '300px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Company (optional)
        </label>
        <input
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Defaults to your company"
          style={{ padding: '10px', fontSize: '16px', minWidth: '300px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Leave empty to use your default company
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Industry (optional)
        </label>
        <input
          type="text"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          placeholder="REST, RETAIL, etc. (defaults to your industry)"
          style={{ padding: '10px', fontSize: '16px', minWidth: '300px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
        <small style={{ display: 'block', color: '#666', marginTop: '5px' }}>
          Leave empty to use your industry, or enter industry code (e.g., "REST") for specific industry, or "null" for global products
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Items</h3>
        {items.map((item, index) => (
          <div key={index} style={{ 
            border: '1px solid #ddd', 
            padding: '15px', 
            marginBottom: '10px',
            borderRadius: '4px',
            background: '#fafafa',
            position: 'relative'
          }}>
            {items.length > 1 && (
              <button
                onClick={() => handleRemoveItem(index)}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '5px 10px',
                  cursor: 'pointer'
                }}
              >
                Remove
              </button>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Item Code *</label>
                <input
                  type="text"
                  value={item.item_code}
                  onChange={(e) => handleItemChange(index, 'item_code', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Item Name *</label>
                <input
                  type="text"
                  value={item.item_name}
                  onChange={(e) => handleItemChange(index, 'item_name', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Price *</label>
                <input
                  type="number"
                  value={item.item_price}
                  onChange={(e) => handleItemChange(index, 'item_price', parseFloat(e.target.value) || 0)}
                  min="0"
                  step="0.01"
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>Item Group</label>
                <input
                  type="text"
                  value={item.item_group}
                  onChange={(e) => handleItemChange(index, 'item_group', e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>UOM</label>
                <input
                  type="text"
                  value={item.uom}
                  onChange={(e) => handleItemChange(index, 'uom', e.target.value)}
                  placeholder="Nos"
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
            </div>
          </div>
        ))}
        <button 
          onClick={handleAddItem}
          style={{ 
            padding: '10px 20px',
            background: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
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
          cursor: loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold'
        }}
      >
        {loading ? 'Creating...' : 'Create Items'}
      </button>

      {error && (
        <div style={{ 
          color: '#721c24', 
          marginTop: '15px', 
          padding: '12px',
          background: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '4px'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ 
          marginTop: '15px', 
          padding: '15px', 
          background: '#d4edda',
          border: '1px solid #c3e6cb',
          borderRadius: '4px'
        }}>
          <h3 style={{ marginTop: 0 }}>✅ Results:</h3>
          <p><strong>Created:</strong> {result.created}</p>
          <p><strong>Skipped:</strong> {result.skipped}</p>
          <p><strong>Total Received:</strong> {result.total_received}</p>
          {result.failed && result.failed.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <strong>❌ Failed Items:</strong>
              <ul>
                {result.failed.map((item, index) => (
                  <li key={index}>
                    {item.item_code || 'Unknown'}: {item.error}
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

/**
 * Component: Complete Dashboard
 * Full-featured product seeding dashboard
 */
import React, { useState } from 'react';
import { useIndustries } from '../hooks/useIndustries';
import { useIndustryProducts } from '../hooks/useIndustryProducts';
import { useBulkUpload } from '../hooks/useBulkUpload';

const ProductSeedingDashboard = () => {
  const { industries, loading: industriesLoading, error: industriesError } = useIndustries();
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const { products, loading: productsLoading, error: productsError, totalProducts } = 
    useIndustryProducts(selectedIndustry);
  const { uploadProducts, loading: uploadLoading, result, error: uploadError } = 
    useBulkUpload();

  const handleBulkUpload = () => {
    if (window.confirm('Upload products from seed data file? This will create product templates for all industries.')) {
      uploadProducts();
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '30px' }}>Product Seeding Dashboard</h1>

      {/* Bulk Upload Section */}
      <section style={{ 
        marginBottom: '30px', 
        padding: '20px', 
        border: '1px solid #ddd',
        borderRadius: '8px',
        background: '#fafafa'
      }}>
        <h2 style={{ marginTop: 0 }}>Bulk Upload</h2>
        <p style={{ color: '#666', marginBottom: '15px' }}>
          Upload products from the seed data file. This will create product templates for all industries.
        </p>
        <button 
          onClick={handleBulkUpload} 
          disabled={uploadLoading}
          style={{ 
            padding: '12px 24px', 
            fontSize: '16px',
            backgroundColor: uploadLoading ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: uploadLoading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          {uploadLoading ? '⏳ Uploading...' : '📤 Upload Products from Seed File'}
        </button>
        
        {uploadError && (
          <div style={{ 
            color: '#721c24', 
            marginTop: '15px', 
            padding: '12px',
            background: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px'
          }}>
            <strong>Error:</strong> {uploadError}
          </div>
        )}
        
        {result && (
          <div style={{ 
            marginTop: '15px', 
            padding: '15px', 
            background: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '4px'
          }}>
            <h3 style={{ marginTop: 0 }}>✅ Upload Results:</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
              <div><strong>Created:</strong> {result.created}</div>
              <div><strong>Skipped:</strong> {result.skipped}</div>
              <div><strong>Total Processed:</strong> {result.total_processed}</div>
              {result.ignored_industries?.length > 0 && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <strong>⚠️ Ignored Industries:</strong> {result.ignored_industries.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Industry Selection */}
      <section style={{ marginBottom: '30px' }}>
        <h2>Select Industry</h2>
        {industriesLoading ? (
          <div>Loading industries...</div>
        ) : industriesError ? (
          <div style={{ color: 'red' }}>Error: {industriesError}</div>
        ) : (
          <select
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            style={{ 
              padding: '12px', 
              fontSize: '16px', 
              minWidth: '350px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
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
          ) : productsError ? (
            <div style={{ 
              color: '#721c24',
              padding: '12px',
              background: '#f8d7da',
              border: '1px solid #f5c6cb',
              borderRadius: '4px'
            }}>
              Error: {productsError}
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '18px', fontWeight: 'bold' }}>
                Total Products: <span style={{ color: '#007bff' }}>{totalProducts}</span>
              </p>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                gap: '15px',
                marginTop: '20px'
              }}>
                {products.map((product) => (
                  <div 
                    key={product.sku}
                    style={{ 
                      padding: '15px', 
                      border: '1px solid #ddd', 
                      borderRadius: '6px',
                      background: '#ffffff',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      transition: 'transform 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                  >
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '8px' }}>
                      {product.name}
                    </div>
                    <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>
                      SKU: <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: '3px' }}>
                        {product.sku}
                      </code>
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      color: '#28a745', 
                      fontWeight: 'bold'
                    }}>
                      ✓ {product.status}
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
