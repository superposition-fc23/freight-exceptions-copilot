# DevRev customers by industry, and open-source copilots for each

Research note, 2026-10-31. The question: this repo is a freight exceptions copilot (Shipsy, a logistics customer, is the closest DevRev match). Which other industries does DevRev sell into, and is there an open-source copilot on GitHub, ideally one that ships its own industry data, for each of them?

## How this was gathered, and its limits

- devrev.ai could not be reached from the build environment (the proxy refuses it), so the customer list and URLs come from search-engine results for `devrev.ai/customers` and `devrev.ai/case-study`, not from reading the pages. The URLs are the ones the search index returned; the figures are DevRev's own claims.
- GitHub repos come from `gh api search/repositories`, sorted by stars. Star counts and last-push dates are as of the search. I read descriptions, not code: a repo listed here has not been run or reviewed.
- Most single-industry "copilot" repos are 0 to 3 star portfolio projects from 2026. The ones worth building on are marked **strong**.

## 1. DevRev customers (17, across 12 industries)

| # | Customer | Industry | Story URL | What they use DevRev for (per the story) |
|---|---|---|---|---|
| 1 | Shipsy | Logistics SaaS | https://devrev.ai/customers/shipsy | Unified support across email, Jira and in-app; ~5M shipments a day |
| 2 | BILL | Fintech, AP/AR | https://devrev.ai/customers/bill | AI agent at a 70% resolution rate; $5M saved |
| 3 | ICICI Prudential Life | Life insurance | https://devrev.ai/customers/icici-prudential-life | Resolution time from up to 48h to under 2h |
| 4 | Aditya Birla Capital | Lending, financial services | https://devrev.ai/customers/aditya-birla-capital | User experience and observability |
| 5 | L&T Financial Services | Digital banking, NBFC | https://devrev.ai/customers/lt-financial-services-advances-digital-banking-with-enhanced-observability | Observability for digital banking |
| 6 | Jar | Consumer fintech, savings | https://devrev.ai/customers/jar | Funnel analytics found the failures behind conversion drop-off; +3% conversion |
| 7 | Binah.ai | Health tech | https://devrev.ai/customers/binah-ai | Response times cut 50% |
| 8 | Bolt | E-commerce checkout | https://devrev.ai/customers/bolt | 40% faster resolution, 25% higher retention |
| 9 | Spotnana | Travel | listed on https://devrev.ai/customers (page URL not returned by search) | Customer engagement and team collaboration |
| 10 | Phenom | HR tech | https://devrev.ai/customers/phenom | 30% less ticket resolution time |
| 11 | Uniphore | Conversational AI, contact center | https://devrev.ai/case-study/uniphore | Single source of truth; alerts become tickets |
| 12 | Deepdub | Media, AI dubbing | https://devrev.ai/customers/deepdub | 24/7 support with no added headcount |
| 13 | ShemarooMe | Media, OTT streaming | https://devrev.ai/customers/shemaroome | Agentic AI; UI update rate at least doubled |
| 14 | Descope | Identity, auth | https://devrev.ai/customers/descope | 54% less average resolution time |
| 15 | Pixee | Application security | https://devrev.ai/customers/pixee | Developer experience and support |
| 16 | FOSSA | Open-source compliance | https://devrev.ai/customers/fossa | Migrated 10,000+ Zendesk tickets; two-way Jira sync |
| 17 | MAD Rewards | Loyalty, rewards | https://devrev.ai/case-study/mad-rewards | Email-only support to live chat plus AI chatbot |

Also named on the index without a story URL in the results: BigBasket (grocery), Orum (sales tech, https://devrev.ai/customers/orum), FAME (enterprise search, https://devrev.ai/customers/fame), Goodmeetings, Pebl, ToughTrucks For Kids, and in Japan, Macnica and KOKUYO.

## 2. Open-source copilots matched to each customer's industry

| Customer | Closest open-source copilot | Stars | Industry data included | Fit |
|---|---|---|---|---|
| Shipsy | this repo; [nrsundar/pgaiaba-proj3-multiagent-delivery-exceptions](https://github.com/nrsundar/pgaiaba-proj3-multiagent-delivery-exceptions); [1Arpan05/shipment-exception-resolution-system](https://github.com/1Arpan05/shipment-exception-resolution-system) | 0 | Last-mile and shipment exception cases, eval harness | Same shape as this repo |
| BILL | [FaranMustafa/threeway-agent](https://github.com/FaranMustafa/threeway-agent); [singhaditya261996-boop/invoice-agent](https://github.com/singhaditya261996-boop/invoice-agent); [Abuubkar/ledgerline](https://github.com/Abuubkar/ledgerline) | 0 | EDI 850/856/810 documents, three-way match, PRD plus eval framework | **Strong on shape**: invoice exceptions with deterministic guardrails is the AP twin of freight exceptions |
| ICICI Prudential Life | [kevinlimk/insurance-claims-copilot](https://github.com/kevinlimk/insurance-claims-copilot); [ethicalByte1443/Insurance-AI-Agent-RAG-Based](https://github.com/ethicalByte1443/Insurance-AI-Agent-RAG-Based); [Chandana18G/motor-claims-copilot](https://github.com/Chandana18G/motor-claims-copilot) | 0 to 24 | CMS synthetic Medicare claims (public data) | Claims, not life-policy servicing; the data is real-shaped |
| Aditya Birla Capital | [nimb-ou/loan-underwriting-copilot](https://github.com/nimb-ou/loan-underwriting-copilot); [MusabUmama/CreditLens](https://github.com/MusabUmama/CreditLens); [dumbgesh/ai-nbfc-chatbot](https://github.com/dumbgesh/ai-nbfc-chatbot) | 0 to 2 | Credit scoring with SHAP, RAG over precedents, NBFC loan FAQs | Underwriting copilot, plus an NBFC support bot |
| L&T Financial Services, Jar | [Kasper-Bankler/customer-message-router](https://github.com/Kasper-Bankler/customer-message-router); [amih/intent-router](https://github.com/amih/intent-router) | 0 | BANKING77 (13k banking support queries, 77 intents) | **Strong data**: BANKING77 is the standard public banking-support set; it routes with grounded refusal, like this repo's abstention |
| Binah.ai | [Sakshi3027/healthclaim-copilot](https://github.com/Sakshi3027/healthclaim-copilot) (support side); [ubicomplab/rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox) (domain side) | 1; 1.2k | Health-claim RAG with RAGAS evals; camera-based vital-sign datasets and models | No open-source health-tech *support* copilot found; rPPG-Toolbox is the open version of Binah's core tech |
| Bolt | [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) retail domain; [aneeshkolloju/freshcart-support-copilot](https://github.com/aneeshkolloju/freshcart-support-copilot) | 2.4k; 0 | Retail policy doc, orders/users database, graded tasks | **Strong**: MIT, maintained, policy plus tools plus evals |
| Spotnana | [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) airline domain; [openai/openai-cs-agents-demo](https://github.com/openai/openai-cs-agents-demo); [Punam-8767/AI-Powered-Automated-Auditor-for-Corporate-Travel-Claims](https://github.com/Punam-8767/AI-Powered-Automated-Auditor-for-Corporate-Travel-Claims) | 2.4k; 6.6k; 1 | Airline policy, bookings DB, tasks; airline CS agents with guardrails; travel-expense policy rules | **Strong**: tau2 airline is the closest public data to corporate travel support |
| Uniphore | [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench) telecom domain; [bitext/customer-support-llm-chatbot-training-dataset](https://github.com/bitext/customer-support-llm-chatbot-training-dataset) | 2.4k; 95 | Telecom troubleshooting tasks; labelled generic support intents (orders, refunds, accounts) | Data for testing a contact-center agent |
| Phenom | [srbhr/Resume-Matcher](https://github.com/srbhr/Resume-Matcher); [Naji-Najari/career-copilot](https://github.com/Naji-Najari/career-copilot) | 29k; 5 | Resume and job-description matching | Candidate side, not HR support |
| Deepdub | [krillinai/OpenCreator](https://github.com/krillinai/OpenCreator) | 14k | Video translation and dubbing pipeline | Open-source version of the product, not of its support |
| Pixee | [pixee/codemodder-python](https://github.com/pixee/codemodder-python), [codemodder-java](https://github.com/pixee/codemodder-java) | 43; 42 | Security codemods (fix rules) | **Pixee's own product is open source**: a security-fix copilot |
| FOSSA | [fossas/fossa-cli](https://github.com/fossas/fossa-cli) | 1.5k | Dependency and license analysis | The customer's own OSS tool, not a copilot |
| Descope | [descope/mcp-express](https://github.com/descope/mcp-express) | 39 | None | Auth for MCP servers; no copilot |
| ShemarooMe, MAD Rewards, BigBasket | nothing relevant found | | | Searches for OTT, loyalty and grocery support copilots returned nothing usable |

## 3. What to take from it

1. **The pattern in this repo transfers best to "exceptions" industries.** AP invoice exceptions (BILL) and insurance claims (ICICI Prudential) have the same structure: a queue of items that break a rule, a policy document that says what to do, and a cost to acting on the wrong answer. Both already have small open-source copilots with deterministic guardrails.
2. **For data, use the maintained benchmarks, not the portfolio repos.** tau2-bench (airline, retail, telecom: policy, database, graded tasks) covers Spotnana, Bolt and Uniphore. BANKING77 covers L&T, Jar and Aditya Birla. Bitext covers generic support intents.
3. **Three customers ship open source themselves** (Pixee, FOSSA, Descope). That is a source of real issues and docs for a support-copilot demo built on their own public tickets.
4. **Gaps**: no open-source support copilot for health tech, OTT media, loyalty or grocery turned up.

## Next step, if wanted

Port this repo to one adjacent industry by swapping only the data: `ai-stack/data/exceptions.json` (the queue), `ai-stack/docs/` (the playbook), and the eval questions. AP invoice exceptions is the shortest jump: replace customs holds with price and quantity mismatches against PO and receipt, and the guard rule "sources disagree" becomes "PO, receipt and invoice disagree".
