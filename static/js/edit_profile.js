
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.querySelector("#phone");
    const phoneCountryCode = document.querySelector("#phone_country_code");
    const phoneNumber = document.querySelector("#phone_number");
    const phoneCountryIso = document.querySelector("#phone_country_iso");
    const fullPhoneNumber = document.querySelector("#full_phone_number");
    const phoneError = document.querySelector("#phoneError");
    const phoneValid = document.querySelector("#phoneValid");
    const form = document.querySelector("#editProfileForm");
    
    // Get initial country from saved data or default to Uganda
    const initialCountry = "{{ user.phone_country_iso or 'ug' }}".toLowerCase();
    
    // Initialize intl-tel-input
    const iti = window.intlTelInput(phoneInput, {
        separateDialCode: true,
        nationalMode: true,
        autoPlaceholder: "aggressive",
        formatOnDisplay: true,
        initialCountry: initialCountry || "auto",
        
        geoIpLookup: function(callback) {
            fetch('https://ipapi.co/json/')
                .then(response => response.json())
                .then(data => callback(data.country_code))
                .catch(() => callback('ug'));
        },
        
        preferredCountries: ['ug', 'ke', 'tz', 'rw', 'zm', 'us', 'gb'],
        utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@18.5.3/build/js/utils.js",
        countrySearch: true,
        fixDropdownWidth: false,
        dropdownContainer: document.body,
        
        customPlaceholder: function(selectedCountryPlaceholder, selectedCountryData) {
            return "e.g. " + selectedCountryPlaceholder;
        },
    });
    
    // Function to update hidden fields - FIXED VERSION
    function updateHiddenFields() {
        const countryData = iti.getSelectedCountryData();
        
        if (countryData.dialCode) {
            phoneCountryCode.value = '+' + countryData.dialCode;
            phoneCountryIso.value = countryData.iso2 ? countryData.iso2.toUpperCase() : '';
        }
        
        // Get full E.164 number (e.g., +260977654555) - this is always correct
        const e164Number = iti.getNumber(intlTelInputUtils.numberFormat.E164);
        fullPhoneNumber.value = e164Number;
        
        // Extract the national significant number (without country code or trunk prefix)
        if (e164Number && countryData.dialCode) {
            // E.164 format never includes trunk prefix, so we just remove the country code
            const dialCodeWithPlus = '+' + countryData.dialCode;
            const nationalSignificantNumber = e164Number.substring(dialCodeWithPlus.length);
            phoneNumber.value = nationalSignificantNumber;
        } else {
            // Fallback: remove any leading zeros and non-digits
            let rawNumber = phoneInput.value.replace(/\D/g, '');
            // Remove leading zero (trunk prefix) if present
            if (rawNumber.startsWith('0')) {
                rawNumber = rawNumber.substring(1);
            }
            phoneNumber.value = rawNumber;
        }
        
        // Debug logging (remove in production)
        console.log('Country Code:', phoneCountryCode.value);
        console.log('National Number:', phoneNumber.value);
        console.log('Full E.164:', fullPhoneNumber.value);
    }
    
    // Function to validate phone number
    function validatePhone() {
        const inputValue = phoneInput.value.trim();
        
        if (!inputValue) {
            phoneError.classList.remove('show');
            phoneValid.classList.remove('show');
            phoneInput.classList.remove('error');
            return true;
        }
        
        if (iti.isValidNumber()) {
            phoneError.classList.remove('show');
            phoneValid.classList.add('show');
            phoneInput.classList.remove('error');
            updateHiddenFields();
            return true;
        } else {
            phoneError.classList.add('show');
            phoneValid.classList.remove('show');
            phoneInput.classList.add('error');
            
            const errorCode = iti.getValidationError();
            const errorMessages = {
                [intlTelInputUtils.validationError.INVALID_COUNTRY_CODE]: "Invalid country code",
                [intlTelInputUtils.validationError.TOO_SHORT]: "Phone number is too short",
                [intlTelInputUtils.validationError.TOO_LONG]: "Phone number is too long",
                [intlTelInputUtils.validationError.NOT_A_NUMBER]: "Not a valid number",
                [intlTelInputUtils.validationError.INVALID_LENGTH]: "Invalid phone number length",
            };
            
            const errorMessage = errorMessages[errorCode] || "Please enter a valid phone number";
            phoneError.querySelector('span').textContent = errorMessage;
            
            return false;
        }
    }
    
    // Event listeners
    phoneInput.addEventListener('input', function() {
        // Remove leading zero as user types (optional - better UX)
        let value = phoneInput.value;
        if (value.startsWith('0') && value.length > 1) {
            // Optionally auto-remove trunk prefix
            phoneInput.value = value.substring(1);
        }
        validatePhone();
    });
    
    phoneInput.addEventListener('blur', function() {
        validatePhone();
    });
    
    phoneInput.addEventListener('countrychange', function() {
        updateHiddenFields();
        if (phoneInput.value.trim()) {
            validatePhone();
        }
    });
    
    // Form submission
    form.addEventListener('submit', function(e) {
        const inputValue = phoneInput.value.trim();
        
        if (inputValue && !iti.isValidNumber()) {
            e.preventDefault();
            validatePhone();
            phoneInput.focus();
            return false;
        }
        
        if (inputValue) {
            updateHiddenFields();
        } else {
            phoneCountryCode.value = '';
            phoneNumber.value = '';
            phoneCountryIso.value = '';
            fullPhoneNumber.value = '';
        }
    });
    
    // Initialize values on load
    setTimeout(function() {
        if (phoneInput.value.trim()) {
            updateHiddenFields();
        }
    }, 500);
});