# Scenario worksheet (fill this in before touching inputs.json)

Write the answers yourself. These are the decisions an interviewer will probe.

## 1. Scope the scenario (one sentence each)

- **Asset:** Client workspaces in the cloud data warehouse (220 clients, about 40% of whom have personal data about their own end customers).
- **Threat:** A former employee or contractor whose access was not removed in time. "Access" means an active SSO account, a local account in one of the 13 apps not behind SSO, or a shared credential or API key they still know.
- **Effect:** Loss of confidentiality: client data is read or copied, leading to an investigation and client notification.
- **Time frame:** 12 months.
- **Out of scope:** Outside attackers, misuse by current staff, accidental exposure, and sabotage or deletion of data.

**Scenario sentence:** In the next 12 months, a former employee or contractor of M&F Analysis whose access has not yet been removed uses it (an active account or a credential they still know) to read or copy client data in the cloud data warehouse, resulting in a confidentiality incident that requires investigation and client notification.

## 2. Estimate each input as a range (min / most likely / max)

### Threat event frequency (attempts per year)
- min: 0.03
- most likely: 0.1
- max: 0.6
- Why: About 190 departures a year. I assume roughly 8 are contentious (4 to 15) and about 1% of those try to reach client data (0.3% low, 3% high), plus a tiny rate among friendly departures (0.01%, up to 0.05%). Likely: 8 x 1% + 182 x 0.01% = about 0.1 a year, one attempt every ten years. Low: 4 x 0.3% + 182 x 0.01% = about 0.03. High: 15 x 3% + 182 x 0.05% = about 0.55. Cross-check: if no attempt was ever caught over 5 years (950 departures), the rule of three gives at most 0.3% per departure at 95% confidence, or about 0.6 a year. That matches my max. Detection is weak, so "never caught" doesn't mean "never happened."

### Vulnerability (chance an attempt succeeds)
- min: 0.05
- most likely: 0.2
- max: 0.5
- Why: Two steps. First, does access still work when they try? About 30%: SSO is off within 24 hours at best, 13 apps are cleaned by hand, shared credentials rotate only each quarter, and contractor departures are recorded late. Second, do they read or copy data before anyone notices? About 70%, because logs are reviewed only when alerts fire. 0.3 x 0.7 = about 0.2. MFA does not lower this much. It stops outsiders, not a former insider whose phone is still enrolled while the SSO account is active. Low: SSO disabled fast and no shared credential known. High: quarter-end backlog plus a known shared credential.

### Primary loss (USD per event)
- min: 15,000
- most likely: 75,000
- max: 400,000
- Why: Investigation by the outside incident-response firm on hourly billing. About 200 hours at roughly $350 is $70,000, plus internal security team time and legal review. Low: a quick, scoped review of about 40 hours. High: multi-week forensics plus outside counsel.

### Secondary loss probability
- min: 0.25
- most likely: 0.5
- max: 0.85
- Why: Secondary loss needs the event to be discovered, about 0.6, because logs are reviewed only when alerts fire. It then needs costs to follow, about 0.85, because contracts require notice within 72 hours and about 40% of clients hold personal data. 0.6 x 0.85 = about 0.5.

### Secondary loss (USD)
- min: 30,000
- most likely: 150,000
- max: 1,500,000
- Why: One client affected. Notification and legal cost about $60,000, a credit or concession is about 10% of a $400,000 contract ($40,000), and there is about a 15% chance of losing the client (an expected $60,000). Low: a notification letter and legal review only. High: several clients affected, 2 to 3 terminations at $400,000 each, plus about $300,000 of legal and regulatory cost. These figures are before insurance (a $5M limit with a $100,000 retention).

## 3. Assumptions log

List every assumption that, if wrong, changes the answer. These become the "re-evaluation triggers" in the README.

1.
2.
3.

## 4. Decision this analysis supports

Name the decision (fund a control, accept the risk, change a process) and the risk tolerance
threshold in dollars. Put that number in `risk_tolerance_usd` in inputs.json.
