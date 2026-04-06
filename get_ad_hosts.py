#!/usr/bin/env python3
import os
import json
from ldap3 import Server, Connection, ALL

def get_inventory():
    # O AWX vai injetar isso via a Credencial Customizada que você criou
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    server_addr = "winserver2025.local.info" # IP ou FQDN do seu DC

    inventory = {
        "all": {"hosts": [], "vars": {
            "ansible_connection": "winrm",
            "ansible_port": 5985,
            "ansible_winrm_transport": "ntlm",
            "ansible_winrm_server_cert_validation": "ignore"
        }},
        "_meta": {"hostvars": {}}
    }

    try:
        server = Server(server_addr, get_info=ALL)
        with Connection(server, user=user, password=password, auto_bind=True) as conn:
            conn.search(search_base='DC=local,DC=info', # AJUSTE PARA O SEU DOMÍNIO
                        search_filter='(objectClass=computer)',
                        attributes=['dNSHostName', 'ipHostNumber'])
            
            for entry in conn.entries:
                hostname = str(entry.dNSHostName)
                if hostname and hostname != 'None':
                    inventory["all"]["hosts"].append(hostname)
    except Exception:
        pass # Silencioso para não quebrar o JSON se falhar

    return inventory

if __name__ == "__main__":
    print(json.dumps(get_inventory()))
