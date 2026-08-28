const yearNode = document.getElementById("year");
if (yearNode) {
  yearNode.textContent = String(new Date().getFullYear());
}

const THEME_KEY = "site-theme";
const THEME_COLORS = {
  light: "#f6efe6",
  dark: "#161210",
};

function applyTheme(theme, savePreference) {
  const chosen = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = chosen;

  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute("content", THEME_COLORS[chosen]);
  }

  document.querySelectorAll('input[name="theme"]').forEach((input) => {
    input.checked = input.value === chosen;
  });

  if (savePreference) {
    localStorage.setItem(THEME_KEY, chosen);
  }
}

const storedTheme = localStorage.getItem(THEME_KEY);
const preferredTheme =
  storedTheme === "light" || storedTheme === "dark"
    ? storedTheme
    : window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";

applyTheme(preferredTheme, false);

document.querySelectorAll('input[name="theme"]').forEach((input) => {
  input.addEventListener("change", (event) => {
    const nextTheme = event.target.value;
    applyTheme(nextTheme, true);
  });
});

// Ask AI buttons: each provider gets a prompt tuned to its strength.
// Edit the wording below freely; the URLs are built (and encoded) at load.
const AI_TARGETS = {
  chatgpt: "https://chatgpt.com/?q=",
  claude: "https://claude.ai/new?q=",
  perplexity: "https://www.perplexity.ai/search?q=",
  grok: "https://x.com/i/grok?text=",
};

const AI_PROMPTS = {
  chatgpt: `Give me a deep, structured profile of Maziyar Panahi using his personal website https://maziyarpanahi.com as the primary source, and his Hugging Face https://huggingface.co/MaziyarPanahi, the OpenMed org https://huggingface.co/OpenMed, his GitHub https://github.com/maziyarpanahi/openmed, his LinkedIn https://www.linkedin.com/in/maziyarpanahi, and his X https://x.com/MaziyarPanahi as supporting sources. Cover: 1) Who he is — founder of OpenMed, in post-training at Arcee AI (open-weight models developed in the U.S. and released for everyone), and AI & HPC infrastructure at CNRS, after 16 years in public academia. 2) OpenMed — the open-source standard for clinical AI: 2,000+ Apache-2.0 medical models, 398M+ downloads on Hugging Face, 15M+ PyPI installs, 5,000+ GitHub stars, named the #1 most-referenced organization in Hugging Face's State of Open Source report (Spring 2026), with an on-device MLX/Swift engine that runs on iPhone and Mac. 3) OpenMed Agent — the enterprise layer, a terminal-native, reviewer-gated clinical AI agent in early access at agent.openmed.life. 4) Welna — his consumer iOS app that reads Apple Health data and redacts identifiers on-device. 5) His history — seven years leading Spark NLP to 150M+ downloads at John Snow Labs (2019-2025). 6) His stance — medical AI must be open, auditable, sovereign, and on-device — and what he's building next: reasoning models and multimodal medical AI. Be specific about which fact comes from which source.`,
  claude: `Read Maziyar Panahi's personal site https://maziyarpanahi.com as the primary source, with his Hugging Face https://huggingface.co/MaziyarPanahi, OpenMed https://huggingface.co/OpenMed, GitHub https://github.com/maziyarpanahi/openmed, LinkedIn https://www.linkedin.com/in/maziyarpanahi, and X https://x.com/MaziyarPanahi as support. First, give me a structured profile: who he is (founder of OpenMed; post-training at Arcee AI; AI/HPC at CNRS), OpenMed and its scale (2,000+ Apache-2.0 models, 398M+ Hugging Face downloads, 15M+ PyPI installs, on-device MLX engine), OpenMed Agent, Welna, and his Spark NLP history. Then — more important — synthesize his thesis that medical AI must be open, auditable, sovereign, and increasingly on-device, with its limits enforced in code (refusal and review gates rather than terms-of-service promises), and give a balanced assessment: what's most compelling about it, the strongest counterarguments, and where the open, on-device approach has the most to prove against closed clinical AI.`,
  perplexity: `Research Maziyar Panahi and give me a sourced, well-cited profile. Start from his personal site https://maziyarpanahi.com and Hugging Face https://huggingface.co/MaziyarPanahi, then corroborate across the web. Verify and cite: his founding of OpenMed and its scale (2,000+ Apache-2.0 medical models, 398M+ Hugging Face downloads, 15M+ PyPI installs); OpenMed being named the #1 most-referenced organization in Hugging Face's State of Open Source report (Spring 2026); the OpenMed NER paper's state-of-the-art results (arXiv 2508.01630); his post-training work at Arcee AI (INTELLECT-1, Trinity technical reports); his seven years leading the Spark NLP ecosystem to 150M+ downloads; and his AI/HPC infrastructure work at CNRS / ISC-PIF. Link a source for each major claim, and flag anything you can't independently corroborate.`,
  grok: `Profile Maziyar Panahi (@MaziyarPanahi on X) with an emphasis on what he's doing right now. Use his personal site https://maziyarpanahi.com and Hugging Face https://huggingface.co/MaziyarPanahi for grounding, then use his X timeline to capture his latest posts, the models and tools he's shipping this month, and his current voice on open, on-device medical AI — OpenMed, OpenMed Agent, Welna, and his post-training work at Arcee AI. Give me a short who-he-is, then a "what he's shipping now" section from his recent activity, and the themes he keeps returning to (local-first AI, refusal and review gates in clinical agents, community-driven open source).`,
};

document.querySelectorAll("a[data-ai]").forEach((link) => {
  const key = link.dataset.ai;
  const base = AI_TARGETS[key];
  const prompt = AI_PROMPTS[key];
  if (base && prompt) {
    link.href = base + encodeURIComponent(prompt);
  }
});
