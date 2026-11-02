# Exclusive Phase A continuation

This runner implements the 2 November handover while Hegel's user timer and service are paused. It serves the original plain Qwen weight locally on 8082 with four 16K slots and runs four recipe4 workers. The original paraphrase prompts, filters, seeds, targets and gate are unchanged.

Use a new job directory and a frozen source copy. Copy all original data and 542 completed request chains exactly; retain both successful and failed units. The saved partial unit is replayed from its original receipt. A missing end or altered hash prevents continuation. Every new request is written before transmission; an uncertain response is preserved and stops the run without a retry.

The job owns its server process, checks the idle GPU before loading, and records its start, readiness and confirmed exit. It uses the installed startup lock. It never stops an existing listener. Requests have an absolute timeout; workers drain before the owned server receives SIGTERM.

The frozen deadline policy uses the actual Power Guard deadline, with fifteen minutes reserved for shutdown. It accepts the requested one-night extension only after its exact administrator result is verified, and never runs beyond the plan's stop time. A new boot or pending shutdown stops new requests. The runner changes no power setting or Pi service.

After the complete canonical gate passes, the heartbeat can restore Hegel's saved three-slot server and user timer as authorized by the handover. It must reconcile the result and owned exit first. This runner neither trains nor resumes the world itself.

Validation: eleven tests cover four concurrent canonical workers, successful and failed ledger preservation, exact cached replay, uncertain responses, absolute HTTP deadlines, owned fake-server lifecycle and the verified power extension. An additional offline replay checked the real unledgered wallace-logic:334 response and stopped before sending anything.
