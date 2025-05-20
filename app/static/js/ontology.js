// ontology.js - Script per la pagina dell'ontologia

document.addEventListener('DOMContentLoaded', function () {
    // Elementi DOM
    const rootClassDropdown = document.getElementById('root-class-dropdown');
    const allClassDropdown = document.getElementById('all-class-dropdown');
    const classDetails = document.getElementById('class-details');
    const ontologyGraph = document.getElementById('ontology-graph');
    const refreshOntologyBtn = document.getElementById('refresh-ontology-btn');

    let selectedClass = null;

    // Carica le liste al caricamento della pagina
    loadRootClasses();
    loadAllClasses();

    // Event listeners
    rootClassDropdown.addEventListener('change', () => {
        selectedClass = rootClassDropdown.value;
        allClassDropdown.value = '';
        updateClassDetails();
    });

    allClassDropdown.addEventListener('change', () => {
        selectedClass = allClassDropdown.value;
        rootClassDropdown.value = '';
        updateClassDetails();
    });

    refreshOntologyBtn.addEventListener('click', () => {
        loadRootClasses();
        loadAllClasses();
    });

    // Funzione per caricare le classi radice
    async function loadRootClasses() {
        try {
            const rootClasses = await apiRequest('/digital-twins/ontology/root-classes');

            // Pulisci il dropdown
            rootClassDropdown.innerHTML = '<option value="" selected disabled>Seleziona una classe radice...</option>';

            // Aggiungi ogni classe radice al dropdown
            rootClasses.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls;
                option.textContent = cls;
                rootClassDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento delle classi radice:', error);
        }
    }

    // Funzione per caricare tutte le classi
    async function loadAllClasses() {
        try {
            const allClasses = await apiRequest('/digital-twins/ontology/classes');

            // Pulisci il dropdown
            allClassDropdown.innerHTML = '<option value="" selected disabled>Seleziona una classe...</option>';

            // Aggiungi ogni classe al dropdown
            allClasses.sort().forEach(cls => {
                const option = document.createElement('option');
                option.value = cls;
                option.textContent = cls;
                allClassDropdown.appendChild(option);
            });
        } catch (error) {
            console.error('Errore nel caricamento di tutte le classi:', error);
        }
    }

    // Funzione per aggiornare i dettagli della classe selezionata
    async function updateClassDetails() {
        if (!selectedClass) {
            classDetails.innerHTML = '<div class="alert alert-info">Seleziona una classe per visualizzarne i dettagli.</div>';
            Plotly.newPlot(ontologyGraph, []);
            return;
        }

        try {
            const classData = await apiRequest(`/digital-twins/ontology/class/${selectedClass}`);

            if (!classData || !classData.details) {
                classDetails.innerHTML = '<div class="alert alert-danger">Impossibile ottenere i dettagli della classe.</div>';
                return;
            }

            const details = classData.details;
            const superclasses = classData.superclasses || [];
            const subclasses = classData.subclasses || [];

            // Mostra i dettagli della classe
            classDetails.innerHTML = `
                <h4>Classe: ${selectedClass}</h4>
                
                <h5 class="mt-3">Dettagli:</h5>
                <ul class="list-group mb-3">
                    <li class="list-group-item">
                        <strong>Unità di misura:</strong> ${details.unitMeasure ? details.unitMeasure.join(', ') : 'N/A'}
                    </li>
                    <li class="list-group-item">
                        <strong>Valore minimo:</strong> ${details.min !== undefined ? details.min : 'N/A'}
                    </li>
                    <li class="list-group-item">
                        <strong>Valore massimo:</strong> ${details.max !== undefined ? details.max : 'N/A'}
                    </li>
                    <li class="list-group-item">
                        <strong>Valore medio:</strong> ${details.mean !== undefined ? details.mean : 'N/A'}
                    </li>
                </ul>
                
                <h5 class="mt-3">Superclassi:</h5>
                ${superclasses.length > 0 ?
                    `<ul class="list-group mb-3">
                        ${superclasses.map(sc => `<li class="list-group-item">${sc}</li>`).join('')}
                    </ul>` :
                    '<p>Nessuna superclasse</p>'
                }
                
                <h5 class="mt-3">Sottoclassi:</h5>
                ${subclasses.length > 0 ?
                    `<ul class="list-group mb-3">
                        ${subclasses.map(sc => `<li class="list-group-item">${sc}</li>`).join('')}
                    </ul>` :
                    '<p>Nessuna sottoclasse</p>'
                }
            `;

            // Crea il grafo delle relazioni
            createGraph(selectedClass, superclasses, subclasses);
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli della classe:', error);
        }
    }

    // Funzione per creare il grafo dell'ontologia
    function createGraph(className, superclasses, subclasses) {
        // Crea un grafo diretto
        const nodes = [];
        const edges = [];

        // Aggiungi il nodo principale
        nodes.push({
            id: className,
            label: className,
            color: 'red'
        });

        // Aggiungi superclassi
        superclasses.forEach(sc => {
            nodes.push({
                id: sc,
                label: sc,
                color: 'blue'
            });

            edges.push({
                from: className,
                to: sc,
                arrows: 'to'
            });
        });

        // Aggiungi sottoclassi
        subclasses.forEach(sc => {
            nodes.push({
                id: sc,
                label: sc,
                color: 'green'
            });

            edges.push({
                from: sc,
                to: className,
                arrows: 'to'
            });
        });

        // Crea il grafo con Plotly
        createNetworkGraph(nodes, edges);
    }

    // Funzione per creare il grafo di rete con Plotly
    function createNetworkGraph(nodes, edges) {
        // Usa un layout spring embedded per calcolare le posizioni dei nodi
        const positions = springEmbedding(nodes, edges);

        // Prepara i dati per Plotly
        const nodeTrace = {
            x: [],
            y: [],
            text: [],
            mode: 'markers+text',
            textposition: 'top center',
            marker: {
                size: 15,
                color: [],
                line: {
                    width: 2
                }
            },
            hoverinfo: 'text'
        };

        nodes.forEach((node, i) => {
            const pos = positions[node.id];
            nodeTrace.x.push(pos.x);
            nodeTrace.y.push(pos.y);
            nodeTrace.text.push(node.label);
            nodeTrace.marker.color.push(node.color);
        });

        const edgeTraces = [];

        edges.forEach(edge => {
            const fromPos = positions[edge.from];
            const toPos = positions[edge.to];

            const edgeTrace = {
                x: [fromPos.x, toPos.x],
                y: [fromPos.y, toPos.y],
                mode: 'lines',
                line: {
                    width: 1,
                    color: '#888'
                },
                hoverinfo: 'none'
            };

            edgeTraces.push(edgeTrace);

            // Aggiungi una freccia alla fine dell'arco
            if (edge.arrows === 'to') {
                const dx = toPos.x - fromPos.x;
                const dy = toPos.y - fromPos.y;
                const len = Math.sqrt(dx * dx + dy * dy);

                if (len > 0) {
                    const nx = dx / len;
                    const ny = dy / len;

                    // Calcola il punto finale dell'arco (prima della freccia)
                    const endX = toPos.x - nx * 10; // 10 = dimensione del nodo
                    const endY = toPos.y - ny * 10;

                    // Calcola i punti della freccia
                    const arrowSize = 5;
                    const angle = Math.PI / 6; // 30 gradi

                    const ax1 = endX - arrowSize * (nx * Math.cos(angle) + ny * Math.sin(angle));
                    const ay1 = endY - arrowSize * (ny * Math.cos(angle) - nx * Math.sin(angle));

                    const ax2 = endX - arrowSize * (nx * Math.cos(angle) - ny * Math.sin(angle));
                    const ay2 = endY - arrowSize * (ny * Math.cos(angle) + nx * Math.sin(angle));

                    const arrowTrace = {
                        x: [ax1, endX, ax2],
                        y: [ay1, endY, ay2],
                        mode: 'lines',
                        line: {
                            width: 1,
                            color: '#888'
                        },
                        fill: 'toself',
                        hoverinfo: 'none'
                    };

                    edgeTraces.push(arrowTrace);
                }
            }
        });

        const data = [...edgeTraces, nodeTrace];

        const layout = {
            title: `Grafo delle relazioni per ${selectedClass}`,
            showlegend: false,
            hovermode: 'closest',
            margin: {
                b: 20,
                l: 5,
                r: 5,
                t: 40
            },
            xaxis: {
                showgrid: false,
                zeroline: false,
                showticklabels: false
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                showticklabels: false
            },
            height: 600
        };

        Plotly.newPlot(ontologyGraph, data, layout);
    }

    // Funzione per calcolare le posizioni dei nodi con un algoritmo spring embedding
    function springEmbedding(nodes, edges) {
        const positions = {};
        const k = 0.1; // Costante di molla
        const iterations = 50; // Numero di iterazioni

        // Inizializza le posizioni casualmente
        nodes.forEach(node => {
            positions[node.id] = {
                x: Math.random() * 2 - 1,
                y: Math.random() * 2 - 1
            };
        });

        // Esegui il layout
        for (let i = 0; i < iterations; i++) {
            // Calcola le forze repulsive tra i nodi
            nodes.forEach(node1 => {
                const force = { x: 0, y: 0 };

                nodes.forEach(node2 => {
                    if (node1.id !== node2.id) {
                        const dx = positions[node1.id].x - positions[node2.id].x;
                        const dy = positions[node1.id].y - positions[node2.id].y;
                        const distance = Math.sqrt(dx * dx + dy * dy) + 0.01; // Evita divisione per zero

                        // Forza repulsiva: inversamente proporzionale alla distanza
                        const repulsive = k / (distance * distance);

                        force.x += dx / distance * repulsive;
                        force.y += dy / distance * repulsive;
                    }
                });

                // Applica la forza
                positions[node1.id].x += force.x;
                positions[node1.id].y += force.y;
            });

            // Calcola le forze attrattive tra i nodi collegati
            edges.forEach(edge => {
                const from = positions[edge.from];
                const to = positions[edge.to];

                const dx = from.x - to.x;
                const dy = from.y - to.y;
                const distance = Math.sqrt(dx * dx + dy * dy) + 0.01;

                // Forza attrattiva: proporzionale alla distanza
                const attractive = distance / k;

                const fx = dx / distance * attractive;
                const fy = dy / distance * attractive;

                // Applica le forze (divise per 2 per distribuirle equamente)
                from.x -= fx / 2;
                from.y -= fy / 2;
                to.x += fx / 2;
                to.y += fy / 2;
            });
        }

        return positions;
    }
});