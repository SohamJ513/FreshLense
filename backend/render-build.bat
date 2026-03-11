@echo off
echo Installing setuptools and wheel first...
pip install --upgrade pip
pip install setuptools==75.8.0 wheel==0.45.1

echo Installing requirements...
pip install -r requirements-prod.txt