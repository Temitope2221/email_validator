#!/usr/bin/env python3
"""
Simple test script for the email validator
"""

from app.core.validator import is_valid_email, validate_email_simple

def test_email_validator():
    """Test various email addresses"""
    
    test_emails = [
        "user@gmail.com",
        "test@yahoo.com", 
        "admin@company.com",
        "user+tag@gmail.com",
        "user.name@domain.com",
        "invalid-email",
        "test@nonexistentdomain.xyz",
        "user@",
        "@domain.com",
        "user@domain",
        "user@domain.",
        "user..name@domain.com",
        "user@domain..com"
    ]
    
    print("Testing Email Validator")
    print("=" * 50)
    
    for email in test_emails:
        # Test simple validation
        simple_result = validate_email_simple(email)
        
        # Test detailed validation
        detailed_result = is_valid_email(email)
        
        print(f"\nEmail: {email}")
        print(f"Simple Result: {simple_result}")
        print(f"Detailed Result: {detailed_result['is_valid']}")
        
        if detailed_result['errors']:
            print(f"Errors: {detailed_result['errors']}")
        
        print(f"Format Valid: {detailed_result['format_valid']}")
        print(f"Domain Valid: {detailed_result['domain_valid']}")
        print(f"SMTP Valid: {detailed_result['smtp_valid']}")

if __name__ == "__main__":
    test_email_validator() 