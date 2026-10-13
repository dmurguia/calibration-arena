export const site = {
  name: "Calibrated Co.",
  domain: "calibrated.co",
  defaultDirection: "outcomes",
  description:
    "We turn expert judgment into training data, evaluations and environments for AI agents. Explore CloseBench, our work on accounting-agent evaluation.",
};

export function validatedDestination(value, name, allowMail = false) {
  if (!value) return "";
  const url = new URL(value);
  if (url.protocol !== "https:" && !(allowMail && url.protocol === "mailto:")) {
    throw new Error(`${name} must use HTTPS${allowMail ? " or mailto" : ""}.`);
  }
  return url.href;
}
