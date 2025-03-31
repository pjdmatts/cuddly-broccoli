// JavaScript for BOM Manager

document.addEventListener('DOMContentLoaded', function() {
    // Add sorting functionality to tables
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
            
            // Add styling to indicate sortable columns
            header.style.cursor = 'pointer';
            header.title = 'Click to sort';
            header.innerHTML += ' <span class="sort-icon">↕️</span>';
        });
    });
});

// Function to sort table
function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Get current sort direction
    const currentDirection = table.getAttribute('data-sort-dir') === 'asc' ? 'desc' : 'asc';
    table.setAttribute('data-sort-dir', currentDirection);
    
    // Sort the rows
    rows.sort((a, b) => {
        const cellA = a.querySelectorAll('td')[column].textContent.trim();
        const cellB = b.querySelectorAll('td')[column].textContent.trim();
        
        // Try to sort numerically if possible
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return currentDirection === 'asc' ? numA - numB : numB - numA;
        }
        
        // Otherwise sort alphabetically
        return currentDirection === 'asc' 
            ? cellA.localeCompare(cellB) 
            : cellB.localeCompare(cellA);
    });
    
    // Reorder the rows in the table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort icons
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        const icon = header.querySelector('.sort-icon');
        if (index === column) {
            icon.textContent = currentDirection === 'asc' ? '↑' : '↓';
        } else {
            icon.textContent = '↕️';
        }
    });
}
