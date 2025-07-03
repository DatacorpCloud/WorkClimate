// Worklimate Portal - Main JavaScript

// Esegui quando il documento è pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inizializza i tooltip di Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Fix per i modal di Bootstrap che rimangono scuri e non cliccabili
    // Intercetta l'evento show.bs.modal (prima che il modal venga mostrato)
    document.addEventListener('show.bs.modal', function(event) {
        var modal = event.target;
        
        // Imposta immediatamente le proprietà per rendere il modal interattivo
        modal.style.pointerEvents = 'auto';
        modal.style.zIndex = '1055';
        
        var modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.pointerEvents = 'auto';
            modalDialog.style.zIndex = '1056';
        }
        
        // Imposta un timeout molto breve per assicurarsi che il modal sia interattivo
        setTimeout(function() {
            modal.style.pointerEvents = 'auto';
            
            if (modalDialog) {
                modalDialog.style.pointerEvents = 'auto';
            }
            
            // Assicurati che tutti i pulsanti nel modal siano cliccabili
            var buttons = modal.querySelectorAll('button');
            buttons.forEach(function(btn) {
                btn.style.pointerEvents = 'auto';
                btn.style.zIndex = '1060';
                btn.disabled = false;
            });
        }, 10);
    });
    
    // Assicurati che il modal rimanga interattivo anche dopo essere stato mostrato completamente
    document.addEventListener('shown.bs.modal', function(event) {
        var modal = event.target;
        modal.style.pointerEvents = 'auto';
        modal.style.zIndex = '1055';
        
        var modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.style.pointerEvents = 'auto';
            modalDialog.style.zIndex = '1056';
        }
        
        // Assicurati che tutti i pulsanti nel modal siano cliccabili
        var buttons = modal.querySelectorAll('button');
        buttons.forEach(function(btn) {
            btn.style.pointerEvents = 'auto';
            btn.style.zIndex = '1060';
            btn.disabled = false;
        });
    });
    
    // Chiudi automaticamente gli alert dopo 5 secondi
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            setTimeout(function() {
                bsAlert.close();
            }, 5000);
        });
    }, 500);
    
    // Controlla se siamo nella pagina dei report
    if (window.location.pathname.includes('/reports')) {
        // Funzione per rimuovere i report caricati dalla cache
        function removeCachedReports() {
            const cachedReports = document.querySelectorAll('.cached-report');
            const cachedBanner = document.querySelector('.alert-permanent');
            
            if (cachedReports.length > 0) {
                cachedReports.forEach(report => {
                    report.remove();
                });
            }
            
            if (cachedBanner) {
                cachedBanner.remove();
            }
        }
        
        // Rimuovi i report caricati dalla cache quando arrivano i nuovi dati
        // Utilizziamo MutationObserver per rilevare quando vengono aggiunti nuovi elementi alla pagina
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Controlla se sono stati aggiunti nuovi report dal server
                    const freshReports = document.querySelectorAll('.card.shadow-sm.mb-4:not(.cached-report)');
                    if (freshReports.length > 0) {
                        // Rimuovi i report caricati dalla cache
                        removeCachedReports();
                        // Disconnetti l'observer dopo aver rimosso i report dalla cache
                        observer.disconnect();
                    }
                }
            });
        });
        
        // Avvia l'osservazione del container principale
        const container = document.querySelector('.container');
        if (container) {
            observer.observe(container, { childList: true, subtree: true });
        }
        // Recupera i dati salvati in localStorage
        const savedReportsString = localStorage.getItem('worklimateReports');
        if (savedReportsString) {
            try {
                const savedReports = JSON.parse(savedReportsString);
                
                // Controlla se ci sono clienti senza report visualizzati
                const clientCards = document.querySelectorAll('.card.shadow-sm.mb-4');
                
                // Se non ci sono report visualizzati ma abbiamo dati salvati, mostriamoli
                const alertInfos = document.querySelectorAll('.alert-info');
                let noReportsAvailable = false;
                
                alertInfos.forEach(alert => {
                    if (alert.textContent.includes('Nessun report disponibile')) {
                        noReportsAvailable = true;
                    }
                });
                
                if (clientCards.length === 0 || noReportsAvailable) {
                    console.log('Visualizzazione dei report salvati in attesa del caricamento dal server');
                    
                    // Crea un banner per indicare che stiamo visualizzando dati salvati
                    const container = document.querySelector('.container');
                    const reportSection = document.querySelector('.row.mb-4').nextElementSibling;
                    
                    const cachedBanner = document.createElement('div');
                    cachedBanner.className = 'alert alert-info alert-permanent mb-4';
                    cachedBanner.innerHTML = '<i class="fas fa-info-circle me-1"></i> Visualizzazione dei report salvati. <strong>Sincronizzazione in corso...</strong>';
                    
                    // Inserisci il banner prima della sezione dei report
                    if (reportSection) {
                        container.insertBefore(cachedBanner, reportSection);
                    }
                    
                    // Per ogni cliente nei dati salvati, crea la card del report
                    Object.keys(savedReports).forEach(clientId => {
                        const clientData = savedReports[clientId];
                        
                        // Crea la card del cliente
                        const clientCard = document.createElement('div');
                        clientCard.className = 'card shadow-sm mb-4 cached-report';
                        clientCard.innerHTML = `
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">${clientData.company_name}</h5>
                                <div>
                                    <span class="badge bg-secondary me-2">${clientData.city}</span>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="row" id="reports-${clientId}"></div>
                            </div>
                        `;
                        
                        // Aggiungi la card al container
                        if (reportSection) {
                            container.insertBefore(clientCard, reportSection.nextSibling);
                        } else {
                            container.appendChild(clientCard);
                        }
                        
                        // Aggiungi i report per questo cliente
                        const reportsRow = document.getElementById(`reports-${clientId}`);
                        
                        if (clientData.reports && clientData.reports.length > 0) {
                            clientData.reports.forEach(report => {
                                const reportCol = document.createElement('div');
                                reportCol.className = 'col-md-4 mb-3';
                                
                                // Determina le classi in base al livello di rischio
                                let riskClass = 'border-success';
                                let headerClass = 'bg-success text-white';
                                let icon = '<i class="fas fa-check-circle text-success me-1"></i>';
                                
                                if (report.risk && report.risk.toUpperCase() === 'ALTO') {
                                    riskClass = 'border-danger';
                                    headerClass = 'bg-danger text-white';
                                    icon = '<i class="fas fa-exclamation-triangle text-danger me-1"></i>';
                                } else if (report.risk && report.risk.toUpperCase() === 'MEDIO') {
                                    riskClass = 'border-warning';
                                    headerClass = 'bg-warning';
                                    icon = '<i class="fas fa-exclamation-circle text-warning me-1"></i>';
                                }
                                
                                reportCol.innerHTML = `
                                    <div class="card h-100 ${riskClass}">
                                        <div class="card-header ${headerClass}">
                                            <h6 class="mb-0">${report.day_label}</h6>
                                        </div>
                                        <div class="card-body">
                                            <h5 class="card-title">
                                                ${icon}
                                                Rischio: ${report.risk || 'Non disponibile'}
                                            </h5>
                                            <p class="card-text">${report.description || ''}</p>
                                        </div>
                                        <div class="card-footer text-muted">
                                            <small>Aggiornato: ${report.date}</small>
                                        </div>
                                    </div>
                                `;
                                
                                reportsRow.appendChild(reportCol);
                            });
                        } else {
                            reportsRow.innerHTML = `
                                <div class="alert alert-info mb-0">
                                    <i class="fas fa-info-circle me-1"></i> Nessun report disponibile per questo cliente.
                                </div>
                            `;
                        }
                    });
                }
            } catch (error) {
                console.error('Errore nel parsing dei report salvati:', error);
            }
        }
    }
    
    // Gestione della validazione dei form
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                // Mostra un indicatore di caricamento per i form validi
                var submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    var originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Elaborazione...';
                    submitBtn.disabled = true;
                    
                    // Ripristina il pulsante dopo 10 secondi nel caso in cui la richiesta fallisca
                    setTimeout(function() {
                        if (submitBtn.disabled) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    }, 10000);
                }
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Gestione delle azioni di sincronizzazione meteo
    var syncButtons = document.querySelectorAll('.sync-weather-btn');
    syncButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var originalText = button.innerHTML;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sincronizzazione...';
            button.disabled = true;
            
            // Il form gestirà l'invio effettivo, questo è solo per l'UI
            setTimeout(function() {
                if (button.disabled) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            }, 10000);
        });
    });
    
    // Gestione delle azioni di invio notifiche
    var notifyButtons = document.querySelectorAll('.notify-btn');
    notifyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var originalText = button.innerHTML;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Invio...';
            button.disabled = true;
            
            // Il form gestirà l'invio effettivo, questo è solo per l'UI
            setTimeout(function() {
                if (button.disabled) {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            }, 10000);
        });
    });
});

// Funzione per confermare le azioni distruttive
function confirmAction(message) {
    return confirm(message || 'Sei sicuro di voler procedere?');
}

// Funzione per formattare le date
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}