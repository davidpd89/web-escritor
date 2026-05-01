// Mobile nav
const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      siteNav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });
}

// FAQ accordion
document.querySelectorAll(".faq-question").forEach((btn) => {
  btn.addEventListener("click", () => {
    const item = btn.closest(".faq-item");
    const answer = item.querySelector(".faq-answer");
    const isOpen = item.classList.toggle("is-open");
    btn.setAttribute("aria-expanded", String(isOpen));
    answer.hidden = !isOpen;
  });
});

// Newsletter form → mailto fallback
const newsletterForm = document.getElementById("newsletter-form");
if (newsletterForm) {
  newsletterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("newsletter-email").value;
    const subject = encodeURIComponent("Lista de lectores — David Porto Díaz");
    const body = encodeURIComponent(
      `Hola,\n\nQuiero apuntarme a la lista de lectores.\n\nMi correo es: ${email}`
    );
    window.location.href = `mailto:davidpd89@gmail.com?subject=${subject}&body=${body}`;
  });
}
