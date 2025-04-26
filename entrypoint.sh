#!/bin/bash

genflag() {
  NAME="mq_round_robin_hood"
  curl -s https://board.ec.gw.tc/genflag -u admin:b1631bd2cd84bfb0aefbf93382b699d388ed96ef56648378b97412d5aba17244 -X POST -d "task=$NAME"|xargs echo
}

useradd -m task

AUTHOR=${AUTHOR:-anonymous}

CODE=${CODE:-"exit(1)"} # Set default false code

echo "$CODE" > /tmp/source.py
chown task /tmp/source.py



# set limits to make sure it's okay
ulimit -Sm 1028

echo "######   RUNNING PROGRAM BY $AUTHOR  ######"
su task -c '/checker.sh /tmp/source.py'
CODE=$?
echo "######  PROGRAM EXITED WITH CODE $CODE ######"
if [[ "$CODE" -eq 0 ]]; then
  echo "Your flag is $(genflag)"
fi


