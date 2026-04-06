#!/usr/bin/env python3
import os
import json
import sys
import ssl
from ldap3 import Server, Connection, ALL, Tls

def get_inventory():
    # Variáveis injetadas pela sua Credencial Customizada no AWX
    user = os.environ.get('AD_USER')
    password = os.environ.get('AD_PASSWORD')
    
    # --- CONFIGURAÇÕES DO AMBIENTE TRT22 ---
    # Use o IP do Domain Controller para evitar falhas de DNS no container
    server_addr = "10.0.0.4" 
    # Base de busca (Ajuste para o seu domínio real)
    search_base = 'DC=local,DC=info' 
    # ---------------------------------------

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
        # Configura o TLS para aceitar certificados autoassinados (ignora validação)
        # Isso resolve o erro 'strongerAuthRequired' ao usar a porta 636
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        
        # Define o servidor usando LDAPS (Porta 636)
        server = Server(server_addr, port=636, use_ssl=True, tls=tls_config, get_info=ALL)
        
        # Realiza o Bind (Autenticação)
        with Connection(server, user=user, password=password, auto_bind=True) as conn:
            # Busca por objetos do tipo 'computer'
            conn.search(
                search_base=search_base,
                search_filter='(objectClass=computer)',
                attributes=['dNSHostName']
            )
            
            for entry in conn.entries:
                hostname = str(entry.dNSHostName)
                # Filtra entradas vazias ou nulas
                if hostname and hostname != 'None':
                    inventory["all"]["hosts"].append(hostname)
                    # Opcional: Se o DNS não resolver no AWX, podemos forçar o IP aqui
                    # inventory["_meta"]["hostvars"][hostname] = {"ansible_host": "10.0.0.5"}

    except Exception as e:
        # Imprime o erro no stderr para aparecer no log do AWX, sem quebrar o JSON de saída
        sys.stderr.write(f"ERRO DE CONEXÃO AD: {str(e)}\n")

    return inventory

if __name__ == "__main__":
    # O Ansible Inventory espera um JSON na saída padrão (stdout)
    print(json.dumps(get_inventory(), indent=2))
