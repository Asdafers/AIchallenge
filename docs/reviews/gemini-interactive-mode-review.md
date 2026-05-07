# Design & Implementation Review: Interactive Mode (Human-in-the-Loop)

**Reviewer:** gemini-2026-05-07T2300-REVIEW  
**Status:** Completed  
**Task ID:** c99d2c75-6939-4421-90d7-4bb3ad7cec81

---

## Intent Summary
The goal is to introduce an "Interactive Mode" for Methodic, allowing real humans to replace simulated participants in the research interview loop. This requires a blocking agent step (`HumanInputStep`), a session management layer to bridge the ADK runner with FastAPI endpoints, and a new three-state frontend (Config → Interview → Results).

---

## STRENGTHS

1.  **Clean Architecture Separation:** The use of `build_agent_graph()` factory function is excellent. It allows 95% code reuse between demo and interactive modes while cleanly swapping the participant agent and trimming the finalization pipeline.
2.  **Stateless Agent Loop:** The `HumanInputStep` writes to the same state keys (`latest_participant_turn`) as the `participant_sim_agent`. This ensures that `ExtractorStep` and `TurnCheckerStep` work perfectly without modification, preserving the core value of the system (adaptive follow-ups and extraction).
3.  **Robust SSE Pattern:** Moving the `runner.run_async()` into a background task and using an `asyncio.Queue` for SSE is the right choice. It solves the "planning phase delay" and ensures events are not lost if the client connects shortly after the session starts.
4.  **Low-Latency Feedback:** By bypassing the BigQuery export and Quality Reviewer steps in interactive mode, the user gets immediate structured results, which is critical for a "live" demo experience.
5.  **Secure Session Mapping:** The `_session_lookup` map effectively hides ADK's internal session IDs from the public URL, providing a layer of security and allowing for cleaner external-facing IDs (e.g., `INT-xxxx`).

---

## GAPS

### Major

1.  **Race Condition in Participant Message Slot (Severity: HIGH)**
    *   **Issue:** The `InteractiveSession` uses a single `message` string slot. If a user (or a bot) sends multiple responses rapidly, Message N+1 will overwrite Message N before the `HumanInputStep` consumes it.
    *   **Impact:** Possible loss of human input if "Send" is double-clicked or if latency causes overlapping requests.
    *   **Recommendation:** Use a small `asyncio.Queue` for the message slot in `InteractiveSession` instead of a single string. `HumanInputStep` would then `await reg["queue"].get()` instead of `wait()` + read string.

2.  **Incomplete Error Handling in `_start_interactive_pipeline` (Severity: MEDIUM)**
    *   **Issue:** If the ADK runner fails (e.g., Gemini API quota), the background task catches the exception and puts an `error` event in the queue, but it doesn't gracefully close the session in the registry.
    *   **Impact:** The frontend might stay in a "typing" or "waiting" state if it doesn't handle the `error` author correctly.
    *   **Recommendation:** Ensure the frontend explicitly handles the `error` author in `consumeSSE` and displays a user-friendly error banner.

### Minor

1.  **RegistryProxy Complexity (Severity: LOW)**
    *   **Issue:** The `RegistryProxy` override of `__getitem__` is clever but slightly opaque. It manually syncs `isess.message` into a dict entry.
    *   **Impact:** Higher maintenance burden/confusion for future developers.
    *   **Recommendation:** Pass the `InteractiveSession` object directly to `HumanInputStep` or store the object in the registry dict. `reg[adk_sid]` should be the `InteractiveSession` instance.

2.  **Missing "Session Expired" UI State (Severity: LOW)**
    *   **Issue:** Sessions are cleaned up after 30 minutes. If a judge leaves the tab open and returns later, the POST to `/respond` will 404.
    *   **Impact:** Broken user experience.
    *   **Recommendation:** Add a simple 404 handler in the frontend that redirects to State 1 with an "Interview Expired" message.

---

## IMPROVEMENTS

1.  **Human Input Queue:** As noted in Gaps, replace `message: str` with `input_queue: asyncio.Queue` in `InteractiveSession`. This is more "async-native" and prevents overwriting input.
2.  **Typing Indicator Refinement:** The design suggests showing the typing indicator whenever `input_requested` is false. However, during the "planning" phase, the interviewer isn't "typing" yet. The UI should distinguish between `Planning...` and `Interviewer is thinking...`.
3.  **Result Polling/Event:** The Results screen should ideally trigger automatically when the "Stream complete" system event is received, rather than requiring the user to wait and click.
4.  **Persona Consistency:** In `presets.py`, the `persona_hint` is shown to the human. It might be helpful to also pass a *summary* of this persona to the `ExtractorStep` (via session state) to improve extraction context, though the interviewer should still stay "blind" to maintain research integrity.

---

## VERDICT

**VERDICT: SHIP-WITH-CHANGES**

The design is sound and the implementation plan is high-quality. The most critical change is moving from a single message slot to an `asyncio.Queue` for human input to avoid race conditions. Once that and the error handling refinement are addressed, this feature will be a major upgrade to the Methodic demo experience.

---

## Task Complete
Task `c99d2c75-6939-4421-90d7-4bb3ad7cec81` is verified against `mission_strategy['aichallenge']`. Deployment to Cloud Run v8 is planned in Task 8.
