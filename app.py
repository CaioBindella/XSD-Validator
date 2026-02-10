import os
import shutil
from flask import Flask, render_template, request, jsonify
from lxml import etree
# Import the validation logic from your module
from validator import validate_trial_element

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
SUCCESS_FOLDER = 'processed/success'
INVALID_FOLDER = 'processed/invalid'
XSD_FILE = 'who_ictrp.xsd'

# Ensure directories exist
for folder in [UPLOAD_FOLDER, SUCCESS_FOLDER, INVALID_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def clean_processing_folders():
    """Clears the output folders before a new validation run."""
    for folder in [SUCCESS_FOLDER, INVALID_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)

@app.route('/')
def index():
    return render_template('index.html')

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
        # Load XSD Schema once
        xsd_doc = etree.parse(XSD_FILE)
        schema = etree.XMLSchema(xsd_doc)
        
        # Load the large XML file
        xml_doc = etree.parse(file_path)
        
        # Clean old results
        clean_processing_folders()

        results = {
            'success': [],
            'errors': []
        }

        # Find all <trial> elements
        trials = xml_doc.findall('.//trial')

        if not trials:
             return jsonify({'error': 'No <trial> elements found in the XML.'}), 400

        for i, trial in enumerate(trials):
            # Extract ID for filename (sanitize it)
            try:
                trial_id = trial.find('.//trial_id').text
                safe_filename = "".join([c for c in trial_id if c.isalpha() or c.isdigit() or c in ('-','_')]).rstrip()
            except:
                safe_filename = f"unknown_trial_{i+1}"
            
            filename = f"{safe_filename}.xml"

            # --- CALLING THE FUNCTION FROM VALIDATOR.PY ---
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
                # Save to invalid folder
                output_path = os.path.join(INVALID_FOLDER, filename)
                doc_tree.write(output_path, pretty_print=True, encoding='utf-8')
                
                # Format error messages
                # schema.error_log contains specific XSD validation errors
                msgs = [f"Line {e.line}: {e.message}" for e in error_log]
                
                results['errors'].append({
                    'id': safe_filename,
                    'file': filename,
                    'reasons': msgs
                })

        return jsonify(results)

    except etree.XMLSyntaxError as e:
        return jsonify({'error': f'XML Syntax Error in uploaded file: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("Server running! Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)