#!/usr/bin/env python3
import os
import json
import sys
# Importamos NTLM para uma autenticação que o Windows aceita na 389
from ldap3 import Server, Connection, ALL, NTLM 

def get_inventory():
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    
    server_addr = "10.0.0.4" # Seu IP atualizado
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
        # Voltamos para a porta 389 (sem SSL)
        server = Server(server_addr, port=389, get_info=ALL)

        # Garante o formato DOMINIO\usuario para o NTLM
        # Se sua credencial já for 'LOCAL\usuario', o script mantém. 
        # Se for só 'usuario', ele adiciona 'LOCAL\' na frente.
        formatted_user = user if "\\" in user else f"LOCAL\\{user}"
        
        # Usamos authentication=NTLM. Isso geralmente contorna o 'strongerAuthRequired'
        # porque o NTLM já provê uma camada de assinatura/selamento própria.
        with Connection(server, user=user, password=password, authentication=NTLM, auto_bind=True) as conn:
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
