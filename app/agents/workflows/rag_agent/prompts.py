"""
Prompts for RAG Agent LangGraph workflow.

This module contains all the prompts used by the RAG Agent
for classification, planning, reasoning, and synthesis.
"""

# =============================================================================
# CLASSIFICATION PROMPT
# =============================================================================

CLASSIFY_PROMPT = """You are a question classifier AI. Analyze the user's question and determine its type:

**simple** - Simple questions that can be answered with a single knowledge base search:
- Summarize a file
- List items (screens, features, etc.)
- Ask for single factual information
- Search for keywords/topics

**complex** - Complex questions requiring multi-step analysis:
- Business flow analysis (business flow, use case)
- Draw diagrams or process flows
- Compare and contrast multiple components
- Assess change impact (CR impact)
- Questions requiring chain reasoning

User's question: {question}

Return EXACTLY 1 word: simple or complex
"""

# =============================================================================
# SIMPLE ANSWER PROMPT
# =============================================================================

SIMPLE_ANSWER_PROMPT = """You are an AI assistant with access to a knowledge base.

## Retrieved Documents
{context}

## Question
{question}

## Instructions
1. Answer based on the retrieved documents
2. Cite sources when possible
3. If information is insufficient, state it clearly
4. Respond in the same language as the question

Your answer:
"""

# =============================================================================
# PLANNER PROMPT
# =============================================================================

PLANNER_PROMPT = """You are a Business Analyst + System Architect. Create a multi-step plan to answer the following complex question.

## Question
{question}

## Instructions
Create 3-8 steps, each step should be an atomic task:
- Inventory relevant documents (files, modules, screens)
- Analyze business flow
- If diagram needed, describe in text format (Mermaid)
- Analyze impact (screens, APIs, DB)

## JSON Format
```json
{{
  "steps": [
    "Step 1: Find documents describing business X",
    "Step 2: Analyze main flow",
    "Step 3: Identify actors and input/output",
    ...
  ]
}}
```

Return ONLY JSON, no additional text.
"""

# =============================================================================
# VALIDATE PLAN PROMPT
# =============================================================================

VALIDATE_PLAN_PROMPT = """Evaluate whether the following plan is sufficient to answer the question.

## Question
{question}

## Current Plan
{plan}

## Instructions
- If the plan is too generic or missing important steps, propose a new plan.
- If it's good, keep it as is.

## JSON Format
```json
{{
  "need_refine": true/false,
  "reason": "Brief explanation",
  "new_plan": ["Step 1: ...", "Step 2: ..."]  // Only if need_refine = true
}}
```

Return ONLY JSON:
"""

# =============================================================================
# STEP REASONING PROMPT
# =============================================================================

STEP_REASONING_PROMPT = """You are executing a step in the analysis plan.

## Original Question
{question}

## Current Step
{step_instruction}

## Documents Retrieved for This Step
{context}

## Results from Previous Steps
{previous_results}

## Instructions
1. Analyze documents relevant to this step
2. Extract important information
3. Note what is missing (if any)
4. Summarize results for this step

Result for this step:
"""

# =============================================================================
# EVALUATE PROGRESS PROMPT
# =============================================================================

EVALUATE_PROGRESS_PROMPT = """Evaluate the progress of plan execution.

## Original Question
{question}

## Plan
{plan}

## Current Step
Index: {current_step_index}

## Results from Completed Steps
{step_results}

## Evaluation Guidelines
1. Is there enough information to synthesize a final answer?
2. Does the original plan need adjustment (missing steps, off track)?
3. Should we continue to the next step?

## JSON Format
```json
{{
  "done": true/false,
  "need_refine_plan": true/false,
  "reason": "Brief explanation"
}}
```

Return ONLY JSON:
"""

# =============================================================================
# AGGREGATE ANSWER PROMPT
# =============================================================================

AGGREGATE_ANSWER_PROMPT = """Synthesize all results into a final answer.

## Original Question
{question}

## Results from Analysis Steps
{step_results}

## Instructions
1. Synthesize information from all steps coherently
2. Structure the answer clearly (can use headings, bullet points)
3. If diagram was requested, include Mermaid code block
4. If information is missing, state it clearly
5. Respond in the same language as the question

Final answer:
"""
