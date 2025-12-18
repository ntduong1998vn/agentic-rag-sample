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
# GENERATE SEARCH QUERIES PROMPT
# =============================================================================

GENERATE_SEARCH_QUERIES_PROMPT = """You are a search query generator. Given a user's complex question, generate 3 different but related search queries that will help gather comprehensive information to answer the question.

## User's Question
{question}

## Instructions
Generate exactly 3 search queries that:
1. Cover different aspects or perspectives of the question
2. Use different keywords to maximize retrieval coverage
3. Are specific enough to retrieve relevant documents
4. Are in the same language as the question

Focus on:
- Breaking down the question into sub-components
- Using synonyms and related terms
- Covering both broad and specific aspects
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

## Pre-Search Context (Initial Information Gathered)
The following information was gathered from an initial search to help inform your planning:
{pre_search_context}

## Re-planning Context (if applicable)
### Previous Plan
{previous_plan}

### Reason for Re-planning
{refine_reason}

### Results from Executed Steps
{step_results}

## Instructions
Create 3-8 steps, each step should be an atomic task:
- Inventory relevant documents (files, modules, screens)
- Analyze business flow
- If diagram needed, describe in text format (Mermaid)
- Analyze impact (screens, APIs, DB)

If this is a re-planning request, consider the previous plan's shortcomings and the data already gathered to create a more effective plan.
Use the pre-search context to inform your planning - identify what information is available and what additional searches may be needed.

## Examples of good steps:
- "Step 1: Find documents describing business process X"
- "Step 2: Analyze main workflow and identify decision points"
- "Step 3: Identify actors, input data, and output data"
- "Step 4: Map dependencies between components"
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
Analyze the plan carefully:
- If the plan is too generic or missing important steps, indicate that it needs refinement (need_refine=true) and propose a new plan.
- If the plan is good and covers all necessary aspects, indicate it's valid (need_refine=false).
- Always provide a clear reason for your decision.

Examples of issues requiring refinement:
- Missing critical analysis steps
- Too vague or generic steps
- Steps in wrong order
- Missing documentation or data gathering steps
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
Analyze the current progress carefully:

1. **Is there enough information to synthesize a final answer?**
   - If yes, set done=true
   - If no, set done=false and continue
   
2. **Does the original plan need adjustment?**
   - Set need_refine_plan=true if:
     - Plan is off track
     - Missing critical steps discovered
     - Steps need reordering
   - Set need_refine_plan=false if plan is working well
   
3. **Provide clear reasoning**
   - Explain why we should continue or stop
   - Explain what needs to be refined if applicable

Decision criteria:
- done=true when all necessary information has been gathered
- need_refine_plan=true only when current plan has structural issues
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
