
Installation

Clone the repository:
git clone https://github.com/j3ws3r/VCSHackathon.git
cd VCSHackathon

Create and activate virtual environment:
bash# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Run the application:
# Method 1: Using Python module
python -m app.main

# Method 2: Using uvicorn directly
uvicorn app.main:app --reload

# Method 3: Using uvicorn with custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 