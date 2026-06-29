from config import active_adapter
import markdown
import os
import json
import random
from datetime import datetime, timezone
import pytz


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
settings_path = os.path.join(BASE_DIR, 'static', 'settings.json')


admin_mode = False

last_utt_id = ""

def processed_quotes(utt_text):
    lines = utt_text.split('\n')
    wrapped_lines = []
    quote_block = []

    for line in lines:
        if '&gt;' in line.strip():
            quote_block.append(line.strip().replace('&gt;', '', 1))
        else:
            if quote_block:
                wrapped_lines.append('<div class="quote-container">\n' + '\n'.join(quote_block) +'\n</div>')
                quote_block = []
            wrapped_lines.append(line)
    if quote_block:
        wrapped_lines.append('<div class="quote-container">\n' + '\n'.join(quote_block) +'\n</div>')
    if '&gt' in '\n'.join(wrapped_lines):
        return processed_quotes('\n'.join(wrapped_lines))
    return '\n'.join(wrapped_lines)