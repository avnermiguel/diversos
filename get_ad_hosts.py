#!/usr/bin/env python3
import os
import json
import sys
from ldap3 import Server, Connection, ALL

def get_inventory():
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    
    server_addr = "10.0.0.4"
    search_base = 'DC=local,DC=info' 

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
        # Conexão direta na porta 389
        server = Server(server_addr, port=389, get_info=ALL)
        
        # Formato UPN (usuario@dominio) é o mais estável
        if "@" not in user and "\\" not in user:
            bind_user = f"{user}@local.info"
        else:
            bind_user = user

        # Bind SIMPLES (Agora vai funcionar porque baixamos a guarda do Windows no passo 1)
        with Connection(server, user=bind_user, password=password, auto_bind=True) as conn:
            conn.search(
                search_base=search_base,
                search_filter='(objectClass=computer)',
                attributes=['dNSHostName']
            )
            
            for entry in conn.entries:
                hostname = str(entry.dNSHostName)
                if hostname and hostname != 'None':
                    inventory["all"]["hosts"].append(hostname)

    except Exception as e:
        sys.stderr.write(f"ERRO DE CONEXÃO AD: {str(e)}\n")

    return inventory

if __name__ == "__main__":
    print(json.dumps(get_inventory(), indent=2))
