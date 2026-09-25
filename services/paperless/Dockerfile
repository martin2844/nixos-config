FROM ghcr.io/paperless-ngx/paperless-ngx:3.2.1

# The bundled llama-index Ollama adapter uses `think = kwargs.pop(...) or
# self.thinking`, so a per-request think=False falls back to its None default.
# Set the adapter default explicitly: Qwen3.5 otherwise spends its context on
# hidden reasoning and may return empty structured suggestions. This also
# applies to document chat, which has no per-request think flag in Paperless.
RUN python3 - <<'PY'
from pathlib import Path
path = Path('/usr/src/paperless/src/paperless_ai/client.py')
source = path.read_text()
anchor = '                context_window=self.settings.llm_context_size,\n'
assert source.count(anchor) == 1, 'Recheck compatibility patch for this Paperless version'
path.write_text(source.replace(anchor, anchor + '                thinking=False,\n                temperature=0.2,\n'))
PY
