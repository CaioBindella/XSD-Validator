"""Funções auxiliares de texto e limpeza de arquivos.

Reúne utilitários genéricos: remoção de relatórios antigos, sanitização de
nomes de pasta e o enriquecimento das mensagens de erro do lxml.
"""

import os
import re

from config import PROCESSED_FOLDER


def clean_old_csvs():
    """Remove arquivos CSV antigos para não acumular no servidor."""
    if os.path.exists(PROCESSED_FOLDER):
        for file in os.listdir(PROCESSED_FOLDER):
            if file.endswith('.csv'):
                os.remove(os.path.join(PROCESSED_FOLDER, file))


def sanitize_folder_name(name):
    """Sanitizes the error reason."""
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    safe_name = safe_name.replace('\n', ' ').replace('\r', '')
    return safe_name[:80].strip()


def enhance_error_message(msg, trial_element=None):
    """Intercepts native lxml messages and adds dynamic explanatory tips in English.

    intercepta a mensagem crua do lxml e, quando reconhece o
    padrão de "elemento inesperado", devolve uma dica mais clara — diferenciando
    o caso de tag duplicada do caso de tag faltando/fora de ordem.
    """
    match = re.search(r"Element '([^']+)': This element is not expected\. Expected is \( ([^ ]+) \)", msg)

    if match:
        tag_found = match.group(1)
        tag_expected = match.group(2)

        if trial_element is not None:
            ocorrencias = trial_element.findall(f".//{tag_found}")
            if len(ocorrencias) > 1:
                return (f"Duplicated Tag: The tag &lt;{tag_found}&gt; is duplicated. "
                        f"It can only appear once in this block. "
                        f"[TIP: Remove the extra &lt;{tag_found}&gt; tag.]")

        return (f"Missing or Misplaced Tag: The system required the tag &lt;{tag_expected}&gt; "
                f"in this position, but found &lt;{tag_found}&gt;. "
                f"[TIP: Check if you deleted the &lt;{tag_expected}&gt; tag or placed it in the wrong order.]")

    return msg
