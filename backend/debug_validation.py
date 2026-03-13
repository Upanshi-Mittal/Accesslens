from urllib.parse import urlparse
import sys

url = "not-a-valid-url"
parsed = urlparse(url)
print(f"URL: {url}")
print(f"Scheme: '{parsed.scheme}'")
print(f"Netloc: '{parsed.netloc}'")
print(f"Hostname: '{parsed.hostname}'")

if not parsed.scheme or not parsed.netloc:
    print("INVALID")
else:
    print("VALID")
