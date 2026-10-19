# Calibration Arena Terms of Use: draft adapted from Design Arena

Status: working draft for counsel review, 2026-10-15. Not legal advice. Source material is Design Arena's public Terms of Use, Privacy Notice and Model Provider Terms page as of this date, plus the decisions recorded in `docs/pilot/DECISIONS.md` (synthetic documents only, no credential verification yet). Decision on 2026-10-15: adopt Design Arena's default-on, perpetual, sublicensable license to user content so every prompt and judgment can be licensed or sold. This supersedes the opt-in rule at `docs/pilot/DECISIONS.md` line 113 and the profile opt-in described at line 98; both need updating, and the app's Data use page with them.

Design Arena's terms are a consumer-content license dressed as a benchmark. Nearly everything they need commercially sits in one clause: a perpetual, sublicensable license to user content that lets them sell prompts and votes to AI providers. Calibration Arena has two things Design Arena does not at MVP: judges who are professionals with licensing obligations, and a directory of other publishers' benchmarks. The draft below keeps Design Arena's structure where it works and adds clauses for those two. Ranking vendor products beside models (Design Arena's Builder board) is deferred past the MVP; the clause for it is kept at the end as §2.8 so it is ready when that day comes, and nothing else in the draft depends on it.

## 1. Clause map

| Design Arena clause | Keep, change or add | Calibration Arena adaptation | Why |
| --- | --- | --- | --- |
| §1 Agreement, §3 Changes, §4 Who may use | Keep | Standard. Add that professional-context fields are self-reported unless marked verified. | Decisions log: no credential claims until verification exists. |
| §5 Feedback (used "without restriction or compensation") | Keep | Same. | Standard. |
| §6 No fees (unless stated for additional features) | Keep | Same, plus a hook for paid panels or vendor listings later. | Design Arena later added credits under this hook. |
| §7.1 No ownership claim over User Content | Keep | Same, extended to judgments and notebook entries. | Builds trust with professionals. |
| §7.2 Perpetual, sublicensable license incl. (ii) sell to third parties and (iii) train models | Keep | Adopt in full, with identifiers stripped before any third-party share. | Decided 2026-10-15. A broad license can be exercised narrowly later; a narrow one cannot be widened for data already collected. |
| §7.2(iv) and §17.1 "Service Information" (deidentified, aggregated data owned by the company) | Keep | Same. This is what powers rankings and aggregate reports and it is the floor of the data business. | Aggregates are ours under any license model. |
| §7.3 User represents it has rights to share content with AI providers | Keep and extend | Keep the rights representation and the no-compensation waiver; add a confidentiality warranty: no client data, no personal data of third parties, no material under NDA. | Judges are accountants; the real risk is client information in a prompt. |
| §8 Prohibitions, an 18-item list incl. item 8 (bots and scrapers) and item 11 (no commercial use outside the Terms) | Change | Keep scraping and automation bans. Add vote manipulation, sockpuppeting, credential misrepresentation and vendor self-voting. Replace the blanket commercial ban with an attribution rule for rankings. | Our rankings are meant to be cited. |
| §12.2 "You will not rely on the Services or any Output" | Change | Keep, and add that outputs are not accounting, tax, audit or legal advice and do not create a professional relationship. | Professional-liability exposure. |
| §15–16 California law, AAA consumer arbitration, class waiver | Decide | Placeholder. | Business decision for counsel. |
| §17.1 Company owns Services, Service Information and all Output | Keep | Same, naming rankings, ratings, taxonomy and the catalog as ours. | Standard. |
| §18 Third-party model outputs; maintain a public list of model terms | Keep | Same. Mirror Design Arena's `/model-terms` page. | Cheap, and it is what their providers expect. |
| Privacy Notice: user content data incl. votes shared with AI providers; disclosed as "sale or sharing" under CCPA | Keep | Mirror the disclosure, the Do Not Sell or Share link, and the statement that we do not control providers' retention. | Required once judgment data is sold by default. |
| (none) | Defer | Vendor participation terms (§2.8, post-MVP). | The MVP ranks foundation models only. Keep the text, do not publish it. |
| (none) | Add | Publisher content and directory terms. | We cite other people's benchmarks. |
| (none) | Add | Rankings and API attribution. | We will want our rankings quoted the way Design Arena's are. |

## 2. Draft clauses

Bracketed items are decisions, not drafting gaps.

### 2.1 Who we are and what this is

Calibration Arena is operated by Corsac Technologies Inc., a Delaware corporation doing business as Calibrated Co. ("Calibrated", "we", "us"). Calibrated Co. is a trade name of Corsac Technologies Inc.; the public site, footer and communications use it, and Corsac Technologies Inc. is the contracting party under these Terms and the Privacy Notice. The Services are a benchmarking platform where professionals compare AI-drafted accounting and finance work product, record a judgment, and contribute to public rankings of models and products, together with a directory of third-party benchmarks. These Terms, our Privacy Notice and the Model Provider Terms page form the agreement.

### 2.2 Accounts and professional context

You may use the Services as a guest or with an account. Professional context you provide (role, experience, jurisdiction, licensure) is self-reported. We display a status as "verified" only where we have completed a verification step described on the site. You may not state or imply a license, credential or employer you do not hold. [Decision: whether verified status is offered at launch; the decisions log says no.]

### 2.3 Fees

There are no fees for use of the Services unless stated on the Services. We may offer paid features, compensated review panels or paid vendor listings under separate terms. Participation in a compensated panel never changes how your judgments are weighted.

### 2.4 Your content and judgments

(a) Ownership. You keep ownership of prompts, uploads, notes and the judgments you record ("Your Content"). We do not claim ownership of Your Content.

(b) License. By making Your Content available through the Services you grant us an irrevocable, perpetual, non-exclusive, transferable, worldwide, fully paid-up, royalty-free license, with the right to sublicense through multiple tiers, to use, copy, store, reproduce, modify, adapt, create derivative works of, distribute, publicly display and perform, and otherwise exploit Your Content, in any media now known or later developed, for any business purpose, including: (i) to provide, operate, maintain and improve the Services and our other products, services and technologies; (ii) to sublicense and commercialize Your Content, for fees or free of charge, with third parties, including AI model providers, software vendors, research institutions and enterprises; (iii) to evaluate, benchmark, train, fine-tune or otherwise improve machine learning models and computational methods, ours or third parties'; and (iv) to generate Service Information. This license survives termination of your account.

(c) What we strip before sharing. Before Your Content is shared with a third party we remove your name, email address and account identifiers. Professional context you chose to provide (role, experience band, jurisdiction) may travel with a judgment in de-identified form, because it is part of what makes the judgment useful. Content inside a prompt or upload is shared as you wrote it, so §2.5 applies.

(d) Service Information. "Service Information" means data derived from Your Content and your use of the Services in de-identified or aggregated form, including rankings, ratings, statistics and the catalog. We own Service Information and may use and share it for any lawful purpose. We will not attempt to re-identify you from it.

(e) No compensation. You are not entitled to any compensation, royalty or revenue share for any use of Your Content or Service Information under these Terms, unless the written terms of a specific program say otherwise.

(f) Representations. You represent that you have all rights, permissions and authority needed to grant this license, including to share Your Content with third-party partners such as AI providers who may use it to evaluate, benchmark, train and improve their models. You acknowledge that a third party who receives Your Content may retain and use it under its own terms and that we cannot recall it once shared.

(g) Feedback. Suggestions and feedback may be used without restriction or compensation.

[Counsel: (b) and (f) track Design Arena §7.2 and §7.3 almost word for word. The additions are (c), which states what is stripped, and the survival sentence. Professional judges will read this clause more carefully than consumers do; the Data use page should say in one plain sentence that judgments are licensed to AI labs and others, so the terms never surprise anyone.]

### 2.5 Confidentiality and professional responsibility

Every case document provided by us is synthetic. You agree not to upload or paste client records, personal data of third parties, material protected by privilege or NDA, or anything your professional obligations prohibit you from sharing. We may remove such content and suspend accounts. Nothing in the Services replaces your professional judgment or relieves you of obligations under applicable professional standards, codes of conduct or licensing rules. [Counsel: consider a statement that we are not a CPE provider unless we become one.]

### 2.6 Model outputs and rankings are not advice

Outputs shown in the arena are generated by third-party models and products and may be wrong. They are presented for evaluation only. Outputs, rankings and anything else on the Services are not accounting, tax, audit, legal or investment advice and do not create a professional relationship with us or with any model provider. You will not rely on any output and will conduct your own diligence. Rankings are statistical estimates with stated uncertainty; they change as judgments arrive and a model may move without any change to the model.

### 2.7 Third-party model and product terms

Outputs are produced by third-party models and products under their own terms. We maintain a public list of those terms at [/model-terms] and identify which model or product produced an output after a judgment is recorded. Your use of an output is also governed by the applicable third-party terms. We do not control how a provider retains or uses data we send it; the Privacy Notice explains what we send.

### 2.8 Vendor and model-provider participation (deferred, post-MVP)

Not part of the MVP terms. The arena ranks foundation models only until a product row is a deliberate product decision. Retained here so the claim-your-listing mechanics have terms ready when they are built.

(a) Listing. Any model or product may be listed. A listing identifies the vendor, product and version and whether the vendor submitted it, a customer contributed it, or we ran it from a public endpoint. Trademarks and logos are used only to identify the product.

(b) Submissions. By submitting a product or endpoint you confirm you are authorized to do so, grant us a license to run it against arena tasks and to publish the resulting outputs, judgments and rankings, and agree that results are published without vendor approval. You may request a correction of a factual error about identity, version or configuration. You may not demand removal of a result.

(c) Claimed listings. A vendor may claim its listing to add a description, confirm versions, receive result notifications and respond publicly to results. Claiming a listing grants no influence over rankings.

(d) Declined participation. If we invite a vendor and it declines, we may show the listing as "invited, declined to participate" with the invitation date.

(e) Integrity. Vendors, their employees and agents may not vote on their own products, recruit voters, or otherwise manipulate judgments. We may void affected judgments and disclose the manipulation.

### 2.9 Benchmark directory and publisher content (new)

The directory at /benchmarks lists benchmarks published by others and, under "Awaiting public results", vendor accuracy claims with their source; that is a listing of claims, not a ranking of products. We copy a headline figure, metric and date as a cited fact with a link to the source and label its provenance. We do not re-score, combine or rank across benchmarks. Result figures remain the publisher's and are not relicensed by us; our catalog metadata is published under CC BY 4.0. Structured mirroring of a publisher's full leaderboard happens only under an open license or written permission. Publishers may request a listing, a correction or a takedown at [contact]; we respond within [10] business days.

### 2.10 Rankings, data and API attribution (new)

Rankings, ratings, the taxonomy and the catalog are our Service Information. You may quote and reproduce rankings with attribution ("Source: Calibration Arena" and a link to the ranking page) and without implying our endorsement of any model, product or conclusion. Automated access is permitted only through an API we provide, under the API terms and attribution requirements published with it. Scraping, crawling or bulk downloading the Services by any other means is prohibited.

### 2.11 Prohibited conduct

Adapted from Design Arena §8 (items 1 to 18), keeping everything except item 11: unlawful or infringing content, automated account creation, framing and trademark misuse, non-public areas, security probing, circumvention, bots and scrapers outside the API, spam, forged headers, reverse engineering, interference, harvesting personal information, impersonation, violating law, enabling others. Design Arena has no rule against vote manipulation or self-voting; it relies on anonymized, randomly paired outputs instead. Adding: voting on a model made by you or your employer; coordinating or paying for votes; submitting judgments by automation; misrepresenting professional status; uploading confidential or third-party personal data; using the Services to build a competing preference dataset. Removing: item 11, the blanket "no commercial purpose" clause, replaced by §2.10. Design Arena's own API docs allow commercial reuse of rankings with attribution, so item 11 contradicts their practice, and we want firms and labs to cite our rankings.

### 2.12 Ownership, disclaimers, liability, indemnity, termination

Track Design Arena §§11–14 and 17: we and our licensors own the Services, Service Information and the presentation of outputs; Services are provided as is; liability capped at [the greater of $100 and fees paid in 12 months]; you indemnify for your content and conduct; either party may terminate; surviving clauses listed.

### 2.13 Governing law and disputes

Decided 2026-10-19 and live in PR #33: Delaware law and Delaware courts for anything outside arbitration; the Federal Arbitration Act for the arbitration section; AAA Consumer Arbitration Rules before a single arbitrator, hearings by video or in the user's county; AAA fee allocation with no fee recovery against the user unless the claim is frivolous; a 60-day notice-and-confer step; small-claims and IP-injunction carve-outs; a class-action waiver with Design Arena's poison pill; a 30-day opt-out; a conspicuous notice in the opening paragraph. Not included yet: mass-arbitration batching, and a decision on whether the forum should follow the principal place of business rather than the state of incorporation. Counsel to confirm both.

## 3. Privacy Notice adaptations

1. Categories collected: account data; self-reported professional context; prompts, uploads, notes and judgments ("Judgment Data"); device and usage data; payment data via the processor if any.
2. Sharing with model and product providers: prompts and uploads are sent to the provider that generates an output, with account identifiers removed. Name the provider list page. State whether providers may retain or train on what we send, per their terms, and that we do not control their retention.
3. Licensing to third parties: Judgment Data, with name, email and account identifiers removed, is licensed or sold to third parties including AI providers, software vendors and researchers under §2.4(b). Mirror Design Arena's CCPA line: providing Judgment Data to AI providers may be a "sale" or "sharing" of personal information under California law, with a Do Not Sell or Share My Personal Information link. Counsel to confirm how an opt-out is honored for California residents once content has already been shared, and whether GDPR users need a lawful basis other than consent.
4. Aggregated and de-identified data: may be created, used and shared; we will not re-identify.
5. Verification data: if we ever verify licenses, state the source (state board lookups, NASBA), what is stored, and retention.
6. Retention: account life plus a stated period; Judgment Data retained for ranking integrity even after account deletion, de-identified.
7. Analytics and cookies: name vendors; load non-essential cookies only on consent.

## 4. Decisions needed before this goes to counsel

1. Decided 2026-10-19: Corsac Technologies Inc. is the contracting entity. Delaware corporation (confirmed 2026-10-19). Public-facing name stays Calibrated Co., so a DBA for "Calibrated Co." is filed by Corsac Technologies Inc. in the state and county of its principal place of business (and in Delaware if it operates there). Remaining: the principal place of business for the forum clause and the DBA filing. The filing is made by the legal entity (Corsac Technologies Inc.) for the trade name (Calibrated Co.), never the reverse; a contract naming "Calibrated Co." as the party without the DBA on file names an entity that does not exist.
2. Decided 2026-10-15: default-on license mirroring Design Arena §7.2. Remaining sub-decision: whether professional context travels with shared judgments (§2.4(c) says yes, de-identified).
3. Whether verified credential status exists at launch and what evidence it rests on.
4. Whether compensated panels are planned, since they need their own terms. (Vendor listings are deferred with §2.8.)
5. Decided 2026-10-19: Delaware law, AAA consumer arbitration, class waiver, 30-day opt-out (see §2.13). Remaining: batching clause and forum vs principal place of business.
6. Whether an API will exist at launch; if so, publish its attribution terms with it rather than in these Terms.
