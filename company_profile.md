# Fictional company profile: M&F Analysis

> **This company is fictional.** Every detail below is invented for this exercise (by Claude, as the starting
> material) and is not based on any real organization, client, or incident. Any resemblance to a real company
> is coincidental.

## The business
- B2B analytics firm that builds dashboards and data pipelines for mid-size retailers and logistics companies.
- About 800 employees and about 150 contractors at any time. Revenue about $100M.
- 220 active clients, average annual contract value about $400K.
- Each client has a dedicated workspace in a cloud data warehouse and shared project folders. Roughly 40% of
  clients' data includes personal data about their own end customers.

## People and turnover
- Employee attrition about 16% a year, so roughly 128 employee departures a year.
- Contractors rotate often: about 60 contractor engagements end each year.
- Total: roughly 190 offboardings a year, mostly routine and friendly, a small number contentious.

## How offboarding works today
1. HR records the termination in the HR system.
2. The HR system opens a ticket for IT. A service desk analyst disables the person's SSO account. Target: within 24 hours.
3. Of the 35 business applications, 22 are behind SSO, so they lose access when the SSO account is disabled.
   The other 13 have local accounts, API tokens, or shared credentials that IT removes by hand. Target: 5 business days.
4. Shared credentials and API keys the person knew are rotated only during the quarterly access review.

Known weaknesses: the ticket queue backs up around quarter end; contractor departures are recorded late because
they are tracked by the project manager, not HR; and the quarterly review only catches stragglers after the fact.

## Controls in place
- Single sign-on with MFA enforced for all workforce logins.
- Quarterly access reviews.
- Logging of data-warehouse queries, reviewed by an analyst when alerts fire.
- A security team of 6 and an outside incident-response firm on retainer (hourly billing).
- Cyber insurance with a $5M limit and a $100K retention.

## Contracts
- Most client contracts require notification within 72 hours of a confirmed security incident.
- Most also allow the client to terminate for a material security breach.

## The decision on the table
The security team has a vendor proposal for **automated deprovisioning**: the HR system's termination event would
trigger SSO disablement within about 1 hour and automatically remove access in an estimated 9 of the 13 apps that
aren't behind SSO. The quote is about **$140K a year plus about $40K one-time** for integration. The alternative is
to keep the manual process and accept the risk.

## What this profile does not contain
It gives no threat frequencies, loss amounts, or risk tolerance. Those are the estimates in `scenario.md`.

## Scenario used
A former employee or contractor whose access was not removed in time uses it to read client data. The profile
supports other scenarios too, such as an outside attacker using a forgotten account; those are out of scope.
