# BlueIris-Server-0Auth-PoC-Exploit
BlueIris-Server-0Auth-PoC-Exploit

A simple PoC with 0Auth system on BlueIris Server interface.

## Poc Usage:

    usage: poc.py [-h] [-u URL] [-a] [-i] [-l LIST]
    
    BlueIris Server no-auth (0auth) scanner.
    
    options:
      -h, --help            show this help message and exit
      -u URL, --url URL     Scan a single IP
      -a, --all             Scan with infos + capture
      -i, --info            Scan info only
      -l LIST, --list LIST  Scan from a file containing URLs (one per line)

// `python poc.py -u TARGET -i`

![iris_infos](https://github.com/user-attachments/assets/9dee7318-7446-4337-bb46-bae0a7c0c028)

// `python poc.py -u TARGET -a`

![iris_all](https://github.com/user-attachments/assets/6a14b9a5-81b6-489c-8d6a-b88206a16ed3)

## Requirements:

    pip install playwright

## Shodan:

    product:"Blue Server"

![total](https://github.com/user-attachments/assets/0155cb35-050e-4db4-b218-0dcab1e8afa8)

## Disclaimer:
This code is designed and distributed for educational and cyber research purposes. Any misuse or illegal use is not the responsibility of its developer.
