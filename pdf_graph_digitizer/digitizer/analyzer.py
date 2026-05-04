import numpy as np

def analyze_bode(curves):
    """Calculates Phase Margin and 0 dB crossover frequency from digitizer curves."""
    gain_name, phase_name = None, None
    
    # Auto-detect curves by common axis/name assignments
    for name, c in curves.items():
        if 'Left' in c['y_axis'] or 'Gain' in name or 'gain' in name.lower():
            gain_name = name
        elif 'Right' in c['y_axis'] or 'Phase' in name or 'phase' in name.lower():
            phase_name = name
            
    if not gain_name and len(curves) >= 1: gain_name = list(curves.keys())[0]
    if not phase_name and len(curves) >= 2: phase_name = list(curves.keys())[1]
    
    if not gain_name or not phase_name:
        return {"error": "Need at least one Gain (Left Y) and one Phase (Right Y) curve."}
        
    gain_x, gain_y = curves[gain_name]['x'], curves[gain_name]['y']
    phase_x, phase_y = curves[phase_name]['x'], curves[phase_name]['y']
    
    crossings = []
    # Detect 0 dB crossing
    for i in range(len(gain_y) - 1):
        if gain_y[i] * gain_y[i+1] <= 0 and gain_y[i] != gain_y[i+1]:
            xc = gain_x[i] + (0 - gain_y[i]) * (gain_x[i+1] - gain_x[i]) / (gain_y[i+1] - gain_y[i])
            crossings.append(xc)
            
    if not crossings:
        return {"error": "No 0 dB crossing found on the Gain curve."}
        
    results = []
    sort_idx = np.argsort(phase_x)
    px, py = phase_x[sort_idx], phase_y[sort_idx]
    
    # Calculate phase margin
    for xc in crossings:
        curve_y = np.interp(xc, px, py)
        results.append({
            'crossover_freq': xc,
            'curve_y': curve_y,
            'phase': curve_y - 180,
            'phase_margin': curve_y
        })
        
    phase_crossings = []
    for i in range(len(phase_y) - 1):
        if phase_y[i] * phase_y[i+1] <= 0 and phase_y[i] != phase_y[i+1]:
            xc = phase_x[i] + (0 - phase_y[i]) * (phase_x[i+1] - phase_x[i]) / (phase_y[i+1] - phase_y[i])
            phase_crossings.append(xc)
            
    results_gm = []
    g_sort = np.argsort(gain_x)
    gx, gy = gain_x[g_sort], gain_y[g_sort]
    
    for xc in phase_crossings:
        gain_val = np.interp(xc, gx, gy)
        results_gm.append({
            'phase_crossover_freq': xc,
            'gain_margin': -gain_val
        })
        
    return {'results': results, 'results_gm': results_gm, 'gain_name': gain_name, 'phase_name': phase_name}
