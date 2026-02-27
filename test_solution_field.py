#!/usr/bin/env python3
import httpx
import json
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()
API_TOKEN = os.getenv('MOVIDESK_TOKEN')
BASE_URL = 'https://api.movidesk.com/public/v1'

print(f'Token: {API_TOKEN[:20]}...')
print(f'Base URL: {BASE_URL}')

# Teste 0: Lista de tickets (sem ID específico)
print('\n=== TESTE 0: Lista de tickets ===')
try:
    url = f'{BASE_URL}/tickets'
    params = {
        '$select': 'id,protocol,subject,createdDate',
        '$filter': "baseStatus ne 'Closed' and baseStatus ne 'Resolved'",
        '$top': '5',
        'token': API_TOKEN
    }
    
    response = httpx.get(url, params=params)
    print(f'URL: {response.request.url}')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print(f'✓ Encontrados {len(data)} tickets')
            print(f'Primeiro ticket: {data[0]}')
        else:
            print(f'Response type: {type(data)}, content: {data}')
    else:
        print(f'Response (truncated): {response.text[:500]}')
except Exception as e:
    print(f'✗ Exceção: {type(e).__name__}: {e}')

# Teste 1: Tentar slaSolutionDate 
print('\n=== TESTE 1: slaSolutionDate (lista) ===')
try:
    url = f'{BASE_URL}/tickets'
    params = {
        '$select': 'id,protocol,subject,slaSolutionDate,createdDate',
        '$top': '5',
        'token': API_TOKEN
    }
    
    response = httpx.get(url, params=params, timeout=10.0)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'✓ slaSolutionDate FUNCIONA!')
        print(json.dumps(data[:1] if isinstance(data, list) else data, indent=2, ensure_ascii=False))
    else:
        print(f'✗ Erro {response.status_code}')
        print(f'Response: {response.text[:300]}')
except Exception as e:
    print(f'✗ Exceção: {type(e).__name__}: {e}')

# Teste 2: Tentar solutionForecast
print('\n=== TESTE 2: solutionForecast (lista) ===')
try:
    url = f'{BASE_URL}/tickets'
    params = {
        '$select': 'id,protocol,subject,solutionForecast,createdDate',
        '$top': '5',
        'token': API_TOKEN
    }
    
    response = httpx.get(url, params=params, timeout=10.0)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'✓ solutionForecast FUNCIONA!')
        print(json.dumps(data[:1] if isinstance(data, list) else data, indent=2, ensure_ascii=False))
    else:
        print(f'✗ Erro {response.status_code}')
except Exception as e:
    print(f'✗ Exceção: {type(e).__name__}: {e}')

# Teste 3: Ambos juntos
print('\n=== TESTE 3: Ambos (slaSolutionDate + solutionForecast) ===')
try:
    url = f'{BASE_URL}/tickets'
    params = {
        '$select': 'id,protocol,subject,slaSolutionDate,solutionForecast,createdDate',
        '$top': '5',
        'token': API_TOKEN
    }
    
    response = httpx.get(url, params=params, timeout=10.0)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'✓ Ambos juntos FUNCIONAM!')
        print('Primeira entrada:')
        print(json.dumps(data[0] if isinstance(data, list) and data else data, indent=2, ensure_ascii=False))
    else:
        print(f'✗ Erro {response.status_code}')
        print(f'Response: {response.text[:300]}')
except Exception as e:
    print(f'✗ Exceção: {type(e).__name__}: {e}')


