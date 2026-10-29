import posthog from "./posthog";

export const posthogLogger = {
  comparisonCreated({ workflowId, attachmentCount }: { workflowId: string; attachmentCount: number }) {
    posthog?.logger.info("comparison request accepted", {
      event: "comparison.request.accepted",
      workflow_id: workflowId,
      attachment_count: attachmentCount,
    });
  },
  followUpCreated({ workflowId, turnNumber }: { workflowId: string; turnNumber: number }) {
    posthog?.logger.info("comparison follow-up accepted", {
      event: "comparison.follow_up.accepted",
      workflow_id: workflowId,
      turn_number: turnNumber,
    });
  },
  comparisonRetried({ retryReason }: { retryReason: string }) {
    posthog?.logger.warn("comparison retry accepted", {
      event: "comparison.retry.accepted",
      retry_reason: retryReason,
    });
  },
};
