#!/bin/bash

#git clone --depth 1 https://github.com/Chia-Network/chia-blockchain.git

workdir=$(pwd)
tmp=$workdir/tmp
data=$workdir/data

[ -z "$wait_progress" ] && wait_progress=5
[ -z "$wait_count" ] && wait_count=2
plot=1
K=32
thread=2
buckets=64
buffersize=3400
once=0
local_config=0
while [[ $# -ge 1 ]]; do
    case $1 in
        -q)
            echo "quit bin plot"
            while true
            do
                pid=$(pgrep -af "(bin/plot.*-p|plots create)" | head -1 | awk '{print $1}')
                if [ -n "$pid" ]; then
                    kill $pid
                else
                    break
                fi
            done
            exit 0
            ;;
        -p)
            shift && plot="$1" && shift;;
        -k)
            shift && K="$1" && shift;;
        -b)
            shift && buffersize="$1" && shift;;
        -u)
            shift && buckets="$1" && shift;;
        -r)
            shift && thread="$1" && shift;;
        -w)
            shift && wait_count="$1" && shift;;
        -t)
            shift && tmp="$1" && shift;;
        -d)
            shift && data="$1" && shift;;
        -o)
            once=1 && shift;;
        -l)
            local_config=1 && shift;;
        *)
            echo "Invaild option: $1"
            exit 1
    esac
done

if [ -z "$buffersize" ]; then
    if [ "$K" -eq 33 ]; then
        buffersize=7400
    else
        buffersize=6800
    fi
fi

[ -n "$farmerpk" ] && farmerpk="-f $farmerpk"
[ -n "$poolpk" ] && poolpk="-p $poolpk"
[ -z "$CHOME" ] && CHOME=$HOME/chia-blockchain
[ -z "$CLOGS" ] && CLOGS=$HOME/chialogs

mkdir -p $CLOGS

dir=$(basename $tmp)
tmp=$tmp/$plot

if [ -z "$wait" ]; then
    wait=$[(plot-1)*20]
fi

echo "dir=$dir tmp:$tmp plot:$plot wait:${wait}m k=$K buffersize:$buffersize thread:$thread"
#exit

cd $CHOME
. ./activate
sleep ${wait}m

logfile=$CLOGS/$dir$plot.log
rm -f $logfile
while true
do
    rm -rf $tmp
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

    chia plots create -k $K -b $buffersize -r $thread -u $buckets $farmerpk $poolpk -t $tmp -d $data > $logfile

    if [ $(grep -c "Renamed final file from" $logfile) -ne 0 ]; then
        mkdir -p $CLOGS/end && mv $logfile $_/$dir$plot-$(date +%y%m%d%H%M).log
    fi
    if [ "$local_config" -eq 1 ]; then
        source ~/bin/plot.local
    fi
    if [ "$once" -eq 1 ]; then
        echo "plot end"
        exit 0
    fi

    echo "start next plot"
done

