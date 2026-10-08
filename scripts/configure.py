"""Generate local-only secrets without overwriting an existing environment."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / '.env'
with target.open('x', encoding='utf-8') as f:
    f.write(f'POSTGRES_PASSWORD={secrets.token_hex(24)}\nAIRFLOW_JWT_SECRET={secrets.token_hex(32)}\nAIRFLOW_UID=50000\n')
for name in ['logs', 'data/runs']:
    (root / name).mkdir(parents=True, exist_ok=True)
print('Local .env created; values omitted.')
