# FREE_ONLY live use and bounded AI Worker

This guide is the first real-use path for P001. The repository can prepare and gate a live Alibaba Cloud Model Studio request, but it cannot prove provider billing state by itself. A human must confirm the provider console state before every live session.

## Safety model

A live request is allowed only when all of these are true:

1. The local inventory route is `free_only` and has confirmed-free billing plus confirmed-usable quota.
2. The selected resource has a `live_use` attestation with `allow_live=true`.
3. `free_quota_only=true` and `paid_fallback_disabled=true` are explicitly recorded.
4. The attestation is recent (currently no more than 24 hours old).
5. The resource is not expired/exhausted and the selected model meets the requested capability tier.
6. The request is capped to one provider call and a bounded output-token limit.
7. The adapter is called through the gateway; direct live adapter invocation is blocked.

Unknown state always stops. There is no automatic paid fallback or model/provider retry.

## Alibaba Cloud prerequisite

Before a live request, open Model Studio on a computer and check the free-quota page for the exact model you plan to call. Confirm that the model still has free quota and that **Free Quota Only / stop when free quota is used up** is active. Alibaba documents that this protection stops requests with `403 AllocationQuota.FreeTierOnly` after free quota exhaustion instead of continuing to paid usage. The provider also notes that protection-setting changes may take time to become effective, so wait until the console shows the intended state before invoking.

Official reference: <https://help.aliyun.com/en/model-studio/new-free-quota>

## Local one-shot invocation

Copy the synthetic example to an ignored local file:

```bash
cp data/credits_inventory.example.json data/credits_inventory.local.json
```

Edit the local copy. At minimum:

- set top-level `example` to `false`;
- replace the synthetic balance/expiry with what you actually saw;
- keep only models whose current free quota you confirmed;
- set the model tier conservatively (`Unknown` models should not be promoted merely from marketing);
- set `live_use.confirmed_at` to the current ISO timestamp after checking the console;
- set `live_use.free_quota_only=true` only after the protection is visibly active;
- keep `max_requests_per_run=1` and choose a small `max_output_tokens` cap.

Do not put an API key in the inventory. Configure it only in the environment:

```bash
export DASHSCOPE_API_KEY='...'
```

First exercise every repository-side gate with no request:

```bash
credits-radar invoke \
  --inventory data/credits_inventory.local.json \
  --tier A \
  --prompt 'Reply with a one-sentence summary of FREE_ONLY routing.' \
  --max-tokens 200 \
  --dry-run \
  --json
```

Then, while the console confirmation is still current, remove `--dry-run` for one request:

```bash
credits-radar invoke \
  --inventory data/credits_inventory.local.json \
  --tier A \
  --prompt 'Reply with a one-sentence summary of FREE_ONLY routing.' \
  --max-tokens 200
```

Successful live runs append sanitized metadata to `data/usage.local.jsonl`. Model content is not written there.

## Use the free model to help develop P001

Copy the worker example:

```bash
cp data/worker_task.example.json data/worker_task.local.json
```

A worker task contains a goal plus an explicit allowlist of repository context files. The worker reads at most eight files and at most a bounded amount of text. It cannot run shell commands, edit files, commit, push, create PRs, merge, or read GitHub secrets.

Dry-run first:

```bash
python scripts/free_ai_worker.py \
  --task data/worker_task.local.json \
  --inventory data/credits_inventory.local.json \
  --dry-run \
  --output-dir artifacts/free-ai-worker
```

A dry-run writes `run.json` and `prompt-preview.md`. A live run writes `model-output.md` and metadata. Treat that output as a proposal for Strong Chat/human review, not as an applied change.

## GitHub Actions worker

`FREE_ONLY AI worker` is manual-only. Its default is `dry-run`. For `invoke` mode, both checkbox confirmations must be true:

- the exact model currently has free quota;
- Free Quota Only / stop-when-exhausted protection is active.

The provider secret is scoped only to the live step after those checks. Free-text task/model/context inputs enter the script through environment variables rather than shell command interpolation. The workflow uploads artifacts and has read-only repository permissions.

## Expected safe stop

If Alibaba returns `403 AllocationQuota.FreeTierOnly`, the adapter translates it to a FREE_ONLY exhaustion hard stop. The gateway does not retry and does not switch to another model or paid path. Re-check the console and create a new attestation before any later live request.

## Current limitation

P001 does not yet refresh Alibaba remaining quota programmatically. The inventory and live-use confirmation are human-attested facts. This is deliberate: API success alone is not evidence that a request is free. Future provider integrations should add authoritative quota checks only when the provider offers a trustworthy machine-readable mechanism.
