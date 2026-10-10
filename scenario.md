# Scenario worksheet: M&F Analysis (fictional company; see company_profile.md)

> **How this was built:** Claude (Anthropic) drafted the starting estimates and this worksheet text from the
> company profile. They are my working baseline, not measured data. The README lists the corrections made after
> an independent review and has a table where I log any change I make to an estimate. All figures are invented.

## 1. Scope the scenario

- **Asset:** Client workspaces in the cloud data warehouse (220 clients, about 40% of whom have personal data about their own end customers).
- **Threat:** A former employee or contractor whose access was not removed in time. "Access" means an active SSO account, a local account in one of the 13 apps not behind SSO, or a shared credential or API key they still know.
- **Effect:** Loss of confidentiality: client data is read or copied, leading to an investigation and client notification.
- **Time frame:** 12 months.
- **Out of scope:** Outside attackers, misuse by current staff, accidental exposure, and sabotage or deletion of data.

**Scenario sentence:** In the next 12 months, a former employee or contractor of M&F Analysis whose access has not yet been removed uses it (an active account or a credential they still know) to read or copy client data in the cloud data warehouse, resulting in a confidentiality incident that requires investigation and client notification.

## 2. Estimate each input as a range (min / most likely / max)

The model treats min and max as hard limits (nothing outside them is possible). My ranges are therefore a little wider than the 90% ranges I practiced in the calibration quiz.

### Threat event frequency (attempts per year)
- min: 0.03
- most likely: 0.1
- max: 0.6
- Why: About 190 departures a year. I assume roughly 8 are contentious (4 to 15) and about 1% of those try to reach client data (0.3% low, 3% high), plus a tiny rate among friendly departures (0.01%, up to 0.05%). Likely: 8 x 1% + 182 x 0.01% = about 0.1 a year, one attempt every ten years. Low: 4 x 0.3% + 182 x 0.01% = about 0.03. High: 15 x 3% + 182 x 0.05% = about 0.55.
- Cross-check, and why it is weak: no attempt has been caught in about 5 years (950 departures). The rule of three says that if nothing is seen in n trials, the true rate is at most about 3 per n at 95% confidence: 3 / 950 = 0.3% per departure, or about 0.6 *caught* attempts a year. That caps caught attempts only. Detection is weak: if only 60% of attempts would be caught, the true rate could be as high as 0.6 / 0.6 = about 1 a year, and if 30%, about 2. So my max of 0.6 is not a ceiling; it is the top of what I judge plausible, and the clean record is weak evidence against anything much higher. This is the input I trust least, and the README tests what happens if it is higher.
- Published surveys (listed in the README) suggest this range is plausible but low-leaning. I kept it, and the README sweep shows what happens if the true rate is 2 to 5 times higher.

### Vulnerability (chance an attempt succeeds)
- min: 0.05
- most likely: 0.2
- max: 0.5
- Why: Two steps. First, does access still work when they try? About 30%: SSO is off within 24 hours at best, 13 apps are cleaned by hand, shared credentials rotate only each quarter, and contractor departures are recorded late. The split of that 30% by route and by who left is in the table below. Second, do they read or copy data before anyone notices? About 70%, because logs are reviewed only when alerts fire. 0.3 x 0.7 = about 0.2. MFA does not lower this much: it stops outsiders, not a former insider whose phone is still enrolled while the SSO account is active. Low: SSO disabled fast and no shared credential known. High: quarter-end backlog plus a known shared credential.
- Cross-check: in a 2009 Ponemon survey, about 1 in 4 leavers could still access data after leaving, close to the 30% above.

### Primary loss (USD per event)
- min: 15,000
- most likely: 75,000
- max: 400,000
- Why: Investigation by the outside incident-response firm on hourly billing. About 200 hours at roughly $350 is $70,000, plus internal security team time and legal review. Low: a quick, scoped review of about 40 hours. High: multi-week forensics plus outside counsel.
- Simplification: primary loss is counted on every loss event, which assumes every event is eventually investigated. If undiscovered events were never investigated, this would overstate the primary part of expected loss by up to about $1.8K a year (40% of its $4.6K).

### Secondary loss probability
- min: 0.25
- most likely: 0.5
- max: 0.85
- Why: Secondary loss needs the event to be discovered within the year, about 0.6 (the same weak log monitoring as above, so the two are related but not the same question: "stopped in time" versus "found eventually"). It then needs costs to follow, about 0.85, because contracts require notice within 72 hours and about 40% of clients hold personal data. 0.6 x 0.85 = about 0.5.

### Secondary loss (USD)
- min: 30,000
- most likely: 150,000
- max: 1,500,000
- Why: One client affected. Notification and legal cost about $60,000, a credit or concession is about 10% of a $400,000 contract ($40,000), and there is about a 15% chance of losing the client (an expected $60,000). Low: a notification letter and legal review only. High: several clients affected, 2 to 3 terminations at $400,000 each, plus about $300,000 of legal and regulatory cost. These figures are before insurance (a $5M limit with a $100,000 retention).

### With automated deprovisioning (the second scenario): only vulnerability changes
- min: 0.035
- most likely: 0.14
- max: 0.35
- Why: today's vulnerability range multiplied by 0.70. The 0.70 is the share of today's "access still works" exposure that the tool leaves in place, from this table (percentage points of the 30%; routes are added, which ignores small overlaps):

| Route | Today: employees | Today: contractors | Today total | With tool: employees | With tool: contractors | With tool total |
|---|---|---|---|---|---|---|
| SSO account and ticket delay | 7 | 8 | 15 | 1 | 8 | 9 |
| The 13 manual apps | 4.5 | 2.5 | 7 | 1.4 | 2.5 | 3.9 |
| Shared credentials and API keys | n/a | n/a | 8 | n/a | n/a | 8 |
| **Total** | | | **30** | | | **20.9** |

- How to read it: contractors are about one departure in three but carry more than half of the SSO exposure today (8 of 15), because project managers record their end dates late. The tool is triggered by the HR system, so it fixes employees (SSO off in about 1 hour: 7 becomes 1) and about 9 of the 13 manual apps (4 of 13 stay manual: 4.5 x 4/13 = 1.4), but not contractor records or shared credentials. 20.9 / 30 = 0.70. Threat event frequency and all loss amounts are unchanged: I assume no deterrence effect and no change in what an incident costs.
- The split between employees and contractors, and the 1 and 1.4 residuals, are my judgment, not measurements.

## 3. Assumptions log

If any of these is wrong, the answer changes. They are the re-evaluation triggers in the README.

1. **Departures:** about 190 a year, about 8 of them contentious. If contentious departures double, threat event frequency roughly doubles.
2. **No attempt ever caught in about 5 years.** Detection is weak, so undetected attempts would push the true frequency up (see the rule-of-three note). A confirmed attempt would raise my estimate immediately.
3. **About 30% chance access still works when an attempt is made** (SSO delay, 13 manual apps, quarterly shared-credential rotation, late contractor records). Quarter-end backlogs or more shared credentials would raise it.
4. **About 60% of events are discovered within the year** (query logs are reviewed only when alerts fire). Discovery drives secondary loss only. Better alerting would raise discovery, so it would raise modeled secondary losses while lowering vulnerability.
5. **Losses are counted before insurance** ($5M limit, $100,000 retention).
6. **The tool's effect** is the table above: employees' SSO accounts and 9 of 13 manual apps. It does not touch shared credentials or contractor record-keeping, and it does not change how often people try.
7. **Tool cost** is the vendor quote ($140,000 a year plus $40,000 one-time spread over 3 years). Internal administration time and discounting are ignored, and both would make the tool look worse.

## 4. Decision this analysis supports

- **Decision:** Buy the vendor's automated deprovisioning (about $140,000 a year plus about $40,000 one-time) or keep the manual process and accept the risk for this scenario.
- **Risk tolerance:** the chance that this scenario's loss in a year exceeds $250,000 should be at most 5%. Reason: $250,000 is 0.25% of the $100M revenue and above the $100,000 insurance retention, so a year above it from this one scenario would be painful and partly insured, not existential. This is my chosen cutoff, not a number leadership gave me. `risk_tolerance_usd` and `tolerance_max_probability` in `inputs.json` are 250000 and 0.05.

### Cheaper alternatives (rough sketch, not quotes)

The most any control can save in this scenario is today's whole expected loss, about $11.7K a year. Using the table above:

| Option | Exposure left (of 30 points) | Modeled saving a year | Rough cost a year |
|---|---|---|---|
| Vendor tool | 20.9 | about $3.5K | $153K (quote) |
| Rotate shared credentials when a holder leaves (8 becomes 1) | 23 | about $2.7K | about $7K: 190 departures x 25% knew a shared credential = about 48 rotations x 2 hours x $75 |
| HR owns contractor end dates (contractor SSO 8 becomes 3) | 25 | about $1.9K | about $1K: 60 contractor exits x 15 minutes x $75, plus a one-time process change |
| Both cheap moves | 18 | about $4.7K | about $8K |

The 25%, the hours, the $75 rate and the effect sizes are my assumptions. They show the cheap moves remove more exposure than the tool for a small fraction of the price, but on this scenario alone they only roughly break even, so any case for them rests on the other risks they reduce.
