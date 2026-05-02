# Helioscope 🚀 
Realtime Satellite Solar Activity Detection System

## Project Overview
Helioscope is a Flask-based web application streaming
real-time satellite imagery from space telescopes

- Satellits:
  + SOHO (C2, C3)
  + SDO/AIA (1600, 1700),
 
Near solar activity is detectedusing OpenCV.
Detected activity is clipped and stored for postprocessing.

## Key Features:

Realtime video stream from satellite feeds
Computer vision for solar activity detection
Clipped frames for postprocessing
Web-based UI for monitoring

## Technologies Used

* Python 3.9+
* Flask web framework
* NumPy, SciPy, Pandas, python-opencv for data processing


## Install & Run
```
git clone https://github.com/santenova/helioscope.git
cd helioscope
python3.9 -m venv venv
source venv/bin/activate
python3.9 -m pip install -r requirements.txt
python3.9 app.py

```

## Contributing and License

Contributions are welcome! See the `CONTRIBUTING.md` file for guidelines.
This project is licensed under the MIT License. See the `LICENSE` file for details.
