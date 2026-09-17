# NREIP 2027 resume plan

Status: **DRAFT — NOT CONTENT-LOCKED**

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

Final NREIP laboratory preferences are **not yet locked**.

The current unranked screening set is:

- NUWC Newport;
- NRL Washington; and
- NSWC Dahlgren.

The résumé should initially emphasize evidence that transfers well across this
screening set rather than overfitting to one laboratory before preferences are
finalized.

Cross-lab themes currently include:

- cybersecurity;
- AI and machine learning;
- RF sensing and signal/information processing;
- software and computer science;
- modeling, simulation, and autonomy;
- communications/networked systems;
- experimental research; and
- technical communication.

Once laboratory preferences are locked, wording can be checked for legitimate
terminology alignment, but unsupported keywords must not be introduced.

## Artifact contract

Authenticated NREIP portal guidance establishes:

- final artifact format: PDF;
- final file size: strictly less than 1 MB;
- portal upload and save;
- verification by downloading the server copy after upload.

The portal does not establish a résumé page limit.

### Working page budget

**Working target: two pages.**

This is a content-planning decision, not an NREIP requirement.

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

Professional contact fields will be decided separately before final rendering.

Current planning assumption:

- name: include;
- professional email: likely include if candidate approves;
- phone number: not necessary unless candidate chooses to include it;
- street address: omit;
- sensitive demographic/application information: omit.

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
| Digital Forensics TA | Cybersecurity; tooling; communication | INCLUDE IF SPACE | One compact bullet | Verified historical |
| Python/PyTorch/ML pipeline skills | AI/ML/software | CORE | Technical Skills | Verified current |
| RF/IQ/FFT/DCT/polar skills | RF/signal processing | CORE | Technical Skills | Verified current |
| Docker/Linux/networking/security tools | Systems/cybersecurity | CORE, SELECTIVE | Technical Skills | Verified current |
| ROS2/Gazebo | Autonomy/modeling/simulation | INCLUDE | Technical Skills and/or operational-AI entry | Verified current |
| Flask/MongoDB/Nginx | Software/systems | CONDITIONAL | Include where space permits, especially with KMS | Verified current |
| NFPA IT internship | General IT/systems experience | CONDITIONAL | At most compact additional-experience line | Verified historical |
| WBMSHS IT support | General IT experience | OMIT BY DEFAULT | Restore only if target-specific need emerges | Verified historical |
| iD Tech instructor | Teaching/communication | OMIT BY DEFAULT | Teaching evidence already stronger elsewhere | Verified historical |
| Maintenance technician | General employment | OMIT | Low target relevance | Verified historical |
| Java/C historical experience | Software | CONDITIONAL | Include only after current-use confirmation | Verified historical |
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

Initial coursework candidates:

- Scientific Machine Learning — identify as in progress if used;
- Mathematics of Deep Learning;
- Fundamentals of Deep Learning;
- Network Security & Data Assurance;
- Secure Software Development;
- Large Language Models.

The final subset should be chosen for relevance and page density.

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

Include if the two-page budget supports it.

Possible content:

- created Autopsy disk-image and Docker-based log-analysis labs;
- guided incident-style analysis/reporting;
- classroom instruction and technical feedback.

If space becomes constrained, this entry is lower priority than DQNGuard,
HICSS, the NUWC capstone, and the Cyber Defense TA role.

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

NFPA remains conditional because it is the strongest older conventional IT
internship.

### Generic objective statement

Omit.

The application already has personal-statement fields, and résumé space should
be used for evidence rather than a generic objective.

## Content-lock questions still open

Before this plan can become `CONTENT LOCKED`, resolve:

1. final top NREIP laboratory preferences;
2. whether any additional laboratory-specific signal materially changes content;
3. final two-page versus one-page judgment during the pre-render
   content-density review;
4. exact selected-coursework subset;
5. whether Digital Forensics TA earns space;
6. whether NFPA earns a compact line;
7. whether Java or C remain current enough to include;
8. final private professional contact fields;
9. exact placement and wording of mandatory private government-application
   evidence;
10. exact bullet wording and bullet count for DQNGuard and HICSS.

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
