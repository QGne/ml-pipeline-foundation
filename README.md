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


### Complete Pipline Test
```bash
cat > pipeline_test.py << 'EOF'
from src.data_processor import DataProcessor

processor = DataProcessor()
data = processor.load_data('data/iris_simple.csv')
clean_data = processor.clean_data(data)
X, y = processor.split_features_target(clean_data)
X_train, X_test, y_train, y_test = processor.prepare_data(X, y)

train_acc = processor.train_model(X_train, y_train)
test_acc = processor.evaluate_model(X_test, y_test)

print(f'Training accuracy: {train_acc:.3f}')
print(f'Test accuracy: {test_acc:.3f}')
print('✅ Pipeline completed successfully!')
EOF

python pipeline_test.py
rm pipeline_test.py


### Unit Tests
```bash

pytest tests/ -v

# Expected output:
# ===== 5 passed in X.XXs =====
