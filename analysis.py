#! /usr/bin/env python3

import os
import sys
import re
from datetime import datetime
import argparse
from prettytable import PrettyTable

TIME_FORMAT = "%m/%d %H:%M:%S"

PHASE1_WEIGHT = 43.88
PHASE2_WEIGHT = 19.64
PHASE3_WEIGHT = 33.70
PHASE4_WEIGHT = 2.78

TMP_DIRS    = r"^Starting plotting progress into temporary dirs: (.*) and (.*)"
PLOT_ID     = r"^ID: (.+)"
PLOT_SIZE   = r"^Plot size is: (\d+)"
BUFFER_SIZE = r"^Buffer size is: (\d+)MiB"
BUCKETS     = r"^Using (\d+) buckets"
THREADS     = r"^Using (\d+) threads of stripe size (\d+)"
START_TIME  = r"^Starting phase 1/4: Forward Propagation into tmp files\.\.\. (.+)"
PHASE_1     = r"^Time for phase 1 = (\d+\.\d+) seconds. CPU \((\d+\.\d+)%\)"
PHASE_2     = r"^Time for phase 2 = (\d+\.\d+) seconds. CPU \((\d+\.\d+)%\)"
PHASE_3     = r"^Time for phase 3 = (\d+\.\d+) seconds. CPU \((\d+\.\d+)%\)"
PHASE_4     = r"^Time for phase 4 = (\d+\.\d+) seconds. CPU \((\d+\.\d+)%\)"
TOTAL_TIME  = r"^Total time = (\d+\.\d+) seconds. CPU \((\d+\.\d+)%\)"
COPY_TIME   = r"^Copy time = (\d+\.\d+) seconds.*\) (.*)"
FILENAME    = r"^Renamed final file from \".+\" to \"(.+)\""

MY_START        = r"start new plot: (.*)"
MADMAX_TITLE    = r"^Multi-threaded pipelined Chia"
MM_DIR          = r"Final Directory: (.*)"
MM_TMP1         = r"Working Directory:\s+(.*)"
MM_TMP2         = r"Working Directory 2:\s+(.*)"
MM_NUM          = r"Number of Plots: (\d+)"
MM_ID           = r"Process ID: (\d+)"
MM_THREADS      = r"Number of Threads: (\d+)"
MM_BUCKETS      = r"Number of Buckets P1:.*\((.*)\)"
MM_START        = r"Plot Name: "
MM_P1_TIME      = r"\[P1\] Table.*took (\d+)"
MM_P1_END       = r"Phase 1 took (\d+)"
MM_P2_TIME      = r"\[P2\] Table.*took (\d+)"
MM_P2_END       = r"Phase 2 took (\d+)"
MM_P3_TIME      = r"\[P3.*Table.*took (\d+)"
MM_P3_END       = r"Phase 3 took (\d+)"
MM_P4_END       = r"Phase 4 took (\d+)"
MM_PARSE_END    = r"Total plot creation time was (\d+)"
MM_COPY_START   = r"^Started copy to (.*)"
MM_COPY_END     = r"^Copy to.*finished, took (\d+)"
MM_FILENAME     = r"^Renamed final plot to (.*)"

plot_list = []
progress_sum = 0
plot_type = "madmax"


class plot_data:
    def __init__(self):
        self.is_madmax = 0
        self.tmp_dir1 = ""
        self.tmp_dir2 = ""
        self.plot_id = ""
        self.plot_size = ""
        self.buffer_size = ""
        self.buckets = 0
        self.threads = ""
        self.stripe_size = ""
        self.start_time = datetime.now()
        self.phase1_time = 0.0
        self.phase2_time = 0.0
        self.phase3_time = 0.0
        self.phase4_time = 0.0
        self.phase1_cpu = ""
        self.phase2_cpu = ""
        self.phase3_cpu = ""
        self.phase4_cpu = ""
        self.total_time = 0.0
        self.totalCpu = ""
        self.copy_time = 0.0
        self.filename = ""
        self.progress = 0.0
        self.elapsed_time = 0
        self.phase1_weight = 0.0
        self.phase2_weight = 0.0
        self.phase3_weight = 0.0
        self.phase4_weight = 0.0

def open_log(file):
    new_plot = plot_data()
    parse_step = 0
    percent = 0
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if (ret := re.search(MY_START, line)) != None:
                new_plot.start_time = datetime.strptime(ret.group(1), "%Y/%m/%d-%H:%M")
            elif (ret := re.search(TMP_DIRS, line)) != None:
                plot_list.append(new_plot)
                new_plot.tmp_dir1 = ret.group(1)
                new_plot.tmp_dir2 = ret.group(2)
                new_plot.is_madmax = 0
            elif (ret := re.search(MADMAX_TITLE, line)) != None:
                plot_list.append(new_plot)
                new_plot.is_madmax = 1
                new_plot.plot_size = "32"
                new_plot.buffer_size = "madmax"
                new_plot.elapsed_time = 0

            if new_plot.is_madmax:
                if (ret := re.search(MM_ID, line)) != None:
                    new_plot.plot_id = ret.group(1)
                elif (ret := re.search(MM_TMP1, line)) != None:
                    new_plot.tmp_dir1 = ret.group(1)
                elif (ret := re.search(MM_TMP2, line)) != None:
                    new_plot.tmp_dir2 = ret.group(1)
                elif (ret := re.search(MM_THREADS, line)) != None:
                    new_plot.threads = ret.group(1)
                elif (ret := re.search(MM_BUCKETS, line)) != None:
                    new_plot.buckets = int(ret.group(1))
                elif (ret := re.search(MM_START, line)) != None:
                    parse_step = 1
                    new_plot.progress = 0
                    percent = PHASE1_WEIGHT / 7;
                elif (ret := re.search(MM_P1_TIME, line)) != None:
                    new_plot.progress += percent
                elif (ret := re.search(MM_P1_END, line)) != None:
                    parse_step = 2
                    new_plot.phase1_time = int(ret.group(1))
                    new_plot.progress = PHASE1_WEIGHT
                    percent = PHASE2_WEIGHT / 12
                elif (ret := re.search(MM_P2_TIME, line)) != None:
                    new_plot.progress += percent
                elif (ret := re.search(MM_P2_END, line)) != None:
                    parse_step = 3
                    new_plot.phase2_time = int(ret.group(1))
                    new_plot.progress = PHASE1_WEIGHT + PHASE2_WEIGHT
                    percent = PHASE3_WEIGHT / 12
                elif (ret := re.search(MM_P3_TIME, line)) != None:
                    new_plot.progress += percent
                    new_plot.phase3_time = int(ret.group(1))
                elif (ret := re.search(MM_P3_END, line)) != None:
                    parse_step = 4
                    new_plot.phase3_time = int(ret.group(1))
                    new_plot.progress = PHASE1_WEIGHT + PHASE2_WEIGHT + PHASE3_WEIGHT
                    percent = PHASE4_WEIGHT / 4
                elif (ret := re.search(MM_P4_END, line)) != None:
                    parse_step = 5
                    new_plot.phase4_time = int(ret.group(1))
                elif (ret := re.search(MM_PARSE_END, line)) != None:
                    parse_step = 5
                    new_plot.elapsed_time = int(ret.group(1))
                    new_plot.total_time = new_plot.elapsed_time
                    new_plot.phase1_weight = new_plot.phase1_time / new_plot.total_time * 100
                    new_plot.phase2_weight = new_plot.phase2_time / new_plot.total_time * 100
                    new_plot.phase3_weight = new_plot.phase3_time / new_plot.total_time * 100
                    new_plot.phase4_weight = new_plot.phase4_time / new_plot.total_time * 100
                elif (ret := re.search(MM_COPY_START, line)) != None:
                    new_plot.filename = os.path.split(ret.group(1))[1]
                elif (ret := re.search(MM_COPY_END, line)) != None:
                    parse_step = 0
                    new_plot.progress = 100
                    new_plot.copy_time = int(ret.group(1))
                    new_plot = plot_data()
                elif (ret := re.search(MM_FILENAME, line)) != None:
                    parse_step = 0
                    new_plot.progress = 100
                    new_plot = plot_data()
                if parse_step < 5:
                    new_plot.elapsed_time = int((datetime.now() - new_plot.start_time).total_seconds())
            else:
                if (ret := re.search(PLOT_ID, line)) != None:
                    new_plot.plot_id = ret.group(1)
                elif (ret := re.search(PLOT_SIZE, line)) != None:
                    new_plot.plot_size = ret.group(1)
                elif (ret := re.search(BUFFER_SIZE, line)) != None:
                    new_plot.buffer_size = ret.group(1)
                elif (ret := re.search(BUCKETS, line)) != None:
                    new_plot.buckets = int(ret.group(1))
                elif (ret := re.search(THREADS, line)) != None:
                    new_plot.threads = ret.group(1)
                    new_plot.stripe_size = ret.group(2)
                elif (ret := re.search(START_TIME, line)) != None:
                    new_plot.start_time = datetime.strptime(ret.group(1), "%a %b %d %H:%M:%S %Y")
                    parse_step = 1
                    new_plot.progress = 0
                    percent = PHASE1_WEIGHT / 7 / new_plot.buckets;
                elif (ret := re.search(COPY_TIME, line)) != None:
                    new_plot.copy_time = float(ret.group(1))
                elif (ret := re.search(PHASE_1, line)) != None:
                    new_plot.phase1_time = float(ret.group(1))
                    new_plot.phase1_cpu = ret.group(2)
                    parse_step = 2
                    new_plot.progress = PHASE1_WEIGHT
                    percent = PHASE2_WEIGHT / 7
                elif (ret := re.search(PHASE_2, line)) != None:
                    new_plot.phase2_time = float(ret.group(1))
                    new_plot.phase2_cpu = ret.group(2)
                    parse_step = 3
                    new_plot.progress = PHASE1_WEIGHT + PHASE2_WEIGHT
                    percent = PHASE3_WEIGHT / 6
                elif (ret := re.search(PHASE_3, line)) != None:
                    new_plot.phase3_time = float(ret.group(1))
                    new_plot.phase3_cpu = ret.group(2)
                    parse_step = 4
                    percent = PHASE4_WEIGHT / new_plot.buckets;
                    new_plot.progress = PHASE1_WEIGHT + PHASE2_WEIGHT + PHASE3_WEIGHT
                elif (ret := re.search(PHASE_4, line)) != None:
                    new_plot.phase4_time = float(ret.group(1))
                    new_plot.phase1_cpu = ret.group(2)
                elif (ret := re.search(TOTAL_TIME, line)) != None:
                    new_plot.total_time = float(ret.group(1))
                    new_plot.totalCpu = ret.group(2)
                    parse_step = 5
                    new_plot.elapsed_time = int(new_plot.total_time)
                    new_plot.phase1_weight = new_plot.phase1_time / new_plot.total_time * 100
                    new_plot.phase2_weight = new_plot.phase2_time / new_plot.total_time * 100
                    new_plot.phase3_weight = new_plot.phase3_time / new_plot.total_time * 100
                    new_plot.phase4_weight = new_plot.phase4_time / new_plot.total_time * 100
                elif (ret := re.search(FILENAME, line)) != None:
                    parse_step = 0
                    new_plot.progress = 100
                    new_plot.filename = os.path.split(ret.group(1))[1]
                    new_plot = plot_data()

                if parse_step < 5:
                    new_plot.elapsed_time = int((datetime.now() - new_plot.start_time).total_seconds())
                    if parse_step == 1:
                        if (ret := re.search(r"^\sBucket", line)) != None:
                            new_plot.progress += percent
                    elif parse_step == 2:
                        if (ret := re.search(r"^Backpropagating", line)) != None:
                            new_plot.progress += percent
                    elif parse_step == 3:
                        if (ret := re.search(r"^Compressing tables", line)) != None:
                            new_plot.progress += percent
                    elif parse_step == 4:
                        if (ret := re.search(r"^\sBucket", line)) != None:
                            new_plot.progress += percent

def conversion_float_time(time):
    try:
        s = int(time)
        if s == 0:
            return ""
    except ValueError:
        return ""
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}".format(h,m)

def analysis_log():
    if options.logdir:
        logdir = options.logdir
    else:
        logdir = os.getenv("CLOGS")
        if logdir == None:
            logdir = os.path.expanduser("~") + "/chialogs"

    tb = PrettyTable()

    title_list = ["k", "Buckets", "Thread", "TmpDir", "StartTime", "ElapsedTime", "PhaseTime", "Progress", "CopyTime"]
    if options.filename:
        title_list.append("PlotFileName")
    if options.phaseweight:
        title_list.append("PHaseWeight")

    tb.field_names = title_list.copy()

    for root,dirs,file_list in os.walk(logdir):
        if options.quicksearch:
            dirs[:] = []
        for filename in file_list:
            file = os.path.join(root, filename)
            open_log(file)

    average_phase1_weight = 0.0
    average_phase2_weight = 0.0
    average_phase3_weight = 0.0
    average_phase4_weight = 0.0
    for plot in plot_list:
        phase_time = conversion_float_time(plot.phase1_time)
        if plot.phase2_time:
            phase_time = phase_time + " / " + conversion_float_time(plot.phase2_time)
        if plot.phase3_time:
            phase_time = phase_time + " / " + conversion_float_time(plot.phase3_time)
        if plot.phase4_time:
            phase_time = phase_time + " / " + conversion_float_time(plot.phase4_time)

        progress = "{:.2f}".format(plot.progress) + "%"
        global progress_sum
        if options.progress:
            if plot.progress < int(options.progress):
                progress_sum += 1

        row = [plot.plot_size, plot.buckets, plot.threads, plot.tmp_dir1,
               plot.start_time.strftime(TIME_FORMAT),
               conversion_float_time(plot.elapsed_time),
               phase_time,
               progress,
               conversion_float_time(plot.copy_time),
               ]
        if options.filename:
            row.append(plot.filename)
        if options.phaseweight:
            if plot.phase4_weight != 0:
                average_phase1_weight = (average_phase1_weight + plot.phase1_weight)/2
                average_phase2_weight = (average_phase2_weight + plot.phase2_weight)/2
                average_phase3_weight = (average_phase3_weight + plot.phase3_weight)/2
                average_phase4_weight = (average_phase4_weight + plot.phase4_weight)/2
                phase_weight = "{:.2f} / {:.2f} / {:.2f} / {:.2f}".format(
                    plot.phase1_weight,plot.phase2_weight,plot.phase3_weight,plot.phase4_weight)
            else:
                phase_weight = ""
            row.append(phase_weight)
        tb.add_row(row)

    print(tb.get_string(sortby="StartTime"))
    if options.phaseweight:
        average_phase_weight = "average phase weight: {:.2f} / {:.2f} / {:.2f} / {:.2f}".format(
            average_phase1_weight,average_phase2_weight,average_phase3_weight,average_phase4_weight)
        print(average_phase_weight)
    if options.progress:
        print("plot progress < {}% have {}".format(options.progress, progress_sum))

if __name__ == "__main__":
    title = "analysis"
    parse = argparse.ArgumentParser(title)
    parse.add_argument("-f", "--filename", action="store_true", help="display filename")
    parse.add_argument("-q", "--quicksearch", action="store_true", help="not search subdir")
    parse.add_argument("-w", "--phaseweight", action="store_true", help="check parse weight")
    parse.add_argument("-p", "--progress", help="return progress < xx%% count")
    parse.add_argument("-d", "--logdir", help="set chia log dir (default: ~/chialogs)")
    options = parse.parse_args()

    if options.progress:
        options.quicksearch = True

    analysis_log()

    if options.progress:
        sys.exit(progress_sum)
    else:
        sys.exit(0)
