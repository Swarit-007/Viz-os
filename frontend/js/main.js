// Main JavaScript file for VizOS
class VizOS {
    constructor() {
        this.currentAlgorithm = 'fcfs';
        this.currentTab = 'cpu-scheduling';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabSwitching();
        this.setupAlgorithmSelector();
        this.setupSimulationButtons();
        this.setupProcessInput();
        this.addDefaultProcesses();
        this.setupAdvancedEditors();
        this.setupHeaderToolbar();
    }

    setupHeaderToolbar() {
        const themeToggle = document.getElementById('theme-toggle');
        const navToggle = document.getElementById('nav-toggle');
        const helpBtn = document.getElementById('help-btn');

        // Initialize theme from localStorage
        const saved = localStorage.getItem('vizos_theme');
        if (saved === 'light') document.documentElement.classList.add('light');
        this.updateThemeIcon();

        themeToggle?.addEventListener('click', () => {
            document.documentElement.classList.toggle('light');
            const isLight = document.documentElement.classList.contains('light');
            localStorage.setItem('vizos_theme', isLight ? 'light' : 'dark');
            this.updateThemeIcon();
        });

        // keyboard shortcut 't' toggles theme
        window.addEventListener('keydown', (e) => { if (e.key.toLowerCase() === 't') themeToggle?.click(); });

        navToggle?.addEventListener('click', () => {
            const nav = document.querySelector('.nav-tabs');
            if (!nav) return;
            nav.classList.toggle('collapsed');
            localStorage.setItem('vizos_nav_collapsed', nav.classList.contains('collapsed') ? '1' : '0');
        });

        // restore nav collapsed state
        const nav = document.querySelector('.nav-tabs');
        const navCollapsed = localStorage.getItem('vizos_nav_collapsed');
        if (navCollapsed === '1') nav?.classList.add('collapsed');

        helpBtn?.addEventListener('click', () => {
            alert('Tip: Use the toolbar to toggle theme (T), collapse navigation, and access quick help.');
        });
    }

    updateThemeIcon() {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (document.documentElement.classList.contains('light')) {
            icon.className = 'fas fa-moon';
            themeToggle.title = 'Switch to dark theme (T)';
        } else {
            icon.className = 'fas fa-sun';
            themeToggle.title = 'Switch to light theme (T)';
        }
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // Algorithm selector
        document.getElementById('algorithm-select').addEventListener('change', (e) => {
            this.currentAlgorithm = e.target.value;
            this.toggleQuantumInput();
        });

        // Simulation buttons
        document.getElementById('simulate-btn').addEventListener('click', () => {
            this.simulateCPUScheduling();
        });

        document.getElementById('bankers-simulate-btn').addEventListener('click', () => {
            this.simulateBankers();
        });

        document.getElementById('deadlock-simulate-btn').addEventListener('click', () => {
            this.simulateDeadlock();
        });

        document.getElementById('page-replacement-simulate-btn').addEventListener('click', () => {
            this.simulatePageReplacement();
        });

        document.getElementById('memory-allocation-simulate-btn').addEventListener('click', () => {
            this.simulateMemoryAllocation();
        });
    }

    setupAdvancedEditors() {
        // Toggle buttons
        document.getElementById('bankers-toggle-advanced')?.addEventListener('click', () => {
            const adv = document.getElementById('bankers-advanced');
            adv.style.display = adv.style.display === 'none' ? 'block' : 'none';
            if (adv.style.display === 'block') this.renderBankersEditors();
        });
        document.getElementById('deadlock-toggle-advanced')?.addEventListener('click', () => {
            const adv = document.getElementById('deadlock-advanced');
            adv.style.display = adv.style.display === 'none' ? 'block' : 'none';
            if (adv.style.display === 'block') this.renderDeadlockEditors();
        });
        // Re-render editors when counts change
        document.getElementById('bankers-processes')?.addEventListener('change', () => this.renderBankersEditors());
        document.getElementById('bankers-resources')?.addEventListener('change', () => this.renderBankersEditors());
        document.getElementById('deadlock-processes')?.addEventListener('change', () => this.renderDeadlockEditors());
        document.getElementById('deadlock-resources')?.addEventListener('change', () => this.renderDeadlockEditors());
    }

    buildMatrix(rows, cols, containerId, min=0, max=9) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const table = document.createElement('table');
        const tbody = document.createElement('tbody');
        for (let i = 0; i < rows; i++) {
            const tr = document.createElement('tr');
            for (let j = 0; j < cols; j++) {
                const td = document.createElement('td');
                const input = document.createElement('input');
                input.type = 'number';
                input.value = Math.floor(Math.random() * (max - min + 1)) + min;
                input.min = String(min);
                input.max = String(max);
                td.appendChild(input);
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
        table.appendChild(tbody);
        container.innerHTML = '';
        container.appendChild(table);
    }

    buildVector(size, containerId, min=0, max=9) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const table = document.createElement('table');
        const tr = document.createElement('tr');
        for (let i = 0; i < size; i++) {
            const td = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'number';
            input.value = Math.floor(Math.random() * (max - min + 1)) + min;
            input.min = String(min);
            input.max = String(max);
            td.appendChild(input);
            tr.appendChild(td);
        }
        table.appendChild(tr);
        container.innerHTML = '';
        container.appendChild(table);
    }

    renderBankersEditors() {
        const p = parseInt(document.getElementById('bankers-processes').value) || 3;
        const r = parseInt(document.getElementById('bankers-resources').value) || 3;
        if (document.getElementById('bankers-advanced')?.style.display !== 'none') {
            this.buildMatrix(p, r, 'bankers-allocation', 0, 5);
            this.buildMatrix(p, r, 'bankers-max', 0, 7);
            this.buildVector(r, 'bankers-available', 0, 9);
        }
    }

    renderDeadlockEditors() {
        const p = parseInt(document.getElementById('deadlock-processes').value) || 4;
        const r = parseInt(document.getElementById('deadlock-resources').value) || 3;
        if (document.getElementById('deadlock-advanced')?.style.display !== 'none') {
            this.buildMatrix(p, r, 'deadlock-allocation', 0, 2);
            this.buildMatrix(p, r, 'deadlock-request', 0, 2);
            this.buildVector(r, 'deadlock-available', 0, 5);
        }
    }

    readMatrix(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return null;
        const rows = [];
        container.querySelectorAll('tr').forEach(tr => {
            const row = [];
            tr.querySelectorAll('input').forEach(inp => row.push(parseInt(inp.value) || 0));
            rows.push(row);
        });
        return rows.length ? rows : null;
    }

    readVector(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return null;
        const values = [];
        container.querySelectorAll('input').forEach(inp => values.push(parseInt(inp.value) || 0));
        return values.length ? values : null;
    }

    setupTabSwitching() {
        // Initialize first tab as active
        this.switchTab('dashboard');
    }

    setupAlgorithmSelector() {
        // Initialize algorithm selector
        this.currentAlgorithm = document.getElementById('algorithm-select').value;
        this.toggleQuantumInput();
    }

    setupSimulationButtons() {
        // Setup is handled in setupEventListeners
    }

    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;
    }

    toggleQuantumInput() {
        const quantumGroup = document.getElementById('quantum-group');
        if (this.currentAlgorithm === 'roundrobin') {
            quantumGroup.style.display = 'block';
        } else {
            quantumGroup.style.display = 'none';
        }
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('show');
    }

    async simulateCPUScheduling() {
        try {
            this.showLoading();
            
            const processes = this.getProcessData();
            if (processes.length === 0) {
                throw new Error('Please add at least one process');
            }
            
            let result;
            const quantum = document.getElementById('quantum-input').value;

            switch (this.currentAlgorithm) {
                case 'fcfs':
                    result = FCFS.simulate(processes);
                    break;
                case 'sjf':
                    result = SJF.simulate(processes);
                    break;
                case 'priority':
                    result = Priority.simulate(processes);
                    break;
                case 'roundrobin':
                    result = RoundRobin.simulate(processes, parseInt(quantum));
                    break;
                default:
                    throw new Error('Invalid algorithm selected');
            }

            this.displayCPUSchedulingResults(result);
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async simulateBankers() {
        try {
            this.showLoading();
            
            const numProcesses = parseInt(document.getElementById('bankers-processes').value);
            const numResources = parseInt(document.getElementById('bankers-resources').value);
            const advancedOpen = document.getElementById('bankers-advanced')?.style.display === 'block';
            let result;
            if (advancedOpen) {
                const allocation = this.readMatrix('bankers-allocation');
                const max = this.readMatrix('bankers-max');
                const available = this.readVector('bankers-available');
                const response = await fetch('/api/bankers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        num_processes: numProcesses,
                        num_resources: numResources,
                        allocation,
                        max,
                        available
                    })
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                result = await response.json();
                if (result.success === false || result.error) throw new Error(result.error || 'Server error')
            } else {
                // Fallback to local generation
                result = Bankers.simulate(numProcesses, numResources);
            }
            this.displayBankersResults(result);
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async simulateDeadlock() {
        try {
            this.showLoading();
            
            const numProcesses = parseInt(document.getElementById('deadlock-processes').value);
            const numResources = parseInt(document.getElementById('deadlock-resources').value);
            const advancedOpen = document.getElementById('deadlock-advanced')?.style.display === 'block';
            let result;
            if (advancedOpen) {
                const allocation = this.readMatrix('deadlock-allocation');
                const request = this.readMatrix('deadlock-request');
                const available = this.readVector('deadlock-available');
                const response = await fetch('/api/deadlock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        num_processes: numProcesses,
                        num_resources: numResources,
                        allocation,
                        request,
                        available
                    })
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                result = await response.json();
                if (result.success === false || result.error) throw new Error(result.error || 'Server error')
            } else {
                result = Deadlock.simulate(numProcesses, numResources);
            }
            this.displayDeadlockResults(result);
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayCPUSchedulingResults(result) {
        // Display Gantt chart
        this.drawGanttChart(result.ganttChart);
        
        // Display metrics
        document.getElementById('avg-waiting-time').textContent = result.metrics.avgWaitingTime.toFixed(2);
        document.getElementById('avg-turnaround-time').textContent = result.metrics.avgTurnaroundTime.toFixed(2);
        document.getElementById('avg-response-time').textContent = result.metrics.avgResponseTime.toFixed(2);
        document.getElementById('cpu-utilization').textContent = (result.metrics.cpuUtilization * 100).toFixed(1) + '%';

        // Optional: steps and process table
        if (!this.cpuDetailsInited) {
            const resultsSection = document.querySelector('#cpu-scheduling .results-section');
            const details = document.createElement('div');
            details.className = 'results-section';
            details.style.marginTop = '1rem';
            details.innerHTML = `
                <h3>Details</h3>
                <div id="cpu-steps" class="steps-list"></div>
                <div class="matrix-grid" id="cpu-table"></div>
            `;
            resultsSection.parentNode.insertBefore(details, resultsSection.nextSibling);
            this.cpuDetailsInited = true;
        }
        const stepsDiv = document.getElementById('cpu-steps');
        stepsDiv.innerHTML = '';
        (result.steps || []).forEach((s, idx) => {
            const step = document.createElement('div');
            step.className = 'step';
            const info = Object.entries(s).map(([k,v]) => `${k}=${JSON.stringify(v)}`).join(', ');
            step.innerHTML = `<strong>Step ${idx + 1}:</strong> ${info}`;
            stepsDiv.appendChild(step);
        });
        const tableDiv = document.getElementById('cpu-table');
        tableDiv.innerHTML = this.renderMatrices({ Processes: (result.processResults || []).map(p => [p.id, p.arrivalTime, p.burstTime, p.startTime, p.completionTime, p.turnaroundTime, p.waitingTime, p.responseTime]) });
    }

    displayBankersResults(result) {
        // Display RAG visualization
        this.drawRAGChart(result.rag);
        
        // Display safe sequence
        const safeSequenceDiv = document.getElementById('safe-sequence-result');
        if (result.safeSequence.length > 0) {
            safeSequenceDiv.innerHTML = `<strong>Safe Sequence Found:</strong><br>${result.safeSequence.join(' → ')}`;
            safeSequenceDiv.style.borderLeftColor = '#28a745';
        } else {
            safeSequenceDiv.innerHTML = '<strong>No Safe Sequence Found</strong><br>System is in unsafe state';
            safeSequenceDiv.style.borderLeftColor = '#dc3545';
        }

        // Matrices and steps
        const details = document.getElementById('bankers-details');
        details.style.display = 'block';
        const matricesDiv = document.getElementById('bankers-matrices');
        matricesDiv.innerHTML = this.renderMatrices({
            Allocation: result.allocation,
            Max: result.max,
            Need: result.need,
            Available: [result.available]
        });
        const stepsDiv = document.getElementById('bankers-steps');
        stepsDiv.innerHTML = '';
        (result.steps || []).forEach((s, idx) => {
            const step = document.createElement('div');
            step.className = 'step';
            step.innerHTML = `<strong>Step ${idx + 1}:</strong> work=${JSON.stringify(s.work)}${s.chosenProcess ? `, chose ${s.chosenProcess}, released ${JSON.stringify(s.allocationsReleased)}` : ''}`;
            stepsDiv.appendChild(step);
        });
    }

    displayDeadlockResults(result) {
        // Display deadlock detection result
        const deadlockDiv = document.getElementById('deadlock-result');
        if (result.hasDeadlock) {
            deadlockDiv.innerHTML = `<strong>Deadlock Detected!</strong><br>Processes involved: ${result.deadlockedProcesses.join(', ')}`;
            deadlockDiv.style.borderLeftColor = '#dc3545';
        } else {
            deadlockDiv.innerHTML = '<strong>No Deadlock Detected</strong><br>System is safe';
            deadlockDiv.style.borderLeftColor = '#28a745';
        }
        
        // Display wait-for graph
        this.drawWaitForGraph(result.waitForGraph);

        // Matrices and steps
        const details = document.getElementById('deadlock-details');
        details.style.display = 'block';
        const matricesDiv = document.getElementById('deadlock-matrices');
        matricesDiv.innerHTML = this.renderMatrices({
            Allocation: result.allocation,
            Request: result.request,
            Available: [result.available]
        });
        const stepsDiv = document.getElementById('deadlock-steps');
        stepsDiv.innerHTML = '';
        (result.steps || []).forEach((s, idx) => {
            const step = document.createElement('div');
            step.className = 'step';
            const allocated = s.allocated && s.allocated.length ? `, progressed: ${s.allocated.join(', ')}` : '';
            step.innerHTML = `<strong>Iter ${idx + 1}:</strong> work=${JSON.stringify(s.work || [])}${allocated}`;
            stepsDiv.appendChild(step);
        });
    }

    async simulatePageReplacement() {
        try {
            this.showLoading();
            
            const algorithm = document.getElementById('page-replacement-algorithm').value;
            const frames = parseInt(document.getElementById('page-replacement-frames').value) || 3;
            const pageRequestsInput = document.getElementById('page-requests-input').value.trim();
            
            if (!pageRequestsInput) {
                throw new Error('Please enter page requests');
            }
            
            // Parse page requests from space-separated string
            const pageRequests = pageRequestsInput.split(/\s+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            
            if (pageRequests.length === 0) {
                throw new Error('Invalid page requests. Please enter space-separated numbers.');
            }
            
            if (frames < 1) {
                throw new Error('Number of frames must be at least 1');
            }
            
            const response = await fetch('/api/page-replacement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    algorithm: algorithm,
                    frames: frames,
                    page_requests: pageRequests
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.displayPageReplacementResults(result);
            } else {
                throw new Error(result.error || 'Simulation failed');
            }
        } catch (error) {
            console.error('Page Replacement simulation error:', error);
            alert('Error simulating page replacement: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayPageReplacementResults(result) {
        // Display total page faults
        const totalFaultsDiv = document.getElementById('total-page-faults');
        totalFaultsDiv.textContent = result.total_page_faults || result.totalPageFaults || 0;
        
        // Get container and clear it
        const container = document.getElementById('page-replacement-visualization-container');
        container.innerHTML = '';
        container.style.display = 'flex';
        container.style.overflowX = 'auto';
        container.style.gap = '8px';
        
        const frames = result.frames || 3;
        const steps = result.steps || [];
        
        if (steps.length === 0) {
            container.innerHTML = '<p style="color: #fff; padding: 20px;">No steps to display</p>';
            return;
        }
        
        // Create a column for each step
        steps.forEach((step, stepIndex) => {
            // Create card-like container for each step
            const stepCard = document.createElement('div');
            stepCard.style.cssText = `
                display: flex;
                flex-direction: column;
                min-width: 70px;
                background-color: #2a2d35;
                border-radius: 6px;
                padding: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            `;
            
            // Requested Page Cell (Top)
            const requestedPageCell = document.createElement('div');
            requestedPageCell.textContent = step.requested_page || step.requestedPage;
            requestedPageCell.style.cssText = `
                background-color: #3a3f47;
                color: #ffffff;
                padding: 10px 8px;
                text-align: center;
                font-weight: bold;
                font-size: 1.1em;
                border-radius: 4px;
                margin-bottom: 6px;
                min-height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 1px solid rgba(255, 255, 255, 0.1);
            `;
            stepCard.appendChild(requestedPageCell);
            
            // Memory Frame Cells (Middle)
            const memoryAfter = step.memory_after || step.memoryAfter || [];
            for (let f = 0; f < frames; f++) {
                const frameCell = document.createElement('div');
                frameCell.style.cssText = `
                    padding: 10px 8px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 1.1em;
                    border-radius: 4px;
                    margin-bottom: 6px;
                    min-height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                `;
                
                // Check if frame has content
                if (f < memoryAfter.length && memoryAfter[f] !== null && memoryAfter[f] !== undefined) {
                    frameCell.textContent = memoryAfter[f];
                    frameCell.style.backgroundColor = '#ADD8E6'; // Light blue for filled frames
                    frameCell.style.color = '#000000';
                } else {
                    frameCell.textContent = '';
                    frameCell.style.backgroundColor = '#3a3f47'; // Dark gray for empty frames
                    frameCell.style.color = '#ffffff';
                }
                
                stepCard.appendChild(frameCell);
            }
            
            // Hit/Miss Cell (Bottom)
            const hitMissCell = document.createElement('div');
            const isFault = step.page_fault || step.pageFault;
            hitMissCell.textContent = isFault ? 'Miss' : 'Hit';
            hitMissCell.style.cssText = `
                background-color: #3a3f47;
                color: ${isFault ? '#ff6b6b' : '#51cf66'};
                padding: 10px 8px;
                text-align: center;
                font-weight: bold;
                font-size: 1em;
                border-radius: 4px;
                margin-top: 2px;
                min-height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 1px solid rgba(255, 255, 255, 0.1);
            `;
            stepCard.appendChild(hitMissCell);
            
            container.appendChild(stepCard);
        });
    }

    async simulateMemoryAllocation() {
        try {
            this.showLoading();
            
            const algorithm = document.getElementById('memory-allocation-algorithm').value;
            const blocksInput = document.getElementById('memory-blocks-input').value.trim();
            const processesInput = document.getElementById('process-memory-input').value.trim();
            
            if (!blocksInput) {
                throw new Error('Please enter memory blocks');
            }
            
            if (!processesInput) {
                throw new Error('Please enter process memory requirements');
            }
            
            // Parse blocks and processes from space-separated strings
            const blocks = blocksInput.split(/\s+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            const processes = processesInput.split(/\s+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            
            if (blocks.length === 0) {
                throw new Error('Invalid memory blocks. Please enter space-separated numbers.');
            }
            
            if (processes.length === 0) {
                throw new Error('Invalid process memory requirements. Please enter space-separated numbers.');
            }
            
            const response = await fetch('/api/memory-allocation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy: algorithm,
                    blocks: blocks,
                    processes: processes
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.displayMemoryAllocationResults(result);
            } else {
                throw new Error(result.error || 'Simulation failed');
            }
        } catch (error) {
            console.error('Memory Allocation simulation error:', error);
            alert('Error simulating memory allocation: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayMemoryAllocationResults(result) {
        // Display allocation results in a table format
        const resultsContainer = document.getElementById('allocation-results-container');
        resultsContainer.innerHTML = '';
        
        const resultsWrapper = document.createElement('div');
        resultsWrapper.style.cssText = `
            background-color: #2a2d35;
            border-radius: 6px;
            padding: 1.5rem;
            margin-top: 1rem;
        `;
        
        const title = document.createElement('h4');
        title.textContent = `Allocation Results (${result.strategy.toUpperCase()} FIT)`;
        title.style.cssText = `
            color: #ffffff;
            margin-bottom: 1rem;
            font-size: 1.2em;
        `;
        resultsWrapper.appendChild(title);
        
        // Create table for allocation results
        const resultsTable = document.createElement('table');
        resultsTable.style.cssText = `
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
        `;
        
        // Header row
        const headerRow = document.createElement('tr');
        headerRow.style.backgroundColor = '#3a3f47';
        
        const processHeader = document.createElement('th');
        processHeader.textContent = 'Process ID';
        processHeader.style.cssText = `
            padding: 12px;
            text-align: left;
            color: #ffffff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: bold;
        `;
        headerRow.appendChild(processHeader);
        
        const blockHeader = document.createElement('th');
        blockHeader.textContent = 'Allocated Block';
        blockHeader.style.cssText = `
            padding: 12px;
            text-align: left;
            color: #ffffff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: bold;
        `;
        headerRow.appendChild(blockHeader);
        
        resultsTable.appendChild(headerRow);
        
        // Data rows
        (result.allocation || []).forEach((alloc) => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
            
            const processCell = document.createElement('td');
            processCell.textContent = alloc.process;
            processCell.style.cssText = `
                padding: 12px;
                color: #ffffff;
            `;
            row.appendChild(processCell);
            
            const blockCell = document.createElement('td');
            if (alloc.block !== null && alloc.block !== undefined) {
                blockCell.textContent = alloc.block;
                blockCell.style.color = '#51cf66'; // Green for successful allocation
            } else {
                blockCell.textContent = 'no free block available';
                blockCell.style.color = '#ff6b6b'; // Red for failed allocation
            }
            blockCell.style.cssText = `
                padding: 12px;
                font-weight: bold;
            `;
            row.appendChild(blockCell);
            
            resultsTable.appendChild(row);
        });
        
        resultsWrapper.appendChild(resultsTable);
        resultsContainer.appendChild(resultsWrapper);
        
        // Add visual block representation
        this.displayMemoryBlockVisualization(result, resultsContainer);
        
        // Display step-by-step allocation in a table
        const stepsContainer = document.getElementById('allocation-steps-container');
        stepsContainer.innerHTML = '';
        
        if (result.steps && result.steps.length > 0) {
            const stepsWrapper = document.createElement('div');
            stepsWrapper.style.cssText = `
                background-color: #2a2d35;
                border-radius: 6px;
                padding: 1.5rem;
                margin-top: 1rem;
            `;
            
            const stepsTitle = document.createElement('h4');
            stepsTitle.textContent = 'Step-by-Step Allocation';
            stepsTitle.style.cssText = `
                color: #ffffff;
                margin-bottom: 1rem;
                font-size: 1.2em;
            `;
            stepsWrapper.appendChild(stepsTitle);
            
            // Create table for step-by-step allocation
            const stepsTable = document.createElement('table');
            stepsTable.style.cssText = `
                width: 100%;
                border-collapse: collapse;
                margin-top: 0.5rem;
            `;
            
            // Header row
            const stepsHeaderRow = document.createElement('tr');
            stepsHeaderRow.style.backgroundColor = '#3a3f47';
            
            const stepNumHeader = document.createElement('th');
            stepNumHeader.textContent = 'Step';
            stepNumHeader.style.cssText = `
                padding: 12px;
                text-align: left;
                color: #ffffff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: bold;
            `;
            stepsHeaderRow.appendChild(stepNumHeader);
            
            const processHeader = document.createElement('th');
            processHeader.textContent = 'Process';
            processHeader.style.cssText = `
                padding: 12px;
                text-align: left;
                color: #ffffff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: bold;
            `;
            stepsHeaderRow.appendChild(processHeader);
            
            const allocatedBlockHeader = document.createElement('th');
            allocatedBlockHeader.textContent = 'Allocated Block';
            allocatedBlockHeader.style.cssText = `
                padding: 12px;
                text-align: left;
                color: #ffffff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: bold;
            `;
            stepsHeaderRow.appendChild(allocatedBlockHeader);
            
            const remainingHeader = document.createElement('th');
            remainingHeader.textContent = 'Remaining Space';
            remainingHeader.style.cssText = `
                padding: 12px;
                text-align: left;
                color: #ffffff;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: bold;
            `;
            stepsHeaderRow.appendChild(remainingHeader);
            
            stepsTable.appendChild(stepsHeaderRow);
            
            // Data rows
            (result.steps || []).forEach((step, idx) => {
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
                
                // Step number
                const stepCell = document.createElement('td');
                stepCell.textContent = step.process_index || (idx + 1);
                stepCell.style.cssText = `
                    padding: 12px;
                    color: #ffffff;
                    font-weight: bold;
                `;
                row.appendChild(stepCell);
                
                // Process
                const processCell = document.createElement('td');
                processCell.textContent = step.process;
                processCell.style.cssText = `
                    padding: 12px;
                    color: #ffffff;
                `;
                row.appendChild(processCell);
                
                // Allocated Block
                const blockCell = document.createElement('td');
                if (step.block !== null && step.block !== undefined) {
                    blockCell.textContent = step.block;
                    blockCell.style.color = '#51cf66'; // Green for successful allocation
                } else {
                    blockCell.textContent = 'no free block available';
                    blockCell.style.color = '#ff6b6b'; // Red for failed allocation
                }
                blockCell.style.cssText = `
                    padding: 12px;
                    font-weight: bold;
                `;
                row.appendChild(blockCell);
                
                // Remaining Space (extract from description or calculate)
                const remainingCell = document.createElement('td');
                if (step.description) {
                    // Extract remaining space from description like "Process 212 allocated to block 2 (remaining: 288)"
                    const match = step.description.match(/remaining:\s*(\d+)/);
                    if (match) {
                        remainingCell.textContent = match[1];
                        remainingCell.style.color = '#51cf66';
                    } else {
                        remainingCell.textContent = step.status === 'allocated' ? '-' : 'N/A';
                        remainingCell.style.color = '#ffffff';
                    }
                } else {
                    remainingCell.textContent = step.status === 'allocated' ? '-' : 'N/A';
                    remainingCell.style.color = '#ffffff';
                }
                remainingCell.style.cssText = `
                    padding: 12px;
                    color: #51cf66;
                `;
                row.appendChild(remainingCell);
                
                stepsTable.appendChild(row);
            });
            
            stepsWrapper.appendChild(stepsTable);
            stepsContainer.appendChild(stepsWrapper);
        }
        
        // Display final block status
        const blockStatusContainer = document.getElementById('block-status-container');
        blockStatusContainer.innerHTML = '';
        
        if (result.final_block_status && result.final_block_status.length > 0) {
            const statusTable = document.createElement('table');
            statusTable.style.cssText = `
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
                background-color: #2a2d35;
                border-radius: 6px;
                overflow: hidden;
            `;
            
            // Header row
            const statusHeaderRow = document.createElement('tr');
            statusHeaderRow.style.backgroundColor = '#3a3f47';
            
            const headers = ['Block Number', 'Block Size', 'Allocated', 'Remaining', 'Status'];
            headers.forEach(headerText => {
                const header = document.createElement('th');
                header.textContent = headerText;
                header.style.cssText = `
                    padding: 12px;
                    text-align: left;
                    color: #ffffff;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                `;
                statusHeaderRow.appendChild(header);
            });
            
            statusTable.appendChild(statusHeaderRow);
            
            // Data rows
            (result.final_block_status || []).forEach((block, idx) => {
                const row = document.createElement('tr');
                row.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
                
                const cells = [
                    block.block_number || (idx + 1),
                    block.size,
                    block.allocated || 0,
                    block.remaining || block.size,
                    block.is_free ? 'Free' : 'Partially Allocated'
                ];
                
                cells.forEach((cellText, cellIdx) => {
                    const cell = document.createElement('td');
                    cell.textContent = cellText;
                    cell.style.cssText = `
                        padding: 12px;
                        color: #ffffff;
                    `;
                    
                    if (cellIdx === 4) { // Status column
                        cell.style.color = block.is_free ? '#51cf66' : '#ffa726';
                        cell.style.fontWeight = 'bold';
                    }
                    
                    row.appendChild(cell);
                });
                
                statusTable.appendChild(row);
            });
            
            blockStatusContainer.appendChild(statusTable);
        }
    }

    displayMemoryBlockVisualization(result, container) {
        // Create a mapping of processes allocated to each block
        const blockProcessMap = {};
        (result.allocation || []).forEach((alloc, idx) => {
            if (alloc.block !== null && alloc.block !== undefined) {
                if (!blockProcessMap[alloc.block]) {
                    blockProcessMap[alloc.block] = [];
                }
                blockProcessMap[alloc.block].push({
                    process: alloc.process,
                    processIndex: idx + 1
                });
            }
        });

        // Create visualization container
        const vizWrapper = document.createElement('div');
        vizWrapper.style.cssText = `
            background: rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 2rem;
            margin-top: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.15);
        `;

        const vizTitle = document.createElement('h4');
        vizTitle.textContent = 'Memory Block Visualization';
        vizTitle.style.cssText = `
            color: #ffffff;
            margin-bottom: 1.5rem;
            font-size: 1.3em;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        `;
        vizWrapper.appendChild(vizTitle);

        // Get block status data or create from blocks array
        const blockStatuses = result.final_block_status || [];
        const blocks = result.blocks || [];

        // Create visualization for each block
        blocks.forEach((blockSize, blockIndex) => {
            const blockNumber = blockIndex + 1;
            const blockStatus = blockStatuses[blockIndex] || {
                block_number: blockNumber,
                size: blockSize,
                allocated: 0,
                remaining: blockSize,
                is_free: true
            };

            // Block container
            const blockContainer = document.createElement('div');
            blockContainer.style.cssText = `
                margin-bottom: 2rem;
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            `;

            // Block header with number and size
            const blockHeader = document.createElement('div');
            blockHeader.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            `;

            const blockLabel = document.createElement('div');
            blockLabel.textContent = `Block ${blockNumber}`;
            blockLabel.style.cssText = `
                font-weight: 700;
                font-size: 1.1em;
                color: #ffffff;
            `;

            const blockSizeLabel = document.createElement('div');
            blockSizeLabel.textContent = `Size: ${blockStatus.size} KB`;
            blockSizeLabel.style.cssText = `
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.95em;
            `;

            blockHeader.appendChild(blockLabel);
            blockHeader.appendChild(blockSizeLabel);
            blockContainer.appendChild(blockHeader);

            // Visual block bar
            const blockBarContainer = document.createElement('div');
            blockBarContainer.style.cssText = `
                position: relative;
                width: 100%;
                height: 60px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                overflow: hidden;
                border: 2px solid rgba(255, 255, 255, 0.2);
                margin-bottom: 1rem;
            `;

            const allocatedPercent = blockStatus.size > 0 
                ? (blockStatus.allocated / blockStatus.size) * 100 
                : 0;
            const remainingPercent = 100 - allocatedPercent;

            // Allocated portion
            if (allocatedPercent > 0) {
                const allocatedBar = document.createElement('div');
                allocatedBar.style.cssText = `
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: ${allocatedPercent}%;
                    height: 100%;
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ffffff;
                    font-weight: 700;
                    font-size: 0.9em;
                    border-right: 2px solid rgba(255, 255, 255, 0.3);
                    transition: width 0.5s ease;
                `;
                allocatedBar.textContent = allocatedPercent > 15 
                    ? `${blockStatus.allocated} KB` 
                    : '';
                blockBarContainer.appendChild(allocatedBar);
            }

            // Remaining portion
            if (remainingPercent > 0) {
                const remainingBar = document.createElement('div');
                remainingBar.style.cssText = `
                    position: absolute;
                    right: 0;
                    top: 0;
                    width: ${remainingPercent}%;
                    height: 100%;
                    background: rgba(255, 255, 255, 0.08);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: rgba(255, 255, 255, 0.6);
                    font-weight: 600;
                    font-size: 0.9em;
                    transition: width 0.5s ease;
                `;
                remainingBar.textContent = remainingPercent > 15 
                    ? `${blockStatus.remaining} KB` 
                    : '';
                blockBarContainer.appendChild(remainingBar);
            }

            // Center label for small allocations
            if (allocatedPercent > 0 && allocatedPercent <= 15) {
                const centerLabel = document.createElement('div');
                centerLabel.textContent = `${blockStatus.allocated} KB`;
                centerLabel.style.cssText = `
                    position: absolute;
                    left: ${allocatedPercent / 2}%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    color: #ffffff;
                    font-weight: 700;
                    font-size: 0.85em;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
                    pointer-events: none;
                    z-index: 10;
                `;
                blockBarContainer.appendChild(centerLabel);
            }

            blockContainer.appendChild(blockBarContainer);

            // Process allocation info
            const processInfo = document.createElement('div');
            processInfo.style.cssText = `
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.5rem;
            `;

            const allocatedProcesses = blockProcessMap[blockNumber] || [];
            if (allocatedProcesses.length > 0) {
                const processesLabel = document.createElement('span');
                processesLabel.textContent = 'Processes: ';
                processesLabel.style.cssText = `
                    color: rgba(255, 255, 255, 0.7);
                    font-weight: 600;
                `;
                processInfo.appendChild(processesLabel);

                allocatedProcesses.forEach((proc, idx) => {
                    const processBadge = document.createElement('span');
                    processBadge.textContent = `${proc.process}`;
                    processBadge.title = `Process ${proc.processIndex} (${proc.process} KB)`;
                    processBadge.style.cssText = `
                        background: linear-gradient(135deg, rgba(102, 126, 234, 0.6), rgba(118, 75, 162, 0.6));
                        color: #ffffff;
                        padding: 0.4rem 0.8rem;
                        border-radius: 6px;
                        font-size: 0.9em;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        cursor: help;
                        transition: transform 0.2s ease;
                    `;
                    processBadge.addEventListener('mouseenter', () => {
                        processBadge.style.transform = 'scale(1.05)';
                    });
                    processBadge.addEventListener('mouseleave', () => {
                        processBadge.style.transform = 'scale(1)';
                    });
                    processInfo.appendChild(processBadge);
                });
            } else {
                const freeLabel = document.createElement('span');
                freeLabel.textContent = 'Free (Not Allocated)';
                freeLabel.style.cssText = `
                    color: rgba(255, 255, 255, 0.5);
                    font-style: italic;
                `;
                processInfo.appendChild(freeLabel);
            }

            blockContainer.appendChild(processInfo);

            // Stats row
            const statsRow = document.createElement('div');
            statsRow.style.cssText = `
                display: flex;
                gap: 1.5rem;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            `;

            const stats = [
                { label: 'Allocated', value: `${blockStatus.allocated} KB`, color: '#667eea' },
                { label: 'Remaining', value: `${blockStatus.remaining} KB`, color: '#51cf66' },
                { label: 'Status', value: blockStatus.is_free ? 'Free' : 'Partially Allocated', color: blockStatus.is_free ? '#51cf66' : '#ffa726' }
            ];

            stats.forEach(stat => {
                const statItem = document.createElement('div');
                statItem.style.cssText = `
                    display: flex;
                    flex-direction: column;
                    gap: 0.3rem;
                `;

                const statLabel = document.createElement('span');
                statLabel.textContent = stat.label;
                statLabel.style.cssText = `
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 0.85em;
                `;

                const statValue = document.createElement('span');
                statValue.textContent = stat.value;
                statValue.style.cssText = `
                    color: ${stat.color};
                    font-weight: 700;
                    font-size: 1em;
                `;

                statItem.appendChild(statLabel);
                statItem.appendChild(statValue);
                statsRow.appendChild(statItem);
            });

            blockContainer.appendChild(statsRow);
            vizWrapper.appendChild(blockContainer);
        });

        container.appendChild(vizWrapper);
    }

    renderMatrices(namedMatrices) {
        const wrap = document.createElement('div');
        wrap.className = 'matrix-grid';
        Object.entries(namedMatrices).forEach(([name, matrix]) => {
            const card = document.createElement('div');
            card.className = 'matrix-card';
            const title = document.createElement('h4');
            title.textContent = name;
            const table = document.createElement('table');
            (matrix || []).forEach(row => {
                const tr = document.createElement('tr');
                row.forEach(val => {
                    const td = document.createElement('td');
                    td.textContent = String(val);
                    tr.appendChild(td);
                });
                table.appendChild(tr);
            });
            card.appendChild(title);
            card.appendChild(table);
            wrap.appendChild(card);
        });
        return wrap.outerHTML;
    }

    drawGanttChart(ganttData) {
        const canvas = document.getElementById('gantt-chart');
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Set up dimensions
        const barHeight = 40;
        const startY = (height - barHeight) / 2;
        const timeUnit = 20; // pixels per time unit
        
        // Draw background
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);
        
        // Draw time axis
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(50, height - 30);
        ctx.lineTo(width - 20, height - 30);
        ctx.stroke();
        
        // Draw time labels
        ctx.fillStyle = '#333';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        for (let i = 0; i <= ganttData.totalTime; i++) {
            const x = 50 + i * timeUnit;
            ctx.fillText(i.toString(), x, height - 10);
        }
        
        // Draw process bars
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];
        let currentX = 50;
        
        ganttData.processes.forEach((process, index) => {
            const barWidth = process.duration * timeUnit;
            const color = colors[index % colors.length];
            
            // Draw process bar
            ctx.fillStyle = color;
            ctx.fillRect(currentX, startY, barWidth, barHeight);
            
            // Draw process label
            ctx.fillStyle = 'white';
            ctx.font = 'bold 12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(process.name, currentX + barWidth/2, startY + barHeight/2 + 4);
            
            // Draw start time
            ctx.fillStyle = '#333';
            ctx.font = '10px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(process.startTime.toString(), currentX, startY - 5);
            
            currentX += barWidth;
        });
        
        // Draw legend
        ctx.font = '12px Inter';
        ctx.textAlign = 'left';
        let legendX = 50;
        let legendY = 20;
        
        ganttData.processes.forEach((process, index) => {
            const color = colors[index % colors.length];
            ctx.fillStyle = color;
            ctx.fillRect(legendX, legendY - 10, 15, 15);
            ctx.fillStyle = '#333';
            ctx.fillText(process.name, legendX + 20, legendY);
            legendX += 100;
        });
    }

    drawRAGChart(ragData) {
        const svg = document.getElementById('rag-chart');
        svg.innerHTML = '';
        
        const width = parseInt(svg.getAttribute('width')) || svg.clientWidth || 600;
        const height = parseInt(svg.getAttribute('height')) || svg.clientHeight || 400;
        const centerX = width / 2;
        const centerY = height / 2;
        const nodeRadius = 25;
        const processRadius = Math.max(Math.min(width, height) / 2 - nodeRadius - 50, nodeRadius + 40);
        const resourceRadius = processRadius + 80;
        
        // Store node positions for edge drawing
        const nodePositions = {};
        
        // Define arrow markers
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Allocation arrow (Resource -> Process) - solid line
        const allocMarker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        allocMarker.setAttribute('id', 'arrow-alloc');
        allocMarker.setAttribute('markerWidth', '12');
        allocMarker.setAttribute('markerHeight', '12');
        allocMarker.setAttribute('refX', '9');
        allocMarker.setAttribute('refY', '6');
        allocMarker.setAttribute('orient', 'auto');
        const allocPolygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        allocPolygon.setAttribute('points', '0 0, 12 6, 0 12');
        allocPolygon.setAttribute('fill', '#28a745');
        allocMarker.appendChild(allocPolygon);
        defs.appendChild(allocMarker);
        
        // Request arrow (Process -> Resource) - dashed line
        const reqMarker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        reqMarker.setAttribute('id', 'arrow-request');
        reqMarker.setAttribute('markerWidth', '12');
        reqMarker.setAttribute('markerHeight', '12');
        reqMarker.setAttribute('refX', '9');
        reqMarker.setAttribute('refY', '6');
        reqMarker.setAttribute('orient', 'auto');
        const reqPolygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        reqPolygon.setAttribute('points', '0 0, 12 6, 0 12');
        reqPolygon.setAttribute('fill', '#ffc107');
        reqMarker.appendChild(reqPolygon);
        defs.appendChild(reqMarker);
        
        svg.appendChild(defs);
        
        // Create processes (circles)
        ragData.processes.forEach((process, index) => {
            const angle = (2 * Math.PI * index) / ragData.processes.length;
            const x = centerX + processRadius * Math.cos(angle);
            const y = centerY + processRadius * Math.sin(angle);
            nodePositions[process.name] = { x, y, type: 'process' };
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
            circle.setAttribute('r', nodeRadius);
            circle.setAttribute('fill', '#667eea');
            circle.setAttribute('stroke', '#333');
            circle.setAttribute('stroke-width', '2');
            svg.appendChild(circle);
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y + 5);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '14');
            text.setAttribute('font-weight', 'bold');
            text.textContent = process.name;
            svg.appendChild(text);
        });
        
        // Create resources (rectangles)
        ragData.resources.forEach((resource, index) => {
            const angle = (2 * Math.PI * index) / ragData.resources.length;
            const x = centerX + resourceRadius * Math.cos(angle);
            const y = centerY + resourceRadius * Math.sin(angle);
            nodePositions[resource.name] = { x, y, type: 'resource' };
            
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', x - 25);
            rect.setAttribute('y', y - 18);
            rect.setAttribute('width', 50);
            rect.setAttribute('height', 36);
            rect.setAttribute('fill', '#764ba2');
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', '2');
            svg.appendChild(rect);
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y + 5);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '12');
            text.setAttribute('font-weight', 'bold');
            text.textContent = resource.name;
            svg.appendChild(text);
        });
        
        // Draw edges (draw allocation edges first, then request edges)
        if (ragData.edges && ragData.edges.length > 0) {
            // Draw allocation edges (Resource -> Process) - solid green
            ragData.edges.filter(e => e.type === 'allocation').forEach(edge => {
                const fromPos = nodePositions[edge.from];
                const toPos = nodePositions[edge.to];
                if (!fromPos || !toPos) return;
                
                const dx = toPos.x - fromPos.x;
                const dy = toPos.y - fromPos.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                const offsetX = (dx / distance) * (fromPos.type === 'resource' ? 25 : nodeRadius + 4);
                const offsetY = (dy / distance) * (fromPos.type === 'resource' ? 18 : nodeRadius + 4);
                const toOffsetX = (dx / distance) * (toPos.type === 'process' ? nodeRadius + 4 : 25);
                const toOffsetY = (dy / distance) * (toPos.type === 'process' ? nodeRadius + 4 : 18);
                
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', fromPos.x + offsetX);
                line.setAttribute('y1', fromPos.y + offsetY);
                line.setAttribute('x2', toPos.x - toOffsetX);
                line.setAttribute('y2', toPos.y - toOffsetY);
                line.setAttribute('stroke', '#28a745');
                line.setAttribute('stroke-width', '3');
                line.setAttribute('stroke-linecap', 'round');
                line.setAttribute('marker-end', 'url(#arrow-alloc)');
                svg.appendChild(line);
            });
            
            // Draw request edges (Process -> Resource) - dashed yellow
            ragData.edges.filter(e => e.type === 'request').forEach(edge => {
                const fromPos = nodePositions[edge.from];
                const toPos = nodePositions[edge.to];
                if (!fromPos || !toPos) return;
                
                const dx = toPos.x - fromPos.x;
                const dy = toPos.y - fromPos.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                const offsetX = (dx / distance) * (fromPos.type === 'process' ? nodeRadius + 4 : 25);
                const offsetY = (dy / distance) * (fromPos.type === 'process' ? nodeRadius + 4 : 18);
                const toOffsetX = (dx / distance) * (toPos.type === 'resource' ? 25 : nodeRadius + 4);
                const toOffsetY = (dy / distance) * (toPos.type === 'resource' ? 18 : nodeRadius + 4);
                
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', fromPos.x + offsetX);
                line.setAttribute('y1', fromPos.y + offsetY);
                line.setAttribute('x2', toPos.x - toOffsetX);
                line.setAttribute('y2', toPos.y - toOffsetY);
                line.setAttribute('stroke', '#ffc107');
                line.setAttribute('stroke-width', '2.5');
                line.setAttribute('stroke-dasharray', '5,5');
                line.setAttribute('stroke-linecap', 'round');
                line.setAttribute('marker-end', 'url(#arrow-request)');
                svg.appendChild(line);
            });
        }
    }

    drawWaitForGraph(waitForData) {
        const svg = document.getElementById('wait-for-chart');
        svg.innerHTML = '';
        
        const width = parseInt(svg.getAttribute('width')) || svg.clientWidth || 600;
        const height = parseInt(svg.getAttribute('height')) || svg.clientHeight || 400;
        const centerX = width / 2;
        const centerY = height / 2;
        const nodeRadius = 25;
        const radius = Math.max(Math.min(width, height) / 2 - nodeRadius - 30, nodeRadius + 40);

        // Define arrow marker before drawing edges
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '12');
        marker.setAttribute('markerHeight', '12');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '6');
        marker.setAttribute('orient', 'auto');
        marker.setAttribute('markerUnits', 'strokeWidth');

        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 12 6, 0 12');
        polygon.setAttribute('fill', '#dc3545');
        marker.appendChild(polygon);
        defs.appendChild(marker);
        svg.appendChild(defs);
        
        // Create process nodes
        waitForData.processes.forEach((process, index) => {
            const angle = (2 * Math.PI * index) / waitForData.processes.length;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
            circle.setAttribute('r', nodeRadius);
            circle.setAttribute('fill', process.isDeadlocked ? '#dc3545' : '#28a745');
            circle.setAttribute('stroke', '#333');
            circle.setAttribute('stroke-width', '2');
            svg.appendChild(circle);
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y + 5);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '12');
            text.setAttribute('font-weight', 'bold');
            text.textContent = process.name;
            svg.appendChild(text);
        });
        
        // Draw wait-for edges
        waitForData.edges.forEach(edge => {
            const fromProcess = waitForData.processes[edge.from];
            const toProcess = waitForData.processes[edge.to];
            
            const fromAngle = (2 * Math.PI * edge.from) / waitForData.processes.length;
            const toAngle = (2 * Math.PI * edge.to) / waitForData.processes.length;
            
            const fromX = centerX + radius * Math.cos(fromAngle);
            const fromY = centerY + radius * Math.sin(fromAngle);
            const toX = centerX + radius * Math.cos(toAngle);
            const toY = centerY + radius * Math.sin(toAngle);
            
            const dx = toX - fromX;
            const dy = toY - fromY;
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            const offsetX = (dx / distance) * (nodeRadius + 4);
            const offsetY = (dy / distance) * (nodeRadius + 4);

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('stroke', '#dc3545');
            line.setAttribute('stroke-width', '3');
            line.setAttribute('stroke-linecap', 'round');
            line.setAttribute('marker-end', 'url(#arrowhead)');
            line.setAttribute('x1', fromX + offsetX);
            line.setAttribute('y1', fromY + offsetY);
            line.setAttribute('x2', toX - offsetX);
            line.setAttribute('y2', toY - offsetY);
            svg.appendChild(line);
        });
    }

    setupProcessInput() {
        // Add process button
        document.getElementById('add-process-btn').addEventListener('click', () => {
            this.addProcessInput();
        });
    }

    addDefaultProcesses() {
        // Add 2 default processes
        this.addProcessInput();
        this.addProcessInput();
    }

    addProcessInput() {
        const container = document.getElementById('processes-container');
        const processCount = container.children.length;
        const processId = `P${processCount + 1}`;
        
        const processItem = document.createElement('div');
        processItem.className = 'process-item';
        processItem.innerHTML = `
            <div class="input-field">
                <label>Process ID</label>
                <input type="text" class="process-id" value="${processId}" readonly>
            </div>
            <div class="input-field">
                <label>Arrival Time</label>
                <input type="number" class="arrival-time" value="${processCount}" min="0">
            </div>
            <div class="input-field">
                <label>Burst Time</label>
                <input type="number" class="burst-time" value="${Math.floor(Math.random() * 10) + 1}" min="1">
            </div>
            <div class="input-field">
                <label>Priority</label>
                <input type="number" class="priority" value="${Math.floor(Math.random() * 5) + 1}" min="1">
            </div>
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        container.appendChild(processItem);
        
        // Show empty state if no processes
        this.updateEmptyState();
    }

    updateEmptyState() {
        const container = document.getElementById('processes-container');
        const emptyState = container.querySelector('.empty-state');
        
        if (container.children.length === 0) {
            if (!emptyState) {
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'empty-state';
                emptyDiv.innerHTML = `
                    <i class="fas fa-plus-circle"></i>
                    <p>No processes added. Click "Add Process" to get started.</p>
                `;
                container.appendChild(emptyDiv);
            }
        } else if (emptyState) {
            emptyState.remove();
        }
    }

    getProcessData() {
        const processes = [];
        const processItems = document.querySelectorAll('.process-item');
        
        processItems.forEach((item, index) => {
            const id = item.querySelector('.process-id').value;
            const arrival = parseInt(item.querySelector('.arrival-time').value) || 0;
            const burst = parseInt(item.querySelector('.burst-time').value) || 1;
            const priority = parseInt(item.querySelector('.priority').value) || 1;
            
            if (id && burst > 0) {
                processes.push({
                    id: id,
                    arrival: arrival,
                    burst: burst,
                    priority: priority
                });
            }
        });
        
        return processes;
    }

}

// Global function for dashboard navigation
function switchToTab(tabName) {
    // Remove active class from all tabs and tab buttons
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to selected tab and button
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VizOS();
});
