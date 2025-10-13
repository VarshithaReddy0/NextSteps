// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.querySelector('.filter-card form');

    if (filterForm) {
        // Auto-submit on filter change
        filterForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', function() {
                if (this.name !== 'search') {
                    filterForm.submit();
                }
            });
        });

        // Search with debounce
        const searchInput = filterForm.querySelector('input[name="search"]');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (this.value.length >= 3 || this.value.length === 0) {
                        filterForm.submit();
                    }
                }, 500);
            });
        }
    }

    // Track filter usage
    if (typeof gtag !== 'undefined') {
        document.querySelectorAll('.btn-outline-primary, .btn-outline-warning, .btn-outline-info').forEach(btn => {
            btn.addEventListener('click', function() {
                gtag('event', 'quick_filter_click', {
                    'filter_type': this.textContent.trim()
                });
            });
        });
    }
});