"""Ponto de entrada da aplicação Flask (Validador XSD de trials).

Define as rotas HTTP e orquestra o fluxo de validação: recebe o XML enviado,
aplica as correções de pré-processamento, valida cada <trial> contra o XSD e
monta os relatórios de sucesso, erro e avisos. A lógica de detalhe vive nos
módulos auxiliares (config, helpers, trial_processor e reports).
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from lxml import etree

from validator import validate_trial_element
from config import UPLOAD_FOLDER, PROCESSED_FOLDER, XSD_FILE, ensure_base_folders
from helpers import clean_old_csvs, sanitize_folder_name, enhance_error_message
from trial_processor import preprocess_trial, check_empty_fields
from reports import write_error_report, write_warning_report

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# Limite generoso (500MB) só para dar uma mensagem clara em vez de um erro
# genérico caso o upload estoure. Não é a causa conhecida de falhas com
# arquivos grandes — isso costuma estar no timeout do proxy/gunicorn na VPS.
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Ensure base directories exist
ensure_base_folders()


@app.errorhandler(413)
def file_too_large(e):
    """Devolve um JSON claro quando o upload excede MAX_CONTENT_LENGTH."""
    return jsonify({'error': 'Uploaded file is too large (limit: 500MB).'}), 413


@app.route('/')
def index():
    """Renderiza a página inicial com o formulário de upload."""
    return render_template('index.html')


@app.route('/download/<filename>')
def download_csv(filename):
    """Route to download the generated CSV report.

    Em português: disponibiliza para download um relatório CSV já gerado na
    pasta de processados.
    """
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


@app.route('/process', methods=['POST'])
def process_file():
    """Recebe o XML, valida cada trial contra o XSD e devolve o resultado em JSON.

    Salva o upload temporariamente, pré-processa e valida cada <trial>, separa
    os sucessos dos erros, grava os relatórios CSV e, ao final, remove o arquivo
    enviado. Erros de sintaxe ou inesperados são retornados como JSON de erro.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save uploaded file temporarily for processing
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    if not os.path.exists(XSD_FILE):
        return jsonify({'error': f'XSD file not found: {XSD_FILE}'}), 500

    try:
        xsd_doc = etree.parse(XSD_FILE)
        schema = etree.XMLSchema(xsd_doc)

        # Nomes de tags válidos (em minúsculo) -> grafia correta, extraídos do
        # próprio XSD. Usado para aceitar tags com capitalização errada
        # (ex: <Scientific_acronym>) como warning em vez de erro.
        valid_tags = {
            name.lower(): name
            for name in xsd_doc.xpath('//xs:element/@name', namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})
        }

        xml_doc = etree.parse(file_path)

        # Limpa relatórios antigos da memória/disco
        clean_old_csvs()

        results = {
            'success': [],
            'errors': [],
            'csv_report': None,
            'csv_warning_report': None
        }

        csv_data = []
        warning_csv_data = []
        trials = xml_doc.xpath("//*[translate(local-name(), 'TRIAL', 'trial')='trial']")

        if not trials:
            return jsonify({'error': 'No <trial> elements found in the XML.'}), 400

        for i, trial in enumerate(trials):
            trial.tag = 'trial'
            try:
                trial_id = trial.find('.//trial_id').text
                safe_filename = "".join([c for c in trial_id if c.isalpha() or c.isdigit() or c in ('-', '_')]).rstrip()
            except Exception:
                safe_filename = f"unknown_trial_{i+1}"

            filename = f"{safe_filename}.xml"

            trial_warnings = preprocess_trial(trial, valid_tags)

            # Aplica a política de campos vazios (EMPTY_FIELD_POLICY):
            # campos vazios marcados como 'warning' viram avisos; os marcados
            # como 'error' tornam o trial inválido.
            policy_errors, policy_warnings = check_empty_fields(trial)
            trial_warnings.extend(policy_warnings)

            is_valid, doc_tree, error_log = validate_trial_element(trial, schema)

            if is_valid and not policy_errors:
                # O XML válido não é mais salvo no disco, apenas listado no retorno
                results['success'].append({
                    'id': trial_id,
                    'file': filename,
                    'warnings': trial_warnings
                })

                for w in trial_warnings:
                    warning_csv_data.append([trial_id, w])
            else:
                first_error = error_log[0] if error_log else None
                error_reason = first_error.message if first_error else (
                    policy_errors[0][1] if policy_errors else "Unknown Validation Error"
                )
                safe_error_folder = sanitize_folder_name(error_reason)

                msgs = []
                for e in error_log:
                    better_msg = enhance_error_message(e.message, trial)
                    msgs.append(f"Line {e.line}: {better_msg}")
                    csv_data.append([trial_id, e.line, better_msg])

                # Erros vindos da política de campos vazios obrigatórios
                for line, better_msg in policy_errors:
                    msgs.append(f"Line {line}: {better_msg}")
                    csv_data.append([trial_id, line, better_msg])

                # O XML inválido também não é mais salvo no disco
                results['errors'].append({
                    'id': trial_id,
                    'file': filename,
                    'folder': f"invalid/{safe_error_folder}",
                    'reasons': msgs
                })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if csv_data:
            results['csv_report'] = write_error_report(csv_data, timestamp)

        if warning_csv_data:
            results['csv_warning_report'] = write_warning_report(warning_csv_data, timestamp)

        return jsonify(results)

    except etree.XMLSyntaxError as e:
        return jsonify({'error': f'XML Syntax Error in uploaded file: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected Error: {str(e)}'}), 500

    finally:
        # Garante que o arquivo XML pesado enviado pelo usuário será deletado no fim do processo
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == '__main__':
    print("Server running! Open http://127.0.0.1:5000 in your browser.")
    app.run(host='0.0.0.0', port=5000, debug=True)
