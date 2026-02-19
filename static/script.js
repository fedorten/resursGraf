let priceChart = null;

async function fetchPrice(resource) {
    try {
        const response = await fetch(`/api/price/${resource}`);
        const data = await response.json();
        
        if (data.price) {
            document.getElementById('currentPrice').textContent = 
                typeof data.price === 'number' ? data.price.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : data.price;
        }
        return data;
    } catch (error) {
        console.error('Error fetching price:', error);
        document.getElementById('currentPrice').textContent = 'Ошибка';
        return null;
    }
}

async function fetchHistory(resource, period = 'all') {
    try {
        const response = await fetch(`/api/history/${resource}/${period}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching history:', error);
        return [];
    }
}

function calculateChange(history) {
    if (!history || history.length < 2) return null;
    
    const latest = history[history.length - 1].price;
    const first = history[0].price;
    const change = ((latest - first) / first) * 100;
    
    const changeEl = document.getElementById('priceChange');
    changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    changeEl.className = change >= 0 ? 'positive' : 'negative';
    
    return change;
}

function renderChart(history, resourceName) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    const labels = history.map(h => h.date);
    const prices = history.map(h => h.price);
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: resourceName,
                data: prices,
                borderColor: '#3b82f6',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a2332',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: '#2d3748',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y.toLocaleString('ru-RU', { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(45, 55, 72, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(45, 55, 72, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

async function loadChart(resource, period = 'all') {
    const history = await fetchHistory(resource, period);
    
    if (history && history.length > 0) {
        renderChart(history, resourceName);
        calculateChange(history);
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    if (typeof resource !== 'undefined') {
        await fetchPrice(resource);
        await loadChart(resource, 'all');
        
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', async function() {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const period = this.dataset.period;
                await loadChart(resource, period);
            });
        });
    }
});
