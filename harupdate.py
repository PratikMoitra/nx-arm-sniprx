#!/usr/bin/python3

import argparse
import json
import re
from datetime import datetime

def extract_domains_from_har(har_file, verbose=False):
    domains = set()
    with open(har_file, 'r') as file:
        har_data = json.load(file)
        for entry in har_data['log']['entries']:
            request = entry['request']
            url = request['url']
            domain_match = re.match(r'https?://([^/]+)', url)
            if domain_match:
                domain = domain_match.group(1)
                if verbose:
                    print(f"Extracted domain: {domain}")
                domains.add(domain)
    return domains

def append_domains_to_file(domains, output_file, verbose=False):
    existing_domains = set()
    try:
        with open(output_file, 'r') as file:
            existing_domains = set(line.strip() for line in file)
    except FileNotFoundError:
        pass

    new_domains = domains - existing_domains

    if new_domains:
        with open(output_file, 'a') as file:
            for domain in new_domains:
                file.write(domain + '\n')
                if verbose:
                    print(f"Appended domain to {output_file}: {domain}")
    else:
        if verbose:
            print("No new domains to append.")

def update_dnsmasq_conf(ip_address, dnsmasq_conf_file, domains, verbose=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(dnsmasq_conf_file, 'r') as file:
        dnsmasq_config = file.read()

    # Update or add entries for each domain and its subdomains
    for domain in domains:
        entry_pattern = fr'(?<=^address=/{re.escape(domain)}/)\d+\.\d+\.\d+\.\d+'
        replacement = ip_address
        if not re.search(entry_pattern, dnsmasq_config, re.MULTILINE):
            # If the domain entry doesn't exist, add it
            dnsmasq_config += f'\naddress=/{domain}/{ip_address} ### added on {timestamp} ####'
            if verbose:
                print(f"Added entry for {domain} to {dnsmasq_conf_file}")
        else:
            # If the domain entry exists, update it
            updated_config = re.sub(entry_pattern, replacement, dnsmasq_config, flags=re.MULTILINE)
            if updated_config != dnsmasq_config:
                dnsmasq_config = updated_config
                if verbose:
                    print(f"Updated entry for {domain} in {dnsmasq_conf_file}")

    with open(dnsmasq_conf_file, 'w') as file:
        file.write(dnsmasq_config)
        if verbose:
            print(f"Updated {dnsmasq_conf_file} to resolve to IP: {ip_address}")

def main():
    parser = argparse.ArgumentParser(description="Extract domains from a .har file and update dnsmasq.conf file.")
    parser.add_argument("har_file", help="Path to the .har file")
    parser.add_argument("-o", "--output-file", default="proxy-domains.txt", help="Output file to append domains (default: proxy-domains.txt)")
    parser.add_argument("-e", "--external-ip", help="External IP address to update or append to dnsmasq.conf")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()

    if args.verbose:
        print("Verbose mode enabled.")

    domains = extract_domains_from_har(args.har_file, args.verbose)
    append_domains_to_file(domains, args.output_file, args.verbose)

    if args.external_ip:
        update_dnsmasq_conf(args.external_ip, "dnsmasq.conf", domains, args.verbose)

if __name__ == "__main__":
    main()
