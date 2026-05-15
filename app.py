import os
import csv
import re
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from lxml import etree

from validator import validate_trial_element

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
XSD_FILE = 'who_ictrp.xsd'

# Ensure base directories exist
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

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
    """Intercepts native lxml messages and adds dynamic explanatory tips in English."""
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

    # Save uploaded file temporarily for processing
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    if not os.path.exists(XSD_FILE):
        return jsonify({'error': f'XSD file not found: {XSD_FILE}'}), 500

    try:
        xsd_doc = etree.parse(XSD_FILE)
        schema = etree.XMLSchema(xsd_doc)
        
        xml_doc = etree.parse(file_path)
        
        # Limpa relatórios antigos da memória/disco
        clean_old_csvs()

        results = {
            'success': [],
            'errors': [],
            'csv_report': None
        }

        csv_data = []
        trials = xml_doc.xpath("//*[translate(local-name(), 'TRIAL', 'trial')='trial']")
        
        if not trials: 
             return jsonify({'error': 'No <trial> elements found in the XML.'}), 400

        for i, trial in enumerate(trials):
            trial.tag = 'trial'
            try:
                trial_id = trial.find('.//trial_id').text
                safe_filename = "".join([c for c in trial_id if c.isalpha() or c.isdigit() or c in ('-','_')]).rstrip()
            except Exception:
                safe_filename = f"unknown_trial_{i+1}"
            
            filename = f"{safe_filename}.xml"

            TRUNCATE_FIELDS = {
                'hc_freetext': 3000,
                'i_freetext': 3000,
                'inclusion_criteria': 4000,
                'exclusion_criteria': 4000,
                'prim_outcome': 8000,
                'sec_outcome': 8000,
                'results_IPD_description': 2000,
                'address': 250,
                'lastname': 50,
                'agemax': 50,
                'results_summary': 4000,
                'results_outcome_measures': 8000
            }
            
            trial_warnings = []
            
            for tag, max_len in TRUNCATE_FIELDS.items():
                for element in trial.findall(f".//{tag}"):
                    if element is not None and element.text and len(element.text) > max_len:
                        # Define o ponto de corte. Ex: Se limite é 50, corta em 45 para sobrar espaço pros '...'
                        cut_point = 45 if max_len == 50 else (max_len - 3)
                        
                        # Efetua o corte e adiciona os 3 pontinhos
                        element.text = element.text[:cut_point] + "..."
                        
                        trial_warnings.append(f"Warning: The &lt;{tag}&gt; tag exceeded the allowed limit. It will be truncated at {cut_point} characters...")

            # --- Regra 7: Campo source_support com múltiplos source_name ---
            source_support_node = trial.find('.//source_support')
            if source_support_node is not None:
                # Verifica se existem múltiplos source_name
                sources = source_support_node.findall('source_name')
                if len(sources) > 1:
                    trial_warnings.append("Warning: Multiple &lt;source_name&gt; tags found under &lt;source_support&gt;. The ICTRP imports this correctly, but please verify if this is intended.")

            # --- Correção de múltiplos países (Ex: Sri Lanka) ---
            countries_node = trial.find('.//countries')
            if countries_node is not None:
                for country_elem in countries_node.findall('country2'):
                    if country_elem.text and ',' in country_elem.text:
                        country_list = [c.strip() for c in country_elem.text.split(',') if c.strip()]
                        
                        if len(country_list) > 1:
                            for c_name in country_list:
                                new_c = etree.Element('country2')
                                new_c.text = c_name[:50]
                                country_elem.addprevious(new_c)
                            
                            countries_node.remove(country_elem)
                            trial_warnings.append("Warning: Multiple countries sent in a single &lt;country2&gt; tag. They will be separated automatically. Correct behavior: use a separate tag for each country.")
            
            date_fields_to_strip = [
                'date_registration',
                'results_date_posted',
                'results_date_completed',
                'results_date_first_publication'
            ]
            
            for date_tag in date_fields_to_strip:
                date_node = trial.find(f'.//{date_tag}')
                if date_node is not None and date_node.text:
                    stripped_date = date_node.text.strip()
                    if date_node.text != stripped_date:
                        date_node.text = stripped_date
                        trial_warnings.append(f"Warning: The &lt;{date_tag}&gt; tag contained leading or trailing whitespace. The spaces were automatically ignored for import, but please correct the formatting in your source file.")
            
            is_valid, doc_tree, error_log = validate_trial_element(trial, schema)

            if is_valid:
                # O XML válido não é mais salvo no disco, apenas listado no retorno
                results['success'].append({
                    'id': safe_filename,
                    'file': filename,
                    'warnings': trial_warnings
                })
            else:
                first_error = error_log[0] if error_log else None
                error_reason = first_error.message if first_error else "Unknown Validation Error"
                safe_error_folder = sanitize_folder_name(error_reason)
                
                msgs = []
                for e in error_log:
                    better_msg = enhance_error_message(e.message, trial)
                    msgs.append(f"Line {e.line}: {better_msg}")
                    csv_data.append([safe_filename, e.line, better_msg])
                
                # O XML inválido também não é mais salvo no disco
                results['errors'].append({
                    'id': safe_filename,
                    'file': filename,
                    'folder': f"invalid/{safe_error_folder}",
                    'reasons': msgs
                })

        # Generate CSV se houver erros (é um arquivo de texto muito leve, seguro de manter até a próxima validação)
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
    
    finally:
        # Garante que o arquivo XML pesado enviado pelo usuário será deletado no fim do processo
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    print("Server running! Open http://127.0.0.1:5000 in your browser.")
    app.run(host='0.0.0.0', port=5000, debug=True)