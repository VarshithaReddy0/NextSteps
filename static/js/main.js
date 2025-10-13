// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('NextSteps loaded successfully!');

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add loading state to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-clock me-2"></i>Loading...';

                // Reset after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        }, 5000);
    });

    // Enhanced analytics tracking for apply buttons
    document.querySelectorAll('.btn-apply').forEach(btn => {
        btn.addEventListener('click', function() {
            const jobCard = this.closest('.job-card');
            if (jobCard) {
                const company = jobCard.querySelector('.company-name')?.textContent.trim();
                const role = jobCard.querySelector('.job-title')?.textContent.trim();

                // Track application click
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'job_application', {
                        'company': company,
                        'role': role,
                        'source': 'nextsteps'
                    });
                }
            }
        });
    });

    // Track filter usage
    const filterForm = document.querySelector('.filter-card form');
    if (filterForm) {
        filterForm.addEventListener('submit', function() {
            const formData = new FormData(this);
            const filters = Object.fromEntries(formData.entries());

            if (typeof gtag !== 'undefined') {
                gtag('event', 'filter_used', {
                    'filters': JSON.stringify(filters)
                });
            }
        });
    }
});