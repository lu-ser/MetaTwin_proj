// dashboard.js - Script per la pagina dashboard

document.addEventListener('DOMContentLoaded', function () {
    // Elementi DOM
    const digitalTwinDropdown = document.getElementById('digital-twin-dropdown');
    const digitalTwinInfo = document.getElementById('digital-twin-info');
    const sensorTypeDropdown = document.getElementById('sensor-type-dropdown');
    const sensorDataGraph = document.getElementById('sensor-data-graph');
    const refreshBtn = document.getElementById('refresh-btn');
    const generateDataBtn = document.getElementById('generate-data-btn');

    let selectedDigitalTwinId = null;
    let selectedSensorType = null;

    // Carica la lista dei digital twins al caricamento della pagina
    loadDigitalTwins();

    // Event listeners
    digitalTwinDropdown.addEventListener('change', onDigitalTwinChange);
    sensorTypeDropdown.addEventListener('change', onSensorTypeChange);
    refreshBtn.addEventListener('click', refreshData);
    generateDataBtn.addEventListener('click', generateRandomData);

    // Funzione per caricare i digital twins
    async function loadDigitalTwins() {
        try {
            const digitalTwins = await apiRequest('/digital-twins/');

            // Pulisci il dropdown prima di aggiungere nuove opzioni
            digitalTwinDropdown.innerHTML = '<option value="" selected disabled>Seleziona un digital twin...</option>';

            // Aggiungi ogni digital twin al dropdown
            digitalTwins.forEach(dt => {
                const option = document.createElement('option');
                option.value = dt.id;
                option.textContent = dt.name;
                digitalTwinDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento dei digital twins:', error);
        }
    }

    // Funzione chiamata quando cambia il digital twin selezionato
    async function onDigitalTwinChange() {
        selectedDigitalTwinId = digitalTwinDropdown.value;

        if (!selectedDigitalTwinId) {
            digitalTwinInfo.innerHTML = '';
            sensorTypeDropdown.innerHTML = '<option value="" selected disabled>Seleziona un tipo di sensore...</option>';
            return;
        }

        try {
            const dt = await apiRequest(`/digital-twins/${selectedDigitalTwinId}`);

            // Visualizza le informazioni del digital twin
            digitalTwinInfo.innerHTML = `
                <p><strong>Nome:</strong> ${dt.name}</p>
                <p><strong>ID Dispositivo:</strong> ${dt.device_id}</p>
                <p><strong>Tipo:</strong> ${dt.device_type}</p>
                <p><strong>Ultimo aggiornamento:</strong> ${formatDateTime(dt.digital_replica?.last_updated || null)}</p>
                
                <h5 class="mt-3">Sensori compatibili:</h5>
                <ul>
                    ${dt.compatible_sensors.map(sensor => `<li>${sensor}</li>`).join('')}
                </ul>
                
                <h5 class="mt-3">Operazioni disponibili:</h5>
                <ul>
                    ${dt.service_layer.available_operations.map(op => `<li>${op}</li>`).join('')}
                </ul>
                
                <h5 class="mt-3">Dashboard disponibili:</h5>
                <ul>
                    ${dt.application_layer.dashboards.map(dash => `<li>${dash}</li>`).join('')}
                </ul>
            `;

            // Popola il dropdown dei sensori
            sensorTypeDropdown.innerHTML = '<option value="" selected disabled>Seleziona un tipo di sensore...</option>';

            const compatibleSensors = dt.compatible_sensors || [];
            const sensorData = dt.digital_replica?.sensor_data || {};

            compatibleSensors.forEach(sensor => {
                const option = document.createElement('option');
                option.value = sensor;

                let label = sensor;
                if (sensorData[sensor]) {
                    label += ` (${sensorData[sensor].length} misurazioni)`;
                }

                option.textContent = label;
                sensorTypeDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli del digital twin:', error);
        }
    }

    // Funzione chiamata quando cambia il tipo di sensore selezionato
    async function onSensorTypeChange() {
        selectedSensorType = sensorTypeDropdown.value;

        if (!selectedDigitalTwinId || !selectedSensorType) {
            // Svuota il grafico
            Plotly.newPlot(sensorDataGraph, []);
            return;
        }

        await updateSensorGraph();
    }

    // Funzione per aggiornare il grafico dei dati del sensore
    async function updateSensorGraph() {
        if (!selectedDigitalTwinId || !selectedSensorType) return;

        try {
            const data = await apiRequest(`/digital-twins/${selectedDigitalTwinId}/data?sensor_type=${selectedSensorType}`);

            if (selectedSensorType in data && data[selectedSensorType].length > 0) {
                const sensorData = data[selectedSensorType];

                // Ordina i dati per timestamp
                sensorData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

                // Estrai i dati per il grafico
                const timestamps = sensorData.map(d => new Date(d.timestamp));
                const values = sensorData.map(d => d.value);
                const unitMeasure = sensorData[0].unit_measure || '';

                // Ottieni dettagli del sensore dall'ontologia
                const sensorDetails = await apiRequest(`/sensors/types/${selectedSensorType}`);

                // Crea traccia principale
                const trace = {
                    x: timestamps,
                    y: values,
                    mode: 'lines+markers',
                    name: selectedSensorType,
                    line: {
                        color: 'rgb(0, 100, 200)',
                        width: 2
                    },
                    marker: {
                        size: 6
                    }
                };

                const layout = {
                    title: `Dati del sensore: ${selectedSensorType}`,
                    xaxis: {
                        title: 'Tempo'
                    },
                    yaxis: {
                        title: `Valore ${unitMeasure ? `(${unitMeasure})` : ''}`
                    },
                    template: 'plotly_white',
                    showlegend: true
                };

                const shapes = [];

                // Aggiungi linee di riferimento per min, max e mean se disponibili
                if (sensorDetails && sensorDetails.details) {
                    const details = sensorDetails.details;

                    if ('min' in details) {
                        shapes.push({
                            type: 'line',
                            x0: timestamps[0],
                            x1: timestamps[timestamps.length - 1],
                            y0: details.min,
                            y1: details.min,
                            line: {
                                color: 'red',
                                width: 1,
                                dash: 'dash'
                            }
                        });
                    }

                    if ('max' in details) {
                        shapes.push({
                            type: 'line',
                            x0: timestamps[0],
                            x1: timestamps[timestamps.length - 1],
                            y0: details.max,
                            y1: details.max,
                            line: {
                                color: 'red',
                                width: 1,
                                dash: 'dash'
                            }
                        });
                    }

                    if ('mean' in details) {
                        shapes.push({
                            type: 'line',
                            x0: timestamps[0],
                            x1: timestamps[timestamps.length - 1],
                            y0: details.mean,
                            y1: details.mean,
                            line: {
                                color: 'green',
                                width: 1,
                                dash: 'dash'
                            }
                        });
                    }
                }

                layout.shapes = shapes;

                Plotly.newPlot(sensorDataGraph, [trace], layout);
            } else {
                // Nessun dato per questo sensore
                Plotly.newPlot(sensorDataGraph, [], {
                    title: `Nessun dato disponibile per il sensore: ${selectedSensorType}`,
                    xaxis: {
                        title: 'Tempo'
                    },
                    yaxis: {
                        title: 'Valore'
                    }
                });
            }
        } catch (error) {
            console.error('Errore nel caricamento dei dati del sensore:', error);
        }
    }

    // Funzione per aggiornare i dati
    async function refreshData() {
        if (selectedDigitalTwinId) {
            await onDigitalTwinChange();

            if (selectedSensorType) {
                await updateSensorGraph();
            }
        } else {
            await loadDigitalTwins();
        }
    }

    // Funzione per generare dati casuali
    async function generateRandomData() {
        if (!selectedDigitalTwinId) {
            showError('Seleziona prima un Digital Twin');
            return;
        }

        try {
            await apiRequest(`/digital-twins/${selectedDigitalTwinId}/generate-data`, 'POST');

            // Aggiorna il grafico se c'è un sensore selezionato
            if (selectedSensorType) {
                await updateSensorGraph();
            }

            // Aggiorna le informazioni del digital twin
            await onDigitalTwinChange();
        } catch (error) {
            console.error('Errore nella generazione dei dati casuali:', error);
        }
    }
});