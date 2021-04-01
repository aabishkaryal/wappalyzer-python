import argparse # Module to parse the command line arguments
from os.path import exists, isfile # Function to check if a file exists
from sys import exit # Function to exit the program
import requests # Module to make requests to the API
import json # Module to parse JSON
from time import sleep # Function to wait for x seconds
from tldextract import extract # Function to extract different parts of url

# URL to check if the api key is valid and has credits to be used.
CHECK_URL = "https://api.wappalyzer.com/credits/v2/balance/"
# URL of Wappalyzer endpoint
URL = "https://api.wappalyzer.com/lookup/v2/"

def main():
    # Using argparse to parse the command line arguments
    parser = argparse.ArgumentParser(description='Tool that uses the Wappalyzer API to find out the technology stack of any website')

    parser.add_argument('key', help='API key of Wappalyzer (https://www.wappalyzer.com/)')
    parser.add_argument('-f', '--file', default='domains.txt', help='File with the list of domains')
    parser.add_argument('-o', '--output', help='File to output the json data')
    parser.add_argument('-v', '--verbose', help='Increase Output Verbosity', action="store_true")
    parser.add_argument('-h', '--help', help='Display the help message')

    args = parser.parse_args()

    if (args.help){
        print()
        parser.print_help()
        exit(1)
    }

    if(args.verbose and args.file == 'domains.txt'):
        print("INFO: No Input file mentioned, using domains.txt as default input file.")

    # Check to make sure the file with the domains list exists
    if(exists(args.file) and isfile(args.file)):
        # Check for valid API key with enough credits
        credits = check_key(args.key)
        # Get the list of domains from the default file or the provided file
        domains_list = get_domains_list(args.file)
        num_domains = len(domains_list)
        # Header for the API call
        headers = {'x-api-key': args.key}

        i = 0
        data = []
        while i < num_domains:
            # Combine either all remaining domains or next 10 domains 
            # or the next (number of credits) domains
            # Since the API can only process 10 per request per second 
            params = {'urls':','.join(domains_list[i:min(num_domains, i+10, i+credits)])}
            # Send the get requests with appropriate parameters and headers
            r = requests.get(URL, headers=headers, params=params)

            if(r.status_code == 400):
                print("ERROR: There was an error with the domain list")
                print(r.json())
                exit()
            elif (r.status_code == 429):
                print("INFO: Rate Limit Exceeded.")
                print("Retrying in 5 seconds.")
                sleep(5)
                continue
            data.extend(r.json())
            #  Update the counter
            i = min(num_domains, i+10, i+credits)

            credits = int(r.headers['wappalyzer-credits-remaining'])
            
            if (i < num_domains and credits == 0):
                # If no credit is left but domains are yet to be processed, ask for a new API key.
                print("WARNING: No credit left in the key.")
                print("Enter a new API Key to continue or enter to quit.")
                key = input("Enter new API key: ")
                if (key == ''): 
                    break
                credits = check_key(key)
                headers = {'x-api-key': key}
        
        if(args.output is not None and exists(args.output) and isfile(args.output)):
            with open(args.output, 'a') as f:
                f.write(data)
        else:
            if(args.verbose):
                print("INFO: No Output file mentioned, creating seperate file for each domain as output file.")
            # Loop through data for each domain
            for domain_data in data:
                url = domain_data['url']
                ext = extract(url)
                filename = '{}_{}.json'.format(ext.subdomain, ext.domain)
                if(exists(filename)):
                    print("INFO: {} already exists.".format(filename))
                    filename = input("Enter new filename for {} : ".format(url))

                with open(filename, 'w') as f:
                    f.write(json.dumps(domain_data))
                    if(args.verbose):
                        print("INFO: Created file {}".format(filename))
    else:
        # Display error message and exit
        print("ERROR: Missing domain file. Please make sure the file exists in the same directory.")
        print()
        parser.print_help()
        exit(1)

def check_key(key):
    headers = {'x-api-key': key}
    r = requests.get(CHECK_URL, headers=headers)
    data = r.json()
    if 'message' in data:
        print('ERROR: Invalid API Key.')
        exit(1)
    elif 'credits' in data:
        if(data['credits'] > 0):
            return data['credits'] 
        print('ERROR: No credit available to use.')
        exit(1)
    else:
        print("ERROR: System error. Please try again.")
        exit(1)

def get_domains_list(path):
    with open(path, 'r') as reader:
        domains = reader.read().splitlines()

    
    return [x if x[:5]=='https' else 'https://' + x for x in domains  ]
    
main()

