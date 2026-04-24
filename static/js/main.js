// Handle adding food entries via API
document.addEventListener('DOMContentLoaded', () => {
    const addFoodForm = document.getElementById('add-food-form');
    
    if (addFoodForm) {
        addFoodForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = addFoodForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            submitBtn.innerText = 'Logging...';
            submitBtn.disabled = true;

            const data = {
                food_name: document.getElementById('food_name').value,
                calories: document.getElementById('calories').value,
                category: document.getElementById('category').value
            };

            try {
                const response = await fetch('/api/add_food', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    // Quick animation for success
                    submitBtn.innerText = 'Logged!';
                    submitBtn.style.background = '#059669';
                    
                    setTimeout(() => {
                        window.location.reload(); // Reload to show updated data
                    }, 1000);
                } else {
                    alert('Error: ' + result.error);
                    submitBtn.innerText = originalText;
                    submitBtn.disabled = false;
                }
            } catch (error) {
                console.error('Error logging food:', error);
                alert('Failed to connect to server.');
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});
