# #!/bin/bash

# DATA_DIR=~/.chargnet
# if [ ! -f "$DATA_DIR/geth.ipc" ]; then
#     #geth --datadir=$DATA_DIR init /root/chargnet.json
#     sleep 3
# fi

# #cp /root/trusted-nodes.json $DATA_DIR
# #cp /root/static-nodes.json $DATA_DIR
# #cp /root/config.toml $DATA_DIR

# ls -l $DATA_DIR

# ls -l /root

# killall geth

# #cat ~/.chargnet/config.toml


# #BOOTSTRAP_IP=`getent hosts bootstrap | cut -d" " -f1`
# #BOOTSTRAP_IP=`getent hosts bootstrap`

# #BOOTSTRAP_IP=`ip a | grep 'scope global eth0' | cut -d' ' -f2`

# GETH_OPTS=${@/XXX/$BOOTSTRAP_IP}

# #ip a | grep inet
# #echo "======= $BOOTSTRAP_IP"

# echo $GETH_OPTS

# #geth $GETH_OPTS


#!/bin/bash






# DATA_DIR=~/.chargnet
# if [ ! -f "$DATA_DIR/geth.ipc" ]; then
#     geth --datadir=$DATA_DIR init /root/chargnet.json
#     sleep 3
# fi

# ls -l $DATA_DIR
# ls -l /root

# killall geth

# GETH_OPTS=${@/XXX/$BOOTSTRAP_IP}
# echo $GETH_OPTS

# exec geth $GETH_OPTS




# #!/bin/bash

# DATA_DIR=~/.chargnet
# ls -l $DATA_DIR
# ls -l /root

# GETH_OPTS=${@/XXX/$BOOTSTRAP_IP}
# echo $GETH_OPTS

# exec geth $GETH_OPTS






# #!/bin/bash

# DATA_DIR=~/.chargnet
# if [ ! -f "$DATA_DIR/geth.ipc" ]; then
#     geth --datadir=$DATA_DIR init /root/chargnet.json
#     sleep 3
# fi

# ls -l $DATA_DIR
# ls -l /root

# GETH_OPTS=${@/XXX/$BOOTSTRAP_IP}
# echo $GETH_OPTS

# exec geth $GETH_OPTS --allow-insecure-unlock





#!/bin/bash

DATA_DIR=~/.chargnet
if [ ! -f "$DATA_DIR/geth.ipc" ]; then
    geth --datadir=$DATA_DIR init /root/chargnet.json
    sleep 3
fi

# cp /root/static-nodes.json $DATA_DIR/geth/
# cp /root/trusted-nodes.json $DATA_DIR/geth/

ls -l $DATA_DIR
ls -l /root

GETH_OPTS=${@/XXX/$BOOTSTRAP_IP}
echo $GETH_OPTS

exec geth $GETH_OPTS --allow-insecure-unlock