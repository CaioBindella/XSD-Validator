import os
import shutil
import csv
import re
import io
import zipfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from lxml import etree

# Import the validation logic from your module
from validator import validate_trial_element

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
SUCCESS_FOLDER = os.path.join(PROCESSED_FOLDER, 'success')
INVALID_FOLDER = os.path.join(PROCESSED_FOLDER, 'invalid')
XSD_FILE = 'who_ictrp.xsd'

# Ensure directories exist
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, SUCCESS_FOLDER, INVALID_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def clean_processing_folders():
    """Clears the output folders before a new validation run."""
    for pasta in [SUCCESS_FOLDER, INVALID_FOLDER]:
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
            os.makedirs(pasta)

def sanitize_folder_name(name):
    """Sanitizes the error reason to create a valid OS directory name."""
    # Remove invalid characters for folders (\ / * ? : " < > |)
    safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Remove newlines and limit to 80 characters to avoid OS path length issues
    safe_name = safe_name.replace('\n', ' ').replace('\r', '')
    return safe_name[:80].strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<filename>')
def download_csv(filename):
    """Route to download the generated CSV report."""
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Save uploaded file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Check if XSD exists
    if not os.path.exists(XSD_FILE):
        return jsonify({'error': f'XSD file not found: {XSD_FILE}'}), 500

    try:
        # Load XSD Schema
        xsd_doc = etree.parse(XSD_FILE)
        schema = etree.XMLSchema(xsd_doc)
        
        # Load the large XML file
        xml_doc = etree.parse(file_path)
        
        # Clean old results
        clean_processing_folders()

        results = {
            'success': [],
            'errors': [],
            'csv_report': None
        }

        # Data structure to hold CSV rows
        csv_data = []

        # Find all <trial> elements
        trials = xml_doc.findall('.//trial')

        if not trials:
             return jsonify({'error': 'No <trial> elements found in the XML.'}), 400

        for i, trial in enumerate(trials):
            # Extract ID for filename (sanitize it)
            try:
                trial_id = trial.find('.//trial_id').text
                safe_filename = "".join([c for c in trial_id if c.isalpha() or c.isdigit() or c in ('-','_')]).rstrip()
            except Exception:
                safe_filename = f"unknown_trial_{i+1}"
            
            filename = f"{safe_filename}.xml"

            # --- CALLING THE MODULARIZED FUNCTION FROM VALIDATOR.PY ---
            is_valid, doc_tree, error_log = validate_trial_element(trial, schema)

            if is_valid:
                # Save to success folder
                output_path = os.path.join(SUCCESS_FOLDER, filename)
                doc_tree.write(output_path, pretty_print=True, encoding='utf-8')
                
                results['success'].append({
                    'id': safe_filename,
                    'file': filename
                })
            else:
                # Get the first error message to categorize the folder
                first_error = error_log[0] if error_log else None
                error_reason = first_error.message if first_error else "Unknown Validation Error"
                safe_error_folder = sanitize_folder_name(error_reason)
                
                # Create the specific error folder: processed/invalid/<error_reason>/
                specific_invalid_folder = os.path.join(INVALID_FOLDER, safe_error_folder)
                os.makedirs(specific_invalid_folder, exist_ok=True)
                
                # Save the invalid XML inside its specific category folder
                output_path = os.path.join(specific_invalid_folder, filename)
                doc_tree.write(output_path, pretty_print=True, encoding='utf-8')
                
                # Format error messages for UI and append to CSV data
                msgs = []
                for e in error_log:
                    msgs.append(f"Line {e.line}: {e.message}")
                    # Prepare CSV row: [Trial ID, Line Number, Error Reason]
                    csv_data.append([safe_filename, e.line, e.message])
                
                results['errors'].append({
                    'id': safe_filename,
                    'file': filename,
                    'folder': f"invalid/{safe_error_folder}",
                    'reasons': msgs
                })

        # Generate CSV if there are any errors
        if csv_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"error_report_{timestamp}.csv"
            csv_filepath = os.path.join(PROCESSED_FOLDER, csv_filename)
            
            with open(csv_filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Trial ID', 'Line Number', 'Error Reason'])
                writer.writerows(csv_data)
            
            results['csv_report'] = csv_filename

        return jsonify(results)

    except etree.XMLSyntaxError as e:
        return jsonify({'error': f'XML Syntax Error in uploaded file: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected Error: {str(e)}'}), 500
    
@app.route('/download_success')
def download_success():
    """Route to download all successful valid XMLs as a ZIP file."""
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Percorre a pasta SUCCESS_FOLDER e adiciona cada arquivo ao zip
        for root, _, files in os.walk(SUCCESS_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                # Adiciona o arquivo usando apenas o nome dele, ignorando diretórios locais do servidor
                zf.write(file_path, file)
    
    memory_file.seek(0)
    return send_file(memory_file, download_name='valid_trials.zip', as_attachment=True)

@app.route('/download_invalid')
def download_invalid():
    """Route to download all invalid XMLs and the CSV report as a ZIP file."""
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        
        # 1. Adicionar os arquivos XML inválidos (mantendo a estrutura de subpastas dos erros)
        for root, _, files in os.walk(INVALID_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                # Cria um caminho relativo para manter as pastas categorizadas dentro do ZIP
                # Colocamos tudo dentro de uma pasta base chamada "xmls_com_erro"
                arcname = os.path.join('xmls_com_erro', os.path.relpath(file_path, INVALID_FOLDER))
                zf.write(file_path, arcname)
        
        # 2. Procurar pelo relatório CSV na pasta de processados e adicionar à raiz do ZIP
        for file in os.listdir(PROCESSED_FOLDER):
            if file.endswith('.csv'):
                file_path = os.path.join(PROCESSED_FOLDER, file)
                # Salva o arquivo CSV solto na raiz do arquivo ZIP
                zf.write(file_path, file)
                
    memory_file.seek(0)
    return send_file(memory_file, download_name='invalid_trials_and_report.zip', as_attachment=True)

if __name__ == '__main__':
    print("Server running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)