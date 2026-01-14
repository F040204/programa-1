// Main JavaScript file for Portal de Operaciones

document.addEventListener('DOMContentLoaded', function() {
    console.log('Portal de Operaciones cargado');
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Confirm delete actions
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar esta operación?')) {
                e.preventDefault();
            }
        });
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const depthFrom = form.querySelector('[name="depth_from"]');
            const depthTo = form.querySelector('[name="depth_to"]');
            
            if (depthFrom && depthTo) {
                const from = parseFloat(depthFrom.value);
                const to = parseFloat(depthTo.value);
                
                if (from >= to) {
                    e.preventDefault();
                    alert('La profundidad "Desde" debe ser menor que la profundidad "Hasta"');
                }
            }
        });
    });
});

// Helper function to format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
