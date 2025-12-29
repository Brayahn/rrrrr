# Email and Phone Verification API Documentation

## Overview

The Verification API provides OTP (One-Time Password) based verification for email addresses and phone numbers during user registration. This ensures that users provide valid contact information and helps prevent fake accounts.

## Features

- **Email Verification**: Send 6-digit OTP codes via email
- **Phone Verification**: Send 6-digit OTP codes via SMS
- **Security Features**:
  - OTP codes expire after 15 minutes
  - Maximum 3 verification attempts per code
  - Rate limiting (60 seconds between resend requests)
  - Verified status stored for 24 hours

## API Endpoints

### 1. Send Email Verification Code

Send a verification code to the user's email address.

**Endpoint:** `savanna_pos.savanna_pos.apis.verification_api.send_email_verification`

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Verification code has been sent to your email address",
  "expires_in_minutes": 15
}
```

**Error Responses:**
- `400 Bad Request`: Invalid email format or email already registered
- `429 Too Many Requests`: Resend cooldown active (wait 60 seconds)

---

### 2. Send Phone Verification Code

Send a verification code to the user's phone number via SMS.

**Endpoint:** `savanna_pos.savanna_pos.apis.verification_api.send_phone_verification`

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request Body:**
```json
{
  "phone": "+254712345678"
}
```

**Note:** Phone number should include country code (e.g., +254 for Kenya)

**Response:**
```json
{
  "success": true,
  "message": "Verification code has been sent to your phone number",
  "expires_in_minutes": 15
}
```

**Error Responses:**
- `400 Bad Request`: Invalid phone format or phone already registered
- `429 Too Many Requests`: Resend cooldown active (wait 60 seconds)
- `500 Internal Server Error`: SMS service not configured

**Prerequisites:** SMS Settings must be configured in Frappe for SMS verification to work.

---

### 3. Verify Email Code

Verify the email verification code entered by the user.

**Endpoint:** `savanna_pos.savanna_pos.apis.verification_api.verify_email_code`

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "verified": true
}
```

**Response (Already Verified):**
```json
{
  "success": true,
  "message": "Email has already been verified",
  "verified": true
}
```

**Error Responses:**
- `400 Bad Request`: Invalid code or code expired
- `429 Too Many Requests`: Maximum verification attempts exceeded

---

### 4. Verify Phone Code

Verify the phone verification code entered by the user.

**Endpoint:** `savanna_pos.savanna_pos.apis.verification_api.verify_phone_code`

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request Body:**
```json
{
  "phone": "+254712345678",
  "code": "123456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Phone number verified successfully",
  "verified": true
}
```

**Response (Already Verified):**
```json
{
  "success": true,
  "message": "Phone number has already been verified",
  "verified": true
}
```

**Error Responses:**
- `400 Bad Request`: Invalid code or code expired
- `429 Too Many Requests`: Maximum verification attempts exceeded

---

### 5. Check Verification Status

Check if an email or phone number has been verified.

**Endpoint:** `savanna_pos.savanna_pos.apis.verification_api.check_verification_status`

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request Body:**
```json
{
  "identifier": "user@example.com",
  "verification_type": "email"
}
```

**Or for phone:**
```json
{
  "identifier": "+254712345678",
  "verification_type": "phone"
}
```

**Response (Verified):**
```json
{
  "verified": true,
  "message": "Email has been verified",
  "verified_at": "2024-01-15T10:30:00"
}
```

**Response (Not Verified):**
```json
{
  "verified": false,
  "message": "Verification pending",
  "expires_at": "2024-01-15T10:45:00"
}
```

**Response (Expired):**
```json
{
  "verified": false,
  "message": "Verification code has expired"
}
```

---

## Integration with User Registration

The verification system can be integrated with user registration in two ways:

### Option 1: Verification Before Registration (Recommended)

1. User requests verification code
2. User enters verification code
3. User registers with verified email/phone

**Example Flow:**
```javascript
// Step 1: Send verification code
await fetch('/api/method/savanna_pos.savanna_pos.apis.verification_api.send_email_verification', {
  method: 'POST',
  body: JSON.stringify({ email: 'user@example.com' })
});

// Step 2: User enters code, verify it
await fetch('/api/method/savanna_pos.savanna_pos.apis.verification_api.verify_email_code', {
  method: 'POST',
  body: JSON.stringify({ 
    email: 'user@example.com',
    code: '123456'
  })
});

// Step 3: Register user with verification code
await fetch('/api/method/savanna_pos.savanna_pos.apis.auth_api.register_user', {
  method: 'POST',
  body: JSON.stringify({
    email: 'user@example.com',
    first_name: 'John',
    last_name: 'Doe',
    password: 'securepassword123',
    require_email_verification: true,
    email_verification_code: '123456'
  })
});
```

### Option 2: Verification After Registration

1. User registers without verification
2. System sends verification code
3. User verifies email/phone later

**Example Flow:**
```javascript
// Step 1: Register user
await fetch('/api/method/savanna_pos.savanna_pos.apis.auth_api.register_user', {
  method: 'POST',
  body: JSON.stringify({
    email: 'user@example.com',
    first_name: 'John',
    last_name: 'Doe',
    password: 'securepassword123'
  })
});

// Step 2: Send verification code after registration
await fetch('/api/method/savanna_pos.savanna_pos.apis.verification_api.send_email_verification', {
  method: 'POST',
  body: JSON.stringify({ email: 'user@example.com' })
});

// Step 3: User verifies later
await fetch('/api/method/savanna_pos.savanna_pos.apis.verification_api.verify_email_code', {
  method: 'POST',
  body: JSON.stringify({ 
    email: 'user@example.com',
    code: '123456'
  })
});
```

---

## Configuration

### Email Verification

Email verification uses Frappe's built-in email system. Ensure that:
1. Email Account is configured in Frappe (Setup > Email Account)
2. Outgoing email server is properly configured
3. Email domain is verified (if required)

### SMS Verification

SMS verification requires SMS Settings to be configured:

1. Go to **Setup > Settings > SMS Settings**
2. Configure your SMS gateway:
   - SMS Gateway URL
   - Message Parameter
   - Receiver Parameter
   - Gateway-specific parameters

**Example SMS Gateway Configuration:**
- Gateway URL: `https://api.smsprovider.com/send`
- Message Parameter: `message`
- Receiver Parameter: `to`
- Method: POST

---

## Security Considerations

1. **OTP Expiry**: Codes expire after 15 minutes for security
2. **Rate Limiting**: 60-second cooldown between resend requests prevents abuse
3. **Attempt Limits**: Maximum 3 verification attempts per code
4. **Verified Status**: Verified status is stored for 24 hours in cache
5. **Code Generation**: Uses cryptographically secure random number generation

---

## Best Practices

1. **Always verify before registration**: This prevents fake accounts
2. **Show clear error messages**: Help users understand what went wrong
3. **Implement resend functionality**: Allow users to request new codes after cooldown
4. **Handle SMS failures gracefully**: SMS may fail due to network issues or configuration
5. **Store verification status**: Check verification status before allowing sensitive operations

---

## Error Handling

### Common Errors

1. **"Verification code not found or expired"**
   - Solution: Request a new verification code

2. **"Maximum verification attempts exceeded"**
   - Solution: Request a new verification code

3. **"Please wait X seconds before requesting a new verification code"**
   - Solution: Wait for the cooldown period to expire

4. **"SMS service is not configured"**
   - Solution: Configure SMS Settings in Frappe admin panel

5. **"Failed to send verification email/SMS"**
   - Solution: Check email/SMS configuration and try again

---

## Example Implementation

### React/JavaScript Example

```javascript
class VerificationService {
  async sendEmailVerification(email) {
    const response = await fetch(
      '/api/method/savanna_pos.savanna_pos.apis.verification_api.send_email_verification',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      }
    );
    return response.json();
  }

  async verifyEmailCode(email, code) {
    const response = await fetch(
      '/api/method/savanna_pos.savanna_pos.apis.verification_api.verify_email_code',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code })
      }
    );
    return response.json();
  }

  async sendPhoneVerification(phone) {
    const response = await fetch(
      '/api/method/savanna_pos.savanna_pos.apis.verification_api.send_phone_verification',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      }
    );
    return response.json();
  }

  async verifyPhoneCode(phone, code) {
    const response = await fetch(
      '/api/method/savanna_pos.savanna_pos.apis.verification_api.verify_phone_code',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code })
      }
    );
    return response.json();
  }
}
```

---

## Testing

### Test Email Verification

1. Send verification code to a test email
2. Check email inbox for 6-digit code
3. Verify code using the API
4. Check verification status

### Test Phone Verification

1. Ensure SMS Settings are configured
2. Send verification code to a test phone number
3. Check SMS for 6-digit code
4. Verify code using the API
5. Check verification status

---

## Troubleshooting

### Email Not Received

1. Check spam/junk folder
2. Verify email account configuration
3. Check email queue in Frappe (Email Queue doctype)
4. Verify email domain is not blacklisted

### SMS Not Received

1. Verify SMS Settings configuration
2. Check SMS gateway logs
3. Verify phone number format (include country code)
4. Test SMS gateway directly
5. Check SMS queue in Frappe

### Verification Code Expired

- Codes expire after 15 minutes
- Request a new code if expired
- Implement auto-refresh in frontend if needed

---

## Support

For issues or questions:
1. Check Frappe logs for detailed error messages
2. Verify email/SMS configuration
3. Test with a known working email/phone number
4. Contact system administrator for configuration issues

