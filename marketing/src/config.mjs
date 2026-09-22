export const site = {
  name: "Calibrated Co.",
  domain: "calibrated.co",
  defaultDirection: "outcomes",
  description:
    "Calibrated builds training data, evaluations and reinforcement learning environments with domain experts.",
};

export function validatedDestination(value, name, allowMail = false) {
  if (!value) return "";
  const url = new URL(value);
  if (url.protocol !== "https:" && !(allowMail && url.protocol === "mailto:")) {
    throw new Error(`${name} must use HTTPS${allowMail ? " or mailto" : ""}.`);
  }
  return url.href;
}
