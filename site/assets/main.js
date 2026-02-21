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
