# WHO ICTRP Clinical Trials Validator

A web-based tool developed in Python (Flask) to validate monthly XML datasets of clinical trials against the **WHO ICTRP (International Clinical Trials Registry Platform)** XSD schema.

This application solves the problem of validating large batch files by splitting them into individual trials, validating each one against the strict XSD rules, and organizing them into "Success" or "Invalid" directories.

## 🚀 Features

* **Batch Processing:** Upload a single large XML file containing multiple clinical trials.
* **Atomized Validation:** The script splits the main file and validates each `<trial>` element individually.
* **Automated Sorting:**
    * ✅ **Success:** Valid XML files are saved in the `processed/success` folder.
    * ❌ **Invalid:** Files with errors are saved in `processed/invalid`.
* **Web Interface:** User-friendly Frontend (Bootstrap) to upload files and view results.
* **Detailed Error Logging:** Displays specific XSD validation errors (line numbers and reasons) for invalid trials.

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

## 📂 Project Structure

Ensure your project folder looks like this before running:

```text
/who-ictrp-validator
│
├── app.py                # Main application logic (Server + Validation)
├── who_ictrp.xsd         # The official WHO XSD Schema file
├── templates/
│   └── index.html        # Frontend user interface
└── uploads/              # Temporary folder for uploaded files
