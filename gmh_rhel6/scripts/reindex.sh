#!/bin/bash

##nohup sh -c ./LogMemUsage.sh
#nohup python2.5 ~/meresco-wc/tools/reindexclient.py localhost:8000 all_may06_with_valgrind A > /data/meresco/reindex.log


nohup sh -c ./LogMemUsage.sh > /data/meresco/LogMemUsage_all_100511_with_logmemusage.log &

#nohup sh -c "exec /usr/bin/python2.5 /home/meresco/meresco-wc/tools/reindexclient.py localhost:8000 all_100511_with_logmemusage A > /data/meresco/reindex_all_100511_with_logmemusage.log 2>&1" > /dev/null &

#nohup python2.5 ~/meresco-wc/tools/reindexclient.py localhost:8000 all_100511_with_logmemusage A > /data/meresco/reindex_all_100511_with_logmemusage.log
