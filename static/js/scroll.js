document.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);

function revealOnScroll() {
    const reveals = document.querySelectorAll(".reveal");

    reveals.forEach(el => {
        const windowHeight = window.innerHeight;
        const elementTop = el.getBoundingClientRect().top;
        const elementVisible = 100;

        if (elementTop < windowHeight - elementVisible) {
            el.classList.add("active");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {

    const reveals = document.querySelectorAll(".reveal");
    const counters = document.querySelectorAll(".counter");
    let counterStarted = false;

    function revealOnScroll() {
        reveals.forEach(el => {
            const windowHeight = window.innerHeight;
            const elementTop = el.getBoundingClientRect().top;
            const elementVisible = 100;

            if (elementTop < windowHeight - elementVisible) {
                el.classList.add("active");
            }
        });

        startCounterIfVisible();
    }

    function startCounterIfVisible() {
        if (counterStarted) return;

        counters.forEach(counter => {
            const rect = counter.getBoundingClientRect();
            const windowHeight = window.innerHeight;

            if (rect.top < windowHeight - 100) {
                counterStarted = true;
                animateCounter(counter);
            }
        });
    }

    function animateCounter(counter) {
        const target = +counter.getAttribute("data-target");
        let current = 0;
        const increment = target / 200; // Slower increment (denominator increased from 80 to 200)

        function update() {
            current += increment;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(update);
            } else {
                counter.textContent = target;
            }
        }

        update();
    }

    window.addEventListener("scroll", revealOnScroll);
    revealOnScroll(); // run once on load
});

function showSection(sectionId) {

    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // Remove active state from buttons
    document.querySelectorAll('.sidebar button').forEach(button => {
        button.classList.remove('active');
    });

    // Show selected section
    document.getElementById(sectionId).classList.add('active');

    // Activate clicked button
    event.target.classList.add('active');
}

