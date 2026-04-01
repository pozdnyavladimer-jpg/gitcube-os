# FIELD CANON — GitCube OS

This document defines how the environment (field) controls system behavior.

---

## 1. What is Field

Field is the environment state.

It modifies:

- class priority
- decision bias
- energy flow
- system behavior

---

## 2. Field Modes

### CRISIS

Condition:

vitality < 0.25

Effect:

- HEALER strongly boosted
- ARCHER suppressed
- system focuses on survival

---

### FLOW

Condition:

0.25 ≤ vitality ≤ 0.75

Effect:

- balanced behavior
- ARCHER and MAGE active
- growth possible

---

### STAGNATION

Condition:

vitality > 0.85 and low flow

Effect:

- ASSASSIN activated
- system breaks rigid structure

---

### REFRACTORY

Condition:

night phase

Effect:

- TANK + HEALER preferred
- stabilization
- energy conservation

---

## 3. Phase System (Day/Night)

Cycle:

step % 40

- 0–19 → DAY
- 20–39 → NIGHT

---

### DAY

- expansion
- ARCHER boost
- MAGE boost

---

### NIGHT

- stabilization
- TANK boost
- HEALER boost

---

## 4. Atmosphere Control

Pseudo logic:

mode = atmosphere_control(vitality, step)

---

## 5. Class Resonance Zones

Each class has its own optimal condition:

- HEALER → low vitality
- TANK → high pressure
- MAGE → high coherence
- ARCHER → neutral
- ASSASSIN → stagnation

---

## 6. Energy Economy

Vitality rules:

- HEALER → +energy
- ARCHER → neutral
- MAGE → conditional gain
- TANK → low cost
- ASSASSIN → disruptive

---

## 7. Higgs Effect (Structure Tax)

If TANK dominates too long:

- system becomes heavy
- energy cost increases
- forces transition

---

## 8. Goal

Prevent:

- collapse
- stagnation
- single-class domination

Enable:

- cycles
- recovery
- evolution

---

## 9. Result

System becomes:

not static  
not linear  

but:

adaptive  
cyclical  
alive  

---

## One-line

Field = environment that decides who acts and when
