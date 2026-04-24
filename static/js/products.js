// Products Interaction Scripts

/**
 * Toggle between WhatsApp and Email purchase methods
 * @param {string} type - 'whatsapp' or 'email'
 */
function showPurchase(type) {
  const whatsapp = document.getElementById("whatsapp-box");
  const email = document.getElementById("email-box");

  // Scoped strictly to purchase toggle buttons to prevent interference
  const toggleContainer = document.querySelector('.purchase-toggle');
  if (!toggleContainer) return;

  const buttons = toggleContainer.querySelectorAll(".toggle-btn");
  buttons.forEach(btn => btn.classList.remove("active"));

  if (type === "whatsapp") {
    if (whatsapp) whatsapp.classList.add("active");
    if (email) email.classList.remove("active");
    if (buttons[0]) buttons[0].classList.add("active");
  } else {
    if (email) email.classList.add("active");
    if (whatsapp) whatsapp.classList.remove("active");
    if (buttons[1]) buttons[1].classList.add("active");
  }
}
