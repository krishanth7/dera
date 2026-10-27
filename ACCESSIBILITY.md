# Accessibility Policy

**DERA — Database Engineering & Reverse Analysis**  
*Understand Every Schema. Engineer Every Change.*

---

## 1. Our Commitment

DERA is committed to developing an accessible, inclusive, and dependable database engineering platform that supports a broad range of users, technologies, and interaction methods.

Accessibility is a core consideration throughout our software development lifecycle, including product architecture, interface design, technical documentation, testing, and community collaboration.

Our objective is to reduce barriers for developers, database administrators, engineers, researchers, students, and contributors who interact with DERA through different devices, input methods, and assistive technologies.

We recognize that accessibility is a continuous process requiring practical evaluation, user feedback, and ongoing improvement.

Our principle: Essential functionality and information should remain understandable and operable without dependence on a single sensory ability, input device, or presentation method.

This policy defines DERA's accessibility priorities, contribution requirements, issue-reporting procedures, evaluation approach, and maintenance responsibilities.

---

## 2. Accessibility Objectives

DERA uses the principles of the Web Content Accessibility Guidelines (WCAG) 2.2 Level AA as an aspirational target for applicable web interfaces and documentation.

This target does not represent a verified conformance claim.

Formal conformance will only be stated after a documented evaluation identifying the assessed product scope, evaluation date, methodology, and evaluator.

### 2.1 Keyboard Accessibility

User-facing interfaces should:

- Support keyboard operation for essential functionality.
- Maintain predictable and logical focus navigation.
- Provide clearly visible focus indicators.
- Avoid keyboard traps.
- Support accessible dialog, menu, and form interactions.
- Avoid requiring pointer-only gestures for critical tasks.

### 2.2 Assistive Technology Compatibility

Where applicable, interfaces should:

- Use semantic HTML and appropriate accessibility attributes.
- Provide meaningful accessible names for interactive controls.
- Maintain logical heading and content structures.
- Communicate important status changes and validation errors.
- Present tabular data with understandable headers and relationships.
- Provide equivalent access to essential visual information.

### 2.3 Visual Accessibility

DERA aims to support:

- Readable typography and consistent spacing.
- Sufficient text and interface contrast.
- Information that does not depend on color alone.
- Content resizing and responsive layouts.
- Reduced-motion preferences.
- Clear visual hierarchy and recognizable interaction states.

### 2.4 Cognitive Accessibility

Documentation and interfaces should prioritize:

- Clear and consistent terminology.
- Predictable navigation.
- Concise instructions.
- Actionable error messages.
- Consistent interaction patterns.
- Appropriate feedback during long-running operations.

### 2.5 Accessible Database Engineering

DERA's database engineering capabilities may include schema explorers, metadata tables, dependency diagrams, and entity-relationship visualizations.

These features should be designed to support:

- Keyboard-accessible schema navigation.
- Searchable and structured metadata.
- Text-based alternatives to visual relationships.
- Accessible filtering and selection.
- Understandable status and error feedback.
- Clear descriptions of dependencies and database objects.

Essential database information should not be available exclusively through graphical representations.

---

## 3. Contributor Accessibility Requirements

Accessibility is a shared engineering responsibility.

Contributors introducing or modifying user-facing functionality are expected to consider accessibility throughout implementation and review.

### 3.1 Implementation Requirements

Contributions should:

- Prefer semantic HTML and native interactive controls.
- Associate form controls with accessible labels.
- Maintain visible keyboard focus.
- Support keyboard interaction.
- Use accessibility attributes appropriately.
- Provide meaningful alternative text for informative images.
- Avoid using color as the sole information indicator.
- Respect reduced-motion preferences where relevant.
- Preserve readable layouts at increased zoom levels.
- Provide accessible feedback for loading, success, and error states.
- Ensure important visualizations have appropriate nonvisual alternatives.

### 3.2 Documentation Requirements

Documentation contributions should:

- Use descriptive Markdown headings.
- Maintain a logical heading hierarchy.
- Use meaningful link text.
- Provide context for images, tables, and diagrams.
- Identify code languages in fenced code blocks.
- Keep instructions clear and sequential.
- Avoid unnecessary formatting that reduces readability.
- Preserve language and navigation consistency across translations.

### 3.3 Accessibility Verification

Contributors should perform relevant checks before submitting user-facing changes.

| Verification area | Expected review |
| :--- | :--- |
| **Keyboard navigation** | Essential workflows can be completed without a mouse |
| **Focus visibility** | Interactive elements display a visible focus indicator |
| **Screen reader support** | Relevant labels, headings, controls, and announcements are understandable |
| **Forms and validation** | Inputs and errors are clearly associated |
| **Visual contrast** | Important text and controls remain distinguishable |
| **Responsive layout** | Essential functionality remains available at supported sizes |
| **Content structure** | Headings, lists, tables, and links are meaningful |
| **Visual alternatives** | Diagrams and visualizations provide equivalent information where required |
| **Motion** | Essential tasks do not depend on animation |

Automated accessibility checks may supplement manual testing but do not replace it.

Only tools and CI checks actually configured in the repository should be represented as operational requirements.

### 3.4 Pull Request Expectations

Pull requests affecting user-facing functionality should include an accessibility review summary.

A suggested format is:

```markdown
### Accessibility Review
- [ ] Keyboard navigation reviewed
- [ ] Focus visibility reviewed
- [ ] Accessible labels and names reviewed
- [ ] Form validation and error feedback reviewed
- [ ] Responsive layout reviewed
- [ ] Visual alternatives reviewed where applicable
- [ ] Relevant assistive technology testing completed or limitations documented

**Testing performed:** Describe the environments and checks used.
**Known limitations:** List unresolved barriers or state that none were identified within the tested scope.
```

Not every check applies to every contribution. Contributors should document exclusions where appropriate.

---

## 4. Reporting Accessibility Issues

Accessibility barriers, usability concerns, and requests for accessible alternatives can be reported through DERA's public issue tracker.

- **Issue tracker:** [https://github.com/krishanth7/dera/issues](https://github.com/krishanth7/dera/issues)
- **Submit an issue:** [https://github.com/krishanth7/dera/issues/new](https://github.com/krishanth7/dera/issues/new)

Use the title format:
`[Accessibility] Short description of the issue`

If an accessibility-specific issue template is available, use it. Otherwise, a standard GitHub issue is acceptable.

### 4.1 Recommended Report Details

Reports may include:

| Field | Description |
| :--- | :--- |
| **Affected component** | Page, workflow, feature, or documentation section |
| **Affected URL** | Link to the relevant resource |
| **Intended task** | What the user was attempting to accomplish |
| **Observed behavior** | What happened and how it created a barrier |
| **Expected behavior** | What would make the task accessible |
| **Environment** | Browser, operating system, and device, if relevant |
| **Assistive technology** | Screen reader, keyboard navigation, or other technology, if relevant |
| **Reproduction steps** | Steps that help maintainers understand the issue |
| **Suggested improvement** | Optional proposed solution or workaround |

**Privacy:** Reporters are not required to disclose a disability, diagnosis, or personal medical information.

Screenshots and recordings are optional.

Do not include credentials, private database information, access tokens, or other sensitive data in public reports.

Security-sensitive issues should follow the repository's security reporting policy.

---

## 5. Severity Classification

Accessibility issues are evaluated according to their impact on essential user tasks.

| Severity | Classification | Impact | Example |
| :--- | :--- | :--- | :--- |
| **S1** | Critical | Essential functionality is inaccessible without a reasonable workaround | A keyboard-only user cannot complete a primary application workflow |
| **S2** | High | A major workflow is inaccessible or substantially impaired | A screen reader user cannot configure a database connection |
| **S3** | Medium | A significant barrier exists, but an alternative workflow may be available | A dependency diagram lacks an equivalent structured relationship view |
| **S4** | Low | A limited barrier or inconsistency affects usability without blocking the main task | A secondary control has an unclear accessible label |

Severity is determined during maintainer triage. Reporters do not need to assign a severity level.

These classifications do not establish guaranteed resolution deadlines.

---

## 6. Issue Management and Response

DERA aims to manage accessibility reports through a transparent, evidence-based process.

### 6.1 Review and Triage

Reported issues are assessed for:

- User impact.
- Affected functionality.
- Reproducibility.
- Availability of workarounds.
- Technical dependencies.
- Implementation complexity.

### 6.2 Resolution Process

The intended workflow is:

```text
Issue Submitted -> Initial Review -> Impact Assessment -> Reproduction and Investigation -> Fix or Accessible Alternative -> Accessibility Verification -> Review and Resolution
```

### 6.3 Communication

Maintainers aim to:

- Acknowledge actionable reports when capacity permits.
- Request clarification when necessary.
- Explain available workarounds.
- Track significant implementation progress.
- Document unresolved limitations.
- Invite reporter feedback during verification where appropriate.

Response and resolution times depend on project resources, severity, and technical complexity. DERA does not currently guarantee fixed response or remediation deadlines.

---

## 7. Accessibility Governance

Accessibility is maintained as part of DERA's engineering quality and community governance.

### 7.1 Responsibilities

Project maintainers are responsible for:

- Maintaining accessibility guidance.
- Reviewing reported barriers.
- Prioritizing significant accessibility defects.
- Considering accessibility during architecture and feature reviews.
- Encouraging appropriate testing.
- Maintaining relevant documentation.
- Coordinating improvements across affected components.

### 7.2 Review and Maintenance

This policy should be reviewed:

- During major releases.
- Following significant interface changes.
- When accessibility evaluation identifies new requirements.
- When reporting or contribution procedures change.
- When project governance responsibilities change.

Changes should be submitted through the standard repository review process.

### 7.3 Ownership Continuity

Accessibility responsibilities remain with the project's active maintainers.

When responsibilities are reassigned, relevant governance documentation should be updated to reflect the current process.

---

## 8. Supported Environments

DERA's accessibility objectives apply to its documentation, command-line workflows, and applicable graphical interfaces.

Actual compatibility depends on implementation status and testing evidence.

### 8.1 Web Interfaces

Intended environments include modern desktop and mobile browsers, including:

- Google Chrome and other Chromium-based browsers.
- Mozilla Firefox.
- Apple Safari.
- Microsoft Edge.

Specific browser versions and combinations will be documented when tested.

### 8.2 Input Methods

Relevant interaction methods include:

- Keyboard.
- Mouse.
- Touch.
- Assistive input technologies.

Support for individual interaction methods must be verified against implemented features.

### 8.3 Assistive Technologies

Relevant testing environments may include:

- NVDA.
- JAWS.
- VoiceOver.
- TalkBack.
- Screen magnification tools.
- Keyboard-only navigation.

Listing these technologies does not imply that every combination has been evaluated or certified.

### 8.4 Command-Line Interfaces

Where applicable, command-line tools should provide:

- Readable text output.
- Meaningful errors.
- Documented command options.
- Non-color-dependent status information.
- Predictable exit behavior.
- Accessible alternatives to interactive-only workflows.

---

## 9. Known Limitations

DERA is under active development. A comprehensive accessibility evaluation has not yet been documented for all planned interfaces and workflows.

The following areas require continued attention:

### 9.1 Schema and Dependency Visualizations

Complex visual diagrams may be difficult to navigate without a mouse or visual interpretation. The intended approach is to provide structured, searchable metadata and text-based relationship information.

### 9.2 Interactive Engineering Interfaces

Advanced tables, filters, dialogs, and engineering workspaces require verification of keyboard navigation, focus management, and assistive technology announcements. Support should not be assumed before evaluation.

### 9.3 Documentation and Technical Diagrams

Some diagrams and technical explanations may require improved text alternatives. Users can request equivalent written explanations through the accessibility issue-reporting process.

### 9.4 Cross-Platform Compatibility

Comprehensive testing across all browsers, operating systems, devices, and assistive technologies has not yet been completed or documented. Compatibility claims will be updated as evidence becomes available.

### 9.5 Limitation Tracking

Confirmed accessibility barriers should be documented in GitHub issues with their affected scope, available workaround, and resolution status.

Tracked issues: [https://github.com/krishanth7/dera/issues](https://github.com/krishanth7/dera/issues)

This section will be updated as limitations are verified and resolved.

---

## 10. Continuous Improvement

DERA encourages accessibility improvements through:

- Community feedback.
- Code reviews.
- Documentation contributions.
- Manual accessibility testing.
- Automated checks where configured.
- Regression testing.
- Usability evaluation.
- Accessible design practices.

Accessibility improvements should be incorporated into normal engineering workflows rather than treated exclusively as separate corrective work.

---

## 11. Feedback and Policy Updates

Suggestions for improving this policy, accessibility practices, or the user experience are welcome.

Contributors may:

- Open a GitHub issue describing the proposed improvement.
- Submit a pull request with a focused documentation or implementation change.
- Participate in relevant project discussions when available.

For active accessibility barriers, use the reporting process in Section 4.

- **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)
- **Issues:** [https://github.com/krishanth7/dera/issues](https://github.com/krishanth7/dera/issues)
- **Contributing:** [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Security:** [SECURITY.md](./SECURITY.md)

---

### Policy Statement

DERA recognizes accessibility as an essential dimension of software quality, reliability, and inclusive engineering.

We are committed to progressively reducing barriers, evaluating user-facing functionality, and supporting meaningful participation across the open-source community.

*DERA — Understand Every Schema. Engineer Every Change.*
