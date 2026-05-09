# Adversarial VC Pitch Review: Methodic

**Reviewer Focus:** Market sizing, Competitive landscape, Overclaims, Business model realism, and Fundability gaps.
**Objective:** Provide a harsh, blind adversarial review to stress-test the pitch before investor exposure.

---

## 1. Market Sizing Plausibility
**Verdict: Plausible framework, but the SOM and pricing mechanics reveal a mismatch.**
*   **The Mismatch:** The target segment table claims B2B SaaS will pay $2K-$5K/mo, but the Business Model section lists Phase 1 self-serve SaaS at $99-$499/mo. Which is it? If your SOM is $48M in Year 3 off a $99/mo product, you need ~40,000 logos. If it's off a $3K/mo product, you need ~1,300 logos. 
*   **Willingness to Pay (WTP) Skepticism:** $2K-$5K/mo is Enterprise software territory. Teams spending that much expect full-service white-glove consulting (like Clozd) or deeply embedded platforms (like Gong). A self-serve AI surveying tool will face immense downward pricing pressure toward the $99-$499/mo tier.
*   **TAM/SAM Focus:** The SAM ($2.4B) is realistic for qualitative B2B research, but qualitative research budgets are often highly discretionary compared to quantitative data tooling. 

## 2. Competitive Landscape Accuracy and Completeness
**Verdict: Dangerously incomplete. You are missing your biggest indirect competitors.**
*   **The "Gong" Threat (Revenue Intelligence):** You do not mention Gong, Chorus.ai, or Clari. This is a fatal omission for your initial wedge (Win-Loss). Why would a RevOps leader pay for Methodic to conduct a *new* interview when Gong already recorded all 15 hours of the sales cycle and its native AI can extract the exact reasons for the loss? 
*   **Traditional CX/UX Platforms:** You omitted Qualtrics, Medallia, and UserTesting. These giants are rapidly bolting on AI capabilities. You need a better answer for "What happens when Qualtrics adds an adaptive AI chat node to their surveys?"
*   **Outset.ai Comparison:** Outset *does* do AI-moderated interviews. Claiming they lack "methodology governance" sounds like a feature gap, not a structural weakness. They could build a "methodology" prompt chain in a weekend.

## 3. Overclaims & Weak Spots a VC Will Probe
**Verdict: The "Moat" is an implementation detail, and participant incentives are entirely ignored.**
*   **The "Moat" Illusion:** *“7 LLM agents + 6 custom steps”* is not a moat; it's a software architecture. VCs know that multi-agent orchestration is becoming commoditized. Your moat needs to be data gravity, network effects, or proprietary distribution, not the fact that you use multiple prompts under the hood.
*   **The Respondent Acquisition Problem (The Biggest Weakness):** B2B buyers are notoriously difficult to get on the phone for win-loss interviews, even when offered $100+ gift cards. Why would a busy VP of Engineering who just bought a competitor's product spend 15 minutes chatting with your AI bot? If you cannot guarantee a high response rate, your software is useless. The pitch completely ignores *how* you get people to talk to the agent.
*   **The Quality Metric:** *"+0.692 composite improvement"* sounds like made-up AI lab science. Investors care about business metrics. Did the insights increase win rates? Did it reduce churn? Lab metrics don't sell software.

## 4. Business Model Realism for a Vertical AI Agent
**Verdict: Serviceable, but COGS and unit economics need clarification.**
*   **Cost per Interview ($15-$50):** This is very high for pure software COGS. If a customer runs a 500-person churn study, that costs you up to $25,000 in LLM API calls? If the customer is paying $499/mo, you are deeply underwater. You need to clarify if the $15-$50 includes respondent incentives (gift cards) or if that's purely LLM/Compute costs. If it's purely compute, your unit economics are broken.
*   **Marketplace Pivot (Phase 2):** Pivoting to a marketplace (participant panels) is a completely different business model than B2B SaaS. It requires massive capital to build both supply and demand. VCs will see this as a lack of focus. 

## 5. What's Missing to Make This Fundable
**To move this from a "cool AI project" to a fundable Seed/Series A company, you must add:**
1.  **The Incentive Strategy:** Explicitly address how you solve the "cold start" problem of getting B2B professionals to talk to an AI. Do you integrate with Tremendous for auto-bounties? 
2.  **The "Why Not Gong" Slide:** A clear, aggressive takedown of why post-deal conversational intelligence (Gong) is insufficient for true Win-Loss analysis (e.g., "Gong only captures what the buyer was willing to tell the rep to their face; Methodic captures the unvarnished truth").
3.  **Defensible IP/Moat:** Shift the moat away from "we use ADK and multiple agents" to "we have proprietary methodologies co-developed with top researchers" or "we integrate deeply into CRM to create autonomous trigger-to-insight loops that can't be easily ripped out."
4.  **Unit Economics Breakdown:** Reconcile the pricing mismatch between the Target Segments table and the Phase 1 Business Model, and clarify the margin structure on a $15-$50 interview.
5.  **Traction Context:** 133 automated tests and BigQuery exports are engineering milestones, not business traction. You need design partners. "Launch beta with 20 B2B SaaS companies" is a goal, but you need to show you have at least 3-5 signed Letters of Intent (LOIs) right now.