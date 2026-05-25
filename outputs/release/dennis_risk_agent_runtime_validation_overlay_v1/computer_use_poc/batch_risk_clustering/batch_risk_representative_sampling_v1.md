# Batch Risk Representative Sampling v1

## 1. Purpose

Representative sampling prevents large batch analysis from becoming unsafe or low-quality one-by-one lookup.

## 2. Sampling by Scale

### 5-9 entities

- Can recommend full investigation or sampling.
- If sampling, choose 3-5 representative samples.
- Use sampling when evidence is uneven, cost is unclear, or user asks for pattern first.

### 10+ entities

- Default: choose 3-5 representative samples.
- Do not investigate every entity online by default.
- Use samples to validate cluster hypotheses and false-positive boundaries.

## 3. Sample Types

### high-confidence positive sample

- Multiple strong evidence types overlap.
- Represents the main risk cluster.
- Use to validate primary attack path.

### boundary / ambiguous sample

- Has risk clues but incomplete evidence.
- Use to draw judgement boundary.
- Good for preventing overblocking.

### suspected false positive sample

- Strategy hit exists but user behavior, profile, or context may be normal.
- Use for false-positive control and grey release design.

### high-impact sample

- High value user, high impact behavior, high complaint, high amount, high propagation risk.
- Use to protect business impact and escalation handling.

### source-gap sample

- Key evidence missing, source blocked, log over window, platform unavailable, DataAgent / Hive needed.
- Use to define offline query plan.

## 4. Required Sample Output

Each representative sample must generate an evidence card with:

- case_id.
- sample_type.
- cluster_assignment.
- why_selected.
- raw evidence.
- derived evidence.
- user claim.
- model inference.
- missing evidence.
- blocked evidence.
- source metadata.
- preliminary judgement.
- required follow-up.

## 5. Boundary

- Sampling is not proof that all cluster members are risky.
- A sample can validate a hypothesis only for the represented cluster when common evidence is present.
- If clusters are heterogeneous, each major cluster needs at least one representative sample.
- If only one sample supports a cluster, output confidence limit and required follow-up.
