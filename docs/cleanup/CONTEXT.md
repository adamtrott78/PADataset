# Repository maintenance and evidence preservation

Use this context to inspect checkout state, distinguish source from local runtime
artifacts, preserve a local change, or investigate incomplete banks and runs.
Generation, training, and paper editing belong to their owning contexts below.
Run commands from the repository root unless stated otherwise.

## Ownership and boundaries

The tracked repository contains code, configuration, documentation, and selected
research evidence. A prepared Lambda checkout also contains ignored captures,
banks, feature caches, checkpoints, result tables, and local source changes.
A file absent from GitHub is not necessarily absent from Lambda. A Git branch
preserves committed files only; it does not back up ignored or untracked files.

[.gitignore](../../.gitignore) uses path and extension rules, not a file-size
threshold. For example, CSVs, H5 caches, model checkpoints, and generated result
roots are ignored. Later rules and existing tracked status matter: an ignore
pattern does not remove an already tracked file. Untracked Python and shell
scripts can be valuable source that has never been committed.

Use current source/configuration to establish executable behavior. Use scoped
contexts for intended workflows and scientific interpretation. Saved configs,
summaries, and cache headers establish what a particular run actually did.
If those disagree, retain both claims with their provenance and investigate;
do not relabel a historical run or change a scientific setting to hide the
disagreement. Generated indexes are discovery aids, not normative instructions.

## Common tasks

### Inspect a checkout before planning changes

These commands are read-only and do not switch branches:

```bash
git rev-parse --show-toplevel
git branch --show-current
git log -1 --format='%H %s'
git status --short
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard
```

Expected output identifies the checkout, commit, tracked edits, staged changes,
and nonignored untracked files. A clean status does not mean local datasets or
caches are absent. Inspect the specific artifact path needed for the task;
avoid recursively inventorying tensor storage just to answer a source question.


### Complete an AI-assisted source change safely

The preferred collaboration loop is:

inspect exact local/GitHub state
→ make one bounded change
→ execute and validate on the prepared machine when runtime behavior matters
→ inspect the explicit diff
→ stage reviewed paths
→ commit
→ push
→ have ChatGPT reread the pushed commit before the next source mutation.

If the prepared Lambda checkout contains unrelated tracked edits, untracked
research source, paper work, or ignored runtime artifacts, do not
stash/clean/switch it merely to perform documentation or source work. An
isolated Git worktree from the reviewed branch is often safer. Record both
worktree paths and branches so later commands cannot silently operate on the
wrong checkout.

JupyterLab and other long-lived graphical workspaces do not automatically
follow the terminal into a new Git worktree. Before editing, verify the
actual checkout with `pwd`, `git branch --show-current`, and
`git rev-parse HEAD`.

Before staging a successful change, use the narrow sequence:

```bash
git diff --check
git status --short
git diff -- path/to/reviewed_file1 path/to/reviewed_file2
git add path/to/reviewed_file1 path/to/reviewed_file2
git diff --cached --check
git diff --cached
git commit -m "descriptive message"
git push origin "$(git branch --show-current)"
```


Do not use `git add .` as a shortcut in a prepared research checkout.
After pushing, compare the remote branch/commit with the intended local
commit and let the next ChatGPT turn reread that pushed GitHub state.

For a large copy/paste operation in an interactive SSH session, put strict
Bash mode inside a child process rather than enabling `errexit` in the
persistent login shell:

```bash
bash <<'TASK'
set -euo pipefail

# bounded operation here

TASK

rc=$?
echo "task exit status: $rc"
```


A failure then terminates the bounded child operation without terminating
the user's SSH login shell.

Copy/paste integrity is also a source-safety issue. If a ChatGPT response
visibly terminates a code fence early and shell commands continue as prose,
do not infer where the boundary was supposed to be and do not run a
reconstructed command. Request a corrected single block. Responses that
generate Markdown containing fenced code should use a longer outer fence or
another representation that cannot collide with the embedded fence.

### Determine why a required file is missing from GitHub

Set the path to one specific required file:

```bash
artifact_path='results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv'
git ls-files -- "$artifact_path"
git check-ignore -v -- "$artifact_path"
python - "$artifact_path" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
print('symlink:', p.is_symlink())
print('exists:', p.exists(), 'file:', p.is_file(), 'directory:', p.is_dir())
if p.is_symlink():
    print('link target:', p.readlink())
if p.is_file():
    print('bytes:', p.stat().st_size)
PY
```

`git check-ignore` returns 1 when no supplied path is ignored; that alone is not
a failure. An empty `ls-files` result means the path is not tracked. A broken
symlink can exist while `exists()` is false. Confirm its storage mount/target
before rebuilding or removing anything. A fresh checkout needs separately
provided or regenerated runtime artifacts; see [preprocessing](../../scripts/preprocess/CONTEXT.md)
and [results](../../experiments/context/RESULTS.md) for prerequisites.

### Preserve selected local source before integrating documentation

Review exact files and their dependencies first. For an existing tracked file:

```bash
git diff -- experiments/pa_dashboard.py
```

For an untracked script, inspect its contents and required imports/configuration;
`git diff` does not display untracked file contents. Compare against the intended
branch before deciding whether it is a new implementation or an older copy.
Record the source checkout commit and the selected file hashes alongside any
inspection bundle. Do not include API credentials or tensor payloads in a source
review bundle.

Once the selected change is ready to commit, stage only its reviewed paths and
inspect `git diff --cached` before committing. Do not use a broad `git add .` to
preserve a dirty research environment. Integrating GitHub documentation into a
dirty Lambda checkout is a separate operation: inspect branch divergence and
local edits first, and preserve local-only files outside Git where necessary.

### Investigate an incomplete bank, cache, or experiment

Start with the owner's validation workflow:

- [Banks, labels, and cache headers](../../scripts/preprocess/CONTEXT.md).
- [Training artifacts, completion, and partial runs](../../experiments/CONTEXT.md).
- [Capture and resplice recovery](../../txrx/CONTEXT.md).
- [Result provenance and source CSVs](../../experiments/context/RESULTS.md).

An existing H5 file is not proof that it has the requested pooled length; the
cache builder can skip it without validation. An old progress file is not proof
that a worker is still running. Inspect the worker process/log and the actual
completion artifacts before choosing a recovery operation. Preserve failed-run
evidence and use a new run/output name when appropriate.

[tools/quarantine_banks.py](../../tools/quarantine_banks.py) is a mutation tool,
not a read-only validator. It scans `data/<protocol>/ota/<bank-name>` for
`<bank-name>__shard_*__PA*.mat`, checks HDF5 dataset `X` for rank 3, first dimension
equal to `--expected-rows`, and second dimension 2. It does not validate labels,
signal quality, or all possible MATLAB/HDF5 axis layouts. Confirm the layout
against the producing code before classifying a file as bad.

Its default action moves failing files to `results/bank_quarantine_<timestamp>`;
`--quarantine-dir` selects another destination and `--delete` unlinks them.
It has no dry-run flag. Omitting `--protocol` scans all three protocols, and
missing bank directories are silently skipped, so zero scanned files is not a
successful bank validation. Review exact source/destination paths and preserve
provenance before choosing to run it; do not use it as a routine health check.

### Recover an old documentation statement

The pre-modularization documentation is preserved at commit
`077c8d9466e1a4e70bb8163560e4b52e108cef92`, also named by
`context-pre-modularization`. If that object is available locally:

```bash
git show 077c8d9466e1a4e70bb8163560e4b52e108cef92:README.md
```

Otherwise inspect that commit on GitHub or fetch the preservation branch before
using `git show`. Recover only the needed evidence and verify it against current
source. Do not restore an old handoff as a competing active entry point.

## Historical cleanup is not a current workflow

[spring_clean_padataset.sh](spring_clean_padataset.sh) is a one-off restructuring
script with a hardcoded Lambda path. Although its default mode prints a dry run,
`--apply` switches/creates a cleanup branch, moves files, appends ignore rules,
and overwrites README placeholders describing the experiment system as future
work. It must not be used for routine maintenance or replayed after this context
refactor. [spring_clean.md](spring_clean.md) records that earlier migration.

The [migration audit](CONTEXT_MIGRATION_AUDIT.md) is a finite documentation-change
record. It is not a runtime runbook or a source of scientific settings. Historical
notebooks, incident reports, exemplar analyses, and generated result inventories
can remain useful evidence without becoming current instructions.
