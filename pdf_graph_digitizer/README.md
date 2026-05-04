# PDF Graph Digitizer

A production-ready desktop application for digitizing graphs from PDF files and performing engineering analysis (e.g., Bode plot phase margin calculations).

## Features
- **PDF Extraction**: Extracts high-resolution images from PDFs.
- **Interactive Calibration**: Click 2 points on the X and Y axes to map pixels to real values (supports linear and log scales).
- **Curve Digitization**: Color-based curve extraction with automatic Savitzky-Golay filtering and smoothing.
- **Bode Analysis**: Detects 0 dB gain crossovers and calculates Phase Margins.
- **Exporting**: Save the digitized data to CSV or export a clean replotted graph to PNG.

## Setup & Usage
1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`
3. Click **Load PDF** and select a file.
4. Use the **Calibration** tools to set up your axes.
5. Click **Extract Curve** and click on a curve in the image to digitize it.
6. Click **Analyze Bode** if you have Gain and Phase curves.
7. Use **Export** to save your results.
