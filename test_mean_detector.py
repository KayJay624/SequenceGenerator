import numpy as np
import sys; sys.path.append('./detectors/')
import pandas as pd
import encoders as en
from detector import ChangeDetector
from online_simulator import OnlineSimulator
from mean_detector import MeanDetector


#Numerical data
df = pd.read_csv('sequences/sequence_2017_11_28-18.07.57.csv')
seq = np.array(df['attr_1'])

# Symbolic data
#df = pd.read_csv('sequences/sequence_2017_11_22-19.35.27.csv')
#seq = np.array(df['day_of_week'])
#seq = en.encode(signal)

detector = MeanDetector(threshold=1)

simulator = OnlineSimulator(None,
                            [detector],
                            [seq],
                            ['attr_1'])
simulator.run(plot=True, detect_rules=False)

detected_change_points = simulator.get_detected_changes()
print(np.array(detected_change_points))
