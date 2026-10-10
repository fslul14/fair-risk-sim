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

For each: write the range, then write *why*. "Gut feel" is not a reason; "similar to X because Y" is.

| Input | Question to answer | min | most likely | max | Why this range |
|---|---|---|---|---|---|
| Threat event frequency | How many times a year would someone try to use or misuse access they should not have? | | | | |
| Vulnerability | Given an attempt, how likely is it to succeed and cause a loss? | | | | |
| Primary loss | Cost per event: investigation time, response, remediation, downtime | | | | |
| Secondary loss probability | How often does an event also trigger fines, legal, notification, client fallout? | | | | |
| Secondary loss | Cost when that happens | | | | |

Calibration checks before you commit a range:
- Would you be surprised if reality landed outside it? You should be (about 1 time in 10).
- Run `python calibration/quiz.py` first. If you scored 7 or less, widen every range.
- Is the min really the plausible low end, not zero? Is the max a bad-but-realistic year, not a catastrophe?

## 3. Assumptions log

List every assumption that, if wrong, changes the answer. These become the "re-evaluation triggers" in the README.

1.
2.
3.

## 4. Decision this analysis supports

Name the decision (fund a control, accept the risk, change a process) and the risk tolerance
threshold in dollars. Put that number in `risk_tolerance_usd` in inputs.json.
