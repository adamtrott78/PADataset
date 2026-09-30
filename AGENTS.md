# PADataset agent route

This file is a thin executor adapter. It does not own scientific, workflow,
artifact, result, or task-state truth.

1. Start with `README.md` at the task's actual PADataset ref.
2. Follow only the relevant task route and scoped PADataset context named there;
   do not recursively inventory unrelated repository areas.
3. When work involves repository mutation, runtime coordination, Git
   synchronization, executor handoff, or a durable task capsule, start from the
   [workspace-control root route](https://github.com/adamtrott78/workspace-control)
   and follow its shared operator policy.
4. When a task capsule supplies an exact workflow/checkpoint and
   `next_safe_action`, use that durable task state rather than this adapter as
   the handoff.
5. PADataset remains authoritative for project-domain facts and project-specific
   validation. workspace-control owns generic cross-project operator semantics.

Do not copy the shared workspace-control policy into this file or into PADataset
contexts. This adapter exists only to make the canonical routes easy for
executor-specific tooling to discover.
