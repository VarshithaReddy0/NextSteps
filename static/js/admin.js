/**
 * NextSteps - Admin Panel JavaScript
 */

const AdminPanel = {
    init() {
        this.setupFormToggle();
        this.setupConfirmations();
        this.setupAutoSave();
        this.setupTableSearch();
    },

    // Debounce utility function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Setup opportunity type form toggle
    setupFormToggle() {
        const toggleFields = () => {
            const type = document.getElementById('opportunityType')?.value;
            if (!type) return;

            const fullTimeFields = document.getElementById('fullTimeFields');
            const internshipFields = document.getElementById('internshipFields');
            const hackathonFields = document.getElementById('hackathonFields');
            const companyLabel = document.getElementById('companyLabel');
            const roleLabel = document.getElementById('roleLabel');
            const linkLabel = document.getElementById('linkLabel');

            // Hide all fields first
            [fullTimeFields, internshipFields, hackathonFields].forEach(field => {
                if (field) field.style.display = 'none';
            });

            // Show relevant fields and update labels
            const fieldConfigs = {
                full_time: {
                    show: fullTimeFields,
                    labels: {
                        company: 'Company Name',
                        role: 'Role',
                        link: 'Application Link'
                    }
                },
                internship: {
                    show: internshipFields,
                    labels: {
                        company: 'Company Name',
                        role: 'Role',
                        link: 'Application Link'
                    }
                },
                hackathon: {
                    show: hackathonFields,
                    labels: {
                        company: 'Event/Platform Name',
                        role: 'Hackathon Title',
                        link: 'Registration Link'
                    }
                }
            };

            const config = fieldConfigs[type];
            if (config) {
                if (config.show) config.show.style.display = 'block';

                if (companyLabel) companyLabel.textContent = config.labels.company;
                if (roleLabel) roleLabel.textContent = config.labels.role;
                if (linkLabel) linkLabel.textContent = config.labels.link;
            }
        };

        // Initial setup
        toggleFields();

        // Listen for changes
        const typeSelect = document.getElementById('opportunityType');
        if (typeSelect) {
            typeSelect.addEventListener('change', toggleFields);
        }

        // Make function globally available
        window.toggleFields = toggleFields;
    },

    // Setup confirmation dialogs
    setupConfirmations() {
        document.querySelectorAll('[data-confirm]').forEach(element => {
            element.addEventListener('click', (e) => {
                const message = element.dataset.confirm || 'Are you sure?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });

        // Enhanced delete confirmation
        document.querySelectorAll('form[action*="delete"]').forEach(form => {
            form.addEventListener('submit', (e) => {
                const itemName = form.closest('tr')?.querySelector('.fw-semibold')?.textContent || 'this item';
                if (!confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
                    e.preventDefault();
                }
            });
        });
    },

    // Auto-save functionality
    setupAutoSave() {
        const forms = document.querySelectorAll('form[data-autosave]');
        forms.forEach(form => {
            let autoSaveTimeout;
            const fields = form.querySelectorAll('input, textarea, select');

            fields.forEach(field => {
                field.addEventListener('input', () => {
                    clearTimeout(autoSaveTimeout);
                    autoSaveTimeout = setTimeout(() => {
                        this.autoSave(form);
                    }, 2000);
                });
            });
        });
    },

    // Auto-save implementation
    autoSave(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Save to localStorage
        const saveKey = `autosave_${form.id || 'form'}`;
        localStorage.setItem(saveKey, JSON.stringify({
            data,
            timestamp: Date.now()
        }));

        // Show auto-save indicator
        this.showAutoSaveIndicator();
    },

    // Show auto-save indicator
    showAutoSaveIndicator() {
        let indicator = document.querySelector('.autosave-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'autosave-indicator position-fixed bottom-0 end-0 m-3 p-2 bg-success text-white rounded';
            indicator.style.zIndex = '1050';
            document.body.appendChild(indicator);
        }

        indicator.textContent = '✓ Auto-saved';
        indicator.style.display = 'block';

        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    },

    // Table search functionality
    setupTableSearch() {
        const searchInput = document.querySelector('[data-table-search]');
        if (!searchInput) return;

        const table = document.querySelector(searchInput.dataset.tableSearch);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');

        searchInput.addEventListener('input', this.debounce((e) => {
            const searchTerm = e.target.value.toLowerCase();

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const matches = text.includes(searchTerm);
                row.style.display = matches ? '' : 'none';
            });

            // Update row count
            const visibleRows = Array.from(rows).filter(row =>
                row.style.display !== 'none'
            ).length;

            this.updateRowCount(visibleRows, rows.length);
        }, 300));
    },

    // Update row count display
    updateRowCount(visible, total) {
        let countDisplay = document.querySelector('.table-row-count');

        if (!countDisplay) {
            countDisplay = document.createElement('div');
            countDisplay.className = 'table-row-count text-muted small mt-2';
            document.querySelector('.table-responsive')?.appendChild(countDisplay);
        }

        if (visible === total) {
            countDisplay.textContent = `Showing ${total} items`;
        } else {
            countDisplay.textContent = `Showing ${visible} of ${total} items`;
        }
    },

    // Batch operations
    setupBatchOperations() {
        const selectAll = document.querySelector('[data-select-all]');
        const checkboxes = document.querySelectorAll('[data-batch-select]');
        const batchActions = document.querySelector('.batch-actions');

        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.toggleBatchActions();
            });
        }

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.toggleBatchActions();
            });
        });
    },

    // Toggle batch action visibility
    toggleBatchActions() {
        const checked = document.querySelectorAll('[data-batch-select]:checked').length;
        const batchActions = document.querySelector('.batch-actions');

        if (batchActions) {
            batchActions.style.display = checked > 0 ? 'block' : 'none';
        }
    }
};

// Initialize admin panel
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AdminPanel.init());
} else {
    AdminPanel.init();
}

// Export for global access
window.AdminPanel = AdminPanel;