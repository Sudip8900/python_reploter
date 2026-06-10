import os
import fitz

def generate_pdf():
    pdf_path = "project_documentation.pdf"
    temp_path = "project_documentation_temp.pdf"
    
    # Define A4 paper dimensions in points (595 x 842)
    rect = fitz.paper_rect("a4")
    margin = 54  # 0.75 inch margins
    where = rect + (margin, margin, -margin, -margin)
    
    # CSS styles for high-quality, professional layout
    css_content = """
    body {
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        line-height: 1.6;
    }
    h1 {
        font-size: 20pt;
        font-weight: bold;
        color: #0f172a;
        margin-top: 0;
        margin-bottom: 15px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8px;
    }
    h2 {
        font-size: 14pt;
        font-weight: bold;
        color: #1e3a8a;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    p {
        font-size: 10pt;
        margin-bottom: 12px;
        text-align: justify;
    }
    ul, ol {
        font-size: 10pt;
        margin-bottom: 15px;
        padding-left: 20px;
    }
    li {
        margin-bottom: 6px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    th {
        font-size: 9.5pt;
        font-weight: bold;
        background-color: #1e40af;
        color: #ffffff;
        padding: 8px;
        border: 1px solid #cbd5e1;
        text-align: left;
    }
    td {
        font-size: 9pt;
        padding: 8px;
        border: 1px solid #cbd5e1;
        text-align: left;
    }
    pre {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px;
        border-radius: 4px;
        font-family: Courier, monospace;
        font-size: 8.5pt;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    code {
        font-family: Courier, monospace;
        background-color: #f1f5f9;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 8.5pt;
        color: #0f172a;
    }
    """
    
    # Define pages separated by a unique marker
    pages_html = [
        # PAGE 1: Cover Page
        """
        <div style="text-align: center; margin-top: 120px; font-family: Helvetica, Arial, sans-serif;">
            <div style="font-size: 14pt; font-weight: bold; color: #3b82f6; letter-spacing: 2px; text-transform: uppercase;">Technical Design & System Manual</div>
            <div style="font-size: 32pt; font-weight: bold; color: #0f172a; margin-top: 20px; margin-bottom: 20px; line-height: 1.2;">PDF Graph Digitizer</div>
            <div style="font-size: 13pt; color: #64748b; margin-bottom: 60px;">A High-Precision Engineering Tool for Digitizing Graphs & Bode Plots</div>
            
            <div style="width: 150px; height: 4px; background-color: #3b82f6; margin: 0 auto 100px auto;"></div>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 100px; text-align: left; font-size: 10pt; color: #475569;">
                <tr>
                    <td style="width: 50%; padding-bottom: 10px; border: none;"><strong>Document Version:</strong> 1.0.0</td>
                    <td style="width: 50%; padding-bottom: 10px; border: none;"><strong>Status:</strong> Release</td>
                </tr>
                <tr>
                    <td style="padding-bottom: 10px; border: none;"><strong>Release Date:</strong> June 10, 2026</td>
                    <td style="padding-bottom: 10px; border: none;"><strong>Language / Env:</strong> Python 3.10+ / Windows</td>
                </tr>
                <tr>
                    <td colspan="2" style="border: none; border-top: 1px solid #e2e8f0; padding-top: 20px; font-style: italic;">
                        This document details the system design, architecture, key functionalities, computer vision algorithms, and critical implementation challenges of the PDF Graph Digitizer application.
                    </td>
                </tr>
            </table>
        </div>
        """,
        
        # PAGE 2: Introduction & Overview
        """
        <div>
            <h1>1. Executive Summary & Overview</h1>
            <p>The <b>PDF Graph Digitizer</b> is a desktop productivity application developed to extract numerical data points from static graphs embedded inside PDF files. In engineering, manufacturing, and research disciplines, legacy charts (such as frequency response, stress-strain curve, or thermophysical characteristics) are frequently distributed as static rasterized or vector images. Manually reading these values introduces substantial operator errors and is highly inefficient.</p>
            
            <p>This software solves these limitations by implementing a modern desktop GUI that allows users to:</p>
            <ul>
                <li><b>Load & Rasterize:</b> Open PDF documents and render individual pages at a high-resolution 300 DPI layout.</li>
                <li><b>Interactive Calibration:</b> Configure linear or logarithmic scales, supporting dual independent Y-axes (e.g., Left-Y for Gain and Right-Y for Phase).</li>
                <li><b>Automated Extraction:</b> Digitize curves in single clicks using HSV color matching and thinned morphological filters.</li>
                <li><b>Advanced Replotting:</b> Live interactive chart analysis using an embedded Matplotlib canvas.</li>
                <li><b>Bode Analysis:</b> Solve feedback control loop properties, calculating phase margin, gain margin, and crossovers.</li>
                <li><b>Signal Processing:</b> Apply Savitzky-Golay smoothing, custom resampling, derivatives, integrations, and peak detection.</li>
                <li><b>Data Portability:</b> Export structured values straight to CSV files.</li>
            </ul>
        </div>
        """,
        
        # PAGE 3: Architecture & Tech Stack
        """
        <div>
            <h1>2. Architecture & Technology Stack</h1>
            <p>The application is built on top of a modular Python architecture. Core computation libraries (PyMuPDF, OpenCV, NumPy, SciPy) are isolated from the layout/GUI modules (Tkinter), establishing clean boundaries and testable sub-modules.</p>
            
            <h2>2.1 Selected Library Roles</h2>
            <table>
                <thead>
                    <tr style="background-color: #f1f5f9;">
                        <th style="width: 25%;">Package</th>
                        <th style="width: 20%;">Standard Version</th>
                        <th>Functional Role in Codebase</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>Tkinter / ttk</b></td>
                        <td>Standard Library</td>
                        <td>Renders the desktop GUI window, frame layouts, parameter inputs, and handles window/canvas resize events.</td>
                    </tr>
                    <tr>
                        <td><b>PyMuPDF (fitz)</b></td>
                        <td>1.22.x +</td>
                        <td>Loads PDF data, parses vector graphics, and converts page layouts to high-definition pixel buffers.</td>
                    </tr>
                    <tr>
                        <td><b>OpenCV (cv2)</b></td>
                        <td>4.x +</td>
                        <td>Converts pixel colors to HSV space, filters out unwanted content with tolerances, and performs closing morphology.</td>
                    </tr>
                    <tr>
                        <td><b>NumPy / SciPy</b></td>
                        <td>1.2x / 1.x</td>
                        <td>Manages calibration interpolation, thins masks to single-value functions, and smooths curves via Savitzky-Golay filters.</td>
                    </tr>
                    <tr>
                        <td><b>Matplotlib</b></td>
                        <td>3.x +</td>
                        <td>Provides the replotted chart widget, interactive cursors with live annotations, and plot settings.</td>
                    </tr>
                    <tr>
                        <td><b>Pandas / Pillow</b></td>
                        <td>1.5+ / 9.x</td>
                        <td>Pandas coordinates series data to aligned CSV. Pillow converts OpenCV/NumPy images to Tkinter-compatible canvas images.</td>
                    </tr>
                </tbody>
            </table>
            
            <h2>2.2 Core Codebase Modules</h2>
            <ul>
                <li><code>main.py</code>: Window bootstrap that instantiates the <code>DigitizerApp</code>.</li>
                <li><code>digitizer/ui.py</code>: Handles layout structures, canvas bindings, Matplotlib embedding, and calculations.</li>
                <li><code>digitizer/pdf_loader.py</code>: High-resolution DPI page rendering using PyMuPDF.</li>
                <li><code>digitizer/calibration.py</code>: Linear and logarithmic axis coordinate transforms.</li>
                <li><code>digitizer/image_processor.py</code>: Color thresholding and single-value function thinning.</li>
                <li><code>digitizer/curve_extractor.py</code>: Integrates neighbor sampling, thresholding, and Savitzky-Golay filtering.</li>
                <li><code>digitizer/analyzer.py</code>: Numerical crossovers and Bode margins calculations.</li>
                <li><code>digitizer/exporter.py</code>: CSV file generator using Pandas.</li>
            </ul>
        </div>
        """,
        
        # PAGE 4: Key Functionalities & Workflows
        """
        <div>
            <h1>3. System Workflows & User Operations</h1>
            <p>The PDF Graph Digitizer features an intuitive step-by-step workflow designed to transition from a static document to structured digital data within minutes.</p>
            
            <h2>3.1 Calibration Step</h2>
            <p>Before digitizing, the pixel space must be mapped to engineering values. The calibration process is as follows:</p>
            <ol>
                <li>The user clicks "Calibrate" and inputs reference coordinates (e.g., X1=10, X2=1000, Y1=-40, Y2=20).</li>
                <li>The user clicks twice on the X-axis (defining pixel offsets Px1 and Px2) and twice on the Y-axis (defining Py1 and Py2).</li>
                <li>The system stores these parameters. If "Log Scale" is enabled, the coordinate transforms are calculated using <code>log10</code> base representation.</li>
                <li>The system supports "Dual-Y" axes, allowing separate left and right vertical calibrations.</li>
            </ol>
            
            <h2>3.2 Curve Isolation & Digitization</h2>
            <p>Once calibrated, the user clicks "Extract Curve" and clicks directly on a colored line. The system automatically isolates it:</p>
            <ol>
                <li><b>Sample:</b> The application samples a 3x3 pixel area around the click coordinate.</li>
                <li><b>Color Extraction:</b> It picks the most saturated color (or the darkest, if grayscale) to avoid anti-aliasing artifacts on the line borders.</li>
                <li><b>Thresholding:</b> It applies HSV tolerances to create a binary mask of the curve.</li>
                <li><b>Thinning:</b> For every X pixel coordinate, the median of the matching Y pixels is calculated, producing a single-pixel curve representation.</li>
                <li><b>Interpolation:</b> Pixel coordinates are passed to the <code>Calibrator</code> to yield real-world X and Y arrays.</li>
            </ol>
            
            <h2>3.3 Replotting & Signal Processing Dashboard</h2>
            <p>Extracted curves are displayed in an interactive Matplotlib panel. Users can track data using interactive cursors, smooth lines, resample points, calculate derivatives/integrals, compute statistics, or run Bode analysis to find phase and gain margins.</p>
        </div>
        """,
        
        # PAGE 5: Challenges & Solutions (Part 1)
        """
        <div>
            <h1>4. Engineering Challenges & Solutions (I)</h1>
            
            <h2>4.1 Color Sampling and Anti-Aliasing Edge Errors</h2>
            <p><b>Challenge:</b> In PDF pages rendered to raster images, curve lines are smoothed using anti-aliasing. If the user clicks on the boundary of a line, the clicked pixel is a blend of the line and background color (low saturation). Sampling this pixel results in an inaccurate color representation, yielding an empty mask.</p>
            <p><b>Solution:</b> The app searches a small 3x3 (or 7x7) neighborhood around the click. It converts all pixels in the patch to HSV. If any pixel has saturation &gt; 30, it selects the pixel with the <i>maximum saturation</i>, which corresponds to the true core color. If all pixels are low-saturation (grayscale), it selects the <i>darkest pixel</i>.</p>
            
            <h2>4.2 OpenCV Red Hue Wrap-Around</h2>
            <p><b>Challenge:</b> In OpenCV, the Hue channel is bounded between 0 and 179. Pure red wraps around the boundary (e.g., Hue values [0, 15] and [165, 179]). Standard thresholding filters out half of the red color spectrum because they lie on opposite sides of the range.</p>
            <p><b>Solution:</b> The system checks if the selected Hue lies near 0 or 179. If it does, it splits the thresholding into two ranges and merges them using a bitwise OR operation:</p>
            <pre>
# If Hue is near 0
lower1 = np.array([0, s_min, v_min])
upper1 = np.array([h_val + h_tol, s_max, v_max])
lower2 = np.array([180 - (h_tol - h_val), s_min, v_min])
upper2 = np.array([179, s_max, v_max])
mask = cv2.bitwise_or(cv2.inRange(hsv, lower1, upper1),
                      cv2.inRange(hsv, lower2, upper2))
            </pre>
        </div>
        """,
        
        # PAGE 6: Challenges & Solutions (Part 2)
        """
        <div>
            <h1>5. Engineering Challenges & Solutions (II)</h1>
            
            <h2>5.1 Logarithmic Axis Interpolation</h2>
            <p><b>Challenge:</b> Linear mapping fails on logarithmic axes (e.g. frequency response). Applying linear interpolation scales values incorrectly and distorts data.</p>
            <p><b>Solution:</b> The <code>Calibrator</code> performs mapping in log-space, interpolating the logarithm of coordinates and then mapping back via base-10 exponentiation:</p>
            <pre>
# Inside calibration.py
if is_log:
    log_v1 = np.log10(v1)
    log_v2 = np.log10(v2)
    log_v = log_v1 + (p_vals - p1) * (log_v2 - log_v1) / (p2 - p1)
    return 10 ** log_v
else:
    return v1 + (p_vals - p1) * (v2 - v1) / (p2 - p1)
            </pre>
            
            <h2>5.2 NumPy uint8 Arithmetic Underflow & Overflow</h2>
            <p><b>Challenge:</b> Adding/subtracting tolerances to HSV elements can exceed 255 or drop below 0. Since HSV data uses 8-bit unsigned integers (<code>np.uint8</code>), standard addition can overflow, wrapping around to incorrect values (e.g. 240 + 20 = 4).</p>
            <p><b>Solution:</b> Color coordinates are explicitly cast to Python integers prior to arithmetic checks, and are safely clamped using <code>min</code> and <code>max</code> bounds:</p>
            <pre>
h_val = int(color_hsv[0])
lower = np.array([max(0, h_val - h_tol), ...])
upper = np.array([min(179, h_val + h_tol), ...])
            </pre>
            
            <h2>5.3 Single-Value Function Extraction (Median Y Filter)</h2>
            <p><b>Challenge:</b> A color mask extracts lines that are multiple pixels thick. Grouping them directly would create multiple values of Y for a single X coordinate, preventing proper curve resampling or calculations.</p>
            <p><b>Solution:</b> The system thins the mask by grouping all active pixel coordinates by X. For each unique X coordinate, it calculates the median of all matching Y coordinates. This guarantees a single-valued function <i>y = f(x)</i>.</p>
        </div>
        """,
        
        # PAGE 7: Operational Guidelines & Future Enhancements
        """
        <div>
            <h1>6. Summary & Future Scope</h1>
            
            <h2>6.1 Quick Operational Guidelines</h2>
            <ol>
                <li><b>Start:</b> Launch the app using <code>python main.py</code>. Click "Load PDF" to select your target file.</li>
                <li><b>Calibrate:</b> Input the axes coordinates and click the respective tick positions on the canvas. Click "Submit Calibration".</li>
                <li><b>Extract:</b> Click "Extract Curve". Click directly on the target curve. The app samples the color and extracts the line points automatically.</li>
                <li><b>Analyze:</b> View the data on the Matplotlib dashboard. For Bode plots, click "Analyze Bode" to calculate phase margin, gain margin, and crossovers.</li>
                <li><b>Export:</b> Click "Export to CSV" to save the raw digitized points, or export charts to PDF and PNG formats.</li>
            </ol>
            
            <h2>6.2 Future Enhancements</h2>
            <ul>
                <li><b>Automatic Gridline Removal:</b> Implementing automatic line suppression. If gridlines share the same color as the curve, the app will separate the overlapping gridlines to prevent digital anomalies.</li>
                <li><b>OCR Axis Recognition:</b> Automating axis calibration by reading tick texts and scales via Optical Character Recognition (OCR), eliminating manual calibration clicks.</li>
                <li><b>Multi-Page Batch Processing:</b> Extending the pipeline to process multiple pages or PDF reports automatically if they share the same graphical format.</li>
            </ul>
        </div>
        """
    ]
    
    # Generate the PDF document using DocumentWriter
    writer = fitz.DocumentWriter(temp_path)
    
    for part in pages_html:
        story = fitz.Story(html=part, user_css=css_content)
        more = True
        while more:
            device = writer.begin_page(rect)
            more, _ = story.place(where)
            story.draw(device)
            writer.end_page()
            
    writer.close()
    del writer, device, story
    print("Base PDF generated successfully!")
    
    # Post-processing: Add headers, footers, and page numbers
    with fitz.open(temp_path) as doc:
        total_pages = len(doc)
        
        for i in range(total_pages):
            page = doc[i]
            
            # Skip header/footer on cover page
            if i == 0:
                continue
                
            # Draw running header
            page.insert_text(
                fitz.Point(54, 35),
                "PDF Graph Digitizer — System Documentation",
                fontsize=8,
                fontname="helv",
                color=(0.39, 0.45, 0.55)  # #64748b
            )
            
            # Draw running header rule
            shape = page.new_shape()
            shape.draw_line(fitz.Point(54, 42), fitz.Point(541, 42))
            shape.finish(color=(0.88, 0.91, 0.94), width=0.5)  # #e2e8f0
            shape.commit()
            
            # Draw running footer rule
            shape = page.new_shape()
            shape.draw_line(fitz.Point(54, 800), fitz.Point(541, 800))
            shape.finish(color=(0.88, 0.91, 0.94), width=0.5)  # #e2e8f0
            shape.commit()
            
            # Draw running footer page number
            page.insert_text(
                fitz.Point(54, 815),
                "Confidential & Proprietary",
                fontsize=8,
                fontname="helv",
                color=(0.39, 0.45, 0.55)
            )
            page.insert_text(
                fitz.Point(500, 815),
                f"Page {i+1} of {total_pages}",
                fontsize=8,
                fontname="helv",
                color=(0.39, 0.45, 0.55)
            )
            
        # Save the final numbered version
        doc.save(pdf_path)
    
    # Clean up
    if os.path.exists(temp_path):
        os.remove(temp_path)
    print("Numbered PDF saved successfully!")

if __name__ == "__main__":
    generate_pdf()
