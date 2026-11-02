# Personal research management workspace

The dashboard is the owner's local management desk. Its primary job is to expose
active agent assignments, queued work, evidence, dependencies and the next useful
action. It does not establish investment performance or complete the broader
private research and eventual execution operation.

## Final design direction

The owner corrected an earlier DeepMind-inspired proposal: this is a personal
management dashboard and should not resemble a company landing page. That direct
preference governs the final implementation. The oversized hero, constellation,
marketing copy, call-to-action banner and footer slogans were removed.

Palette: paper `#ffffff`, workspace `#f5f7fb`, ink `#20314b`, restrained blue
`#2858cf`, rule `#dfe6f1`, and secondary slate `#62768f`. Green and amber indicate
recorded states. Typography uses local Avenir Next / system sans with compact
headings, legible task copy and small secondary metadata. No external fonts,
images, gradients or decorative performance statistics are used.

The left rail provides quick navigation. The top bar holds the project stage,
snapshot freshness, health and refresh/pause controls. The workboard appears
immediately below a compact project summary. A right-hand task inspector stays
available while selecting agents or milestones. Evidence, decisions, dependencies,
activity, costs and health details form a secondary management layer.

```text
navigation | project / stage              health / freshness / controls
           | short observed summary / milestone counts
           | planned | active | completed | persistent task inspector
           | milestones and evidence     | health / costs / activity
           | decisions / dependencies
           | contextual assistant drawer when opened
```

Each actual agent has a deterministic local geometric SVG icon on its work card.
The board columns can scroll independently to keep the work overview compact.
Search and state filters reduce the visible work; selection exposes exact role,
model, task, last observation and recorded detail. On narrower screens the task
inspector and secondary information stack, then the board becomes one column.
Visible focus and reduced-motion preferences are supported.

## Dependency map

An explicit Board / Dependency map switch provides a compact alternative view of
the same saved work. The map uses milestone titles, statuses and evidence plus
optional `dependencies: [{from, to, reason}]` records referencing milestone IDs.
No edges are inferred from task names, layout, completion states or agent roles.
The server validates references and acyclicity; the client also rejects malformed,
duplicate or cyclic relationships rather than drawing a partial misleading graph.
Missing relationships produce an explicit empty-map message.

The local SVG places prerequisites left of dependent milestones using topological
depth. Every node displays its actual text state and a corresponding status color.
Nodes support click, Enter and Space selection. The existing task inspector shows
the selected milestone's evidence, incoming prerequisite status/reasons, unresolved
prerequisite count, and downstream relationships. A completed prerequisite does
not by itself certify that the next activity is approved or ready for execution.

The diagram refreshes from every successful status poll while visible. It retains
the chosen view, selected milestone, keyboard focus and scroll position; changed
statuses, edges and prerequisite counts come from the new snapshot. It shares the
workspace's observation time, stale indicator and fetch-error notice. Polling is
not native-agent telemetry. Arrows describe recorded prerequisite relationships,
not runtime agent messages. The scrollable canvas keeps the diagram usable within
the management layout and at narrow widths. Search de-emphasizes nonmatching
milestone titles while retaining the graph's relationship context.

## Work and evidence semantics

The board uses saved observations only. Planned work combines planned agent tasks
with saved pending milestones, explicitly labeled "Planned milestone / no worker
assigned." Milestone cards show their recorded status and open their evidence;
they have no invented agent, model or inbox. Blocked agent work remains visible
with its actual blocked state. Empty columns do not invent future work.

Milestone counts describe records marked complete in the snapshot, not the
completion percentage of the whole operation. Every milestone retains its evidence
text. Unknown budget values remain unknown. Snapshot refresh every two seconds
does not imply continuous native-agent telemetry; observations older than 90
seconds are labeled stale. Refresh failure retains the last valid snapshot with
an explicit notice.

## Conversations and original-worker inquiries

A persistent user-opened drawer exposes the server's roles and exact models:
the larger desk helper and smaller contextual assistants for recorded agents.
These are labeled new contextual assistants, not the original Codex workers.
Session initialization uses `GET /api/session`; session-owned conversation history
uses `GET /api/conversations?agent_id=...`.

Only manual sends issue `POST /api/chat`, with the CSRF header, a fresh request ID,
and a 1–4000-character message. There is no automatic retry of a paid request.
Model, observed context time, hash, source paths and conservative cost estimate
are inspectable on replies. Errors and incomplete/unknown outcomes remain
explicit. Project model calls can be paused/resumed separately from snapshot
refresh. The budget observation is refreshed after a model request.

Each original worker also has a separate inquiry inbox. `POST /api/inbox` records
a pending question without calling a model. The local lead must retrieve it and
record an actual worker response with actor and source provenance. Submitting a
question does not establish delivery or an answer. `GET /api/inbox?agent_id=...`
loads session-owned questions and recorded replies; open inboxes check every 15
seconds. Desk helper has no original-worker inbox. Task details offer separate
actions for the contextual assistant and the worker inquiry inbox.

The UI renders snapshot/model/source text as text, accepts only HTTPS repository
links, and uses local assets compatible with the server CSP. Missing backend or
disabled models produces an unavailable state rather than sample replies.
`/api/health-details` displays observed local service metadata; browser reachability
alone does not establish continuous monitoring. Continuous local operation needs
an awake Mac. The project budget cannot control unrelated account clients.

## Verification and ownership

The frontend producer changed only `src/quanto/web/*` and this design document for
the revised interface. JavaScript syntax checks pass. The structural audit confirms
all JavaScript element references exist, all 76 HTML IDs are unique, and CSS braces
balance. These are software checks, not investment evidence or independent review.
Isolated synthetic graph checks pass for topological depth, changed milestone
state, unknown references, cycles, duplicate relationships and missing edges.
These checks validate software behavior, not the recorded operation's progress.

The root also verified dynamic behavior through its task browser on a separate
three-node synthetic fixture: without a reload, milestone `b` changed from running
to completed, its SVG state class changed to `node-completed`, selected milestone
`c` stayed selected, and its unresolved prerequisites changed from 1/1 to 0/1.
The Dependency map view remained selected. This is observed interface verification
using a fixture, not a change to actual recorded research progress. The four-column
actual graph uses 184px nodes and 40px gaps (900px total width including margins)
to fit the main pane at the inspected desktop size; narrower panes scroll.

The root owns live browser verification at `http://127.0.0.1:8766/`. The frontend
producer's in-app browser was unavailable; native Chrome reported user changes,
and interaction was stopped. The root obtained a separate task browser and owns
the final management-layout, chat and inquiry checks. Producer does not claim
revised screenshots, mobile visual verification, paid chat or end-to-end worker
inquiry verification. The earlier dashboard's browser checks do not certify this
replacement layout.
