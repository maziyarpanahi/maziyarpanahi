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
  chatgpt: `Give me a deep, structured profile of Maziyar Panahi using his personal website https://maziyarpanahi.com as the primary source, and his Hugging Face https://huggingface.co/MaziyarPanahi, the OpenMed org https://huggingface.co/OpenMed, his LinkedIn https://www.linkedin.com/in/maziyar-panahi/, and his X https://x.com/MaziyarPanahi as supporting sources. Cover: 1) Who he is — 16+ years across public research and enterprise, and his conviction that medical AI must be open, auditable, sovereign, and deployable inside a hospital's own walls. 2) OpenMed — what it is, why he founded it, its scale (hundreds of Apache-2.0 medical models, 1M+ PyPI downloads), and being named the #1 most-referenced organization in Hugging Face's State of Open Source report (Spring 2026). 3) His healthcare NLP/LLM track record — leading the Spark NLP ecosystem (150M+ downloads, 100k+ pipelines), clinical NER, de-identification, and PII redaction. 4) OpenMed Agent — his terminal-native, reviewer-gated clinical AI agent with on-device PII redaction that runs on iPhone. 5) His research and infrastructure work at CNRS/ISC-PIF. 6) His stance and what he's building next. Be specific about which fact comes from which source.`,
  claude: `Read Maziyar Panahi's personal site https://maziyarpanahi.com as the primary source, with his Hugging Face https://huggingface.co/MaziyarPanahi, OpenMed https://huggingface.co/OpenMed, LinkedIn https://www.linkedin.com/in/maziyar-panahi/, and X https://x.com/MaziyarPanahi as support. First, give me a structured profile: who he is, OpenMed and why he founded it, his Spark NLP and healthcare-NLP track record, OpenMed Agent, and his CNRS/ISC-PIF research. Then — more important — synthesize his thesis that medical AI must be open, auditable, sovereign, and deployable on-prem, and give a balanced assessment: what's most compelling about it, the strongest counterarguments, and where the open/sovereign approach has the most to prove against closed clinical AI.`,
  perplexity: `Research Maziyar Panahi and give me a sourced, well-cited profile. Start from his personal site https://maziyarpanahi.com and Hugging Face https://huggingface.co/MaziyarPanahi, then corroborate across the web. Verify and cite: his founding of OpenMed and its open-source medical models; OpenMed being named the #1 most-referenced organization in Hugging Face's State of Open Source report (Spring 2026); his leadership of the Spark NLP ecosystem and its adoption numbers; his research papers and Google Scholar record; and his work at CNRS / ISC-PIF. Link a source for each major claim, and flag anything you can't independently corroborate.`,
  grok: `Profile Maziyar Panahi (@MaziyarPanahi on X) with an emphasis on what he's doing right now. Use his personal site https://maziyarpanahi.com and Hugging Face https://huggingface.co/MaziyarPanahi for grounding, then use his X timeline to capture his latest posts, the models and tools he's shipping this month, the conversations he's part of, and his current voice on open, sovereign medical AI and OpenMed. Give me a short who-he-is, then a "what he's shipping now" section from his recent activity, and the themes he keeps returning to.`,
};

document.querySelectorAll("a[data-ai]").forEach((link) => {
  const key = link.dataset.ai;
  const base = AI_TARGETS[key];
  const prompt = AI_PROMPTS[key];
  if (base && prompt) {
    link.href = base + encodeURIComponent(prompt);
  }
});
