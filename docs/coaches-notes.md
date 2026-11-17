# Coaches Notes assistant

Open **Coaches Notes** in the dashboard sidebar or **Open game-plan assistant** beneath a selected call. Select a live game session to ask questions about its saved situation, evaluation, eligible playbook calls, designs, and recorded plays. Facts, calculations and plan drafts run in the backend. Ollama helps select catalog options for other questions; no hosted model API key is required.

Install Ollama separately, start its local service, and pull a model (the default is `llama3.2`, for example `ollama pull llama3.2`). Configure `DIGITALOC_OLLAMA_MODEL` to use another installed model. `DIGITALOC_OLLAMA_URL` defaults to `http://127.0.0.1:11434` and only loopback hosts are accepted. If Ollama is unavailable, model-assisted selection reports an error. Fact questions, supported hypothetical calculations and chat plan drafts still work.

Conversation messages are held only in the browser for the current view and sent to the local Ollama service with current session context. They are not written to the session database. The assistant can explain existing evaluation outputs but does not calculate new statistics or change model inputs. Game plans requested in chat are returned as structured proposals in the editor. Review and edit the proposal, then explicitly save it. A chat message or generated proposal never changes game state, queues a call, or records a play.

The assistant saves a title, notes, up to five opening calls, and up to five conditional alternatives. The opening order comes from existing situational-fit rules, constrained by the installed playbook, run/pass filter, personnel, formation, and field space. Opponent historical coverage tags inform conditional alternatives; catalog-related calls supply additional review options. These are templates for review, not optimized sequences or concept outcome predictions.

Choose **Edit plan** to change notes, select calls, edit purposes and observations, add/remove entries, or move entries earlier. Both script and counter sections allow up to 15 entries. Save persists the draft in the session; discard restores the saved content. Navigation and game switching are disabled during edits, and browser unload warns about unsaved edits. Regeneration asks before replacing the previous draft and coach edits. There is one current saved plan per session, not a version history.

Each plan retains the generation-time game state, preferences, catalog version, and opponent evidence (source, seasons, sample size, matching scope, and coverage frequencies). Missing coverage is explicitly shown, and playbook-only drafting still works. Free-text edits are coach-authored notes, not verified evidence. No player availability, film analysis, new model training, or next-snap forecast is inferred.

Situation or preference changes make the previous plan stale. It remains readable, but regeneration is required before editing/saving for the new situation. Opening calls require fresh eligibility checks after each snap. Plans do not enqueue calls, record outcomes, or change game state. Saving or regenerating does clear latest-play undo, following other session mutations.

## API

- `POST /api/sessions/<id>/plan/generate`: `{revision, mutation_id}` generates and saves a replacement draft.
- `POST /api/sessions/<id>/assistant`: `{revision, message, history}` reads a live session and returns a reply plus an optional validated plan proposal. This endpoint is read-only and uses local Ollama only for catalog selection.
- `PUT /api/sessions/<id>/plan`: `{revision, mutation_id, context_id, content, source?}` validates and saves coach-approved content. Creating or replacing a plan requires `source: "local_assistant"` or `source: "coaching_rules"` (use the assistant response’s `proposal_source`); ordinary edits update the current plan without a source field.
- `GET /api/sessions/<id>` includes `coaching_plan` when present.

Both mutations use revision conflict protection and retry deduplication. The server owns evidence and generation context; the editor can only change content. Invalid/unavailable call IDs and oversized sections/text are rejected. Historical review batches cannot generate plans. This remains a local service with the existing authentication limitations.

## Situation-focused responses and plan layout

Coaches Notes now separates the saved situation, conversation, and plan editor. A six-cell situation summary shows score, clock, down/distance, field position, timeouts, and objective. Script and counter cards sit side by side on wider screens and stack on mobile; saved-plan evidence is expandable. Each new assistant reply carries a backend-generated situation snapshot so its game context remains visible even after subsequent game changes. Only message role/text is sent back as conversation history.

## Grounding boundary

All displayed facts and explanations now come from backend templates, game-state calculations, catalog entries or model evidence with explicit units and scope. Ollama can return only a `focus` enum and up to three `call_ids`. The server rejects extra fields, unknown or currently ineligible IDs, duplicates, malformed JSON and token-limit termination. It retries once, then reports a clear error. No arbitrary model prose or numeric claims are rendered. This deliberately narrows the assistant: it cannot provide unrestricted football analysis or reliably resolve every conversational reference.

Supported gains/losses are applied to an isolated state using the existing game transition engine, not saved. The response labels hypothetical assumptions and holds the clock constant unless a supported elapsed-time expression is supplied. Unclear penalties, unsupported scenarios and conflicting premises request clarification. Phrase parsing is bounded and not a universal natural-language interpreter; unsupported wording may require restating the question. Game state/revision changes during inference reject stale responses.

Requests to draft opening calls and counters produce an editable rules-based proposal without Ollama. Recognized numeric counts are bounded to 15 and to the available distinct calls; the default is three opening calls and two counters. Drafts use existing situational-fit ordering, catalog reads and opponent-evidence-backed conditional templates. They cannot promise optimized sequencing. No eligible calls means an explanation and no empty proposal. Coach approval is still required to save; saved source stays `coaching_rules`.

Call eligibility covers installed plays, action filter, personnel, formation and field space. Distance bands are preferences, not hard exclusions in the existing suitability engine. The response displays a caution if a selected call falls outside its preferred distance band; an eligible call is not necessarily a good conversion decision. No new concept probabilities, kicking model or causal play values are introduced.

Ollama uses a 16,384-token context window and a 512-token selection budget. History is bounded to 6,000 characters. The context includes the saved state, available calls, recent plays, a compact plan summary and evaluation evidence. Past chat cannot change the server-rendered snapshot. Model choice can still affect relevance of selected calls, and starter templates require coach review.

See `assistant-wording-audit.md` for the original failures and `assistant-wording-retest.md` for the post-change evaluation. These are exploratory cases, not a general accuracy guarantee.

## Optional Gemini analysis

Set `DIGITALOC_ASSISTANT_PROVIDER=gemini` to add model-authored contextual analysis, displayed separately from the server-grounded answer. This is an explicit exception to the local selection-only boundary above: Gemini prose is not fact-verified and requires review. See [setup and data flow](gemini-coaching-assistant.md). Ollama remains the default; hosted requests require a backend-only `GEMINI_API_KEY`.
