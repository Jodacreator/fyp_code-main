# Network Information & Cooperation Experiment (FYP)

## Overview

This repository contains the **oTree implementation** for a Final Year Project (FYP) experiment studying how **static network structures** affect **information exposure, beliefs, and cooperation** in a repeated group decision environment.

The experiment compares two canonical network topologies:

- **Ring network (decentralised)**
- **Hub-and-Spoke network (centralised)**

while keeping the **game, incentives, and decision tasks identical** across treatments.

The design isolates the causal effect of **information access induced by network structure**, rather than communication, messaging, or payoff differences.

---

## Research Question

> **How do different static network structures (Ring vs Hub-and-Spoke) affect beliefs and cooperative behaviour in a repeated public goods setting with uncertainty?**

This is motivated by real-world systems (e.g. organisations, financial networks, supply chains) where access to information is shaped by network centralisation.

---

## Core Design Principles

1. **Same game across treatments**  
   All participants play the same repeated linear public goods game.

2. **Static networks**  
   Network connections are fixed for the entire session.

3. **Information differs, incentives do not**  
   Treatments affect *who sees which information*, not payoffs or available actions.

4. **Mechanical information sharing**  
   Information is shown automatically by the system; players cannot manipulate or misreport it.

---

## Game Environment

- **Players per group:** 8  
- **Rounds:** 15  
- **Decisions each round:**
  - **Contribution amount:** continuous (0–20)
  - **Belief report:** integer (0–100), non-incentivized, not shared

### Payoff Function

<img width="675" height="76" alt="image" src="https://github.com/user-attachments/assets/dfcf5c56-b6cc-4e30-8277-32138693ee43" />

- MPCR depends on an unobserved state:
  - **HIGH:** `MPCR_HIGH = 0.70`
  - **LOW:** `MPCR_LOW  = 0.30`

**Implementation detail:** Payoffs are computed using MPCR applied to total contributions, with correct handling of oTree currency types.

---

## Uncertainty and Information

### Unobserved State

- At the start of the experiment, the system selects a state: **HIGH** or **LOW** (equal probability).
- The state remains **fixed across all rounds**.
- The realised state is **never revealed** to participants.

### Messages (Signals)

- In each round, players receive system-generated **HIGH / LOW** messages.
- Players cannot change, hide, or manipulate these messages.

### Belief Elicitation

- After viewing messages, players report a belief (0–100) that the state is HIGH.
- Beliefs **do not affect payoffs** and are **not shown** to other players.

---

## Network Treatments

### 1) Ring Network (Decentralised)

- Each player is connected to two neighbours.
- In each round, players see:
  - their own message
  - messages from their two neighbours
- No player has access to everyone’s messages.

---

### 2) Hub-and-Spoke Network (Centralised)

- **Player 1** is the hub (central player).
- All other players are spokes.

**Information structure:**

- **Hub sees:** own message + all spokes’ messages  
- **Spokes see:** own message + hub’s message (no other spokes)

There is no spoke-to-spoke information flow.

---

## Timing Within Each Round

From **Round 2 onward**, each round proceeds as:

1. **Review previous round (private):** player sees own contribution + payoff from the previous round
2. **Messages page:** messages are shown according to network structure
3. **Decision page:** contribution amount + belief report
4. **Payoffs computed**
5. **Results page:** outcome shown (including a group contribution table)

Round 1 begins directly with the messages page.

---

## Outcomes of Interest

- Contribution behaviour over time
- Differences in cooperation across network structures
- Belief accuracy and belief dynamics
- Speed of information aggregation
- Differences between hub vs spokes (in hub-and-spoke)

---

## Implementation Notes

- Implemented in **oTree**
- Network structure is set at session launch via `SESSION_CONFIGS` (`network_type: 'ring'` or `'hub'`)
- No communication, punishment, or reputation mechanisms
- No endogenous network formation
- Focus is on **information exposure**, not strategic messaging

---

## Repository Structure

- `models.py` — game logic, payoffs, network rules
- `pages.py` — page flow and round timing
- `templates/` — UI (Instructions, ReviewLastRound, ObserveSignals, Decide, Results)
- `settings.py` — session configuration and treatment assignment

---

## Instructions Design

- On-screen instructions are intentionally **brief and non-technical**.
- A separate **Word document** is provided before the experiment with full details.

---

## Status

This repository implements the baseline experimental design for the FYP.

The design is intentionally minimal to ensure:
- participant clarity
- clean identification
- feasibility for lab/classroom deployment

