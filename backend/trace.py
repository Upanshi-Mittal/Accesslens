import traceback
import sys

try:
    import app.main
except Exception as e:
    traceback.print_exc()
