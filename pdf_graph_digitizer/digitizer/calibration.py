import numpy as np

class Calibrator:
    """Handles mapping of pixel coordinates to real-world coordinates."""
    def __init__(self):
        self.calibrations = {}

    def calibrate_axis(self, axis_name, p1, p2, v1, v2, is_log):
        self.calibrations[axis_name] = {
            'p1': p1, 'p2': p2, 'v1': v1, 'v2': v2, 'is_log': is_log
        }

    def apply(self, p_vals, axis_name):
        if axis_name not in self.calibrations:
            raise ValueError(f"Axis {axis_name} not calibrated")
        
        calib = self.calibrations[axis_name]
        p1, p2 = calib['p1'], calib['p2']
        v1, v2 = calib['v1'], calib['v2']
        is_log = calib['is_log']

        p_vals = np.array(p_vals, dtype=float)

        if p1 == p2:
            return p_vals

        if is_log:
            log_v1 = np.log10(v1)
            log_v2 = np.log10(v2)
            log_v = log_v1 + (p_vals - p1) * (log_v2 - log_v1) / (p2 - p1)
            return 10 ** log_v
        else:
            return v1 + (p_vals - p1) * (v2 - v1) / (p2 - p1)
