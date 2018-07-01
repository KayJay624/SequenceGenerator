import numpy as np
import scipy as sp
from scipy import signal
import matplotlib.pyplot as plt
from statistics import mode

from collections import deque
from detector import ChangeDetector

class ZScoreDetector(ChangeDetector):
    def __init__(self, window_size = 100, threshold=0.05):
        super( ZScoreDetector, self ).__init__()
        self.threshold = threshold
        self.window_size = window_size
        self.k = 0  # total seq_size
        self.global_mean_ = 0.0  # global mean
        self.s = 0.0  # for Welford's method. variance = s / (k + 1)
        self.window = deque(maxlen = window_size)
        self.z_score_ = np.nan
        self.window_mean_ = 0.0
        self.global_std_ = 0.0
        self.subseq = []
        self.percent = 0

    def update(self, new_value):
        super(ZScoreDetector, self).update(new_value)

        x = new_value
        self.window.append(x)
        self.subseq.append(new_value)

        # Calculate global statistics using welford's method
        old_mean = self.global_mean_
        new_mean = old_mean + (x - old_mean) / (self.k + 1)
        s = self.s + (x - new_mean) * (x - new_mean)

        g_mean_ = new_mean  # Global mean
        g_std = np.sqrt(s / (self.k+1))  # Global std

        w_mean = np.mean(self.window)  # Window mean
        w_std = np.std(self.window)  # Window std
        self.window_mean_ = w_mean

        self.std_diff = (g_std - w_std) / g_std
        self.SE = g_std / np.sqrt(self.window_size)
        self.mean_diff = (g_mean_ - w_mean) / g_mean_

        self.z_score_ = (w_mean - g_mean_) / self.SE

        self.global_mean_ = g_mean_
        self.global_std_ = g_std
        self.s = s
        self.k += 1

    def reset(self):
        self.k = 0
        self.global_mean_ = 0
        self.s = 0
        self.z_score_ = np.nan
        self.window_mean_ = 0
        self.global_std_ = 0
        self.window.clear()
        self.subseq = []

    def check_change(self, new_value):
        self.is_change_detected = False
        if np.absolute(self.z_score_) > self.threshold:
            self.is_change_detected = True
            self.previous_value = max(set(self.subseq), key=self.subseq.count)
            self.current_value = max(set(self.subseq[-1:]), key=self.subseq[-1:].count)
            self.percent = (self.subseq.count(self.previous_value) / len(self.subseq)) *100
            self.reset()
