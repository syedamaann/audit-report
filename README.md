# Email Audit Pipeline

This project implements an automated pipeline for auditing email content. The pipeline processes .eml files, converts them to HTML, and performs various audits based on configurable rules.

## Features

- EML to HTML conversion
- Configurable audit rules
- Detailed audit reports
- Error handling and logging
- Modular and extensible architecture

## Project Structure

```
.
├── eml-input/          # Input directory for .eml files
├── eml-html/           # Output directory for converted HTML files
├── reports/            # Output directory for audit reports
├── src/
│   └── email_audit/
│       ├── parser/     # EML to HTML conversion
│       ├── auditor/    # Email content auditing
│       ├── reporter/   # Report generation
│       └── utils/      # Utility functions
└── requirements.txt    # Python dependencies
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your .eml files in the `eml-input` directory.

2. Run the pipeline:
   ```bash
   python -m src.email_audit.pipeline
   ```

3. Check the results:
   - Converted HTML files will be in the `eml-html` directory
   - Audit reports will be in the `reports` directory
   - Logs will be in `pipeline.log`

## Audit Rules

The current implementation includes the following audit rules:

1. HTML Structure Check
   - Verifies proper HTML structure
   - Checks for essential HTML tags
   - Validates content structure

2. Content Length Check
   - Ensures sufficient content length
   - Provides scoring based on content size

## Adding New Rules

To add new audit rules:

1. Open `src/email_audit/auditor/email_auditor.py`
2. Add a new rule to the `_initialize_rules` method
3. Implement the corresponding check method
4. The rule will be automatically included in the audit process

## Report Format

Audit reports are generated in JSON format and include:

- Overall score
- Number of passed/failed rules
- Detailed results for each rule
- Human-readable summary
- Timestamp of the audit

## Error Handling

The pipeline includes comprehensive error handling:

- Individual file processing errors are logged
- Failed rules are reported but don't stop the pipeline
- All errors are logged with detailed information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 