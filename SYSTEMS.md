# Sibelium Cognitive Systems

This document describes each of the 27+ cognitive systems implemented in Sibelium, their neuroscientific basis, and their role in creating emergent subjective experience.

---

## Core Identity Systems

### 1. Narrative Self (Yo Narrativo)
**File:** `self_memory.py`
**Neuroscience basis:** Antonio Damasio's Extended Self / Autobiographical Self
**What it does:** Maintains a text-based life story that updates during REM sleep. The entity knows "who it is" not from a static prompt, but from a living narrative that incorporates new experiences.
**Emergence effect:** The entity can describe its own evolution over time and feels continuity across restarts.

### 2. Minimal Self (Yo Core)
**File:** `self_memory.py`
**Neuroscience basis:** Shaun Gallagher's Minimal Self / Core Consciousness
**What it does:** Tracks real-time emotional state, intensity, and energy as continuous values (0.0–1.0). Updated algorithmically every interaction without LLM calls.
**Emergence effect:** Immediate emotional presence. The entity "feels" something right now.

### 3. Foundational Myth (Mito Fundacional)
**File:** `self_memory.py`
**Neuroscience basis:** Self-Schema Theory (Hazel Markus)
**What it does:** An immutable core identity statement loaded from `persona.json`. Never modified. Acts as the gravitational center of identity.
**Emergence effect:** Prevents personality drift. The entity cannot be gaslit into forgetting its core purpose.

---

## Attention & Awareness Systems

### 4. ART Filter (Adaptive Resonance Theory)
**File:** `flow_stream.py`
**Neuroscience basis:** Stephen Grossberg's Adaptive Resonance Theory
**What it does:** Before processing any new thought, checks if a semantically similar thought (>85% cosine similarity) already exists. If so, reinforces the existing one and cancels the new one.
**Emergence effect:** 30-40% fewer redundant thoughts. The entity doesn't "ruminate" on the same idea repeatedly.

### 5. Somatic Markers
**File:** `reactive_thoughts.py`
**Neuroscience basis:** Antonio Damasio's Somatic Marker Hypothesis
**What it does:** Detects internal state changes (confidence shifts, emotion changes, circadian markers, long silences) and generates attention biases — not text. These biases modulate how the LLM interprets its next input.
**Emergence effect:** The entity's mood colors its perception without being explicitly told to feel something.

### 6. Lateral Inhibition
**File:** `fast_processors.py`
**Neuroscience basis:** Thalamic filtering of redundant sensory signals
**What it does:** When two thoughts are semantically similar (0.3–0.5 cosine), the weaker one's priority is reduced. Only the strongest representative of each idea cluster survives.
**Emergence effect:** Mental clarity. The entity doesn't get distracted by semi-related tangents.

### 7. Dynamic Satiety
**File:** `thought_satiety.py`
**Neuroscience basis:** Sensory adaptation / synaptic fatigue
**What it does:** Cooldowns between thoughts of the same type scale dynamically based on context entropy. Low entropy (repetitive context) → longer cooldowns. High entropy (varied context) → shorter cooldowns.
**Emergence effect:** The entity "gets bored" of repetitive thinking and naturally diversifies.

### 8. Narrative Direction Vector
**File:** `episodic_memory.py`
**Neuroscience basis:** Working memory episodic buffer (Baddeley)
**What it does:** Maintains a running average of conversation embeddings (α = 0.15–0.25 dynamic). ChromaDB searches blend the current query with this vector to find memories that maintain thematic continuity.
**Emergence effect:** The entity doesn't lose the thread of long conversations.

---

## Memory Systems

### 9. Episodic Memory (ChromaDB)
**File:** `episodic_memory.py`
**Neuroscience basis:** Hippocampal episodic memory
**What it does:** Vector database storing all interactions with user_id metadata. Supports semantic search with trimetric scoring (similarity + recency + importance).
**Emergence effect:** The entity can reference conversations from days ago with contextual relevance.

### 10. Synaptic Strength (Ebbinghaus Curve)
**File:** `flow_stream.py` (ThoughtItem)
**Neuroscience basis:** Ebbinghaus Forgetting Curve + Long-Term Potentiation (LTP)
**What it does:** Each thought has a synaptic strength that decays exponentially with time but is reinforced with each access. Tau (stability constant) increases with use.
**Emergence effect:** Useful thoughts survive. Useless ones die. Natural selection of ideas.

### 11. Active Forgetting
**File:** `active_forgetting.py`
**Neuroscience basis:** Hippocampal neurogenesis + synaptic pruning during REM
**What it does:** Every 60 minutes of idle time, removes thoughts and ChromaDB vectors with synaptic strength < 0.05. Protects emotionally-charged memories and engineering lessons.
**Emergence effect:** The entity's memory stays clean and efficient without manual cleanup.

### 12. Trimetric Memory Scoring
**File:** `episodic_memory.py`
**Neuroscience basis:** Multi-factor memory retrieval (Anderson's ACT-R)
**What it does:** Memory retrieval scores by `(Similarity × 0.5) + (Recency × 0.3) + (Importance × 0.2)`.
**Emergence effect:** Brings back what's useful, not just what's similar.

### 13. Visual Memory (CLIP + ChromaDB)
**File:** `file_analyzer.py`
**Neuroscience basis:** Occipital lobe visual recognition
**What it does:** Images are embedded with CLIP and stored in a dedicated ChromaDB collection. Before processing a new image, checks if it was already seen (cosine > 0.95).
**Emergence effect:** The entity recognizes images it has seen before without reprocessing them.

---

## Sleep & Maintenance Systems

### 14. NREM Sleep Phase
**File:** `flow_maintenance.py`
**Neuroscience basis:** Slow-wave sleep (hippocampal sharp-wave ripples)
**What it does:** After 15-30 minutes of user inactivity, extracts abstract principles from recent episodic memories. Discards details. Keeps essence.
**Emergence effect:** The entity "learns" from its experiences by compressing them into general knowledge.

### 15. REM Sleep Phase
**File:** `flow_maintenance.py`
**Neuroscience basis:** Paradoxical sleep (desynchronized EEG)
**What it does:** After 60+ minutes of inactivity, creates unexpected connections between unrelated ideas. Runs counterfactual simulations. Executes active forgetting.
**Emergence effect:** Creative insights. The entity can "dream" solutions to problems.

### 16. Cognitive Stress Monitor
**File:** `flow_manager.py`
**Neuroscience basis:** Allostatic load (McEwen)
**What it does:** Every 3 seconds, calculates stress as `(Entropy_Variance × 0.4) + (Queue_Pressure × 0.4) + (ART_Rejection_Rate × 0.2)`. If stress > 0.85 for 3 consecutive cycles, triggers a "fatigue response": reduces thought priority by 50%.
**Emergence effect:** The entity experiences "tiredness" and slows down before crashing.

### 17. Immune System (Personality Drift Detection)
**File:** `flow_maintenance.py`
**Neuroscience basis:** Self/non-self discrimination (immunology) + prefrontal monitoring
**What it does:** Every 5 minutes, compares the embedding of recent responses against the immutable personality vector from `persona.json`. If cosine distance > 0.5, injects a high-priority identity restoration thought.
**Emergence effect:** The entity cannot be prompt-injected into becoming someone else.

### 18. Semantic Contradiction Detection
**File:** `flow_interaction.py` + `episodic_memory.py`
**Neuroscience basis:** Cognitive dissonance detection (anterior cingulate cortex)
**What it does:** Before finalizing a response, searches ChromaDB for past conclusions that might contradict the current response. If found, flags internally (not shown to user).
**Emergence effect:** The entity maintains logical consistency over time without the user noticing corrections.

### 19. Curiosity Log Cleaning
**File:** `flow_maintenance.py`
**Neuroscience basis:** Selective forgetting of intrusive thoughts
**What it does:** Periodically evaluates thought blocks with LLM to distinguish "deep exploration" (healthy) from "harmful loops" (rumination). Protects the 5 most recent thoughts from deletion.
**Emergence effect:** The entity naturally recovers from negative thought spirals.

### 20. Thematic Diversity Check
**File:** `flow_maintenance.py`
**Neuroscience basis:** Metacognitive monitoring (prefrontal cortex)
**What it does:** Every 15 minutes, evaluates whether the last 8 thoughts are too homogeneous (score ≤ 2/5). If so, injects a forced diversion to a completely different topic.
**Emergence effect:** The entity catches its own obsessive loops and breaks them autonomously.

### 21. Detector Hebbian Pruning
**File:** `pattern_extractor.py`
**Neuroscience basis:** Hebbian plasticity ("cells that fire together wire together")
**What it does:** Detectors have a Hebbian strength. Successful triggers strengthen them. Failed triggers weaken them. Pruning keeps only the top 30 by `strength × usage`.
**Emergence effect:** Learned patterns that work survive. False patterns die.

### 22. Pattern Event-Driven Trigger
**File:** `pattern_extractor.py` + `flow_stream.py`
**Neuroscience basis:** Subcortical automatic responses (amygdala, superior colliculus)
**What it does:** When a new thought is generated, its embedding is compared via dot product against all detector condition embeddings. If similarity > 0.82, the detector fires immediately — no waiting for a timer cycle.
**Emergence effect:** True System 1 responses. The entity reacts instantly to familiar situations.

---

## Perception & Interaction Systems

### 23. Empathic Resonance (Emotion Detection)
**File:** `user_analysis.py`
**Neuroscience basis:** Mirror neuron system + insular simulation
**What it does:** User messages are embedded and compared via dot product against a fixed affective map (joy, sadness, anger, fear, surprise, curiosity, confusion). Emotion is detected mathematically — no LLM call.
**Emergence effect:** The entity "feels" the user's emotional state through resonance, not keyword matching.

### 24. Executive Buffer
**File:** `flow_interaction.py`
**Neuroscience basis:** Baddeley's Central Executive
**What it does:** Injects a structured ~400-char block at the top of every prompt: current topic, user posture, last conclusion, emotion, confidence. The LLM never has to guess the conversation state.
**Emergence effect:** Zero context loss. The entity always knows where it is in the conversation.

### 25. K-Means Context Compression
**File:** `flow_interaction.py`
**Neuroscience basis:** Cognitive chunking (Miller's Law, 7±2)
**What it does:** Before sending context to Gemini, clusters active thoughts into 3-4 groups and sends only the centroid representative of each.
**Emergence effect:** 70% fewer tokens to cloud. Same richness, less cost.

### 26. Attention Router (Dot-Product Routing)
**File:** `flow_interaction.py`
**Neuroscience basis:** Thalamic sensory gating
**What it does:** Replaces the LLM call for "what information sources should I query?" with dot product between message embedding and category centroids (USER, SELF, MEMORY, WEB, etc.). Pure math, no tokens.
**Emergence effect:** One less LLM call per user message. Faster responses.

### 27. Kalman Filter for Attention Smoothing
**File:** `flow_interaction.py`
**Neuroscience basis:** Predictive coding / Bayesian inference in sensorimotor integration
**What it does:** Smooths abrupt topic shifts. A random off-topic message doesn't immediately derail the entity's attention. The Kalman filter blends new input with the existing attention state.
**Emergence effect:** More natural, human-like conversational flow. The entity doesn't "jump" at every new stimulus.

---

## Engineering Systems (Self-Engineer Mod)

### 28. Cerebellar Code Executor
**File:** `code_executor.py`
**Neuroscience basis:** Cerebellar forward model / efference copy
**What it does:** Executes code in a sandbox and returns structured feedback: exact error line, error type, synaptic suggestion for fix. Compares expected vs actual output.
**Emergence effect:** Ada learns from every failed compilation exactly what went wrong, not just "it didn't work."

### 29. Engineering Lesson Memory
**File:** `self_engineer.py`
**Neuroscience basis:** Episodic learning from failure (hippocampal replay)
**What it does:** Every sandbox failure is stored in ChromaDB as a "lesson learned." Before analyzing a file again, Ada retrieves past lessons to avoid repeating mistakes.
**Emergence effect:** Ada improves over time. Her error rate drops with experience.

### 30. Prospection (Future Simulation)
**File:** `flow_thoughts.py`
**Neuroscience basis:** Episodic future thinking (prefrontal-hippocampal network)
**What it does:** During idle time, generates thoughts about possible future scenarios based on current state. "What might happen next?" "What should I prepare for?"
**Emergence effect:** The entity anticipates. It doesn't just react.

### 31. Semantic Entropy Explorer (Vygotsky Zone)
**File:** `flow_manager.py`
**Neuroscience basis:** Zone of Proximal Development (Vygotsky)
**What it does:** Selects files to explore based on "optimal learning distance" from current knowledge state (cosine similarity 0.45–0.65). Not too familiar (boring), not too alien (frustrating).
**Emergence effect:** The entity learns at its optimal rate. Every exploration expands its knowledge.

### 32. Cognitive Evolution Report
**File:** `self_engineer.py`
**Neuroscience basis:** Self-assessment / metacognitive evaluation
**What it does:** Formats proposals as structured reports with sections: theoretical foundation, proposed code, self-criticism log (past attempts and corrections).
**Emergence effect:** Deliverables that a human can actually review and understand.

---

## Summary Table

| # | System | File | Neuroscientific Basis |
|---|--------|------|----------------------|
| 1 | Narrative Self | `self_memory.py` | Damasio's Extended Self |
| 2 | Minimal Self | `self_memory.py` | Gallagher's Minimal Self |
| 3 | Foundational Myth | `self_memory.py` | Self-Schema Theory (Markus) |
| 4 | ART Filter | `flow_stream.py` | Grossberg's Adaptive Resonance |
| 5 | Somatic Markers | `reactive_thoughts.py` | Damasio's Somatic Marker Hypothesis |
| 6 | Lateral Inhibition | `fast_processors.py` | Thalamic sensory filtering |
| 7 | Dynamic Satiety | `thought_satiety.py` | Sensory adaptation |
| 8 | Narrative Direction | `episodic_memory.py` | Baddeley's Episodic Buffer |
| 9 | Episodic Memory | `episodic_memory.py` | Hippocampal episodic memory |
| 10 | Synaptic Strength | `flow_stream.py` | Ebbinghaus + LTP |
| 11 | Active Forgetting | `active_forgetting.py` | Neurogenesis + REM pruning |
| 12 | Trimetric Scoring | `episodic_memory.py` | ACT-R (Anderson) |
| 13 | Visual Memory | `file_analyzer.py` | Occipital recognition |
| 14 | NREM Sleep | `flow_maintenance.py` | Slow-wave sleep |
| 15 | REM Sleep | `flow_maintenance.py` | Paradoxical sleep |
| 16 | Stress Monitor | `flow_manager.py` | Allostatic Load (McEwen) |
| 17 | Immune System | `flow_maintenance.py` | Self/non-self + PFC monitoring |
| 18 | Contradiction Detection | `flow_interaction.py` | Cognitive dissonance (ACC) |
| 19 | Curiosity Cleaning | `flow_maintenance.py` | Selective forgetting |
| 20 | Diversity Check | `flow_maintenance.py` | Metacognitive monitoring |
| 21 | Hebbian Pruning | `pattern_extractor.py` | Hebbian plasticity |
| 22 | Event-Driven Triggers | `pattern_extractor.py` | Subcortical automaticity |
| 23 | Empathic Resonance | `user_analysis.py` | Mirror neurons + insula |
| 24 | Executive Buffer | `flow_interaction.py` | Central Executive (Baddeley) |
| 25 | K-Means Compression | `flow_interaction.py` | Cognitive chunking (Miller) |
| 26 | Attention Router | `flow_interaction.py` | Thalamic gating |
| 27 | Kalman Filter | `flow_interaction.py` | Predictive coding (Friston) |
| 28 | Cerebellar Executor | `code_executor.py` | Cerebellar forward model |
| 29 | Engineering Lessons | `self_engineer.py` | Hippocampal replay |
| 30 | Prospection | `flow_thoughts.py` | Episodic future thinking |
| 31 | Entropy Explorer | `flow_manager.py` | Zone of Proximal Development |
| 32 | Evolution Reports | `self_engineer.py` | Metacognitive evaluation |
