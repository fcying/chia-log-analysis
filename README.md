#### Deps
```
python version >= 3.8
pip3 install prettytable
```


#### Run
```
./analysis.py
+----+--------+---------+-------------+----------------+-------------+-------------------------------+----------+----------+
| k  | Buffer | Threads |    TmpDir   |   StartTime    | ElapsedTime |           PhaseTime           | Progress | CopyTime |
+----+--------+---------+-------------+----------------+-------------+-------------------------------+----------+----------+
| 32 |  3400  |    2    | /mnt/tmp0/1 | 05/22 18:13:27 |    13:42    | 05:51 / 02:41 / 04:46 / 00:23 | 100.00%  |  00:11   |
| 32 |  3400  |    2    | /mnt/tmp2/1 | 05/28 15:19:23 |    09:25    |         05:58 / 02:42         |  67.93%  |          |
| 32 |  3400  |    2    | /mnt/tmp3/1 | 05/28 15:19:23 |    09:25    |             09:13             |  36.32%  |          |
+----+--------+---------+-------------+----------------+-------------+-------------------------------+----------+----------+n
```


#### Help
```
./anlysis.py --help
usage: analysis [-h] [-f] [-d LOG_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -f, --filename        display filename
  -d LOG_DIR, --log_dir LOG_DIR
                        set chia log dira (default: ~/chialogs)
```
