import zipfile
from pathlib import Path

zip_path = Path('agentic-ai-platform.zip')
output_dir = Path('.')

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(output_dir)

print(f'Archivo descomprimido: {zip_path}')
print(f'Contenido extraído en: {output_dir.resolve()}')
