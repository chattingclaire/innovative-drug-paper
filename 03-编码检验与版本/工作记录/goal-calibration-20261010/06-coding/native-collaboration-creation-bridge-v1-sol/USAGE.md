# Creation receipt bridge

This component verifies creation metadata and delegates to the existing sealed R1 receiver. It dispatches no agent, creates no chat/campaign/scope, and performs no policy coding or scoring. The original app `create_thread` request/return path and original receiver CLI remain available unchanged.

## ROOT receipt

`receipt_version` is `native-collaboration-creation-bridge-1`; `tool` is `collaboration.spawn_agent`. ROOT declares `purpose` as `technical_only` or `native_coding_creation`, and pins `authority.root_thread_id`, `authority.root_turn_id`, and absolute `authority.scheduling_root`. The caller separately supplies the same trusted ROOT thread/turn/namespace and purpose. Purpose is ROOT authorization, not a model-inferred classification.

`sources` has exactly `spawn_request`, `spawn_return`, `root_read`, and `child_read`. Each source contains `artifact: {path, bytes, sha256}` and an RFC6901 `json_pointer`. The first two pointers select the actual logical dispatched argument object and actual spawn return, respectively. These are ROOT-owned external scheduling records; provider wire capture is not required or claimed. Full request `message`, `model=gpt-6.1-sol`, `reasoning_effort=ultra`, and `fork_turns=none` must be present. The actual return must have the matching `/root/<task_name>`.

Each read pointer selects a capture with actual `request.threadId`, `observed_start_utc`, `observed_end_utc`, and `raw_tool_result`. The optional source `payload_pointer` defaults to `/content/0/text` within that raw result; JSON text is decoded using the strict parser. The payload must be the app's schemaVersion 1 thread/turn/page data. Extracted lifecycle assertions or an actor's own identity declaration are insufficient.

The current pinned ROOT turn must show one matching `subAgentActivity` with `kind=started`. AgentPath→UUID and UUID→agentPath must be unique in the observed ROOT turns. Repeated or `interacted` target events are rejected. The canonical child UUID must match the child app request and response. Child `createdAt` must fall between the ROOT turn's start and its actual read observation; the child's only first turn must start after its creation and before its own read. Child `hasMore=false` and `nextCursor=null` are required to exclude hidden older turns. Unknown exact spawn-call timing remains null. If an actual `spawn_call_observed_interval` is supplied, its timestamps and child creation second are checked. No new pre-spawn API or exact spawn timing is a mandatory gate.

## Preflight only

Run in a new Python process, supplying the sealed binding SHA and actual receipt SHA:

```sh
python3 -B creation_bridge.py preflight \
  --binding /ABS/bridge-binding.json --binding-sha ACTUAL_SHA \
  --receipt /ABS/root-receipt.json --receipt-sha ACTUAL_SHA \
  --scheduling-root /ABS/ROOT_EXTERNAL_NAMESPACE \
  --root-thread ACTUAL_ROOT_UUID --root-turn ACTUAL_ROOT_TURN_UUID \
  --purpose technical_only --report /ABS/NEW_CREATION_ONLY_REPORT.json
```

Creation-only success certifies only the observed creation relation. It does not certify a policy prediction, required source reading, frozen whole history, truncation/compaction status, first output, attempt eligibility, Gold separation, or a full native receipt. Provider telemetry stays null.

## Future coding reception

Only a ROOT-authorized `native_coding_creation` receipt can use `receive`. The `technical_only` route is rejected before normalization or original receiver invocation. Add `--normalized-dir /ABS/NEW_DIR_WITHIN_SCHEDULING_ROOT --native-args-file /ABS/ACTUAL_NATIVE_ARGS.json --native-args-sha ACTUAL_SHA` and use `receive` instead of `preflight`. The argument JSON uses original CLI names with underscores. Required keys: `actor_seal`, `batch`, `attempt`, `report`, `plan`, `plan_sha`, `native_root`, `report_root`, `runtime_binding`, `runtime_binding_sha`, `scheduling_root`. Optional keys: `technical_evidence`, `initial_prompt_file`, `initial_prompt_sha`, `original_instruction_file`, `runtime_pointer`, `runtime_evidence_member`, `runtime_evidence_pointer`, and `prior_report` (a list retaining every prior report). Original creation/pointer arguments cannot be overridden through this JSON.

After creation preflight, the adapter writes an immutable request mapping `message→prompt` and `reasoning_effort→thinking`, and a return mapping the actual app started-event UUID to `threadId`. It seals the provenance, then invokes the bound, unchanged original receiver in a fresh subprocess. The normalized directory and actual evidence must reside in the original plan-authorized external scheduling namespace. The original receiver still checks the actual prompt hash/short initial file, UUID/runtime-tool evidence, whole actor seal and first/whole order, original scope/read/use gate, complete history/truncation/compaction evidence, original schema/manual/runtime binding, prior reports, and max3 attempts. The adapter grants no extra attempt and never registers a campaign or reads Gold.

The original receiver's pending/error/selection behavior and its report seal are authoritative. A normalization seal is not a native selection receipt. The component is prepared but no actual coding receipt or native receiver execution has been performed here.

## Evidence boundary and finite verification

ROOT-owned saved logical tool arguments are the same trust boundary used by the original external create request file; they are not cryptographically signed provider records. The adapter binds their actual path/bytes/SHA and actual app response, and does not upgrade unknown wire model or reasoning telemetry to observed facts. The current real author metadata is explicitly technical-only. Constructed fixture UUIDs/times are visibly synthetic and test only finite creation branches.
