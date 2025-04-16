// Display current date
document.getElementById('date').textContent = new Date().toLocaleString();

// API call example
document.getElementById('apiButton').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/hello');
        const data = await response.text();
        document.getElementById('apiResponse').textContent = data;
    } catch (error) {
        document.getElementById('apiResponse').textContent = 'API call failed';
    }
});