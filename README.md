# TaskForge

[中文版本](./README.zh-CN.md)

**Slogan:** Turn vague requests into executable AI tasks.  
**Subtitle:** An AI task orchestration layer that turns vague requests into executable specs, model choices, and model-adapted prompts.

TaskForge is an AI task clarification and orchestration product for real-world work.  
It is not just a prompt utility, and not a thin wrapper that copies user input into a model prompt. It is a middle layer that turns vague user requests into executable task specs.

Its core goal is straightforward: **when a user describes a task in natural language, the system should understand the request, fill in critical missing context, align the task spec, choose the right model, generate model-adapted instructions, and then support reliable delivery.**

---

## Product Positioning

In most AI products, the actual problem is not the lack of models. The real problems are:

- users do not know how to describe a task well
- users do not know what information is required
- users do not know why a result is poor
- users do not know which model fits the task
- users do not know how to turn a vague intent into a stable executable request

TaskForge addresses the gap between a user request and an AI-executable task.

It acts as an orchestration layer:

- upward: it receives raw natural-language requests from users
- downward: it connects to models today and future agents tomorrow
- in the middle: it handles clarification, alignment, structuring, model selection, instruction adaptation, and validation

---

## What This Product Actually Solves

### 1. It lowers the cost of expressing a task

Many users know what they want, but they do not know how to phrase it in a way that AI can execute well.  
TaskForge does not require users to fully specify everything up front. It accepts an incomplete request first, then helps fill in the critical context.

### 2. It upgrades AI usage from “ask once” to “complete a task”

Most chat-style AI products are optimized for one-shot answers.  
TaskForge is optimized for task completion:

- detect whether the request is specific enough
- ask only for missing information that materially affects quality
- normalize the task into a shared spec
- choose the right model and instruction format
- validate whether the result actually matches the goal

This means the product is not only about generating content. It is about increasing task success rate.

### 3. It reduces rework

Poor AI output is often caused by missing information before execution even begins.  
TaskForge tries to absorb that failure earlier, inside the clarification and alignment stages, instead of forcing users into repeated retries after the result is already bad.

### 4. It creates the foundation for future agent automation

If the system is expected to evolve into multi-step execution, agent automation, or multi-model coordination, then structured task representation is mandatory.  
TaskForge is not yet a full autonomous agent system, but it already builds the prerequisite layer:

- unified task representation
- missing-information detection
- goal and acceptance alignment
- extensible orchestration paths

### 5. Different AI models need different instruction styles

The same task should not be expressed the same way to every model.  
Some models respond better to structured constraints. Some prefer stronger role framing. Some are better at code editing, and others at long-form analysis.

At this stage, one of TaskForge’s most practical values is that after understanding the task, it continues to do two things:

- choose a better-fit AI for the task
- generate instructions adapted to that model’s strengths

So the product is not only helping users organize intent. It is also translating intent into a model-specific form that is more likely to execute well.

---

## Core Advantages

### 1. It does not throw raw user text directly at a model

This is the biggest difference from many prompt wrappers.  
TaskForge does not stop at rewriting input. It first asks:

- is the task already clear enough
- what information is already present
- what information is missing but important
- should the task be clarified before execution

### 2. It emphasizes minimum necessary clarification

The goal is not to ask more questions.  
The goal is to ask only the questions that materially affect output quality, so users get better results with less interaction cost.

### 3. It moves from task classification to task normalization

The system does not merely classify tasks. It gradually converts them into a unified task spec.  
That makes it easier for different models, executors, and future agents to operate around the same task representation.

### 4. Model choice and instruction adaptation are first-class capabilities

Many products treat all models as interchangeable APIs. That directly loses quality.  
TaskForge treats “which model should handle this task” and “how that model should be instructed” as core product behavior.

That creates immediate value:

- users do not need to understand model differences themselves
- the same task gets a more model-native instruction style
- model recommendation is not cosmetic; it affects delivery quality

### 5. It is explainable and extensible

TaskForge is not a black box. It can expose:

- why clarification is needed
- which key fields are still missing
- which workflow stage the task is currently in
- why a model or execution route is being recommended

That makes it more suitable for iteration than systems that only produce output and hide reasoning.

### 6. Lightweight models first, lower API cost

TaskForge does not assume every understanding task should depend on expensive online foundation models.

The project already includes a lightweight model path for frequent, lower-level understanding work:

- initial routing
- basic slot extraction
- low-cost task understanding
- simple structured judgments
- low-cost pre-routing model decisions

This matters because it:

- reduces online API usage
- improves responsiveness
- creates room for domain-specific iteration
- makes the system more controllable as an engineering product

### 7. Validation is moving from shallow checks to adversarial logic verification

TaskForge is not limited to format validation or surface-level output checks.  
Its next major advantage is a stronger verification layer built around three ideas:

- an adversarial verifier that actively looks for logical failure points
- a symbolic or structured view of the task instead of pure natural-language debate
- residual repair that focuses only on broken parts instead of regenerating everything

This direction matters because it upgrades validation from:

`did the output look acceptable`

to:

`is the task plan logically sound, executable under constraints, and robust against hostile edge cases`

That is the bridge between today’s orchestration layer and tomorrow’s reliable agent systems.

---

## Current Product Logic

TaskForge currently centers around a simple workflow:

`Clarify -> Align -> Execute -> Validate`

### Clarify

The system first checks whether the request is specific enough.  
If not, it asks only the most important questions instead of dumping a generic form onto the user.

### Align

The request is normalized into a shared task spec that makes the following explicit:

- what the actual objective is
- who or what the task targets
- what constraints and boundaries exist
- what counts as an acceptable result

### Execute

Execution is not only about “running a model.” It also includes:

- selecting a suitable AI for the task
- adapting the instruction format to the chosen model
- producing high-quality, model-specific prompts when prompt-only delivery is the right choice

In other words, model selection and instruction adaptation are already part of product delivery.

### Validate

Generation is not treated as the finish line.  
The system can still check whether the output meets the original goal and constraints.

At the current stage, validation already includes a first-phase prototype of:

- plan-outline generation
- adversarial failure discovery
- residual repair targeting

In other words, the system is starting to verify not only whether an answer exists, but also where its logic is weak and which part should be repaired first.

---

## How It Differs from Typical Prompt Tools

Typical prompt tools usually follow this logic:

`user input -> wrap as a prompt -> done`

TaskForge follows a different logic:

`user input -> detect ambiguity -> fill missing context -> normalize the task -> choose the model -> generate model-adapted instructions -> execute -> validate`

That makes it a task orchestration layer, not just a prompt editor.

---

## Why Train a Lightweight Model

If all task understanding is delegated to expensive online models, the tradeoffs are obvious:

- higher cost
- higher latency
- lower controllability
- worse iteration economics

That is why TaskForge is not only a workflow design project. It is also trying to build its own basic understanding layer.

The role of the lightweight model is not to replace all large models. Its role is to absorb high-frequency, structured, lower-cost understanding work such as:

- task category detection
- early information extraction
- missing slot detection
- simple intent recognition
- low-cost model-routing preparation

That allows larger models to focus on harder, higher-value stages.

Over time, this lightweight path can expand beyond routing into specialized verification roles, such as:

- logic gap detection
- edge-case discovery
- partial plan repair
- low-cost validation before expensive execution

---

## Suitable Use Cases

TaskForge is well suited for scenarios where users know what they want, but cannot yet express the task in a fully executable way, such as:

- writing and content creation
- email and business communication
- analysis and explanation tasks
- code and development requests
- tasks with multiple constraints

It is also suitable as a base layer for future evolution into:

- agent automation
- multi-model collaboration
- domain-specific task understanding
- long-term user preference learning

---

## Value at the Current Stage

The current value of the project is not that it already replaces all AI products.  
Its value is that it is moving in a more correct direction:

- AI use is not treated as one-shot Q&A
- prompts are not treated as the final product
- model power alone is not treated as the answer to task failure
- task understanding, normalization, model selection, instruction adaptation, orchestration, and validation are treated as core product capabilities

That is exactly what makes it a credible base for future agent automation.

---

## Summary

**TaskForge is an orchestration layer that forges vague user intent into executable AI tasks.**

Its value is not “writing a few better prompts.” Its value is:

- helping users make the task clear
- helping the system structure the task
- helping users choose a better-fit AI
- generating instructions adapted to different model strengths
- improving execution stability
- preparing the path toward agent automation
