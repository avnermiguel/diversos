#!/usr/bin/env python3
import os
import json
import sys
from ldap3 import Server, Connection, ALL, NTLM 

def get_inventory():
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    
    server_addr = "10.0.0.4"
    # Certifique-se de que o search_base condiz com seu domínio
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
        if not user or not password:
            raise Exception("Credenciais AD_USER ou AD_PASSWORD nao encontradas no ambiente.")

        server = Server(server_addr, port=389, get_info=ALL)

        # AQUI ESTAVA O ERRO: Precisamos garantir o DOMINIO\usuario
        # Se seu dominio for diferente de LOCAL, mude o texto abaixo
        if "\\" not in user:
            formatted_user = f"LOCAL\\{user}"
        else:
            formatted_user = user

        # USANDO O FORMATTED_USER AQUI:
        with Connection(server, user=formatted_user, password=password, authentication=NTLM, auto_bind=True) as conn:
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
