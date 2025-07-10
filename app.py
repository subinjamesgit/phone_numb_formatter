from flask import Flask, render_template, request
import phonenumbers
import re

app = Flask(__name__)

# Helper function to format phone numbers
def extract_digits_from_url(raw):
    # Extract digits from wa.me or similar URLs
    match = re.search(r'(?:wa\.me/|/)(\d{10,15})', raw)
    if match:
        return match.group(1)
    return raw

def format_phone_number(raw_number):
    print(f"INPUT: {repr(raw_number)}")
    original = raw_number.strip()
    # Step 1: Extract from WhatsApp/URL if present
    raw = extract_digits_from_url(original)
    # Step 2: Remove all noise (spaces, hyphens, brackets, periods, slashes, etc.)
    cleaned = re.sub(r'[\s\-()./]', '', raw)
    # Step 2.5: Remove leading zeros (except for '00' international prefix)
    if cleaned.startswith('00'):
        pass  # handled in next step
    else:
        cleaned = cleaned.lstrip('0')
    # Step 2.6: Remove one or more zeros after a leading plus sign
    if cleaned.startswith('+0'):
        # Remove all zeros after the plus
        cleaned = '+' + cleaned.lstrip('+0')
    print(f"RAW: {repr(raw_number)} CLEANED: {repr(cleaned)}")
    # Step 3: Handle mixed alphabets (invalid)
    if re.search(r'[a-zA-Z]', cleaned):
        cleaned = ''  # Will fall through to final fallback
    # Step 4: Handle double prefix (e.g., +910...)
    if cleaned.startswith('+91') and len(cleaned) > 13 and cleaned[3] == '0':
        # Remove all leading zeros after +91
        rest = cleaned[3:]
        rest = rest.lstrip('0')
        cleaned = '+91' + rest
    # Step 4.5: Handle numbers like '+0...' (should be +91...)
    if cleaned.startswith('+0'):
        digits = cleaned.lstrip('+0')
        if len(digits) == 10 and digits[0] in '7896':
            return f"'+91{digits}'"
    # Step 5: If starts with '00', replace with '+' and validate as international
    if cleaned.startswith('00'):
        plus_number = '+' + cleaned[2:]
        try:
            parsed = phonenumbers.parse(plus_number, None)
            if phonenumbers.is_valid_number(parsed):
                return f"'+{re.sub(r'[^\d]', '', plus_number)}'"
            else:
                digits = re.sub(r'\D', '', plus_number.lstrip('+'))
                if len(digits) == 10:
                    return f"'+91{digits}'"
        except Exception:
            digits = re.sub(r'\D', '', plus_number.lstrip('+'))
            if len(digits) == 10:
                return f"'+91{digits}'"
    # Step 6: If starts with '+', validate as international
    if cleaned.startswith('+'):
        try:
            parsed = phonenumbers.parse(cleaned, None)
            is_valid = phonenumbers.is_valid_number(parsed)
            if is_valid:
                # Edge: +91 but not 13 chars
                if parsed.country_code == 91 and len(cleaned) != 13:
                    cleaned = ''  # Will fall through to final fallback
                else:
                    return f"'+{re.sub(r'[^\d]', '', cleaned)}'"
        except Exception:
            pass
        # Fallback: always runs if not valid
        digits_no_plus = re.sub(r'\D', '', cleaned.lstrip('+'))
        if len(digits_no_plus) == 10 and digits_no_plus[0] in '7896':
            return f"'+91{digits_no_plus}'"
    # Step 7: If starts with '91' and 12 digits, add '+'
    if cleaned.startswith('91') and len(cleaned) == 12:
        try:
            parsed = phonenumbers.parse('+' + cleaned, None)
            if phonenumbers.is_valid_number(parsed):
                return f"'+{re.sub(r'[^\d]', '', cleaned)}'"
        except Exception:
            pass
    # Step 8: If starts with '0' and 10 digits after, convert to +91
    if cleaned.startswith('0') and len(cleaned) == 11:
        digits = cleaned.lstrip('0')
        if len(digits) == 10:
            return f"'+91{digits}'"
    # Step 9: If starts with 7/8/9/6 and 10 digits, add +91
    if len(cleaned) == 10 and cleaned[0] in '7896':
        return f"'+91{cleaned}'"
    # Step 10: If more than 10 digits and no '+', try to match as international
    digits_only = re.sub(r'\D', '', cleaned)
    if len(digits_only) > 10 and not cleaned.startswith('+'):
        try:
            parsed = phonenumbers.parse('+' + digits_only, None)
            if phonenumbers.is_valid_number(parsed):
                return f"'+{digits_only}'"
        except Exception:
            pass
    # Final fallback: For any number not valid for any country, attach '+'
    return f"'+{digits_only}'" if digits_only else original

def format_phone_number_pair(raw_number):
    formatted = format_phone_number(raw_number)
    # Excel compatible: single quote at start, plus sign, no trailing quote
    if formatted.startswith("'+") and formatted.endswith("'"):
        excel_compatible = "'+" + formatted[2:-1]
        normal = formatted[1:-1]
    elif formatted.startswith("'+"):
        excel_compatible = formatted
        normal = formatted[1:]
    elif formatted.startswith('+'):
        excel_compatible = "'" + formatted  # ensures '+...' becomes ''+...'
        normal = formatted
    else:
        excel_compatible = formatted
        normal = formatted
    return excel_compatible, normal

@app.route('/', methods=['GET', 'POST'])
def index():
    formatted_numbers = []
    input_numbers = []
    if request.method == 'POST':
        numbers = request.form.get('numbers', '')
        # Split by newlines or commas
        raw_numbers = re.split(r'[\n,]+', numbers)
        input_numbers = [num.strip() for num in raw_numbers if num.strip()]
        formatted_numbers = [format_phone_number_pair(num) for num in input_numbers]
    return render_template('index.html', formatted_numbers=formatted_numbers, input_numbers=input_numbers)

if __name__ == '__main__':
    app.run(debug=True) 
