# NREIP 2027 resume plan

Status: **CONTENT LOCKED**

This file is the application-specific content-selection plan for the NREIP 2027
résumé.

It is not yet authorized for final rendering.

Candidate factual claims are governed by `../../context/EVIDENCE.md`.
NREIP requirements and selection signals are governed by `JOB_SPEC.md`.

When this file is eventually marked `CONTENT LOCKED`, production/layout code may
render its decisions but must not silently rewrite them.

## Audience and purpose

The primary audience is Department of Navy laboratory research staff reviewing
NREIP applicants.

Current program evidence indicates that laboratory reviewers consider academic
background, research interests, personal statements, and recommendations. The
résumé should therefore complement the rest of the application by providing
dense, verifiable technical evidence rather than repeating a generic personal
statement.

The résumé should establish, quickly:

- current graduate-level academic preparation;
- ability to conduct and communicate technical research;
- depth in computer science, cybersecurity, AI/ML, RF/signal analysis, and
  software systems;
- experience building and evaluating real technical systems;
- evidence of research ownership and publication;
- relevance to Navy laboratory research without overstating any federal or Navy
  relationship.

## Target-laboratory status

The NREIP portal preferences have been selected separately from the résumé:

- NUWC Newport;
- Naval Research Laboratory — Washington, DC; and
- NSWC Crane.

NUWC Newport is the candidate's primary intended destination.

These selections are **context for relevance**, not résumé fields and not a
prerequisite for content lock.

The résumé should work across the selected laboratories by emphasizing the
supported intersection of:

- cybersecurity;
- artificial intelligence and machine learning;
- RF and signal/information processing;
- detection and classification;
- software and computer science;
- communications and networked systems;
- modeling, simulation, and autonomy;
- experimental research; and
- technical communication.

Do not name the preferred laboratories in the résumé merely because they were
selected in the portal.

The existing NUWC Newport client relationship may appear because it is verified
candidate project evidence, not because Newport is the preferred laboratory.

## Artifact contract

Authenticated NREIP portal guidance establishes:

- final artifact format: PDF;
- final file size: strictly less than 1 MB;
- portal upload and save;
- verification by downloading the server copy after upload.

The portal does not establish a résumé page limit.

### Working page budget

**Content target: one page.**

This is a content-planning decision, not an NREIP requirement.

The initial production specification tested a two-page layout. The first rendered
artifact demonstrated that the locked content occupied only roughly the upper
half of each page and therefore behaved visually like a one-page résumé split
artificially across two sheets.

Based on that implementation evidence, the candidate explicitly revised the
page-budget decision to **one page**.

This revision changes pagination and layout only. It does not remove, shorten,
rewrite, or add résumé content.

A two-page target is justified at this stage because the candidate has:

- current Ph.D.-level academic work;
- two first-author research papers;
- substantial RF/AI/cybersecurity research evidence;
- relevant technical project experience;
- cybersecurity and digital-forensics teaching experience; and
- technical skills that directly map to the screened laboratories.

Do not expand content merely to fill two pages.

Before initial content lock, perform a content-density review against the
two-page target using the planned sections and bullet budget.

After content lock, production may render the artifact. If the rendered result
reveals a real density, hierarchy, or fit problem, explicitly reopen this plan,
revise the owning content decision, review it again, and relock it before
rebuilding.

Production code must never invent, enlarge, delete, or rewrite content merely to
fill or fit space.

## Resume type

Use a **research/technical résumé**.

Do not use the federal qualification-resume conventions from the DCSA
application unless a specific NREIP requirement later establishes a need for
them.

In particular, NREIP does not currently establish a need to show hours per week
for every role.

Employment and project dates must remain accurate, but federal-style explanatory
metadata should not consume space unless it improves the research reader's
understanding.

## Header and private-contact boundary

The portal's general outline explicitly includes the candidate's name.

The tracked public résumé workflow must not expose private contact details merely
for review convenience.

### Tracked review artifact

Use:

- candidate name; and
- non-private placeholders for any submission-only contact fields.

### Final private submission artifact

The candidate approved use of:

- university professional email; and
- cell phone.

The final private submission artifact will omit:

- street address;
- ZIP code;
- personal email; and
- sensitive demographic/application information.

Exact contact values are owned by the ignored private overlay.

Do not place private contact values in tracked SVG, Markdown, PDF, or preview
artifacts.

## Proposed section order

Working order:

1. **Education**
2. **Research Experience**
3. **Selected Publications**
4. **Technical Skills**
5. **Selected Technical and Teaching Experience**

This ordering reflects the NREIP research-review mechanism rather than the order
used in a federal qualification résumé.

Honors and selected coursework should be integrated into Education rather than
given large standalone sections unless later layout evidence supports otherwise.

Older employment should not receive a dedicated section unless it earns space
through target relevance.

## Evidence-selection map

| Candidate evidence | NREIP / lab signal | Decision | Intended treatment | Evidence status |
|---|---|---|---|---|
| Current Ph.D. enrollment | Academic background; graduate research readiness | CORE | Education, first entry | Verified current |
| Graduate GPA 4.0 | Academic achievement | CORE | Compact education line | Verified current |
| Relevant graduate coursework | Academic preparation; AI/cyber/software/math | CORE, SELECTIVE | Use only strongest target-relevant courses | Verified current / in-progress distinction preserved |
| B.S. Computer Science, Cybersecurity | CS/cyber foundation | CORE | Education | Verified current |
| B.S. GPA 3.379, Cum Laude | Academic achievement | CORE | Compact education line | Verified current |
| Dean's/Chancellor's Lists | Academic achievement | CONDITIONAL | Compress heavily or omit if redundant | Verified current |
| Research Assistant appointments | Research experience | CORE | Role/date context; do not imply continuous employment | Verified historical |
| DQNGuard | RF, AI/ML, cybersecurity, experimental research, software | HIGHEST PRIORITY | Major research entry, multiple bullets | Verified current evidence |
| DQNGuard 0.865 unknown F1 result | Quantitative research result | CORE | One concise result bullet with correct calibration wording | Verified current evidence |
| OTA WiFi/Bluetooth/Zigbee workflow | RF/communications; experimental systems | CORE | DQNGuard bullet | Verified current evidence |
| Target-Surrogate Matrix | Experimental design and analysis | CORE | DQNGuard bullet if space supports it | Verified current evidence |
| HICSS-59 research | RF, ML, OSR, experimental design | HIGHEST PRIORITY | Major research entry | Verified current evidence |
| HICSS nine-fold / 30-run evaluation | Rigorous experimentation | CORE | Method/evaluation bullet | Verified current evidence |
| Operational-AI red-team research | AI/cybersecurity; autonomy; simulation | CORE | One concise research bullet or sub-entry | Verified current |
| MILCOM paper | Research communication/publication | CORE | Publications section | Verified accepted/to appear |
| HICSS paper | Research communication/publication | CORE | Publications section | Verified published |
| NUWC-client senior design capstone | Navy context; software; systems; project leadership | CORE | Selected technical experience | Verified historical |
| Cyber Defense & Operations TA | Cybersecurity depth; technical communication | INCLUDE | One or two compact bullets | Verified historical |
| Digital Forensics TA | Cybersecurity; tooling; communication | INCLUDE | One compact bullet | Verified historical |
| Python/PyTorch/ML pipeline skills | AI/ML/software | CORE | Technical Skills | Verified current |
| RF/IQ/FFT/DCT/polar skills | RF/signal processing | CORE | Technical Skills | Verified current |
| Docker/Linux/networking/security tools | Systems/cybersecurity | CORE, SELECTIVE | Technical Skills | Verified current |
| ROS2/Gazebo | Autonomy/modeling/simulation | INCLUDE | Technical Skills and/or operational-AI entry | Verified current |
| Flask/MongoDB/Nginx | Software/systems | CONDITIONAL | Include where space permits, especially with KMS | Verified current |
| NFPA IT internship | General IT/systems experience | OMIT | Strong historical evidence, but lower relevance than current research/teaching within the one-page budget | Verified historical |
| WBMSHS IT support | General IT experience | OMIT BY DEFAULT | Restore only if target-specific need emerges | Verified historical |
| iD Tech instructor | Teaching/communication | OMIT BY DEFAULT | Teaching evidence already stronger elsewhere | Verified historical |
| Maintenance technician | General employment | OMIT | Low target relevance | Verified historical |
| Java/C historical experience | Software | OMIT | Not needed for the current NREIP résumé; historical evidence only | Verified historical |
| Private government-application credential | Government internship context | MANDATORY IN PRIVATE SUBMISSION | Resolve from ignored private overlay; represent only generically in tracked review artifacts | Private candidate-confirmed evidence |

## Education content plan

### Ph.D.

Include:

- University of Massachusetts Dartmouth;
- Ph.D. in Engineering and Applied Science;
- CSIS/Computer Science and Information Science resume-facing curriculum wording;
- expected May 2030;
- graduate GPA 4.0/4.0.

Use a compact selected-coursework line rather than a long course inventory.

Selected coursework for the NREIP résumé:

- Network Security & Data Assurance;
- Secure Software Development;
- Fundamentals of Deep Learning;
- Mathematics of Deep Learning; and
- Scientific Machine Learning — **in progress, Fall 2026**.

This subset is chosen for direct relevance to cybersecurity, AI/ML, software,
and quantitative research across the selected NREIP laboratories.

Do not represent Fall 2026 coursework as completed.

### B.S.

Include:

- B.S. in Computer Science;
- Cybersecurity concentration;
- May 2025;
- GPA 3.379/4.0;
- Cum Laude.

Do not enumerate every Dean's/Chancellor's List term unless the rendered résumé
has space and the information materially strengthens the academic-achievement
signal beyond GPA and Cum Laude.

## Research Experience content plan

Research should receive the largest share of résumé space.

### DQNGuard

Use the exact project/paper identity:

**DQNGuard: Towards Open-World RF Preliminary-Action Detection**

Working bullet objectives:

1. Establish ownership and scope:
   - designed and implemented the end-to-end DQNGuard research pipeline;
   - open-world/open-set RF preliminary-action detection;
   - multi-domain CNN and decision-layer research.

2. Establish real RF/system scope:
   - OTA WiFi, Bluetooth, and Zigbee data;
   - Scan, Burst, Sustain, Hop, Replay preliminary actions;
   - preprocessing/dataset and experiment pipeline.

3. Establish quantitative result:
   - 0.865 mean unknown-class F1;
   - 5% known-rejection calibration budget;
   - comparison values may be included if they remain readable and useful.

4. Establish experimental analysis:
   - 20-condition Target-Surrogate Matrix;
   - demonstrate target-dependent surrogate behavior.

Do not force all four objectives into separate bullets if that creates density.
The content-lock review should select the strongest three or four.

Do not claim that the held-out rejection rate was mathematically guaranteed to
equal exactly 5%.

### HICSS-59 RF open-set-recognition research

Working bullet objectives:

1. Developed and evaluated a class-conditioned RF open-set-recognition pipeline.
2. Used I/Q, FFT, DCT, and polar representations in an eight-channel CNN.
3. Evaluated nine open-set folds with one selected modulation withheld as unknown
   per fold and 30 runs per fold on RadioML 2018.01A.

Preserve the precise fold interpretation from the evidence ledger.

### Operational-AI red-team research

Include one concise item establishing:

- operational-AI red teaming;
- autonomous vehicle;
- ROS2 and Gazebo;
- interdisciplinary cybersecurity/computer-science/electrical-engineering
  research environment.

Do not inflate this project beyond the currently verified evidence.

## Selected Publications content plan

Include both first-author papers in compact scholarly form.

### MILCOM 2026

Adam Trott et al., "DQNGuard: Towards Open-World RF Preliminary-Action
Detection," IEEE MILCOM 2026, accepted / to appear.

This plan owns the citation content, authorship, title, venue, year, and
publication status.

The later production specification may control typography, indentation, line
wrapping, spacing, and other visual presentation, but it must not silently alter
citation content.

### HICSS-59

Adam Trott, Henry Thompson, and Gokhan Kul, "Model Evaluation for Radio-Frequency
Signal Modulation Classifiers in the Existence of Novel Samples," Proceedings of
HICSS-59, 2026.

The publication section should establish research output without repeating all
technical detail already present in Research Experience.

## Technical Skills content plan

Use compact grouped categories rather than a long undifferentiated keyword list.

Working groups:

**AI / Machine Learning**
- Python;
- PyTorch;
- Hugging Face;
- CNNs;
- transformers;
- open-set recognition;
- novelty/OOD detection;
- model calibration;
- experimental/statistical evaluation.

**RF / Signal Processing**
- RF signal analysis;
- I/Q;
- FFT;
- DCT;
- polar representations;
- OTA WiFi/Bluetooth/Zigbee workflows.

**Cybersecurity / Systems / Software**
- Linux/WSL;
- Docker / Docker Compose;
- networking;
- Autopsy;
- Burp Suite;
- WebGoat;
- OpenSSL;
- ROS2;
- Gazebo;
- Flask;
- MongoDB;
- Nginx.

This list will need pruning during content lock.

Do not include Java or C as current strengths without candidate confirmation.

## Selected Technical and Teaching Experience content plan

### NUWC-client Knowledge Management System capstone

Retain because it supplies:

- software/backend evidence;
- project-management/leadership evidence;
- a legitimate Navy-client context.

The relationship must remain explicit:

- unpaid UMass Dartmouth Senior Design capstone;
- client at NUWC Newport;
- not NUWC employment;
- not federal employment.

Working bullet objectives:

1. Led backend development and project management for the university team.
2. Developed a file-storage, viewing, and search system intended for
   implementation within a NUWC department.
3. Use implementation details such as Flask/MongoDB/Nginx only where supported
   and helpful.

### Cyber Defense and Operations TA

Retain compactly because it supplies both cybersecurity and communication
evidence.

Possible content:

- designed and graded practical cybersecurity assignments;
- cryptography, SQL injection, authentication/access-control, risk analysis;
- authored Caesar Cipher/DES/3DES cryptanalysis project.

Do not reproduce the federal résumé's full duty inventory.

### Digital Forensics TA

Include as a compact one-bullet entry because it supplies distinct applied
cybersecurity/tooling evidence:

- created Autopsy disk-image and Docker-based macOS log-analysis labs and guided
  query construction, visualization, and incident-style reporting.

It remains lower priority than DQNGuard, HICSS, the NUWC capstone, and the Cyber
Defense and Operations TA role if a later explicit content revision is required.

## Portal-outline categories not currently planned as standalone sections

The NREIP portal's general outline also mentions:

- memberships/extracurricular activities;
- hobbies/interests;
- volunteerism.

No standalone section is currently planned for these categories.

Reason:

- the portal describes the list as a general outline rather than mandatory
  section structure;
- the current reviewed evidence does not establish stronger NREIP-relevant
  material in those categories than the research/academic/technical evidence
  competing for space.

If later candidate evidence establishes a particularly relevant activity, this
decision can be revisited before content lock.

## Intentional omissions

### Federal-resume metadata

Omit federal-style hours/week and qualification prose unless necessary to
clarify a relationship.

Exception: the evidence ledger retains those facts for accuracy and future use.

### Street address and sensitive personal information

Omit.

### Private government-application evidence

Some application-relevant candidate evidence is intentionally excluded from the
public repository but is mandatory in the private government-application
artifact.

The exact fact and wording are owned by the ignored private evidence layer.

The tracked review artifact may use a neutral placeholder where necessary to
review hierarchy and page density. The final private submission must resolve
that placeholder before generation and submission.

Do not infer that "private" means "omit from the final résumé."

### Older general employment

WBMSHS IT support, maintenance work, and other low-relevance history are omitted
from the working NREIP content budget.

NFPA is also omitted from the NREIP one-page content budget. It remains in the
candidate evidence ledger for future applications.

### Generic objective statement

Omit.

The application already has personal-statement fields, and résumé space should
be used for evidence rather than a generic objective.

## Content-lock status

**CONTENT LOCKED.**

The candidate has approved the résumé content architecture, exact public-safe
copy, one-page content target, private professional contact-field policy, and
mandatory private government-application credential treatment.

The exact private values remain owned by the ignored private overlay and must be
substituted only when generating the final private submission artifact.

Any later substantive wording change requires explicitly reopening this plan,
reviewing the changed content, and content-locking it again.

Production/layout code may control typography, spacing, wrapping, pagination,
and other presentation details, but it may not silently add, delete, or rewrite
résumé content.

## Content-lock checklist

Before changing this file to `CONTENT LOCKED`, verify:

- every material claim is supported by `../../context/EVIDENCE.md`;
- current academic status and dates are correct;
- in-progress coursework is labeled accurately;
- ended employment/project roles are not represented as current;
- the NUWC capstone relationship is represented accurately;
- quantitative research claims trace to appropriate evidence;
- terminology is aligned to NREIP/lab language without keyword fabrication;
- section order reflects the research-review mechanism;
- intentional omissions are deliberate rather than accidental;
- no prohibited or private information has entered tracked public content;
- all mandatory private-overlay content is accounted for in the final private
  submission plan;
- the working page budget is realistic;
- production has not yet been allowed to rewrite content for fit.

## Exact résumé content — candidate for content lock

Status: **CONTENT LOCKED — PRIVATE OVERLAY REQUIRED FOR FINAL SUBMISSION**

The text below is the exact content intended for the NREIP résumé before visual
production.

Square-bracketed private placeholders are not literal final résumé text. They
must be resolved from ignored private inputs for the private submission artifact.

### Header

**ADAM TROTT**

`[PRIVATE PROFESSIONAL CONTACT FIELDS, IF APPROVED]`

### EDUCATION

**University of Massachusetts Dartmouth**
**Ph.D. in Engineering and Applied Science (EAS), Computer Science and
Information Science (CSIS) Curriculum Option**
Expected May 2030 | Graduate GPA: 4.0/4.0

`[MANDATORY PRIVATE GOVERNMENT-APPLICATION CREDENTIAL]`

**Selected Graduate Coursework:** Network Security & Data Assurance; Secure
Software Development; Fundamentals of Deep Learning; Mathematics of Deep
Learning; Scientific Machine Learning *(in progress, Fall 2026)*

**University of Massachusetts Dartmouth**
**B.S. in Computer Science, Cybersecurity concentration** | May 2025
GPA: 3.379/4.0 | Cum Laude

### RESEARCH EXPERIENCE

**Research Assistant — University of Massachusetts Dartmouth** | Dartmouth, MA
Jun–Aug 2025; Jun–Aug 2026

- Developed and tested an operational-AI red-teaming framework on an autonomous
  vehicle with cybersecurity, computer science, and electrical-engineering
  researchers using ROS2 and Gazebo.

**DQNGuard: Towards Open-World RF Preliminary-Action Detection**
First author | IEEE MILCOM 2026, accepted/to appear

- Designed and implemented the end-to-end DQNGuard pipeline for open-world RF
  preliminary-action detection, including a multi-domain CNN and open-set
  decision layer; benchmarked against VarMax and a DQN-IDS-style baseline.
- Built an over-the-air SDR capture, preprocessing, and dataset pipeline for
  WiFi, Bluetooth, and Zigbee RF signals; designed, trained, and evaluated
  experiments across five preliminary actions: Scan, Burst, Sustain, Hop, and
  Replay.
- Achieved 0.865 mean unknown-class F1 under a 5% known-rejection calibration
  budget, compared with 0.745 for VarMax and 0.701 for the DQN-IDS-style
  comparison head; designed and analyzed a 20-condition Target-Surrogate Matrix.

**Model Evaluation for Radio-Frequency Signal Modulation Classifiers in the
Existence of Novel Samples**
First author | HICSS-59, published 2026; presented Jan. 8, 2026

- Developed and evaluated a class-conditioned RF open-set-recognition pipeline
  using an eight-channel CNN over raw I/Q, FFT, DCT, and polar
  representations.
- Evaluated nine open-set folds on RadioML 2018.01A, withholding one selected
  modulation as unknown per fold and running 30 runs per fold.

### SELECTED PUBLICATIONS

Trott, A., Popillo, C., Bastian, N. D., Zhou, R., and Kul, G. **"DQNGuard:
Towards Open-World RF Preliminary-Action Detection."** IEEE MILCOM 2026,
accepted/to appear.

Trott, A., Thompson, H., and Kul, G. **"Model Evaluation for Radio-Frequency
Signal Modulation Classifiers in the Existence of Novel Samples."** Proceedings
of the 59th Hawaii International Conference on System Sciences (HICSS-59), 2026.

### TECHNICAL SKILLS

**AI / Machine Learning:** Python, PyTorch, Hugging Face, Jupyter; CNNs,
transformers, open-set recognition, novelty/OOD detection, model calibration,
experimental design, quantitative/statistical evaluation

**RF / Signal Processing:** software-defined radio (SDR), RF signal analysis,
complex I/Q, FFT, DCT, and polar representations; over-the-air WiFi, Bluetooth,
and Zigbee data workflows

**Cybersecurity / Systems / Software:** Linux/WSL, Docker/Docker Compose,
networking, OpenSSL, Autopsy, Burp Suite, Flask, MongoDB, Nginx, ROS2, Gazebo

### SELECTED TECHNICAL AND TEACHING EXPERIENCE

**Lead Backend Developer & Project Manager — UMass Dartmouth Senior Design
Capstone**
Client: NUWC Newport | Sep. 2024–May 2025

- Led backend development and project management for a university team building
  a file-storage, viewing, and search system for a NUWC Newport client;
  coordinated technical work and delivery with the client.

**Teaching Assistant — Cyber Defense and Operations — University of
Massachusetts Dartmouth** | Jan.–May 2026

- Designed and graded practical cybersecurity assignments involving risk
  analysis, cryptography, WebGoat SQL injection, and Burp Suite
  access-control/authentication attacks.
- Authored a Caesar Cipher/DES/3DES cryptanalysis project requiring
  candidate-key generation, brute-force search, plaintext verification,
  performance measurement, analytical reporting, and a recorded demonstration.

**Teaching Assistant — Digital Forensics — University of Massachusetts
Dartmouth** | Sep.–Dec. 2025

- Created Autopsy disk-image and Docker-based macOS log-analysis labs and guided
  students through query construction, visualization, and incident-style
  reporting.

### Explicit omissions from this NREIP version

The following verified evidence is deliberately omitted from the current
one-page content target:

- NFPA Help Desk / IT internship;
- WBMSHS IT support;
- iD Tech instruction;
- maintenance employment;
- Java and C historical skill claims;
- exhaustive Dean's/Chancellor's List terms;
- federal-resume hours/week metadata;
- generic objective/summary paragraph.

These omissions are application-specific and do not remove the underlying facts
from the candidate evidence ledger.
