"""Configurações globais do projeto.

Centraliza os caminhos de pastas e o arquivo de schema XSD usados em toda a
aplicação, evitando que esses valores fiquem espalhados pelo código.
"""

import os

# Configuration
UPLOAD_FOLDER = 'uploads'        # Pasta onde o XML enviado é salvo temporariamente
PROCESSED_FOLDER = 'processed'   # Pasta onde os relatórios CSV são gravados
XSD_FILE = 'who_ictrp.xsd'       # Schema XSD usado para validar os trials


def ensure_base_folders():
    """Garante que as pastas base (uploads/processed) existam ao iniciar o app."""
    for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
        os.makedirs(folder, exist_ok=True)
