#include <stdio.h>
#include <string.h>
#include <getopt.h>
#include <stdlib.h>
#include <netdb.h>         
#include <netinet/in.h>
#include <sys/socket.h>
#include <ifaddrs.h>
#include <arpa/inet.h>

#define TIMEOUT 1000

void process_ports(char *port_str, char *protocol){
    printf("Port: %d, Protocol: %s\n", current_port, protocol);
}

void display_interfaces() {
    // Correct struct name and pointer initialization
    struct ifaddrs *addrs, *temp;

    if (getifaddrs(&addrs) == -1) {
        perror("getifaddrs");
        return;
    }

    temp = addrs;

    while (temp) {
        if (temp->ifa_addr) {
            int group = temp->ifa_addr->sa_family;

            // IPv4 or IPv6 check
            if (group == AF_INET || group == AF_INET6) {
                char host[INET6_ADDRSTRLEN];

                // getnameinfo converts binary address to string
                int str = getnameinfo(temp->ifa_addr,
                                      (group == AF_INET) ? sizeof(struct sockaddr_in) : sizeof(struct sockaddr_in6),
                                      host, INET6_ADDRSTRLEN,
                                      NULL, 0, NI_NUMERICHOST);
                
                if (str == 0) {
                    // Use 'group' consistently here
                    printf("%-10s %s\t%s\n", temp->ifa_name, (group == AF_INET) ? "IPv4" : "IPv6", host);
                }
            }
        }
        // Advance to the next interface in the linked list
        temp = temp->ifa_next;
    }
    
    freeifaddrs(addrs);
}

void write_help() {
    printf("Usage: portscan [OPTIONS] HOST\n\n");
    printf("Scan TCP/UDP ports on a target host.\n\n");

    printf("Options:\n");
    printf("  -h, --help\n");
    printf("        Display this help message and exit with code 0.\n\n");

    printf("  -i <interface>, --interface <interface>\n");
    printf("        Network interface to use for scanning (e.g., eth0).\n");
    printf("        If -i is specified without a value AND no other\n");
    printf("        parameters are set, a list of active interfaces is\n");
    printf("        printed and the program exits with 0.\n\n");

    printf("  -t <range>, --tcp <range>\n");
    printf("        TCP port range(s) to scan.\n");
    printf("        Examples: -t 22    -t 1-1024    -t 22,23,24\n");
    printf("        Multiple ranges separated by commas are allowed.\n");
    printf("        Only TCP scanning is performed if -u is omitted.\n\n");

    printf("  -u <range>, --udp <range>\n");
    printf("        UDP port range(s) to scan.\n");
    printf("        Examples: -u 53    -u 1-65535    -u 53,67,68\n");
    printf("        Only UDP scanning is performed if -t is omitted.\n\n");

    printf("  -w <ms>, --timeout <ms>\n");
    printf("        Timeout in milliseconds for a single port probe.\n");
    printf("        Default: 1000 ms.\n\n");

    printf("Arguments:\n");
    printf("  HOST\n");
    printf("        Hostname or IPv4/IPv6 address of the target device.\n");
    printf("        Example: merlin.fit.vutbr.cz\n\n");

    printf("Notes:\n");
    printf("  - All arguments can appear in any order.\n");
    printf("  - It is not required to handle mixed port expressions\n");
    printf("    like 22,25-30,35.\n");
    printf("  - At least one of -t or -u must be provided unless only\n");
    printf("    interface listing is desired.\n\n");

    printf("Examples:\n");
    printf("  ./ipk-L4-scan -t 22 merlin.fit.vutbr.cz\n");
    printf("  ./ipk-L4-scan -u 53 -w 3000 192.168.1.10\n");
    printf("  ./ipk-L4-scan -i eth0 -t 1-1024 2001:db8::1\n");
    printf("  ./ipk-L4-scan -i\n");
}

int main(int argc, char *argv[]) {
    int opt;
    char * interface = NULL;
    char * TCP_ports = NULL;
    char * UDP_ports = NULL;    
    int timeout = TIMEOUT;

    static struct option options[] = {
        {"help", no_argument, 0, 'h'},
        {"interface", optional_argument, 0, 'i'},
        {"tcp", required_argument, 0, 't'},
        {"udp", required_argument, 0, 'u'},
        {"timeout", required_argument, 0, 'w'},
        {0,0,0,0}
    };

    // Fulfill all the values based on arguments
    while ((opt = getopt_long(argc, argv, "hi::t:u:w:", options, NULL)) != -1) {
        switch (opt) {
            case 'h':
                write_help();
                return 0;
            case 'i':
                // Add a empty string if there is no interface provided in the argument
                interface = optarg ? optarg : ""; 
                break;
            case 't':
                TCP_ports = optarg;
                break;
            case 'u':
                UDP_ports = optarg;
                break;
            case 'w':
                timeout = atoi(optarg);
                break;
            default:
                return 1;
        }
    }

    if (optind < argc) {
        char *hostname = argv[optind];
        printf("Scanning a host: %s\n", hostname);
    } else if (interface != NULL && strlen(interface) == 0) {
        display_interfaces();
        return 0;
    }

    return 0;
}