#!/bin/sh

NAME=meresco_server
PIDFILE=/home/meresco/gharvester/$NAME.pid
LOG=/data/meresco/logs/gharvester/$NAME.log

PID=`cat $PIDFILE 2>/dev/null`
echo "Shutting down $NAME: $PID"
echo "Shutting down $NAME: $PID" >> $LOG
kill $PID 2>/dev/null
sleep 8
kill -9 $PID 2>/dev/null
rm -f $PIDFILE
echo "STOPPED ${NAME} server, pid=$PID, `date`"
echo "STOPPED ${NAME} server, pid=$PID, `date`" >> $LOG    
