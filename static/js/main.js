// Served at /static/js/main.js and linked from templates/base.html.
console.log("Lang-Q-t app loaded");

const joinForm = document.getElementById("join-form");
if (joinForm) {
  joinForm.addEventListener("submit", () => {
    const button = joinForm.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = "Getting your ticket…";
  });
}

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (form.matches("form[data-confirm]") && !confirm(form.dataset.confirm)) {
    event.preventDefault();
  }
});