# Email Audit System – Prototype Accuracy-First Plan

The focus at this stage is **maximum audit accuracy** with minimal engineering overhead. Scalability, production hardening, and cost optimisation can wait until the prototype proves its value.

---

## Phase 0 – Rapid Environment Setup (1 day)
1. 🗂️ Ensure repository cleanliness; keep current layout.
2. 📜 Add Poetry + pre-commit (black, isort, flake8, mypy) for consistency.
3. 🔑 Create `.env` with high-accuracy model key (`OPENAI_API_KEY` for GPT-4o).

Deliverable → Local dev environment producing identical results on every machine.

---

## Phase 1 – Config-Driven Audit Steps (2 days)
1. 🔄 Move hard-coded `audit_steps` list to `config/audit_steps.yml`.
2. ⚖️ For **each step** store: `title`, `prompt`, `category`, `max_score` (e.g. 3.0 or 5.4), `is_fatal` (bool), `report_column` (exact header text), and `weight` (for overall % calcs).
3. 🗂️ Create `config/category_schema.yml` to group columns into the four buckets seen in the sample report: **PNR Fields, Client Policy & Service, Accounting, Communication**.
4. 🧩 Add a lookup table for **overall spreadsheet columns** (e.g. *Max Score, Quality Score, Score without Fatal, Fatal Transaction*).
5. 🧪 Unit tests: load configs, validate schema via Pydantic, assert unique `report_column` names.

Deliverable → Auditor consumes YAML and can map internal results 1-to-1 to the required spreadsheet columns.

---

## Phase 2 – High-Fidelity Email Parsing (3 days)
1. 📨 Keep current EML→HTML path for speed of implementation.
2. 🔍 Enhance parser:
   • Extract inline image & attachment metadata.
   • Strip quoted previous replies to avoid duplicate analysis.
   • Normalise timestamps to UTC.
3. 🛠️ Create test corpus of 20 real emails; assert 100 % content capture.

Deliverable → Parser that feeds clean, complete text to LLM.

---

## Phase 3 – Message Structuring Accuracy (4 days)
1. 🧱 Iterate on "structuring" prompt; target ≥95 % schema compliance.
2. ✔️ Add assertions: chronological order, presence of `From/To/Subject/Timestamp`.
3. 📊 Collect false-positive/negative stats in `tests/eval_structuring.py`.

Deliverable → Reliable structured conversation object for downstream analysis.

---

## Phase 4 – Scoring Engine & Prompt Tuning (1 week)
### 4A – Scoring Engine (2 days)
1. 🧮 Implement `services/scoring.py` that:
   • Takes raw audit results + config and produces per-step scores (0, partial, full).
   • Computes **Fatal Error logic**: if any `is_fatal` step fails, set *Fatal Transaction* flag and zero out *Quality Score*.
   • Calculates *Quality Score*, *Score without Fatal*, and category subtotals matching sample formulas.
2. 📊 Generate **CSV/Excel** output (`reports/{date}_audit_report.xlsx`) with column order identical to the provided sample.
3. 🧪 Snapshot-test the generated spreadsheet against a golden sample.

### 4B – Prompt Tuning (3 days)
For each audit step:
1. ✍️ Draft 2–3 prompt variants.
2. 🧪 Run on labelled validation set (30 threads) via a Jupyter notebook.
3. 📈 Measure precision/recall → select best prompt.
4. 🔄 Log metrics in `results/prompt_eval.csv`.

Deliverables →
• Deterministic scoring engine producing sample-compliant spreadsheets.
• Best-performing prompts recorded per audit criterion.

---

## Phase 5 – Human-in-the-Loop Review (2 days)
1. 🖥️ Build simple Streamlit UI:
   • Left pane: email thread.
   • Right pane: LLM audit results.
   • Buttons: **Accept / Flag / Edit**.
2. 📄 Persist feedback in `feedback.csv` (email_id, step_id, verdict, notes).
3. 🔁 Flagged items feed back into prompt-tuning loop.

Deliverable → Feedback mechanism to continuously improve accuracy.

---

## Phase 6 – Continuous Accuracy Evaluation (ongoing)
1. 🏃 Script `make evaluate` runs full pipeline on `eval/` corpus, outputs `accuracy_report.md`.
2. 📊 Plot trend of overall score vs. human labels over time.
3. 🛎️ If accuracy < target threshold, trigger notification to data scientist.

Deliverable → Quick, repeatable accuracy dashboard.

---

### Success Criteria (Prototype)
1. ≥95 % schema accuracy in message structuring.
2. ≥85 % average precision & recall across audit steps.
3. Feedback loop integrated and used by testers daily.
4. Ability to tweak audit criteria & prompts without code redeploy.
5. Prototype demo impresses stakeholders with actionable, accurate insights.

---

*Note: Phases related to queues, containers, observability, and large-scale infra are postponed until after accuracy targets are consistently met.*

---

# Detailed Task Breakdown

## Phase 0 Tasks
### Environment Setup
- [ ] Create `.gitignore` with Python, IDE, and env patterns
- [ ] Initialize Poetry project
  ```bash
  poetry init
  poetry add black isort flake8 mypy pytest
  ```
- [ ] Add pre-commit hooks configuration
- [ ] Create `.env.example` template
- [ ] Document setup steps in README.md

## Phase 1 Tasks
### Config Structure
- [ ] Design `audit_steps.yml` schema:
  ```yaml
  - id: logical_itinerary
    title: "Logical Itinerary"
    prompt: "Evaluate if the itinerary..."
    category: "Client Policy & Service"
    max_score: 5.4
    is_fatal: false
    report_column: "Logical Itinerary (Time window, Routing, Connections)"
    weight: 1.0
  ```
- [ ] Create Pydantic models for config validation
- [ ] Implement config loader with error handling
- [ ] Write unit tests for config loading edge cases

### Category Schema
- [ ] Define category weights and groupings
- [ ] Create category subtotal calculator
- [ ] Add validation for column name uniqueness
- [ ] Test category score aggregation

### Report Column Mapping
- [ ] Create enum/constants for fixed columns
- [ ] Build column order enforcer
- [ ] Add header name validator
- [ ] Test report template generation

## Phase 2 Tasks
### Email Parser Enhancement
- [ ] Add MIME part extraction
  - [ ] Text content
  - [ ] HTML content
  - [ ] Inline images
  - [ ] Attachments
- [ ] Implement quoted text detection
  - [ ] Handle "On <date> wrote:" patterns
  - [ ] Handle forwarded message markers
  - [ ] Handle "> " quote prefixes
- [ ] Add timestamp normalization
  - [ ] Parse various date formats
  - [ ] Convert to UTC
  - [ ] Handle timezone edge cases
- [ ] Create test email corpus
  - [ ] Collect 20 representative samples
  - [ ] Add edge cases (forwarded, quoted, attachments)
  - [ ] Document expected parser output

## Phase 3 Tasks
### Message Structuring
- [ ] Design conversation schema
  ```python
  @dataclass
  class EmailMessage:
      sender: str
      recipients: List[str]
      subject: str
      timestamp: datetime
      body: str
      quoted_text: Optional[str]
      attachments: List[Attachment]
  ```
- [ ] Implement chronological sorting
- [ ] Add schema validators
- [ ] Create evaluation metrics
  - [ ] False positive tracker
  - [ ] False negative tracker
  - [ ] Schema compliance checker

## Phase 4A Tasks
### Scoring Engine
- [ ] Implement score calculator
  - [ ] Raw score computation
  - [ ] Fatal error handling
  - [ ] Category subtotals
  - [ ] Overall quality score
- [ ] Build report generator
  - [ ] CSV writer
  - [ ] Excel formatter
  - [ ] Column ordering
  - [ ] Header styling
- [ ] Add test suite
  - [ ] Score calculation tests
  - [ ] Fatal error tests
  - [ ] Report format tests
  - [ ] Golden sample comparison

### Prompt Engineering (Per Audit Step)
- [ ] Create prompt template system
- [ ] Build prompt evaluation notebook
- [ ] Implement metrics collection
- [ ] Add version control for prompts

## Phase 5 Tasks
### Review UI
- [ ] Setup Streamlit app
  - [ ] Basic layout
  - [ ] Email thread viewer
  - [ ] Results display
  - [ ] Feedback buttons
- [ ] Implement feedback storage
  - [ ] CSV writer
  - [ ] Feedback schema
  - [ ] Backup mechanism
- [ ] Add feedback analysis tools
  - [ ] Statistics calculator
  - [ ] Trend viewer
  - [ ] Export functionality

## Phase 6 Tasks
### Evaluation Pipeline
- [ ] Create evaluation runner
  - [ ] Corpus loader
  - [ ] Batch processor
  - [ ] Results aggregator
- [ ] Build accuracy dashboard
  - [ ] Metrics calculator
  - [ ] Trend plotter
  - [ ] Alert system
- [ ] Add reporting tools
  - [ ] Markdown report generator
  - [ ] Performance visualizations
  - [ ] Error analysis

## Testing Tasks (Cross-cutting)
- [ ] Unit tests
  - [ ] Config validation
  - [ ] Parser functionality
  - [ ] Scoring logic
  - [ ] Report generation
- [ ] Integration tests
  - [ ] End-to-end workflow
  - [ ] API contracts
  - [ ] Data consistency
- [ ] Performance tests
  - [ ] Processing speed
  - [ ] Memory usage
  - [ ] Error handling 