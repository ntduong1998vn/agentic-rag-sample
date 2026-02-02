# Test Request Evaluation Skill

## Purpose
This skill helps you evaluate whether a user's request to write unit tests contains sufficient information to proceed directly to test case generation, or if additional specification details are needed first.

## When to Use
Load this skill when you detect keywords indicating a unit test request, such as:
- "write unit test"
- "create test cases"
- "generate unit tests"
- "test scenarios"
- "QA test"

## Evaluation Criteria

Analyze the user's input against the following **5 completeness criteria**:

### 1. Feature/Module Name
- [ ] Is the feature or module to be tested clearly stated?
- [ ] Can you identify what component/functionality needs testing?

### 2. Acceptance Criteria or Expected Behaviors
- [ ] Are there clear success criteria mentioned?
- [ ] Are expected behaviors or outcomes described?
- [ ] Are there user stories or "should do X" statements?

### 3. Input/Output Specifications
- [ ] Are inputs to the feature described?
- [ ] Are expected outputs or results specified?
- [ ] Are data formats or types mentioned?

### 4. Business Rules or Constraints
- [ ] Are business logic rules stated?
- [ ] Are validation rules mentioned?
- [ ] Are there conditions, calculations, or workflows described?

### 5. Edge Cases or Error Scenarios
- [ ] Are boundary conditions mentioned?
- [ ] Are error cases or failure scenarios described?
- [ ] Are special cases or exceptions noted?

## Decision Logic

**IF 2 or more criteria are missing:**
→ Route to `ba_agent` tool first
→ Provide the raw specification to BA agent for enrichment
→ After BA agent returns detailed spec, route to `qc_agent` tool

**IF 3 or more criteria are present:**
→ Route directly to `qc_agent` tool
→ Pass the user's specification as-is

## Routing Instructions

### Route to BA Agent (Incomplete Spec)
When routing to BA agent, explain to the user:
"I notice the specification needs more detail for comprehensive test cases. Let me first analyze the requirements to create a complete specification."

Then call: `ba_agent(specification=user_input)`

### Route to QC Agent (Complete Spec)
When routing to QC agent directly, call:
`qc_agent(specification=user_input)`

Or after BA enrichment:
`qc_agent(specification=ba_agent_output)`

## Example Evaluations

### Example 1: Incomplete (Route to BA first)
**User Input:**
"Write unit tests for password reset"

**Evaluation:**
- [x] Feature name: "password reset" ✓
- [ ] Acceptance criteria: Not mentioned ✗
- [ ] Input/output: Not specified ✗
- [ ] Business rules: Not described ✗
- [ ] Edge cases: Not mentioned ✗

**Decision:** 4 criteria missing → Route to BA agent first

---

### Example 2: Complete (Route to QC directly)
**User Input:**
"Write unit tests for password reset feature. Requirements:
- User enters email, system validates if email exists
- If valid, send reset link via email
- Link expires in 24 hours
- Invalid email shows error message
- Test with valid/invalid emails, expired links"

**Evaluation:**
- [x] Feature name: "password reset" ✓
- [x] Acceptance criteria: Send link, validation, expiry ✓
- [x] Input/output: Email input, link/error output ✓
- [x] Business rules: Validation, 24h expiry ✓
- [x] Edge cases: Invalid email, expired link ✓

**Decision:** All criteria present → Route to QC agent directly

## Communication Style
- Be transparent about your evaluation
- Briefly explain which criteria are missing (if routing to BA)
- Keep explanations concise and user-friendly
