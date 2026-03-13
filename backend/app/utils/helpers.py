import re
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import hashlib
import time

def generate_selector(tag: str, attributes: Dict[str, str], index: int = 0) -> str:

    if 'id' in attributes and attributes['id']:
        return f"#{attributes['id']}"

    selector = tag

    if 'class' in attributes and attributes['class']:
        classes = attributes['class'].split()
        selector += '.' + '.'.join(classes)

    if index > 0:
        selector += f":nth-child({index})"

    return selector

def extract_domain(url: str) -> str:

    try:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path
    except:
        return url

def normalize_url(url: str) -> str:

    try:
        parsed = urlparse(url)

        parsed = parsed._replace(fragment='')

        path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
        parsed = parsed._replace(path=path)
        return parsed.geturl()
    except:
        return url

def format_duration(seconds: float) -> str:

    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:

    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

def safe_json_parse(json_str: str, default: Any = None) -> Any:

    if not json_str:
        return default

    try:
        return json.loads(json_str)
    except:
        return default

def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = True) -> Dict:

    result = dict1.copy()

    for key, value in dict2.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep)
        else:
            result[key] = value

    return result

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:

    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

def generate_hash(data: Any) -> str:

    if not isinstance(data, str):
        data = json.dumps(data, sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()

def extract_element_path(selector: str) -> List[str]:

    return [s.strip() for s in selector.split(' > ')]

def is_valid_email(email: str) -> bool:

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:


    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + '.' + ext if ext else name[:255]
    return filename

class Timer:


    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):

        self.start_time = time.time()
        return self

    def stop(self):

        self.end_time = time.time()
        return self

    def elapsed(self) -> float:

        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()