# Resume candidate evidence ledger

Status: **EXPERIMENTAL — initial public-safe baseline populated**

This file is the factual authority for candidate claims used by the resume
workflow.

A prior resume is evidence, not automatic truth. Older resumes preserve useful
history but can contain stale degree status, obsolete dates, shorthand
relationships, or wording that should not propagate into future applications.

## Evidence classes

Claims below can draw from several evidence classes:

- **TRACKED_PRIMARY** — public source or artifact tracked in PADataset, such as a
  paper source, result table, or context owner.
- **PUBLICATION_PRIMARY** — published or accepted-manuscript material reviewed
  directly.
- **PRIVATE_REVIEWED** — a private or untracked resume, CV, transcript, or other
  source reviewed during evidence reconciliation. Public-safe facts may be
  extracted here without committing the private source itself.
- **CANDIDATE_CONFIRMED** — a fact explicitly reviewed and confirmed by the
  candidate during resume/application work.

When sources disagree, newer and more authoritative evidence governs. Preserve
material discrepancies in the claim notes rather than silently combining them.

## Education

### Ph.D. program

CLAIM
Current doctoral enrollment at the University of Massachusetts Dartmouth.

STATUS
VERIFIED_CURRENT

VALUE
Resume-facing wording: Ph.D. in Engineering and Applied Science (EAS), Computer
Science and Information Science (CSIS) Curriculum Option. Began Spring 2026.
Expected completion May 2030. Graduate GPA: 4.0/4.0.

The reviewed university transcript identifies the current program as
"Engineering & Applied Science PhD Program of Study" with subplan "Computer
Science & Information Systems Concentration."

EVIDENCE
PRIVATE_REVIEWED — university transcript dated 2026-09-03 establishes current
Ph.D. program/subplan and 4.0 graduate cumulative GPA.
PRIVATE_REVIEWED — current DCSA Student Experience '27 resume establishes the
resume-facing program wording, Spring 2026 start, and expected May 2030
completion.

PERMITTED WORDING
"Ph.D. in Engineering and Applied Science (EAS), Computer Science and
Information Science (CSIS) Curriculum Option"
"Ph.D. student, University of Massachusetts Dartmouth"
"Graduate GPA: 4.0/4.0"

FORBIDDEN / MISLEADING WORDING
Do not describe the current degree as an M.S. program.
Do not use the older expected M.S. graduation date.

NOTES
The transcript's official program/subplan labels and the reviewed external
resume wording are not textually identical. Preserve both forms in evidence
rather than silently rewriting one into the other.

Older resumes/CV material records the transition from an M.S. program into the
Ph.D. program. Those records are historical provenance, not current degree
status.

### Bachelor of Science

CLAIM
Completed undergraduate degree at the University of Massachusetts Dartmouth.

STATUS
VERIFIED_CURRENT

VALUE
Bachelor of Science conferred 05/16/2025. Computer Science major; reviewed
resume identifies the concentration as Cybersecurity. Degree GPA: 3.379/4.0.
Degree honor: Cum Laude.

EVIDENCE
PRIVATE_REVIEWED — university transcript dated 2026-09-03 establishes Bachelor
of Science, 05/16/2025 conferral, Computer Science major, 3.379 degree GPA, and
Cum Laude.
PRIVATE_REVIEWED — current DCSA Student Experience '27 resume establishes the
resume-facing "B.S. in Computer Science, Cybersecurity concentration" wording.

PERMITTED WORDING
"B.S. in Computer Science, Cybersecurity concentration"
"University of Massachusetts Dartmouth | May 2025 | GPA 3.379/4.0"
"Graduated Cum Laude"

NOTES
Older resumes round the cumulative GPA to 3.38 or 3.4. Use 3.379 when precision
matters.

## Academic honors and coursework

### Undergraduate academic honors

STATUS
VERIFIED_CURRENT

VALUE
Degree honor: Cum Laude.

Transcript-listed term honors:
- Dean's List — Fall 2023;
- Dean's List — Spring 2024;
- Dean's List — Summer 2024;
- Chancellor's List — Fall 2024;
- Chancellor's List — Spring 2025.

EVIDENCE
PRIVATE_REVIEWED — university transcript dated 2026-09-03.

NOTES
These are reusable academic-achievement facts. A tailored resume need not list
every term honor.

### Completed graduate coursework

STATUS
VERIFIED_CURRENT

VALUE
Completed graduate coursework through Spring 2026 includes:

- CIS 547 — Network Security & Data Assurance;
- CIS 570 — Advanced Computer Systems;
- CIS 602 — Large Language Models;
- CIS 602 — Fundamentals of Deep Learning;
- CIS 546 — Secure Software Development;
- EAS 502 — Numerical Methods; and
- MTH 601 — Mathematics of Deep Learning.

EVIDENCE
PRIVATE_REVIEWED — university transcript dated 2026-09-03.

### Fall 2026 coursework in progress

STATUS
VERIFIED_CURRENT

VALUE
The transcript records Fall 2026 enrollment in:

- CIS 560 — Theoretical Computer Science;
- EAS 501 — Advanced Mathematical Methods; and
- MTH 602 — Scientific Machine Learning.

EVIDENCE
PRIVATE_REVIEWED — university transcript dated 2026-09-03.

NOTES
These courses were in progress when the source transcript was generated. Do not
represent them as completed until later evidence establishes completion.

## University research appointments

### Research Assistant — paid appointments

CLAIM
Paid Research Assistant appointments at the University of Massachusetts
Dartmouth.

STATUS
VERIFIED_HISTORICAL

VALUE
06/2025–08/2025 and 06/2026–08/2026. Part-time, 10 hours/week for each paid
appointment.

EVIDENCE
PRIVATE_REVIEWED — current DCSA Student Experience '27 resume.

FORBIDDEN / MISLEADING WORDING
Do not describe this as continuous 04/2025–Present paid employment.
Do not imply academic-year RA employment unless separately established.

NOTES
An older CV described research activity from April through August 2025. The
current reviewed employment record narrows the paid appointment to June through
August 2025. Research activity and paid appointment dates are therefore not
interchangeable.

### Operational-AI red-team research

CLAIM
Contributed to an operational-AI red-teaming framework implemented and tested on
an autonomous vehicle.

STATUS
VERIFIED_CURRENT

VALUE
Worked with UMass Dartmouth cybersecurity, computer science, and electrical
engineering researchers using ROS2 and Gazebo.

EVIDENCE
PRIVATE_REVIEWED — current DCSA resume and earlier CV.

PERMITTED WORDING
"Developed and tested an operational-AI red-teaming framework on an autonomous
vehicle using ROS2 and Gazebo."

## DQNGuard / MILCOM 2026

### Paper identity and authorship

CLAIM
First-listed author of "DQNGuard: Towards Open-World RF Preliminary-Action
Detection."

STATUS
VERIFIED_CURRENT

VALUE
Authors: Adam Trott, Cameron Popillo, Nathaniel D. Bastian, Roulin Zhou, and
Gokhan Kul. Accepted for IEEE MILCOM 2026; to appear.

EVIDENCE
TRACKED_PRIMARY — `papers/milcom2026/main.tex` establishes title and author
order.
PRIVATE_REVIEWED — current DCSA resume establishes accepted/to-appear status.

NOTES
The tracked manuscript source establishes authorship but does not independently
serve as conference-acceptance evidence.

### Individual research contribution

CLAIM
Designed and implemented the DQNGuard research pipeline end to end and
coordinated the research effort.

STATUS
VERIFIED_CURRENT

VALUE
Work included the open-set decision layer, multi-domain CNN backbone, VarMax and
DQN-IDS-style comparison methods, OTA data workflow, preprocessing/dataset
pipeline, experiment design, training/evaluation, analysis, and manuscript
preparation.

EVIDENCE
PRIVATE_REVIEWED — current DCSA resume.
TRACKED_PRIMARY — PADataset implementation and MILCOM paper support the
technical components and experiment structure.

PERMITTED WORDING
"Designed and implemented DQNGuard end to end."
"Built preprocessing and dataset pipelines and designed, trained, and evaluated
the experimental workflow."

NOTES
Do not use disparaging or exclusionary descriptions of coauthors' contributions.

### OTA protocol and preliminary-action scope

CLAIM
DQNGuard evaluates OTA WiFi, Bluetooth, and Zigbee RF data across five
preliminary-action behaviors.

STATUS
VERIFIED_CURRENT

VALUE
Protocols: WiFi, Bluetooth, Zigbee.
Behaviors: Scan, Burst, Sustain, Hop, Replay.

EVIDENCE
TRACKED_PRIMARY — MILCOM manuscript and PADataset context/implementation.
PRIVATE_REVIEWED — current DCSA resume.

### Main fixed-surrogate operating result

CLAIM
DQNGuard produced a mean unknown-class F1 of 0.865 in the paper's main
fixed-surrogate comparison.

STATUS
VERIFIED_CURRENT

VALUE
DQNGuard: unknown F1 0.865 ± 0.142; known rejection 0.050 ± 0.004.
VarMax surrogate-all: unknown F1 0.745 ± 0.146.
DQN-IDS-style/Shreyash CNN comparison head: unknown F1 0.701 ± 0.197.
The DQNGuard operating rule uses a 5% known-rejection calibration budget.

EVIDENCE
TRACKED_PRIMARY —
`papers/milcom2026/tables/main_results/main_osr_results_table.tex` and associated
MILCOM results/method sections.

PERMITTED WORDING
"Achieved 0.865 mean unknown-class F1 under a 5% known-rejection budget,
compared with 0.745 for VarMax and 0.701 for the DQN-IDS-style comparison head."

NOTES
A 5% calibration budget and the measured held-out known-rejection rate are
related but not identical concepts. Avoid wording that implies a mathematical
guarantee of exactly 5% held-out rejection.

### Target–Surrogate Matrix

CLAIM
Designed and analyzed the paper's Target–Surrogate Matrix.

STATUS
VERIFIED_CURRENT

VALUE
Five PA classes yield 20 ordered target/surrogate combinations with the diagonal
excluded. The analysis demonstrates that surrogate usefulness is strongly
target-dependent.

EVIDENCE
TRACKED_PRIMARY — MILCOM methodology/results and target-surrogate artifact.
PRIVATE_REVIEWED — current DCSA resume supports individual contribution wording.

## HICSS-59 research

### Paper identity and authorship

CLAIM
First author of "Model Evaluation for Radio-Frequency Signal Modulation
Classifiers in the Existence of Novel Samples."

STATUS
VERIFIED_CURRENT

VALUE
Authors: Adam Trott, Henry Thompson, and Gokhan Kul. Published in the
Proceedings of the 59th Hawaii International Conference on System Sciences
(HICSS-59), 2026. Presented January 8, 2026.

EVIDENCE
PUBLICATION_PRIMARY — published HICSS-59 proceedings PDF establishes title,
author order, proceedings identity, and 2026 publication.
PRIVATE_REVIEWED — current DCSA resume and CV establish the January 8, 2026
presentation date.

### Technical method

CLAIM
Developed and evaluated a class-conditioned RF open-set-recognition pipeline
using a multi-domain CNN.

STATUS
VERIFIED_CURRENT

VALUE
The model uses raw I/Q plus FFT, DCT, and polar representations, producing eight
input channels across four signal representations. It applies class-conditioned
variance and energy bands within an OSR decision cascade.

EVIDENCE
PUBLICATION_PRIMARY — HICSS-59 paper.
PRIVATE_REVIEWED — current DCSA resume supports individual-contribution wording.

### Experimental scope

CLAIM
Evaluated nine open-set folds on RadioML 2018.01A, withholding one selected
modulation as unknown in each fold, with 30 runs per fold.

STATUS
VERIFIED_CURRENT

VALUE
The paper organizes modulation types into nine semantically and structurally
related groups and selects one modulation from each group for the experiment.
Evaluation then cycles each of those nine selected modulation types through the
unknown condition. Each fold is run 30 times.

The paper labels its result table "Leave-one-group-out OSR performance," while
the evaluation section explicitly describes one modulation type as the unknown
for each fold.

EVIDENCE
PUBLICATION_PRIMARY — HICSS-59 paper.

NOTES
For resume wording, prefer the explicit evaluation description above. Avoid
phrasing that implies every modulation in an entire group was withheld
simultaneously.

## Teaching experience

### Teaching Assistant — Cyber Defense and Operations

CLAIM
Teaching Assistant at the University of Massachusetts Dartmouth.

STATUS
VERIFIED_HISTORICAL

VALUE
01/2026–05/2026. Part-time, 20 hours/week.

EVIDENCE
PRIVATE_REVIEWED — current DCSA resume.

VERIFIED DUTIES
Designed, administered, and graded cybersecurity assignments involving the CIA
triad, asset/risk analysis, FAIR/ALE, cryptography, WebGoat SQL injection, and
Burp Suite access-control/authentication attacks. Authored a Caesar
Cipher/DES/3DES cryptanalysis project requiring candidate-key generation,
brute-force search, plaintext verification, performance measurement, analytical
reporting, and a recorded demonstration. Evaluated student work and communicated
technical feedback.

### Teaching Assistant — Digital Forensics

CLAIM
Teaching Assistant at the University of Massachusetts Dartmouth.

STATUS
VERIFIED_HISTORICAL

VALUE
09/2025–12/2025. Part-time, 20 hours/week.

EVIDENCE
PRIVATE_REVIEWED — current DCSA resume and earlier CV.

VERIFIED DUTIES
Created an Autopsy disk-image lab and a Docker-based macOS log-analysis lab;
authored setup/usage instructions; guided query construction, visualization, and
incident-style reporting; graded coursework/exams; held office hours; and
delivered more than 100 minutes of classroom instruction across multiple
sessions.

## University technical project

### NUWC-client knowledge-management-system capstone

CLAIM
Lead Backend Developer and Project Manager for an unpaid UMass Dartmouth Senior
Design capstone whose client was at NUWC Newport.

STATUS
VERIFIED_HISTORICAL

VALUE
09/2024–05/2025. Approx. 10–20 hours/week. University project, unpaid.

EVIDENCE
PRIVATE_REVIEWED — current DCSA resume; older resume provides historical project
detail.

PERMITTED WORDING
"Lead Backend Developer & Project Manager — Unpaid Senior Design Capstone,
University of Massachusetts Dartmouth | Client: NUWC Newport."
"Led backend development and project management for a university team building a
file-storage, viewing, and search system intended for implementation within a
NUWC department."

FORBIDDEN / MISLEADING WORDING
"Worked for NUWC."
"NUWC employee."
"Federal employee."
Any presentation of the project as paid NUWC employment.

NOTES
Older resumes used "Naval Undersea Warfare Center" as though it were the
employer. That relationship is superseded by the corrected capstone/client
record.

## Additional historical experience

These roles are retained because they may matter for future applications even
when omitted from research-focused resumes.

### iD Tech Instructor

STATUS
VERIFIED_HISTORICAL

VALUE
05/2024–08/2024.

EVIDENCE
PRIVATE_REVIEWED — curriculum vitae.

VERIFIED DUTIES
Primary instructor for students ages 7–14; designed and facilitated full-day
STEM instruction using technical/game-based activities; developed lesson plans
and managed classroom behavior and engagement.

### NFPA National Headquarters — Help Desk and Information Technology Intern

STATUS
VERIFIED_HISTORICAL

VALUE
Quincy, Massachusetts | 05/2024–08/2024.

EVIDENCE
PRIVATE_REVIEWED — historical IT resume.

VERIFIED DUTIES
Provided in-person IT support; gained hands-on exposure to endpoint, network, and
database administration; participated in project-management/documentation work;
and observed infrastructure/security planning associated with an acquisition.

### WBMSHS — IT Support Technician

STATUS
VERIFIED_HISTORICAL

VALUE
West Bridgewater, Massachusetts | 09/2018–06/2021.

EVIDENCE
PRIVATE_REVIEWED — historical IT resume.

VERIFIED DUTIES
Diagnosed and repaired computer systems; performed hardware/software
maintenance; supported faculty and students; assisted with technology inventory
and device-management/ticketing workflows.

### The Village — Maintenance Technician

STATUS
VERIFIED_HISTORICAL

VALUE
Duxbury, Massachusetts | 07/2023–01/2025.

EVIDENCE
PRIVATE_REVIEWED — later 2025 resume.

VERIFIED DUTIES
Performed hands-on maintenance and resident technical support, including
appliance troubleshooting, technology assistance, event support, and customer
service.

NOTES
An earlier resume listed this position as "Present." The later 2025 resume gives
January 2025 as the endpoint and therefore governs.

## Technical-skill evidence

### Current strongly supported skills

STATUS
VERIFIED_CURRENT

EVIDENCE
Current DCSA resume, CV, teaching artifacts, HICSS publication, MILCOM/PADataset
implementation.

SUPPORTED SKILLS
Python; PyTorch; Hugging Face; Jupyter; CNNs; transformers; machine-learning
pipelines; open-set recognition and novelty/OOD detection; model calibration;
experimental design; quantitative/statistical evaluation; RF signal analysis;
I/Q, FFT, DCT, and polar representations; Autopsy; Burp Suite; WebGoat; Docker
and Docker Compose; Linux/WSL; OpenSSL; networking; Flask; MongoDB; Nginx; ROS2;
Gazebo.

### Historical programming-language claims requiring current-use judgment

STATUS
VERIFIED_HISTORICAL

VALUE
Older resumes state proficiency/experience in Java and C.

EVIDENCE
PRIVATE_REVIEWED — historical IT/general resumes.

NOTES
Do not automatically describe Java or C as current strengths solely from the
older resumes. Include them in a future tailored resume only if still accurate
and useful, or after candidate confirmation.

## Restricted/private evidence boundary

Some valid professional or application facts are intentionally excluded from
this public ledger.

Do not infer that absence from this file means the fact is false.

If a target application requires a private or restricted fact, obtain it from the
candidate or the ignored private evidence layer and keep it out of tracked public
context unless the candidate explicitly authorizes publication.
