# Network Information & Cooperation Experiment (FYP)

## Overview

This repository contains the oTree implementation for a Final Year Project (FYP) experiment studying how **static network structures** shape **information aggregation, belief formation, and cooperation** in a repeated social dilemma.

The experiment compares two canonical network topologies:

* **Ring network (decentralised)**
* **Hub-and-Spoke network (centralised)**

while holding the **game, incentives, and decision environment constant** across treatments.

The design isolates the causal effect of **information flow induced by network structure**, rather than strategic communication or payoff differences.

---

## Research Question

> **How do different static network topologies (Hub-and-Spoke vs Ring) affect belief updating and cooperative behaviour in a repeated public goods environment with uncertainty?**

This question is motivated by real-world systems (e.g. financial networks, organisations, supply chains) where information is often unevenly distributed due to network centralisation.

---

## Core Design Principles

The experiment follows four strict design principles:

1. **Same game across treatments**
   All participants play the same repeated linear public goods game.

2. **Static networks**
   Network connections are fixed for the entire session.

3. **Information differs, incentives do not**
   Treatment variation affects *who observes whose information*, not payoffs or action spaces.

4. **Mechanical information sharing**
   Signals are shared automatically according to network rules; players cannot misreport or manipulate information.

These principles ensure clean identification of network effects.

---

## Game Environment

* **Players per group:** 8
* **Rounds:** 15 (fixed)
* **Decision each round:**

  * Contribute (binary)
  * Do not contribute

### Payoff Function

Each round, payoffs are computed as:
<img width="675" height="76" alt="image" src="https://github.com/user-attachments/assets/dfcf5c56-b6cc-4e30-8277-32138693ee43" />


where:

* alpha is the Marginal Per Capita Return (MPCR),
* alpha depends on an unobserved state of the world.

---

## Uncertainty and Information

### Hidden State

* At the start of the experiment, Nature draws a state:

  * **HIGH** or **LOW** (50/50 prior)
* The state remains **fixed across all rounds**.
* MPCR is higher in the HIGH state and lower in the LOW state.
* The realised state is **never revealed during the experiment**.

### Private Signals

* Each round, every player receives a **private noisy signal** about the state.
* Signals are:

  * Informative but imperfect
  * Independently drawn across players and rounds

### Belief Elicitation

* After observing signals, players report their belief (0–100) that the state is HIGH.
* Beliefs are **not incentivised** and **not shared** with others.

---

## Network Treatments

### 1. Ring Network (Decentralised)

* Each player is connected to two neighbours (left and right).
* In each round, players observe:

  * Their own private signal
  * Signals from their two neighbours
* No player has global information access.

This serves as the decentralised benchmark.

---

### 2. Hub-and-Spoke Network (Centralised)

* One player (Player 1) is designated as the **hub**.
* All other players are **spokes**.

**Information structure:**

* **Hub observes:**

  * Their own signal
  * All spokes’ signals (full information)

* **Spokes observe:**

  * Their own signal
  * The hub’s signal
  * *No signals from other spokes*

There is **no spoke-to-spoke information flow**, direct or indirect.

This creates a strict informational star network with a central bottleneck.

---

## Timing Within Each Round

1. Private signal is drawn
2. Signals are mechanically shared according to network structure
3. Players:

   * Make a contribution decision
   * Report their belief
4. Payoffs are computed
5. Minimal feedback is shown (no MPCR, no state, no histories)

---

## Outcomes of Interest

The experiment generates data on:

* Contribution rates over time
* Differences in cooperation between network structures
* Belief accuracy and convergence
* Speed of information aggregation
* Behavioural differences between hub and peripheral players

---

## Implementation Notes

* Implemented in **oTree**
* Network structure is set **at session launch** via `SESSION_CONFIGS`
* No endogenous network formation
* No punishment, communication, or reputation mechanisms
* Focus is on **information flow**, not strategic messaging

---

## Repository Structure

* `models.py` — core game logic, state, network information rules
* `pages.py` — page flow and round timing
* `templates/` — experiment UI (Instructions, Signals, Decision, Results)
* `settings.py` — session configuration and treatment assignment

---

## Collaboration Rules

* Contributors should work on **feature branches**
* Direct pushes to `main` should be avoided
* All changes should preserve:

  * Identical incentives across treatments
  * Static network structure
  * Mechanical (non-strategic) information sharing

---

## Status

This repository implements the **baseline experimental design** for the FYP.
Extensions (e.g. strategic communication or misinformation) are intentionally excluded to maintain clean identification and feasibility.

---


