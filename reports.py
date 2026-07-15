"""Geração dos relatórios CSV.

Responsável por gravar em disco os dois relatórios produzidos pela validação:
o de erros (trials inválidos) e o de avisos (correções automáticas aplicadas).
"""

import os
import csv

from config import PROCESSED_FOLDER

# Caracteres que o Excel/Sheets interpretam como início de fórmula.
_FORMULA_TRIGGER_CHARS = ('=', '+', '-', '@')


def _sanitize_csv_row(row):
    """Neutraliza CSV/Formula Injection.

    trial_id vem do XML do usuário sem restrição de conteúdo; se começar com
    =, +, - ou @, o Excel/Sheets pode interpretá-lo como fórmula ao abrir o
    relatório. Prefixando com um apóstrofo, vira texto literal.
    """
    sanitized = []
    for value in row:
        if value is None:
            sanitized.append('')
            continue
        text = str(value)
        if text and text[0] in _FORMULA_TRIGGER_CHARS:
            text = "'" + text
        sanitized.append(text)
    return sanitized


def write_error_report(csv_data, timestamp):
    """Gera o CSV de erros de validação e devolve o nome do arquivo gerado.

    É um arquivo de texto muito leve, seguro de manter até a próxima validação.
    """
    csv_filename = f"error_report_{timestamp}.csv"
    csv_filepath = os.path.join(PROCESSED_FOLDER, csv_filename)

    with open(csv_filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Trial ID', 'Line Number', 'Error Reason'])
        writer.writerows(_sanitize_csv_row(row) for row in csv_data)

    return csv_filename


def write_warning_report(warning_csv_data, timestamp):
    """Gera o CSV de avisos (correções automáticas) e devolve o nome do arquivo."""
    warning_csv_filename = f"warning_report_{timestamp}.csv"
    warning_csv_filepath = os.path.join(PROCESSED_FOLDER, warning_csv_filename)

    with open(warning_csv_filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Trial ID', 'Warning Message'])
        writer.writerows(_sanitize_csv_row(row) for row in warning_csv_data)

    return warning_csv_filename
