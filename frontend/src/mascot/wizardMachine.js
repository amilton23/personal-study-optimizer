export function wizardMood({ isGenerating, isReplying, celebration }) {
  if (celebration) return "cast";
  if (isGenerating) return "think";
  if (isReplying) return "talk";
  return "idle";
}

export function wizardBubble({ mood, progressMessage }) {
  if (mood === "cast") return "Excellent. Your study scroll is ready.";
  if (mood === "think") return progressMessage || "Consulting the arcane library...";
  if (mood === "talk") return "Observe closely. One concept at a time.";
  return "Ask, and I shall clarify the path.";
}
