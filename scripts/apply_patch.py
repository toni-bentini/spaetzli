#!/usr/bin/env python3
"""Apply Spaetzli patch to Rotki premium.py"""

import re
import sys

if len(sys.argv) < 2:
    print("Usage: apply_patch.py <path_to_premium.py>")
    sys.exit(1)

premium_py = sys.argv[1]

with open(premium_py, 'r') as f:
    content = f.read()

# Check if already patched
if 'SPAETZLI_MOCK_URL' in content:
    print("✅ Patch already applied")
    sys.exit(0)

new_code = """# Support custom mock server via environment variables (Spaetzli)
        if mock_url := os.environ.get('SPAETZLI_MOCK_URL'):
            log.info(f'Using Spaetzli mock server at {mock_url}')
            self.rotki_api = f'{mock_url}/api/{self.apiversion}/'
            self.rotki_web = f'{mock_url}/webapi/{self.apiversion}/'
            self.rotki_nest = f'{mock_url}/nest/{self.apiversion}/'
        else:
            self.rotki_api = f'https://{rotki_base_url}/api/{self.apiversion}/'
            self.rotki_web = f'https://{rotki_base_url}/webapi/{self.apiversion}/'
            self.rotki_nest = f'https://{rotki_base_url}/nest/{self.apiversion}/'"""

# Replace the three URL assignments with our conditional version
old_urls = r"self\.rotki_api = f'https://\{rotki_base_url\}/api/\{self\.apiversion\}/'\s*\n\s*self\.rotki_web = f'https://\{rotki_base_url\}/webapi/\{self\.apiversion\}/'\s*\n\s*self\.rotki_nest = f'https://\{rotki_base_url\}/nest/\{self\.apiversion\}/'"

if re.search(old_urls, content):
    content = re.sub(old_urls, new_code, content)
    with open(premium_py, 'w') as f:
        f.write(content)
    print("✅ Patch applied successfully")
else:
    print("⚠️  Could not find expected pattern in premium.py")
    print("   The file structure may have changed in this version of Rotki")
    sys.exit(1)
