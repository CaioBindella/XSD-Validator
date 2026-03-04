# WHO ICTRP Clinical Trials Validator

A web-based tool developed in Python (Flask) to validate monthly XML datasets of clinical trials against the **WHO ICTRP (International Clinical Trials Registry Platform)** XSD schema.

This application solves the problem of validating large batch files by splitting them into individual trials, validating each one against the strict XSD rules, and organizing them into "Success" or "Invalid" directories.

## 🚀 Features

* **Batch Processing:** Upload a single large XML file containing multiple clinical trials.
* **Atomized Validation:** The script splits the main file and validates each `<trial>` element individually.
* **Automated Sorting & Categorization:**
    * ✅ **Success:** Valid XML files are saved in the `processed/success/` folder.
    * ❌ **Invalid Categorization:** Files with errors are automatically organized into specific sub-directories based on the error reason (`processed/invalid/<error_reason>/`). This enables easy review of specific validation errors.
* **Automated CSV Reporting:** Generates a detailed, timestamped CSV error report (`error_report_YYYYMMDD_HHMMSS.csv`) containing the Trial ID, Line Number, and Error Reason for all invalid records, facilitating feedback to the registries.
* **Web Interface:** User-friendly Frontend (Bootstrap) to upload files, view results, and download the CSV reports directly from the browser.

## 🛠️ Prerequisites

* **Python 3.x** installed on your machine.
* The following Python libraries:
    * `flask` (for the web server)
    * `lxml` (for high-performance XML/XSD validation)

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/CaioBindella/XSD-Validator.git](https://github.com/CaioBindella/XSD-Validator.git)
    cd XSD-Validator
    ```

2.  **Install dependencies**:
    ```bash
    pip install flask lxml
    ```

## ▶️ How to Run

1.  **Start the Application**:
    Run the following command in your terminal, inside the project folder:
    ```bash
    python app.py
    ```

2.  **Access the Interface**:
    Open your web browser and navigate to:
    **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

3.  **Usage**:
    * Click "Choose File" to upload your monthly XML file.
    * Click "Run Validation".
    * Navigate through the "Success" and "Invalid" tabs to view the results.
    * Click the "Download CSV Error Report" button to get the consolidated error list.

## 📂 Project Structure

```text
/XSD-Validator
│
├── app.py                # Main application logic (Server + Routing)
├── validator.py          # Modular XSD validation functions
├── who_ictrp.xsd         # The official WHO XSD Schema file
├── templates/
│   └── index.html        # Frontend user interface
├── uploads/              # Temporary folder for uploaded files
└── processed/            # Auto-generated output directory
    ├── success/          # Extracted valid XML trials
    ├── invalid/          # Extracted invalid XML trials (categorized by error)
    └── *.csv             # Generated timestamped error reports