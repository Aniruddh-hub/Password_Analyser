import hashlib
import requests
from zxcvbn import zxcvbn

def check_pwned_api(password: str) -> int:
    """
    Checks the Have I Been Pwned API securely using k-Anonymity (SHA-1 prefix).
    Returns the number of times the password has been exposed in breaches.
    """
    if not password:
        return 0
        
    sha1password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1password[:5], sha1password[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return -1 # Error querying API
            
        hashes = (line.split(':') for line in response.text.splitlines())
        for h, count in hashes:
            if h == suffix:
                return int(count)
        return 0
    except requests.RequestException:
        return -1 # Error querying API

def analyze_password(password: str) -> dict:
    """
    Analyzes the password strength and breach count.
    Returns a combined dictionary of metrics.
    """
    if not password:
        return {
            "score": 0,
            "crack_time_str": "instant",
            "crack_time_sec": 0,
            "feedback": {"warning": "", "suggestions": []},
            "pwned_count": 0
        }

    # Run zxcvbn analysis locally
    result = zxcvbn(password)
    
    # Check HIBP API securely
    pwned_count = check_pwned_api(password)
    
    return {
        "score": result.get("score", 0),
        "crack_time_str": result.get("crack_times_display", {}).get("offline_slow_hashing_1e4_per_second", "N/A"),
        "crack_time_sec": result.get("crack_times_seconds", {}).get("offline_slow_hashing_1e4_per_second", 0),
        "feedback": result.get("feedback", {"warning": "", "suggestions": []}),
        "pwned_count": pwned_count
    }
