import { evaluateDraft, projectBrief } from "./demo-core.mjs";

document.documentElement.classList.remove("no-js");

const menu = document.querySelector(".menu-toggle");
const nav = document.querySelector("#navigation");
function closeMenu() {
  nav.classList.remove("is-open");
  menu.setAttribute("aria-expanded", "false");
  menu.querySelector("span").textContent = "+";
}
menu?.addEventListener("click", () => {
  const open = menu.getAttribute("aria-expanded") !== "true";
  menu.setAttribute("aria-expanded", String(open));
  nav.classList.toggle("is-open", open);
  menu.querySelector("span").textContent = open ? "−" : "+";
});
document.addEventListener("keydown", (event) => {
  if (
    event.key === "Escape" &&
    menu?.getAttribute("aria-expanded") === "true"
  ) {
    closeMenu();
    menu.focus();
  }
});
nav?.addEventListener("click", (event) => {
  if (event.target.closest("a")) closeMenu();
});
matchMedia("(min-width: 901px)").addEventListener("change", (event) => {
  if (event.matches && menu) closeMenu();
});

const example = document.querySelector("[data-demo]");
if (example) {
  // Embedded at build time from the repository's authored fixture. No request or loading state.
  const sample = JSON.parse(document.querySelector("#sample-data").textContent);
  let selected = 0;
  const result = example.querySelector(".check-result");
  const renderDraft = () => {
    example
      .querySelectorAll("[data-draft]")
      .forEach((button) =>
        button.setAttribute(
          "aria-pressed",
          String(Number(button.dataset.draft) === selected),
        ),
      );
    const content = example.querySelector(".draft-content");
    content.replaceChildren();
    const el = (tag, cls, text) => {
      const node = document.createElement(tag);
      node.className = cls;
      node.textContent = text;
      return node;
    };
    content.append(
      el(
        "p",
        "small-label",
        `March close / Draft ${selected === 0 ? "A" : "B"}`,
      ),
    );
    content.append(
      el(
        "p",
        "draft-conclusion",
        selected === 0
          ? "No amortization entry. Coverage has not begun."
          : "Recognize $1,200 expense in March, the payment month.",
      ),
    );
    const lines =
      selected === 0
        ? [
            ["Dr Prepaid insurance", "$14,400"],
            ["Cr Cash", "$14,400"],
          ]
        : [
            ["Dr Insurance expense", "$1,200"],
            ["Cr Prepaid insurance", "$1,200"],
          ];
    for (const [account, amount] of lines) {
      const row = el("div", "entry-line", "");
      row.append(el("span", "", account), el("span", "", amount));
      content.append(row);
    }
    content.append(
      el(
        "p",
        "caption",
        selected === 0
          ? "Begin $1,200 monthly recognition in April."
          : "The original $14,400 payment entry is the same as Draft A.",
      ),
    );
    result.textContent = "Check the posting against the stated case policy.";
  };
  example.querySelectorAll("[data-draft]").forEach((button) =>
    button.addEventListener("click", () => {
      selected = Number(button.dataset.draft);
      renderDraft();
    }),
  );
  example.querySelector("[data-check]").addEventListener("click", () => {
    const checks = evaluateDraft(sample.drafts[selected]);
    result.replaceChildren();
    for (const [name, passed] of [
      ["Debits equal credits", checks.balanced],
      ["Matches the stated policy", checks.policyMatch],
    ]) {
      const row = document.createElement("p");
      row.className = "check-row";
      const text = document.createElement("span");
      text.textContent = name;
      const verdict = document.createElement("strong");
      verdict.textContent = passed ? "Pass" : "Needs revision";
      if (!passed) verdict.className = "needs-review";
      row.append(text, verdict);
      result.append(row);
    }
    const note = document.createElement("p");
    note.textContent = checks.policyMatch
      ? "Expense begins in April, when coverage starts."
      : "The entry balances, but expense starts one month too early.";
    result.append(note);
  });
}

const form = document.querySelector("#brief-form");
if (form) {
  form.querySelector("[data-enhance]").disabled = false;
  const params = new URLSearchParams(location.search);
  for (const key of ["purpose", "partnership"]) {
    const field = form.elements.namedItem(key);
    const value = params.get(key);
    if (value && [...field.options].some((option) => option.value === value))
      field.value = value;
  }
  let brief = "";
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(form));
    if (
      !String(values.workflow).trim() ||
      String(values.workflow).trim().length < 10
    ) {
      form.elements.workflow.setCustomValidity(
        "Describe the workflow in at least 10 characters.",
      );
      form.elements.workflow.reportValidity();
      return;
    }
    brief = projectBrief(values);
    document.querySelector("#brief-preview").textContent = brief;
    const result = document.querySelector("#brief-result");
    result.hidden = false;
    result.focus();
  });
  form.elements.workflow.addEventListener("input", () =>
    form.elements.workflow.setCustomValidity(""),
  );
  form.addEventListener("input", () => {
    document.querySelector("#brief-result").hidden = true;
    document.querySelector("#brief-status").textContent = "";
  });
  document.querySelector("#download-brief").addEventListener("click", () => {
    const url = URL.createObjectURL(
      new Blob([brief], { type: "text/plain;charset=utf-8" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "calibrated-project-brief.txt";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    document.querySelector("#brief-status").textContent =
      "Download prepared. The brief has not been sent.";
  });
  document.querySelector("#copy-brief").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(brief);
      document.querySelector("#brief-status").textContent =
        "Copied. The brief has not been sent.";
    } catch {
      document.querySelector("#brief-status").textContent =
        "Clipboard access is unavailable. Select the brief text or use Download brief.";
    }
  });
}
