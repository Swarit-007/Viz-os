# VizOS - Interactive OS Simulation Tool

A comprehensive full-stack web application for visualizing and simulating various operating system algorithms including CPU scheduling, Banker's algorithm, and deadlock detection.

## 🚀 Features

### CPU Scheduling Algorithms
- **First Come First Serve (FCFS)** - Processes executed in arrival order
- **Shortest Job First (SJF)** - Processes with shortest burst time executed first
- **Priority Scheduling** - Processes executed based on priority levels
- **Round Robin** - Processes executed in time slices with configurable quantum

### Deadlock Management
- **Banker's Algorithm** - Deadlock avoidance with resource allocation visualization
- **Deadlock Detection** - Detect and visualize deadlocks in resource allocation

### Visualizations
- Interactive Gantt charts for CPU scheduling
- Resource Allocation Graph (RAG) visualization
- Wait-for graph for deadlock detection
- Performance metrics and statistics

## 🏗️ Project Structure

```
VizOS/
├── frontend/
│   ├── index.html          # Main dashboard
│   ├── styles.css          # Modern CSS styling
│   └── js/
│       ├── main.js         # Main application logic
│       ├── fcfs.js         # FCFS algorithm
│       ├── sjf.js          # SJF algorithm
│       ├── priority.js     # Priority scheduling
│       ├── roundrobin.js   # Round Robin algorithm
│       ├── bankers.js      # Banker's algorithm
│       └── deadlock.js     # Deadlock detection
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── modules/
│       ├── fcfs_module.py
│       ├── sjf_module.py
│       ├── priority_module.py
│       ├── roundrobin_module.py
│       ├── bankers_module.py
│       └── deadlock_module.py
└── docs/
    └── README.md           # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Flask server:**
   ```bash
   python app.py
   ```

   The API server will be available at `http://localhost:5000`

### Frontend Setup

1. **Open the frontend:**
   - Simply open `frontend/index.html` in your web browser
   - Or serve it using a local web server:
     ```bash
     # Using Python's built-in server
     cd frontend
     python -m http.server 8000
     ```
   - Then visit `http://localhost:8000`

## 🎯 Usage

### CPU Scheduling Simulation

1. **Select an algorithm** from the dropdown (FCFS, SJF, Priority, Round Robin)
2. **Enter process data** in JSON format:
   ```json
   [
     {"id": "P1", "arrival": 0, "burst": 8, "priority": 3},
     {"id": "P2", "arrival": 1, "burst": 4, "priority": 1},
     {"id": "P3", "arrival": 2, "burst": 6, "priority": 2}
   ]
   ```
3. **For Round Robin**, set the time quantum
4. **Click Simulate** to see the results

### Banker's Algorithm

1. **Set the number of processes and resources**
2. **Click Simulate** to generate random allocation matrices
3. **View the safe sequence** and RAG visualization

### Deadlock Detection

1. **Set the number of processes and resources**
2. **Click Detect Deadlock** to analyze the system
3. **View deadlock status** and wait-for graph

## 📊 API Endpoints

### CPU Scheduling
- `POST /api/scheduling/fcfs` - FCFS simulation
- `POST /api/scheduling/sjf` - SJF simulation
- `POST /api/scheduling/priority` - Priority scheduling
- `POST /api/scheduling/roundrobin` - Round Robin simulation

### Deadlock Management
- `POST /api/bankers` - Banker's algorithm
- `POST /api/deadlock` - Deadlock detection

### Utility
- `GET /` - API documentation
- `GET /api/health` - Health check

## 🎨 Features

### Modern UI/UX
- Responsive design that works on desktop and mobile
- Beautiful gradient backgrounds and animations
- Interactive tabs and smooth transitions
- Clean, professional interface

### Real-time Visualizations
- Dynamic Gantt charts with color-coded processes
- Interactive Resource Allocation Graphs
- Wait-for graphs for deadlock visualization
- Performance metrics with detailed statistics

### Educational Value
- Step-by-step algorithm simulation
- Visual representation of complex concepts
- Performance comparison between algorithms
- Interactive learning experience

## 🔧 Technical Details

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with animations and gradients
- **Vanilla JavaScript** - No frameworks, pure JS for performance
- **Canvas/SVG** - High-quality visualizations

### Backend
- **Python Flask** - Lightweight web framework
- **Modular Design** - Separate modules for each algorithm
- **RESTful API** - Clean API design
- **CORS Support** - Cross-origin resource sharing

## 🚀 Getting Started

1. **Clone or download** the project
2. **Start the backend** server (`python app.py`)
3. **Open the frontend** (`frontend/index.html`)
4. **Start simulating** OS algorithms!

## 📝 Example Process Data

### CPU Scheduling
```json
[
  {"id": "P1", "arrival": 0, "burst": 8, "priority": 3},
  {"id": "P2", "arrival": 1, "burst": 4, "priority": 1},
  {"id": "P3", "arrival": 2, "burst": 6, "priority": 2},
  {"id": "P4", "arrival": 3, "burst": 3, "priority": 4}
]
```

### API Request Example
```bash
curl -X POST http://localhost:5000/api/scheduling/fcfs \
  -H "Content-Type: application/json" \
  -d '{"processes": [{"id": "P1", "arrival": 0, "burst": 8, "priority": 3}]}'
```

## 🤝 Contributing

This project is designed for educational purposes. Feel free to:
- Add new algorithms
- Improve visualizations
- Enhance the UI/UX
- Fix bugs or add features

## 📄 License

This project is open source and available under the MIT License.

## 🎓 Educational Use

VizOS is perfect for:
- Operating Systems courses
- Computer Science education
- Algorithm visualization
- Understanding OS concepts
- Interactive learning

---

**Happy Learning! 🎉**
