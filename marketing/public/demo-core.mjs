// The two checks mirror backend/app/pilot_cases.py. Values are integer cents.
export function evaluateDraft(draft) {
  const totals = new Map();
  for (const [date, , amount] of draft.postings)
    totals.set(date, (totals.get(date) || 0) + amount);
  const normalize = (rows) => rows.map((row) => JSON.stringify(row)).sort();
  return {
    balanced: [...totals.values()].every((total) => total === 0),
    policyMatch:
      JSON.stringify(normalize(draft.postings)) ===
      JSON.stringify(normalize(draft.expected_postings)),
  };
}

export function projectBrief(values) {
  return `CALIBRATED CO. / PROJECT BRIEF\n\nPurpose: ${values.purpose || "Project inquiry"}\nOrganization: ${values.organization || "Not provided"}\nWork to improve:\n${values.workflow || "Not provided"}\n\nWhat good looks like:\n${values.standard || "Not provided"}\n\nStarting point: ${values.stage || "Not provided"}\nPartnership: ${values.partnership || "To discuss"}\n\nPrepared locally. This brief has not been sent to Calibrated.\n`;
}
