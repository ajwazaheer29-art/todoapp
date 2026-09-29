document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector("[data-menu-toggle]");
  const nav = document.querySelector("[data-mobile-nav]");
  if (menuButton && nav) {
    menuButton.addEventListener("click", () => {
      const expanded = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!expanded));
      nav.classList.toggle("is-open", !expanded);
    });
  }

  document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const confirmed = window.confirm("Are you sure you want to delete this task?\n\nThis action cannot be undone.");
      if (!confirmed) event.preventDefault();
    });
  });
});
