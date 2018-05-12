import numpy as np
import matplotlib.pyplot as plt

from detectors import detector
from change_point import ChangePoint
from rule_component import RuleComponent
from rule import Rule
from collections import defaultdict

class OnlineSimulator(object):
    def __init__(self, rules_detector, change_detectors, sequences, seqs_names):
        self.sequences = sequences
        self.sequences_names = seqs_names
        self.change_detectors = change_detectors
        self.sequence_size = len(sequences[0])
        self.detected_change_points = [[] for i in range(len(self.sequences))]
        self.rules_sets = [set() for i in range(len(self.sequences))]
        self.parameters_history = [defaultdict(list) for i in range(len(self.sequences))]
        self.rules_detector = rules_detector
        self.combined_rules = set()
        self.round_to = 100
        self.predicted = []
        self.predicted_len = 10000

        if rules_detector != None:
            self.rules_detector.set_online_simulator(self)

    def get_detected_changes(self):
        return self.detected_change_points

    def get_rules_sets(self):
        result = []
        for i, rs in enumerate(self.rules_sets):
            if i != self.rules_detector.target_seq_index:
                result.append(rs)
        return result

    def get_combined_rules(self):
        return self.combined_rules

    def run(self, plot=True, detect_rules=True, **kwargs):
        parameters_history = [defaultdict(list) for i in range(len(self.sequences))]

        for i in range(0, self.sequence_size):
            for j, seq in enumerate(self.sequences):
                detector = self.change_detectors[j]

                value = seq[i]
                res = detector.step(value)

                for k, v in res.items():
                    parameters_history[j][k].append(v)

                if detector.is_change_detected is True:
                    prev_at = self.detected_change_points[j][-1].at_ if len(self.detected_change_points[j]) > 0 else 0
                    prev_value_len = i - prev_at

                    change_point = ChangePoint(detector.previous_value, detector.current_value, i, prev_value_len, self.sequences_names[j])
                    self.detected_change_points[j].append(change_point)

                if i == self.sequence_size - 1:
                    detector.is_change_detected = True
                    prev_at = self.detected_change_points[j][-1].at_ if len(self.detected_change_points[j]) > 0 else 0
                    prev_value_len = i - prev_at
                    change_point = ChangePoint(detector.current_value, -1, i, prev_value_len, self.sequences_names[j])
                    self.detected_change_points[j].append(change_point)

                if i == 0:
                    detector.is_change_detected = True
                    change_point = ChangePoint(-1, value, i, 0, self.sequences_names[j])
                    self.detected_change_points[j].append(change_point)

                if detect_rules:
                    self.rules_detector.search_rules(j, i)

                if i >= 10000 and i % self.rules_detector.round_to == 0 and i == self.predicted_len: #self.rules_detector.target_seq_index == j and
                    print(i)
                    self.predict_sequence(j, i)


        def dict_to_arrays(ddict):
            new_dict = {}
            for k, v in ddict.items():
                new_dict[k] = np.array(v)
            return new_dict

        for i in range(0, len(self.sequences)):
            parameters_history[i] = dict_to_arrays(parameters_history[i])
            self.parameters_history[i] = parameters_history[i]

        if plot is True:
            self.display_results(**kwargs)

        return detector.is_change_detected

    def display_results(self, sequence_name='Sequence', **kwargs):
        for i in range(0, len(self.sequences)):
            sequence = self.sequences[i]
            detector = self.change_detectors[i]
            parameters_history = self.parameters_history[i]
            detected_change_points = self.detected_change_points[i]

            plotcount = 1 + len(parameters_history)
            fig, axes = plt.subplots(nrows=plotcount, ncols=1, sharex=True,
                                     figsize=(12, plotcount*3))

            # Plot the sequence
            if plotcount > 1:
                ax = axes[0]
            elif plotcount == 1:
                ax = axes

            ax.plot(sequence, 'b.', markersize=3)
            ax.plot(sequence, 'b-', alpha=0.25)

            if i == 3:
                for pr in self.predicted:
                    ax.plot(pr, linewidth=3.0)
                    #print(pr[1000:])


            ax.set_title(sequence_name)

            ax.set_ylim(
                np.nanmin(sequence)-1,
                np.nanmax(sequence)+1)
            ax.set_xlim(0, len(sequence))
            xl = ax.get_xticks()
            ticks = xl

            ax.set_xticklabels(ticks)

            # Plot a horizontal line where the change_point is detected
            for change_point in detected_change_points:
                ax.axvline(change_point.at_, color='r', linestyle='--')

            # Plot each parameter
            for ii, (res_name, res_values) in enumerate(parameters_history.items()):
                ax = axes[ii+1]
                ax.plot(res_values, '-', alpha=0.7)
                ax.set_title("Parameter #{}: {}".format(ii+1, res_name))

                for change_point in detected_change_points:
                    ax.axvline(change_point.at_, color='r', linestyle='--')

    def predict_sequence(self, seq_index, curr_elem_index):
        #for seq_index, change_point_list in enumerate(self.detected_change_points):
        if seq_index == self.rules_detector.target_seq_index or seq_index != 0:
            return

        window_end = round_to(curr_elem_index, self.round_to)
        window_begin = window_end - 1000

        points_before_window, points_in_window, points_after_window = self.get_change_points_in_window(seq_index, window_begin, window_end)

        lhss = []
        #print(points_in_window)
        predictions = {}
        if not points_in_window:
            lhs_elem_len = round_to(window_end - window_begin, self.round_to)
            if lhs_elem_len > 0:
                for lhs_len in range(self.round_to, lhs_elem_len, self.round_to):
                    lhs_elem = RuleComponent(lhs_len,
                                             points_before_window[-1].curr_value if len(points_before_window) > 0 else np.nan,
                                             self.simulator.sequences_names[seq_index])
                    lhss.append([lhs_elem])
                    for r in sorted(self.rules_sets[seq_index],
                                    key=lambda x: (x.number_of_occurrences, len(x.lhs), x.rhs.len, x.lhs[0].len),
                                    reverse=True):
                        if r.lhs == lhss[-1]:
                            if r.rhs in predictions:
                                predictions[r.rhs] = (lhss[-1], r, predictions[r.rhs][2] + 1)
                            else:
                                predictions[r.rhs] = (lhss[-1], r, 1)
                            #print("In moment:", curr_elem_index, "predict", lhss[-1], "==>", r.rhs, predictions[r.rhs], "because of rule:\n", r)
                            break
        else:
            last_point = points_in_window[-1]
            if last_point.at_ <= window_end:
                lhs_elem_len = round_to(window_end - last_point.at_, self.round_to)
                for lhs_len in range(self.round_to, lhs_elem_len + 1, self.round_to):
                    lhs_elem = RuleComponent(lhs_len,
                                           last_point.curr_value,
                                           last_point.attr_name)
                    lhss.append([lhs_elem])
                    print("lhs:", lhss[-1], curr_elem_index)
                    for r in sorted(self.rules_sets[seq_index],
                                    key=lambda x: (x.number_of_occurrences, len(x.lhs), x.rhs.len, x.lhs[0].len),
                                    reverse=True):
                        if r.lhs == lhss[-1]:
                            if r.rhs in predictions:
                                predictions[r.rhs] = (lhss[-1], r, predictions[r.rhs][2] + 1)
                            else:
                                predictions[r.rhs] = (lhss[-1], r, 1)
                            #print("In moment:", curr_elem_index, "predict", lhss[-1], "==>", r.rhs, predictions[r.rhs], "because of rule:\n", r)
                            break

            for point_index in range(1, len(points_in_window)):
                prefix = lhss[-1] if lhss else []
                point = points_in_window[-point_index]
                # print(point)
                lhs_elem_len = round_to(point.prev_value_len, self.round_to)
                if lhs_elem_len > 0:
                    for lhs_len in range(self.round_to, lhs_elem_len + 1, self.round_to):
                        lhs_elem = RuleComponent(lhs_len,
                                                 point.prev_value,
                                                 point.attr_name)

                        lhss.append([lhs_elem] + prefix)
                        #print("lhs:", lhss[-1], curr_elem_index)
                        #print()
                        for r in sorted(self.rules_sets[seq_index],key=lambda x: (x.number_of_occurrences, len(x.lhs), x.rhs.len, x.lhs[0].len),reverse=True):
                            if r.lhs == lhss[-1]:
                                if r.rhs in predictions:
                                    predictions[r.rhs] = (lhss[-1], r, predictions[r.rhs][2] + 1)
                                else:
                                    predictions[r.rhs] = (lhss[-1], r, 1)

                                break
            if predictions:
                for k, prediction in predictions.items():
                    print("In moment:", curr_elem_index, "predict", prediction[0], "==>", k, "nr of times:", prediction[2],"because of rule:\n", prediction[1])
                    print()
                    li = [-1 for i in range(curr_elem_index)]
                    for i in range(k.len):
                        li.append(k.value)
                    self.predicted.append(li)
                    self.predicted_len = curr_elem_index+k.len
                    break

                # print("Prediction made in:", curr_elem_index)
                # print(predictions)


    def get_change_points_in_window(self, seq_index, window_begin, window_end):
        points_in_window = []
        points_before_window = []
        points_after_window = []
        for change_point in self.detected_change_points[seq_index]:
            if round_to(change_point.at_, self.round_to) > window_begin:
                if round_to(change_point.at_, self.round_to) < window_end:
                    points_in_window.append(change_point)
                else:  # change point is after windows end
                    points_after_window.append(change_point)
            else:  # change point is before windows start
                points_before_window.append(change_point)
        return (points_before_window, points_in_window, points_after_window)

def round_to(x, _to):
    return int(round(x / _to)) * _to