# Project 1 - OMEGA: L4 Scanner

- Contact person: pluskal@vut.cz
- Automated testing: ivondracek@fit.vut.cz

## Assignment
1. Create a simple TCP and UDP network L4 scanner. The program will scan the specified hostname or IP address(es) (plural IP addresses in the case of multiple answers to DNS query) and ports. It will output to stdout port statuses (open, filtered, closed).
2. Create relevant tests for the project.

## Specification
The application scans selected ports of a device (translated onto one or more IPv4/IPv6 addresses) on a given network interface.

Packets/Frames should be sent using sockets. If needed, you can eavesdrop on the responses using the libpcap library.

The program can be terminated at any given moment with `SIGTERM` or `SIGINT` signals (<kbd>Ctrl</kbd> + <kbd>C</kbd> sequence).

Scanning should be done and return results as fast as possible. During development and testing, try scanning only the computers you own or manage.

#### TCP scanning
Sends only SYN packets. It does not perform a complete 3-way-handshake. If an RST response is received - the port is marked as *closed*. If no response is received from the scanned port after a given time interval, it must be verified with another packet and only then the port is marked as *filtered*. If a service is running on the port, the port is marked as *open*. See RFC 793 for more information.

#### UDP scanning
With UDP scanning, you can think of a given computer responding with an ICMP message of type 3, code 3 (port unreachable) when the port is *closed*. Consider the other ports as *open*.

### Synopsis
```
./ipk-L4-scan -i INTERFACE [-u PORTS] [-t PORTS] HOST [-w TIMEOUT] [-h | --help]
```
```
./ipk-L4-scan -i
```
```
./ipk-L4-scan -h
```
```
./ipk-L4-scan --help
```

where:

* `-h`/`--help` writes usage instructions to `stdout` and terminates with `0` exit code.
* `-i eth0` (just one interface to scan through).
  * If `-i` is specified without a value (and any other parameters are unspecified), a list of active interfaces is printed to `stdout` and the program terminates with `0` exit code (additional information beyond the interface list is welcome but not required).
* `-t` or `-u` specify scanned TCP/UDP port ranges.
  * Allowed examples: `-t 22`, `-u 1-65535`, `-t 22,23,24`. The `-u` and `-t` arguments can be specified separately, i.e. they do not have to occur both at once if the user wants only TCP or only UDP scanning.
  * It is not required to handle combinations such as `-t 22,25-30,35`.
* `-w 3000` is the timeout in milliseconds to wait for a response during a single port scan. This parameter is optional, in its absence the value 1000 (i.e., one second) is used.
* _HOST_ which is either hostname (e.g., merlin.fit.vutbr.cz) or IPv4/IPv6 address of scanned device.
* All arguments can be in any order.

### Execution Examples
```
./ipk-L4-scan -i eth0 -u 53,67 2001:67c:1220:809::93e5:917
./ipk-L4-scan -i eth0 -w 1000 -t 80,443,8080 www.vutbr.cz
```

### Functionality Illustration
```sh
./ipk-L4-scan -i lo -t 21,22,143 -u 53,67 localhost
```
```
127.0.0.1 21 tcp closed
127.0.0.1 22 tcp open
127.0.0.1 143 tcp filtered
127.0.0.1 53 udp closed
127.0.0.1 67 udp open
```

### Output Format

> ⚠️ <span style="color:orange">The application is going to be subject to automated testing. It is of utmost
> importance for the application to write the result to `stdout` exactly as specified.</span>

Program output (`stdout`) consists of one or more lines. Individual lines can be in any order. Each line contains values separated by space: scanned IP address (IPv4 or IPv6), port number, protocol type (`tcp` or `udp`), port state (`open`, `filtered`, or `closed`).

```sh
./ipk-L4-scan -i lo -t 22 localhost
```
```
127.0.0.1 22 tcp open
```

```sh
./ipk-L4-scan -i lo -t 21,22 -u 22,21 localhost
```
```
127.0.0.1 21 tcp closed
127.0.0.1 22 tcp open
127.0.0.1 21 udp closed
127.0.0.1 22 udp closed
```

```sh
./ipk-L4-scan -i eth0 -t 80 www.fit.vutbr.cz
```
```
147.229.9.23 80 tcp open
2001:67c:1220:809::93e5:917 80 tcp open
```

## Bibliography
* RFC 793: Transmission Control Protocol, 1981. Online. Request for Comments. Internet Engineering Task Force. [Accessed 17 February 2025]. 
* RFC 791: Internet Protocol, 1981. Online. Request for Comments. Internet Engineering Task Force. [Accessed 17 February 2025]. 
* RFC 768: User Datagram Protocol, 1980. Online. Request for Comments. Internet Engineering Task Force. [Accessed 17 February 2025]. 
* Nmap: The Art of Port Scanning. Online. Available from: https://nmap.org/nmap_doc.html#port_unreach [Accessed 17 February 2025]. 
* TCP SYN (Stealth) Scan (-sS) | Nmap Network Scanning. Online. Available from: https://nmap.org/book/synscan.html [Accessed 17 February 2025]. 
* Port scanner, 2024. Wikipedia. Online. Available from: https://en.wikipedia.org/w/index.php?title=Port_scanner&oldid=1225200572 [Accessed 17 February 2025]. 
* DEERING, Steve E. and HINDEN, Bob, 2017. RFC 8200: Internet Protocol, Version 6 (IPv6) Specification. Online. Request for Comments. Internet Engineering Task Force. [Accessed 17 February 2025]. 
* GILLIGAN, Robert E., BOUND, Jim, THOMSON, Susan and STEVENS, W. Richard, 1999. RFC 2553: Basic Socket Interface Extensions for IPv6. Online. Request for Comments. Internet Engineering Task Force. [Accessed 17 February 2025]. 
* SATRAPA, Pavel. IPv6: internetový protokol verze 6. CZ. NIC, 2019. ISBN: 978-80-88168-43-0