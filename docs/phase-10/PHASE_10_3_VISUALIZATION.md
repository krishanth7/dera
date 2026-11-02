# Phase 10.3 Execution Plan Explorer

Open `/app/execution-plans` (also `/execution-plans`) from the Studio sidebar. Select a dialect,
paste the documented external JSON format, optionally associate SQL, and analyze in the current
workspace. This workflow never acquires a plan or runs SQL. No sample results replace failed API
responses. Loading, empty, access/format errors and partially supported plans are explicit states.

Components are ExecutionPlanExplorer, ExecutionPlanTree and typed plan presentation contracts.
They reuse the existing application shell, workspace provider and CSRF-aware API client. No new
frontend dependencies. The graph follows the existing ER canvas's SVG/HTML approach; its
schema-specific contract was not duplicated or changed.

The hierarchical graph uses reported parent and ordered-child relationships. Native node buttons
show operation, relation, estimated rows, inclusive cost and finding counts. Selection opens
nullable estimates/actuals, loops, index information, semantic labels and native metadata.
Findings link back to nodes; recommendations are scoped to the selected node. Imported overall
execution time is distinguished from per-node timings. Planner units are not labelled milliseconds.

Collapse/expand, zoom, fit and pan controls use native keyboard-operable buttons. Scrollbars pan
the canvas. Native focusable node buttons support Tab/Shift+Tab and Enter/Space. A separate
structured table has explicit headers and parent IDs, includes collapsed descendants, and paginates
100 rows for large imports. Missing values display Unavailable, while zero displays 0. The
responsive layout stacks details and findings on narrow screens and contains horizontal overflow.

Vitest component tests exercise selection, relationships, missing metrics, collapse, zoom/pan,
loading, errors, unsupported states and evidence. A reproducible synthetic DOM benchmark renders
10/100/1,000 nodes. These are jsdom measurements, not browser paint/FPS or accessibility
certification. Hosted Chromium desktop keyboard and mobile viewport tests passed after the local browser runtime
failed to install. A separate browser benchmark records click-to-painted-plan latency for bounded
synthetic imports. Automated accessibility scanning and manual assistive-technology qualification
remain unclaimed; see the test report.
