import re
import dns.resolver
import smtplib
import socket
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_email(email: str) -> Dict[str, Any]:
    """
    Comprehensive email validation with detailed results
    
    Returns:
        Dict containing validation status and details
    """
    result = {
        "email": email,
        "is_valid": False,
        "format_valid": False,
        "domain_valid": False,
        "smtp_valid": False,
        "errors": []
    }
    
    # Step 1: Basic format validation
    if not email or not isinstance(email, str):
        result["errors"].append("Email is empty or not a string")
        return result
    
    email = email.strip().lower()
    
    # More comprehensive regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        result["errors"].append("Invalid email format")
        return result
    
    result["format_valid"] = True
    
    # Step 2: Domain validation
    try:
        domain = email.split("@")[1]
        
        # Check if domain has valid structure
        if len(domain) < 3 or '.' not in domain:
            result["errors"].append("Invalid domain structure")
            return result
        
        # DNS MX record check
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                result["errors"].append("No MX records found for domain")
                return result
            result["domain_valid"] = True
        except dns.resolver.NXDOMAIN:
            result["errors"].append("Domain does not exist")
            return result
        except dns.resolver.NoAnswer:
            result["errors"].append("No MX records found for domain")
            return result
        except Exception as e:
            result["errors"].append(f"DNS resolution error: {str(e)}")
            return result
            
    except IndexError:
        result["errors"].append("Invalid email structure")
        return result
    
    # Step 3: SMTP validation (optional, can be disabled for performance)
    try:
        smtp = smtplib.SMTP(timeout=5)
        smtp.connect(mx_records[0].exchange.to_text())
        smtp.helo()
        smtp.mail("validator@example.com")
        code, message = smtp.rcpt(email)
        smtp.quit()
        
        if code in [250, 251]:
            result["smtp_valid"] = True
            result["is_valid"] = True
        else:
            result["errors"].append(f"SMTP validation failed: {code} - {message}")
            
    except Exception as e:
        result["errors"].append(f"SMTP validation error: {str(e)}")
        # Still consider valid if format and domain are correct
        if result["format_valid"] and result["domain_valid"]:
            result["is_valid"] = True
    
    return result

def validate_email_simple(email: str) -> bool:
    """
    Simple validation for bulk processing
    Returns only boolean result
    """
    result = is_valid_email(email)
    return result["is_valid"]
