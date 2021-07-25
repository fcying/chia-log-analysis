#!/bin/bash

#git clone --depth 1 https://github.com/Chia-Network/chia-blockchain.git
#git clone https://github.com/madMAx43v3r/chia-plotter.git

workdir=$(pwd)
tmp=$workdir/tmp
data=$workdir/data

[ -z "$CLOGS" ] && CLOGS=$HOME/chialogs
mkdir -p $CLOGS

[ -z "$wait_progress" ] && wait_progress=5
[ -z "$wait_count" ] && wait_count=2
plot=1
thread=""
buckets=""
number=0
local_config=0
while [[ $# -ge 1 ]]; do
    case $1 in
        -q)
            echo "quit bin plot"
            while true
            do
                pid=$(pgrep -af "(bin/plot.*-p|chia_plot)" | head -1 | awk '{print $1}')
                if [ -n "$pid" ]; then
                    kill $pid
                else
                    break
                fi
            done
            rm -f $CLOGS/*.log
            exit 0
            ;;
        -p)
            shift && plot="$1" && shift;;
        -u)
            shift && buckets="-u $1" && shift;;
        -r)
            shift && thread="-r $1" && shift;;
        -w)
            shift && wait_count="$1" && shift;;
        -t)
            shift && tmp="$1" && shift;;
        -d)
            shift && data="$1" && shift;;
        -n)
            shift && number="$1" && shift;;
        -l)
            local_config=1 && shift;;
        *)
            echo "Invaild option: $1"
            exit 1
    esac
done

[ -z "$poolca" ] && echo "must set poolca(Pool Contract Address)" && exit 0
[ -z "$farmerpk" ] && echo "must set farmerpk" && exit 0

dir=$(basename $tmp)
tmp=$tmp/$plot

if [ -z "$wait" ]; then
    wait=$[(plot-1)*20]
fi

echo "dir=$dir tmp:$tmp plot:$plot wait:${wait}m thread:$thread number:$number"
#exit

sleep ${wait}m

logfile=$CLOGS/$dir$plot.log
current_loop=1
while true
do
    rm -rf $tmp
    mkdir -p $tmp
    while true
    do
        analysis -p $wait_progress
        if [ "$?" -ge "$wait_count" ]; then
            echo "wait other plot progress"
            sleep 600
        else
            break
        fi
    done
    rm -f $logfile

    echo "start new plot: $(date +%Y/%m/%d-%H:%M)" | tee -a $logfile
    chia_plot -n 1 $buckets $thread -t "$tmp/" -d "$data/" -f $farmerpk -c $poolca | tee -a $logfile

    if [ $(grep -c "Renamed final" $logfile) -ne 0 ] || [ $(grep -Pc "Copy to.*finished" $logfile) -ne 0 ]; then
        echo "move log file"
        mkdir -p $CLOGS/end && mv $logfile $_/$dir$plot-$(date +%y%m%d%H%M).log
    fi
    if [ "$local_config" -eq 1 ]; then
        source ~/bin/plot.local
    fi
    if [ "$current_loop" -eq "$number" ]; then
        echo "plot end"
        exit 0
    fi
    echo "start next plot, sleep 2, loop_count: $current_loop"
    sleep 2
    current_loop=$[current_loop+1]
done

