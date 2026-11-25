---
name: benchmark-checklist
description: Use when reporting or reviewing measured latency, throughput, speedups or performance regressions, or choosing between configurations using benchmark results.
---

# benchmark-checklist

Write down the proposed claim, including the operation, workload, metric and unit. Read the timed region and the code that computes its numerator and denominator. When reviewing supplied results, identify which claims the available measurements support.

| Question | Evidence to inspect |
| --- | --- |
| What work finished inside the timer? | Check the completion boundary for async, lazy or batched work. Count successful, correct outputs against expected work. Record failures, skipped inputs, retries and timeouts on each side. |
| Are the runs comparable? | Match workload, hardware, build mode, warmup and concurrency. Record the intended differences. When comparing implementations, check that each uses its supported production configuration. |
| How variable is the result? | Alternate repeated baseline and candidate runs under similar load. Report the sample count per side, statistic and spread. A single run can support a labeled ballpark after checking completion and errors. |
| What limits this workload? | Use a separate profiling run to locate the bottleneck, including the load generator. Check a proposed explanation against resource limits and the fraction of end-to-end time affected. |
| Does this measure the user's operation? | Match the claim to the measured boundary. A faster kernel establishes a kernel result. An end-to-end claim needs evidence from the end-to-end path. |

**Example.** An inference benchmark increments its counter at GPU submission, then drains the queue after stopping the host timer. That measures submission rate. To measure completed inference throughput, start from a drained queue, time through completion of the measured batch and divide successful outputs by that interval. For a device-only latency claim, use device timing events on the relevant stream. Keep timing scopes explicit.

Report **faster**, **slower**, **no measurable difference**, or **inconclusive** for the stated metric and workload. Give values and units for both sides, run counts, variability, and a command or artifact when available. Use “inconclusive” when completion, correctness or comparability is unknown. If repeated comparable runs cannot resolve the claimed change, report that resolution limit. Separate any observed difference from a proposed cause that still needs profiling.
