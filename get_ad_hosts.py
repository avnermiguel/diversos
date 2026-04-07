#!/usr/bin/env python3
import os
import json
import sys
import ssl
from ldap3 import Server, Connection, ALL, Tls

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
        if not user or not password:
            raise Exception("Credenciais AD_USER ou AD_PASSWORD nao encontradas.")

        # Ignora validação do certificado autoassinado do laboratório
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        
        # Conexão via LDAPS (636)
        server = Server(server_addr, port=636, use_ssl=True, tls=tls_config, get_info=ALL)

        # Garante o prefixo do domínio no usuário
        formatted_user = user if "\\" in user else f"LOCAL\\{user}"

        # Realiza o Bind
        with Connection(server, user=formatted_user, password=password, auto_bind=True) as conn:
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
