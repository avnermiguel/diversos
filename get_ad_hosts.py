#!/usr/bin/env python3
import os
import json
import sys

# Agora podemos importar o NTLM com segurança graças ao OpenSSL Legacy na imagem 8.0
from ldap3 import Server, Connection, ALL, NTLM 

def get_inventory():
    # Puxa as variáveis injetadas pelo Custom Credential Type do AWX
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    
    server_addr = "10.0.0.4"
    search_base = 'DC=local,DC=info' 

    # Estrutura base que o AWX/Ansible espera ler
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
        # Validação de segurança para garantir que a credencial foi mapeada
        if not user or not password:
            raise Exception("Credenciais AD_USER ou AD_PASSWORD nao encontradas no ambiente do AWX.")

        # Definimos o servidor na porta 389 (sem SSL)
        server = Server(server_addr, port=389, get_info=ALL)

        # O NTLM obriga o uso do domínio NetBIOS antes do usuário.
        # Se você digitou só 'administrador' no AWX, ele vira 'LOCAL\administrador'
        formatted_user = user if "\\" in user else f"LOCAL\\{user}"

        # Realiza o Bind com autenticação NTLM. Isso satisfaz a exigência de segurança do Windows!
        with Connection(server, user=formatted_user, password=password, authentication=NTLM, auto_bind=True) as conn:
            
            # Faz a busca por todos os computadores no domínio
            conn.search(
                search_base=search_base,
                search_filter='(objectClass=computer)',
                attributes=['dNSHostName']
            )
            
            # Varre o resultado e adiciona ao inventário do Ansible
            for entry in conn.entries:
                hostname = str(entry.dNSHostName)
                # Remove entradas vazias ou corrompidas
                if hostname and hostname != 'None':
                    inventory["all"]["hosts"].append(hostname)

    except Exception as e:
        # Imprime no log do AWX (stderr) para debug, sem quebrar o formato JSON de saída
        sys.stderr.write(f"ERRO DE CONEXÃO AD: {str(e)}\n")

    return inventory

if __name__ == "__main__":
    # O AWX lê a saída padrão (stdout)
    print(json.dumps(get_inventory(), indent=2))
