#!/usr/bin/env python3
import os
import json
import sys
from ldap3 import Server, Connection, ALL

def get_inventory():
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    # Use o IP do seu Domain Controller se o nome não resolver!
    server_addr = "10.0.0.4" # <-- TROQUE PELO IP DO SEU WINDOWS SERVER (DC)

    inventory = {
        "all": {
            "hosts": [], 
            "vars": {
                "ansible_connection": "winrm",
                "ansible_port": 5985,
                "ansible_winrm_transport": "ntlm",
                "ansible_winrm_server_cert_validation": "ignore"
            }
        },
        "_meta": {"hostvars": {}}
    }

    try:
        server = Server(server_addr, get_info=ALL, use_ssl=False)
        with Connection(server, user=user, password=password, auto_bind=True) as conn:
            # AJUSTE O search_base para o seu domínio real!
            # Se seu domínio é "local.info", use 'DC=local,DC=info'
            conn.search(search_base='DC=local,DC=info', 
                        search_filter='(objectClass=computer)',
                        attributes=['dNSHostName'])
            
            for entry in conn.entries:
                hostname = str(entry.dNSHostName)
                if hostname and hostname != 'None':
                    inventory["all"]["hosts"].append(hostname)
                    # Forçamos o IP para evitar erro de DNS no AWX
                    # inventory["_meta"]["hostvars"][hostname] = {"ansible_host": "10.0.0.5"}
    except Exception as e:
        # Isso vai aparecer no log do AWX se der erro
        sys.stderr.write(f"ERRO DE CONEXÃO AD: {str(e)}\n")

    return inventory

if __name__ == "__main__":
    print(json.dumps(get_inventory()))
