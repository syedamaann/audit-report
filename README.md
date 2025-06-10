# Email Audit Pipeline

This project implements an automated pipeline for auditing email content. The pipeline processes .eml files, converts them to HTML, uses AI language models to analyze content, and performs various audits based on configurable rules.

## Features

- EML to HTML conversion
- AI-powered content analysis and structuring using OpenAI and/or Anthropic models.
- Configurable audit rules and LLM models.
- Detailed audit reports
- Error handling and logging
- Modular and extensible architecture

## Project Structure

```
.
├── .env.local          # Local environment variables (contains API keys, etc.)
├── eml-input/          # Input directory for .eml files
├── eml-html/           # Output directory for converted HTML files
├── reports/            # Output directory for audit reports
├── src/
│   └── email_audit/
│       ├── parser/     # EML to HTML conversion
│       ├── auditor/    # Email content auditing (integrates LLMs)
│       ├── llm/        # LLM client implementations and factory
│       ├── reporter/   # Report generation
│       └── utils/      # Utility functions
└── requirements.txt    # Python dependencies
```

## Setup

1.  **Clone the repository.**
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies:**
    The system uses Python libraries such as `openai` and `anthropic` for interacting with language models.
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    Create a `.env.local` file in the project root directory by copying the `.env.example` file (if one exists) or by creating it manually. This file will store your API keys and LLM preferences.

    *See the "Configuration" section below for details on the required and optional environment variables.*

## Configuration

The pipeline is configured using environment variables. Ensure these are set in your `.env.local` file or your system environment.

### Core API Keys (Required)

*   `OPENAI_API_KEY`: Your API key for OpenAI services.
*   `ANTHROPIC_API_KEY`: Your API key for Anthropic services.

*You need to provide at least one of the above, depending on which provider(s) you intend to use.*

### LLM Provider and Model Selection (Optional)

These variables allow you to specify which LLM provider and model to use for different stages of the audit. The system defaults to using OpenAI for all roles if these are not set.

*   **Primary LLM (for structuring email content):**
    *   `PRIMARY_LLM_PROVIDER`: Provider to use. Can be `"openai"` or `"anthropic"`. (Default: `"openai"`)
    *   `OPENAI_PRIMARY_MODEL`: OpenAI model name. (Default: `"gpt-4"`)
    *   `ANTHROPIC_PRIMARY_MODEL`: Anthropic model name. (Default: `"claude-3-opus-20240229"`)

*   **Reasoning LLM (for comprehensive audit report generation):**
    *   `REASONING_LLM_PROVIDER`: Provider to use. Can be `"openai"` or `"anthropic"`. (Default: `"openai"`)
    *   `OPENAI_REASONING_MODEL`: OpenAI model name. (Default: `"gpt-4"`)
    *   `ANTHROPIC_REASONING_MODEL`: Anthropic model name. (Default: `"claude-3-opus-20240229"`)

*   **Detail LLM (initialized but not heavily used in the current main audit flow):**
    *   `DETAIL_LLM_PROVIDER`: Provider to use. Can be `"openai"` or `"anthropic"`. (Default: `"openai"`)
    *   `OPENAI_DETAIL_MODEL`: OpenAI model name. (Default: `"gpt-4"`)
    *   `ANTHROPIC_DETAIL_MODEL`: Anthropic model name. (Default: `"claude-3-opus-20240229"`)

**Example `.env.local` content:**
```env
OPENAI_API_KEY="your_openai_key_here"
ANTHROPIC_API_KEY="your_anthropic_key_here"

PRIMARY_LLM_PROVIDER="openai"
OPENAI_PRIMARY_MODEL="gpt-4-turbo-preview"

REASONING_LLM_PROVIDER="anthropic"
ANTHROPIC_REASONING_MODEL="claude-3-haiku-20240307"
# If REASONING_LLM_PROVIDER was "openai", you might set:
# OPENAI_REASONING_MODEL="gpt-3.5-turbo"
```

## Usage

1.  Place your .eml files in the `eml-input` directory.
2.  Ensure your `.env.local` file is correctly configured with API keys and any desired LLM settings.
3.  Run the pipeline:
    ```bash
    python -m src.email_audit.pipeline
    ```
4.  Check the results:
    *   Converted HTML files will be in the `eml-html` directory.
    *   Audit reports (JSON format) will be in the `reports` directory.
    *   Logs will be in `pipeline.log`.

## Audit Rules

The audit process involves multiple steps defined within the `EmailAuditor` class. These steps leverage LLMs to analyze aspects of the email conversation, such as:
- Logical itinerary planning
- Application of frequent flyer and loyalty programs
- Adherence to client policies and service standards
- Communication quality

(The "Audit Rules" and "Adding New Rules" sections from the old README were high-level and might need more specific updates if the internal rule definition mechanism significantly changes beyond just LLM invocation.)

## Report Format

Audit reports are generated in JSON format and include:

- Overall score
- Detailed results for each audit step, including scores, analysis, and reasoning provided by the LLM.
- Human-readable summary
- Timestamp of the audit
- Conversation history

## Error Handling

The pipeline includes comprehensive error handling:

- Individual file processing errors are logged.
- LLM invocation errors or parsing issues are logged.
- Failed audit steps are reported but don't stop the pipeline.
- All errors are logged with detailed information.

## Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Commit your changes.
4.  Push to the branch.
5.  Create a Pull Request.
```
