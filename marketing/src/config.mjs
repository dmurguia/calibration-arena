export const site = {
  name: "Calibrated Co.",
  domain: "calibrated.co",
  defaultDirection: "outcomes",
  description:
    "Expert judgment, evaluation and training environments for AI agents doing professional work.",
};

export function validatedDestination(value, name, allowMail = false) {
  if (!value) return "";
  const url = new URL(value);
  if (url.protocol !== "https:" && !(allowMail && url.protocol === "mailto:")) {
    throw new Error(`${name} must use HTTPS${allowMail ? " or mailto" : ""}.`);
  }
  return url.href;
}
