import {
  esc,
  label,
  link,
  actions,
  closing,
  partnership,
  deliverables,
  demo,
  pageHero,
} from "./components.mjs";

export function homeCraft(sample) {
  return companyHome('The art of<br>better agents.');
}

function companyHome(title) {
  return `<section class="hero hero-company wrap">
    <div class="hero-copy">${label('AI training & evaluation')}<h1>${title}</h1>
      <p class="lead">Calibrated builds training data, evaluations and reinforcement learning environments with domain experts. For companies developing AI agents.</p>
      <div class="actions">${link('/get-data/', 'Get data', 'button')}${link('/enterprises/', 'For enterprises', 'button button-quiet')}</div>
    </div>
    <figure class="hero-art"><img src="/assets/open-sketch.webp" width="1536" height="1024" fetchpriority="high" alt="Flowing graphite lines on paper, from the Calibrated brand study."><figcaption>The art of better.</figcaption></figure>
  </section>
  ${deliverables()}
  <section class="arena-note wrap"><span class="mark"><img src="/assets/calibrated-mark-paper.svg" width="32" height="32" alt=""></span><div><h2>Starting with accounting.</h2><p>Calibration Arena lets accountants compare AI drafts and record corrections. Try a practice case to see how the review works.</p></div>${link('/training/#example', 'Try the example')}</section>
  ${partnership()}${closing()}`;
}

export function homeOutcomes(sample) {
  return companyHome('AI training for<br>professional work.');
}

export function enterprisePage() {
  return `${pageHero('For enterprises', 'Train agents on<br>your business.', 'We work with your team to turn specialist knowledge into training data, test cases and environments for AI agents.', actions('Talk to us', 'See the example', '/training/#example'))}
  <section class="section wrap" id="engagement"><div class="section-heading"><h2>Start with the task<br>your agent gets wrong.</h2><p>A missing source, a policy exception or an incorrect calculation. The failure tells us what to build.</p></div>
    <div class="engagement-list">
      <article><span class="index">01 / Evaluate</span><h3>Find the errors.</h3><p>Define representative tasks and have domain experts specify how to grade them. Test your agent against those criteria.</p><p class="deliverable">You receive: test cases, rubrics and a failure analysis.</p></article>
      <article><span class="index">02 / Build</span><h3>Make the training material.</h3><p>Develop demonstrations, corrections or a tool-based environment around the errors. Agree on data permissions and review each version.</p><p class="deliverable">You receive: a reviewed dataset or environment, with source and version records.</p></article>
    </div>
  </section>${partnership()}
  <section class="section wrap faq"><div><h2>Questions.</h2></div><div>
    <details><summary>Can you work with our existing agent?</summary><p>Yes. We start with its inputs, tools and outputs, then agree on the evaluation or training material it needs.</p></details>
    <details><summary>Where do you have a working example?</summary><p>Accounting, through Calibration Arena. Other domains need their own practitioners, tasks and review criteria.</p></details>
    <details><summary>How do you handle our data?</summary><p>Before a project starts, we agree on access, permitted uses, retention and ownership. Permission to evaluate data does not automatically permit using it for training.</p></details>
  </div></section>${closing()}`;
}

export function trainingPage(sample) {
  return `${pageHero('Our approach', 'Expert judgment.<br>Specific feedback.', 'An agent needs to know what it got wrong. We build the tasks and checks that make those errors visible.', actions('Talk to us', 'Try the example', '#example'))}
  ${demo(sample, true)}
  <section class="section wrap split-section"><div><h2>What the checks<br>actually measure.</h2></div><div class="prose"><p>The first check tests whether debits equal credits. The second compares amounts, accounts and dates against the stated policy.</p><p>Draft B passes the arithmetic check but recognizes expense a month early. Rewarding balance alone would reward the wrong answer.</p><p>Real training tasks need expert-reviewed criteria and separate evaluation cases to test whether the agent has learned the behavior.</p></div></section>
  <section class="section wrap"><div class="section-heading"><h2>Inside an evaluation set.</h2></div><div class="artifact-table" role="region" aria-label="Evaluation artifacts" tabindex="0"><table><thead><tr><th scope="col">Artifact</th><th scope="col">Contents</th></tr></thead><tbody><tr><th scope="row">Task</th><td>Inputs, available tools and expected output</td></tr><tr><th scope="row">Rubric</th><td>Automated checks and criteria for expert review</td></tr><tr><th scope="row">Examples</th><td>Demonstrations, errors and corrections</td></tr><tr><th scope="row">Source record</th><td>Origin, permissions, version and reviewer status</td></tr></tbody></table></div></section>${closing()}`;
}

export function companyPage() {
  return `${pageHero('Calibrated Co.', 'The art of better.', 'We are an AI training and evaluation company, starting with the judgment behind professional work.')}
  <figure class="company-image wrap"><img src="/assets/paper-and-cloth-768.webp" width="768" height="512" alt="Notebook paper, dark book cloth and a steel edge from the Calibrated brand study."></figure>
  <section class="section wrap split-section"><div><h2>Built with people<br>who know the work.</h2></div><div class="prose"><p>An accountant notices that an expense belongs in a different month. A model can miss that distinction while producing a convincing explanation.</p><p>We build datasets, evaluations and reinforcement learning environments around decisions like these. Domain experts help define the task, review the answer and explain the correction.</p><p>Our first application is Calibration Arena, where accountants compare AI drafts. The company’s broader focus is training agents for professional work.</p></div></section>
  <section class="section wrap split-section"><div><h2>Work with us.</h2></div><div class="prose"><p>Interested in applied research, engineering or contributing domain expertise? Tell us what you work on.</p>${link('/contact/?purpose=collaborate','Contact Calibrated')}<p class="caption">No open roles listed yet.</p></div></section>`;
}

export function leaderboardPage(config) {
  return `${pageHero('Calibration Arena', 'Leaderboard.', 'Model comparisons on accounting tasks, reviewed by practitioners.')}
  <section class="board-empty wrap"><div class="board-top"><span>ACCOUNTING</span><span>Not yet published</span></div><h2>Results are not available yet.</h2><p>Published rankings will include the tasks, model versions and review method.</p>${config.arenaUrl ? link(config.arenaUrl,'Open Calibration Arena','button') : link('/training/#example','Try a practice case','button')}</section>`;
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
    ? `<h2>Information on this site</h2><p>This marketing preview does not have accounts, analytics scripts, advertising trackers or a form submission service. Fonts and images are served with the site. The interactive work study runs in your browser.</p><h2>Project briefs</h2><p>Text you enter in the project brief form stays in page memory. The site does not submit it to Calibrated or save it in browser storage. The site does not persist your entries; your browser may retain form fields or page history. Downloading a brief saves a file to your device; copying it uses your clipboard. You decide whether to share that file or text.</p><h2>Hosting and external destinations</h2><p>A website host may process ordinary request information, such as an IP address, browser details and the requested page, to serve a site. Hosting-specific details and retention periods must be confirmed before public launch. External destinations handle information according to their own policies.</p><h2>Changes before launch</h2><p>If contact submission, analytics or other services are added, this notice must describe their actual data handling. Legal operator details and a privacy contact will be provided with the launch version.</p>`
    : `<h2>Purpose of this preview</h2><p>This site introduces Calibrated Co.’s proposed evaluation and training work. Descriptions are for discussion and do not create a service commitment, guarantee a model outcome or establish a commercial agreement.</p><h2>Examples and evaluation</h2><p>The accounting work study is a fictional, authored practice case from Calibration Arena. It is not financial or accounting advice, a live model run, or an independently validated benchmark. Do not rely on it for a real transaction or professional decision.</p><h2>Project scope</h2><p>Any commercial engagement requires a separate agreement covering scope, deliverables, pricing, data permissions, confidentiality, intellectual property and acceptance criteria.</p><h2>Assets and use</h2><p>The brand illustrations are generated material studies. The website’s bundled IBM Plex fonts are licensed under the SIL Open Font License. Company names and third-party references do not imply endorsement.</p><h2>Launch version</h2><p>These preview terms need the confirmed legal operator and contact details before public release. They do not replace a negotiated customer agreement.</p>`;
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
    <section class="section wrap"><div class="section-heading"><h2>What changed in this pass.</h2></div><div class="prose"><p>The homepage now names the business immediately: AI training for professional work. The introduction names the three services: training data, evaluations and reinforcement learning environments.</p><p>We removed the generic process section, repeated philosophy statements and full homepage demo. The graphite artwork is in the hero. The working accounting example remains on the approach page.</p></div></section>`;
}
