import numpy as np
import scipy as sp
from scipy import signal
import matplotlib.pyplot as plt

from collections import deque
from detector import ChangeDetector

class ZScoreDetector(ChangeDetector):
    def __init__(self, window_size = 100, threshold=0.05):
        super( ZScoreDetector, self ).__init__()
        self.threshold = threshold
        self.window_size = window_size
        self.k = 0  # total seq_size
        self.g_mean_ = 0.0  # global mean
        self.s_ = 0.0  # for Welford's method. variance = s / (k + 1)
        self.window = deque(maxlen = window_size)
        self.z_score_ = np.nan
        self.window_mean_ = 0.0
        self.g_std_ = 0.0

    def update(self, new_value):
        super(ZScoreDetector, self).update(new_value)

        x = new_value
        self.window.append(x)

        # Calculate global statistics using welford's method
        old_mean = self.g_mean_
        new_mean = old_mean + (x - old_mean) / (self.k + 1)
        s = self.s_ + (x - new_mean) * (x - new_mean)

        g_mean_ = new_mean  # Global mean
        g_std = np.sqrt(s / (self.k+1))  # Global std

        w_mean = np.mean(self.window)  # Window mean
        w_std = np.std(self.window)  # Window std
        self.window_mean_ = w_mean

        self.std_diff_ = (g_std - w_std) / g_std
        self.SE_ = g_std / np.sqrt(self.window_size)
        self.mean_diff_ = (g_mean_ - w_mean) / g_mean_

        self.z_score_ = (w_mean - g_mean_) / self.SE_

        self.g_mean_ = g_mean_
        self.g_std_ = g_std
        self.s_ = s
        self.k += 1

    def reset(self):
        self.k = 0
        self.g_mean_ = 0
        self.s_ = 0
        self.z_score_ = np.nan
        self.window_mean_ = 0
        self.g_std_ = 0
        self.window.clear()

    def check_stopping_rules(self, new_value):
        self.rules_triggered = False
        if np.absolute(self.z_score_) > self.threshold:
            self.rules_triggered = True
            self.reset()
