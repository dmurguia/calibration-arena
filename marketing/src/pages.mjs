import {
  esc,
  label,
  link,
  actions,
  closing,
  partnership,
  deliverables,
  systems,
  pageHero,
} from "./components.mjs";

export function homeCraft(sample) {
  return companyHome('Your expertise.<br>Better agents.');
}

function companyHome(title) {
  return `<section class="hero hero-company wrap">
    <div class="hero-copy"><h1>${title}</h1>
      <p class="lead">Turn your company’s expertise into better AI agents. We build training data, evaluations and reinforcement learning environments around the work your people know best.</p>
      <div class="actions">${link('/get-data/', 'Get data', 'button')}${link('/enterprises/', 'For enterprises', 'button button-quiet')}</div>
    </div>
    <figure class="hero-art"><img src="/assets/open-sketch.webp" width="1536" height="1024" fetchpriority="high" alt="Flowing graphite lines on paper, from the Calibrated brand study."></figure>
  </section>
  ${systems()}
  <section class="section wrap split-section knowledge-thesis"><div><h2>Knowledge work is<br>the next frontier.</h2></div><div class="prose"><p>The people doing the work know its exceptions, tradeoffs and standards. That expertise is a company’s advantage.</p><p>We believe companies will own their knowledge work through open-weight models trained on their expertise. Calibrated builds the data, evaluations and environments to get there.</p></div></section>
  ${deliverables()}${partnership()}${closing()}`;
}

export function homeOutcomes(sample) {
  return companyHome('Hone your agents.');
}

export function enterprisePage() {
  return `${pageHero('For enterprises', 'Train agents on<br>your business.', 'We work with your team to turn specialist knowledge into training data, test cases and environments for AI agents.', actions('Talk to us', 'See our approach', '/training/'))}
  <section class="section wrap" id="engagement"><div class="section-heading"><h2>Start with the task<br>your agent gets wrong.</h2><p>A missing source, a policy exception or an incorrect calculation. The failure tells us what to build.</p></div>
    <div class="engagement-list">
      <article><span class="index">01 / Evaluate</span><h3>Find the errors.</h3><p>Define representative tasks and have domain experts specify how to grade them. Test your agent against those criteria.</p><p class="deliverable">You receive: test cases, rubrics and a failure analysis.</p></article>
      <article><span class="index">02 / Build</span><h3>Make the training material.</h3><p>Develop demonstrations, corrections or a tool-based environment around the errors. Agree on data permissions and review each version.</p><p class="deliverable">You receive: a reviewed dataset or environment, with source and version records.</p></article>
    </div>
  </section>${partnership()}
  <section class="section wrap faq"><div><h2>Questions.</h2></div><div>
    <details><summary>Can you work with our existing agent?</summary><p>Yes. We start with its inputs, tools and outputs, then agree on the evaluation or training material it needs.</p></details>
    <details><summary>Can we start with an open-weight model?</summary><p>Yes. We scope the tasks, training data and evaluation around your chosen model and the systems it needs to use.</p></details>
    <details><summary>How do you handle our data?</summary><p>Before a project starts, we agree on access, permitted uses, retention and ownership. Permission to evaluate data does not automatically permit using it for training.</p></details>
  </div></section>${closing()}`;
}

export function trainingPage() {
  return `${pageHero('Our approach', 'Practice the work.<br>Refine the model.', 'Your experts know what a good result takes. We turn that knowledge into tasks, feedback and repeatable evaluations.', actions('Talk to us', 'See the workflow', '#example'))}
  <section class="section wrap" id="example"><div class="section-heading"><h2>From a real task<br>to a training environment.</h2><p>An illustrative knowledge-work workflow.</p></div><ol class="workflow-study">
    <li><span class="index">01 / Task</span><h3>Resolve a customer escalation.</h3><p>The agent reads a support thread, checks the current product documentation and reviews a related engineering issue.</p></li>
    <li><span class="index">02 / Judgment</span><h3>Know when to act.</h3><p>A domain expert defines which evidence is sufficient, which actions are permitted and when the agent should ask for help.</p></li>
    <li><span class="index">03 / Feedback</span><h3>Check the decision.</h3><p>Evaluate the sources, proposed action and escalation choice. Capture the expert’s corrections as training examples.</p></li>
    <li><span class="index">04 / Evaluation</span><h3>Test what carries over.</h3><p>Evaluate the next model version on held-out cases. Check whether it handles unfamiliar situations with the same care.</p></li>
  </ol></section>
  <section class="section wrap split-section"><div><h2>Built around<br>your model.</h2></div><div class="prose"><p>Start with the open-weight model and workflow you want to improve. We define the tasks, curate expert examples and design the checks that guide training.</p><p>Your team brings the context: tools, permissions, policies and people. Together, we define what the agent must get right.</p></div></section>
  ${systems()}${closing()}`;
}

export function companyPage() {
  return `${pageHero('Company', 'Your knowledge.<br>Your models.', 'We believe the next frontier for AI is the knowledge inside companies.')}
  <section class="section wrap split-section no-top"><div><h2>The expertise<br>is already there.</h2></div><div class="prose"><p>It lives in the people who know when a policy has an exception, why a customer needs a different answer and what makes a decision sound.</p><p>We believe companies will own that knowledge work through open-weight models shaped by their expertise. Calibrated turns expert decisions into training data, evaluations and environments that help agents improve.</p></div></section>
  <section class="section wrap team-background"><div class="section-heading"><h2>Our team brings<br>experience from</h2></div><ul class="affiliation-list" aria-label="Team backgrounds"><li>Stanford</li><li>MIT</li><li>Verkada</li></ul></section>
  <figure class="company-image wrap"><img src="/assets/paper-and-cloth-768.webp" width="768" height="512" alt="Notebook paper, dark book cloth and a steel edge from the Calibrated brand study."></figure>
  <section class="section wrap split-section"><div><h2>Help shape<br>how agents work.</h2></div><div class="prose"><p>We’re interested in people who know a field deeply, build models or design the systems agents work in.</p>${link('/contact/?purpose=collaborate','Work with Calibrated')}</div></section>`;
}

export function leaderboardPage(config) {
  return `${pageHero('Evaluation', 'Leaderboard.', 'How models perform on knowledge work, judged against expert-defined criteria.')}
  <section class="board-empty wrap"><div class="board-top"><span>KNOWLEDGE WORK</span><span>Not yet published</span></div><h2>Results are not available yet.</h2><p>Published rankings will include the tasks, model versions and review method.</p>${config.arenaUrl ? link(config.arenaUrl,'Open Calibration Arena','button') : link('/training/#example','Explore our approach','button')}</section>`;
}

export function dataPage() {
  return `${pageHero('Get data', 'Training data<br>for your agent.', 'Tell us the domain, the task and the format you need.')}
  <section class="section wrap split-section no-top"><div><h2>Custom datasets.</h2></div><div class="prose"><p>Expert demonstrations, preference comparisons and evaluation tasks. Our data offering is in development; a self-service catalog is not available yet.</p>${link('/contact/?purpose=data','Describe what you need','button')}</div></section>`;
}

export function contactPage(config) {
  return `${pageHero("Contact", "Tell us about<br>your project.", "What should your agent do, and where does it need help?")}<section class="contact-layout wrap"><div class="contact-aside">${label("Project brief")}<h2>Project details.</h2><p>Describe the workflow without including confidential records or personal information.</p>${config.contactUrl ? `<p>Prefer to reach out directly?</p>${link(config.contactUrl, "Contact Calibrated")}` : `<p class="contact-status">Contact opens soon. For now, this form creates a brief you can download. It does not send an inquiry.</p>`}</div><form id="brief-form"><div class="field"><label for="purpose">I’m interested in</label><select name="purpose" id="purpose"><option value="project">An enterprise project</option><option value="data">Training data</option><option value="collaborate">Working with Calibrated</option><option value="company">Learning about the company</option></select></div><div class="field"><label for="organization">Organization <span>(optional)</span></label><input name="organization" id="organization" autocomplete="organization" maxlength="120"></div><div class="field"><label for="workflow">What work should the agent do?</label><textarea name="workflow" id="workflow" required minlength="10" maxlength="2000" rows="4" placeholder="Describe the task and the errors you want to fix"></textarea></div><div class="field"><label for="standard">What would a good result look like? <span>(optional)</span></label><textarea name="standard" id="standard" maxlength="2000" rows="3" placeholder="The details an expert would check"></textarea></div><div class="field-pair"><div class="field"><label for="stage">Your starting point</label><select id="stage" name="stage"><option>Exploring a workflow</option><option>Evaluating an existing agent</option><option>Preparing training material</option><option>Building an RL environment</option></select></div><div class="field"><label for="partnership">Partnership</label><select id="partnership" name="partnership"><option value="discuss">To discuss</option><option value="embedded">Embedded</option><option value="managed">Managed</option></select></div></div><button class="button" type="submit" disabled data-enhance>Prepare brief</button><p class="caption">Prepared locally. No account, upload or email submission. <a href="/privacy/">How this page handles information</a>.</p><noscript><p>Enable JavaScript to generate a brief, or write down the questions above for your project conversation.</p></noscript><div id="brief-result" class="brief-result" hidden tabindex="-1"><h2>Your brief is ready.</h2><p>Review it below. It has not been sent.</p><pre id="brief-preview"></pre><div class="actions"><button class="button" type="button" id="download-brief">Download brief</button><button class="button button-quiet" type="button" id="copy-brief">Copy brief</button></div><p id="brief-status" role="status"></p>${config.contactUrl ? link(config.contactUrl, "Share through your preferred contact method") : ""}</div></form></section>`;
}

export function legalPage(kind, config) {
  const privacy = kind === "privacy";
  const content = privacy
    ? `<h2>Information on this site</h2><p>This marketing preview does not have accounts, analytics scripts, advertising trackers or a form submission service. Fonts and images are served with the site. The workflow example is illustrative.</p><h2>Project briefs</h2><p>Text you enter in the project brief form stays in page memory. The site does not submit it to Calibrated or save it in browser storage. The site does not persist your entries; your browser may retain form fields or page history. Downloading a brief saves a file to your device; copying it uses your clipboard. You decide whether to share that file or text.</p><h2>Hosting and external destinations</h2><p>A website host may process ordinary request information, such as an IP address, browser details and the requested page, to serve a site. Hosting-specific details and retention periods must be confirmed before public launch. External destinations handle information according to their own policies.</p><h2>Changes before launch</h2><p>If contact submission, analytics or other services are added, this notice must describe their actual data handling. Legal operator details and a privacy contact will be provided with the launch version.</p>`
    : `<h2>Purpose of this preview</h2><p>This site introduces Calibrated Co.’s proposed evaluation and training work. Descriptions are for discussion and do not create a service commitment, guarantee a model outcome or establish a commercial agreement.</p><h2>Examples and evaluation</h2><p>The workflow example illustrates a proposed approach. It is not a live model run, customer result or independently validated benchmark. Listed systems describe areas of workflow expertise; they do not imply vendor endorsement. Team affiliations describe backgrounds, not institutional partnerships.</p><h2>Project scope</h2><p>Any commercial engagement requires a separate agreement covering scope, deliverables, pricing, data permissions, confidentiality, intellectual property and acceptance criteria.</p><h2>Assets and use</h2><p>The brand illustrations are generated material studies. The website’s bundled IBM Plex fonts are licensed under the SIL Open Font License. Company names and third-party references do not imply endorsement.</p><h2>Launch version</h2><p>These preview terms need the confirmed legal operator and contact details before public release. They do not replace a negotiated customer agreement.</p>`;
  return `${pageHero(privacy ? "Privacy" : "Terms", privacy ? "Privacy notice." : "Website terms.", "Preview draft / 22 September 2026")}<article class="legal prose wrap"><p class="legal-note">${config.publicLaunch ? "Launch copy requires operator review." : "This notice describes the local marketing preview. Operator details and hosting practices need confirmation before public launch."}</p>${content}${link("/contact/", "Contact information")}</article>`;
}

export function reviewPage(results) {
  const names = {enterprise_buyer:'Enterprise buyer',technical_lead:'Technical lead',procurement_sponsor:'Procurement sponsor',investor:'Investor',prospective_employee:'Prospective employee',domain_expert:'Domain expert'};
  const choice = (run,key) => {
    const answer=run.answers[key+'_preference'];
    const name=run.candidateMapping[answer.choice] || 'No clear difference';
    return `${name === 'craft' ? 'Craft' : name === 'outcomes' ? 'Outcomes' : name} (${answer.probabilities[answer.choice].toFixed(2)})`;
  };
  return `${pageHero('Design review', 'The original<br>JEV results.', 'These results compare the first two drafts. They do not evaluate or endorse the revised copy.', `<div class="actions">${link('/','View revised homepage','button')}${link('/directions/craft/','View craft variation','button button-quiet')}</div>`)}
    <section class="review-verdict wrap"><h2>One consistent preference.<br>Five unstable results.</h2><p>Only the enterprise-buyer persona chose Outcomes in both passes. The others changed when we reversed the candidate order. Both drafts shared much of the same copy, and the rubric did not test for boilerplate.</p>
    <div class="artifact-table" tabindex="0" role="region" aria-label="Original JEV results"><table><thead><tr><th scope="col">Persona</th><th scope="col">Craft shown first</th><th scope="col">Outcomes shown first</th></tr></thead><tbody>${Object.entries(names).map(([key,name])=>`<tr><th scope="row">${name}</th><td>${choice(results[0],key)}</td><td>${choice(results[1],key)}</td></tr>`).join('')}</tbody></table></div>
    <p class="caption">Parentheses show the probability JEV assigned to its selected answer. These are not conversion rates, human survey results or design-quality scores.</p>
    <p>JEV identified the missing contact destination as the largest gap in both drafts. It did not establish that either homepage clearly explained the business.</p>
    <div class="actions">${link('/reports/jev-run-1.json','Download run 1','button button-quiet')}${link('/reports/jev-run-2.json','Download run 2','button button-quiet')}</div>
    ${results.map((run,index)=>`<details class="raw-result"><summary>Full response: run ${index+1}</summary><pre>${esc(JSON.stringify(run,null,2))}</pre></details>`).join('')}
    </section>
    <section class="section wrap"><div class="section-heading"><h2>What changed in this pass.</h2></div><div class="prose"><p>The current homepage focuses on honing agents with company expertise. It names training data, evaluations and reinforcement learning environments, and explains our belief in company-owned knowledge work through open-weight models.</p><p>The graphite artwork remains in the hero. The approach page illustrates a knowledge-work workflow; the Company page presents the thesis and team backgrounds. These revisions have not been evaluated by the original JEV runs.</p></div></section>`;
}
