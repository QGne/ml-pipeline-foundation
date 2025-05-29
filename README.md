# ml-pipeline-foundation
Simple ML pipeline foundation for future implementation



#Current project structure 
ml-pipeline-foundation/
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI/CD pipeline
├── src/
│   ├── init.py
│   └── data_processor.py   # Main ML pipeline implementation
├── tests/
│   ├── init.py
│   └── test_data_processor.py  # Unit tests
├── data/
│   └── iris_simple.csv     # Sample dataset
├── requirements.txt        # Python dependencies
└── README.md

### Installation & Setup(MAC
```bash

# 1. Clone the repository
git clone https://github.com/QGne/ml-pipeline-foundation.git
cd ml-pipline-foundation

# 2. Create virtual environment
python3 -m venv ml-env
source ml-env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

