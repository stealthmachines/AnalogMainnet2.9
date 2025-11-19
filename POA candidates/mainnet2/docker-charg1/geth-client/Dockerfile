# FROM boltz/geth:1.13.12

# RUN apk add --update bash

# ADD chargnet.json /root/chargnet.json
# #ADD trusted-nodes.json /root/trusted-nodes.json
# #ADD static-nodes.json /root/static-nodes.json
# ADD config.toml /root/config.toml
# ADD pass.txt /root/pass.txt

# ADD start.sh /root/start.sh
# RUN chmod +x /root/start.sh

# #RUN echo 111
# #RUN ls -l /root

# ENTRYPOINT /root/start.sh




# FROM boltz/geth:1.13.12

# RUN apt-get update && apt-get install -y bash jq && rm -rf /var/lib/apt/lists/*

# ADD chargnet.json /root/chargnet.json
# ADD config.toml /root/config.toml
# ADD pass.txt /root/pass.txt
# ADD start.sh /root/start.sh
# RUN chmod +x /root/start.sh

# ENTRYPOINT ["/root/start.sh"]



FROM boltz/geth:1.13.12

RUN apt-get update && apt-get install -y bash jq && rm -rf /var/lib/apt/lists/*

ADD chargnet.json /root/chargnet.json
ADD config.toml /root/config.toml
ADD pass.txt /root/pass.txt
ADD start.sh /root/start.sh
ADD static-nodes.json /root/static-nodes.json
ADD trusted-nodes.json /root/trusted-nodes.json
RUN chmod +x /root/start.sh

ENTRYPOINT ["/root/start.sh"]