#!/usr/bin/env python3
"""
Script para testar as melhorias implementadas no MCP Server.
"""

import argparse
import json
import time
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()

def test_cache(base_url, topic="python"):
    """Testa o sistema de cache."""
    console.print(Panel.fit("Testando Sistema de Cache", style="bold blue"))
    
    # Primeira requisição (sem cache)
    console.print("Fazendo primeira requisição (sem cache)...")
    start_time = time.time()
    response = requests.get(f"{base_url}/generate_mcp?topic={topic}")
    first_time = time.time() - start_time
    
    if response.status_code != 200:
        console.print(f"[bold red]Erro na primeira requisição: {response.status_code}[/bold red]")
        return
    
    console.print(f"[green]Primeira requisição concluída em {first_time:.2f} segundos[/green]")
    
    # Segunda requisição (com cache)
    console.print("Fazendo segunda requisição (com cache)...")
    start_time = time.time()
    response = requests.get(f"{base_url}/generate_mcp?topic={topic}")
    second_time = time.time() - start_time
    
    if response.status_code != 200:
        console.print(f"[bold red]Erro na segunda requisição: {response.status_code}[/bold red]")
        return
    
    console.print(f"[green]Segunda requisição concluída em {second_time:.2f} segundos[/green]")
    
    # Comparação
    speedup = first_time / second_time if second_time > 0 else float('inf')
    console.print(f"[bold green]Aceleração com cache: {speedup:.2f}x mais rápido![/bold green]")
    
    # Verificar estatísticas do cache
    console.print("Verificando estatísticas do cache...")
    response = requests.get(f"{base_url}/cache/stats")
    
    if response.status_code == 200:
        stats = response.json()
        table = Table(title="Estatísticas do Cache")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Tamanho do Cache", str(stats.get("cache_size", "N/A")))
        table.add_row("Tamanho Máximo", str(stats.get("max_size", "N/A")))
        table.add_row("TTL (segundos)", str(stats.get("ttl_seconds", "N/A")))
        table.add_row("Tópicos em Cache", ", ".join(stats.get("cached_topics", [])))
        
        console.print(table)
    else:
        console.print(f"[bold red]Erro ao obter estatísticas do cache: {response.status_code}[/bold red]")

def test_personalization(base_url):
    """Testa a personalização de MCPs."""
    console.print(Panel.fit("Testando Personalização de MCPs", style="bold blue"))
    
    tests = [
        {
            "name": "MCP Padrão",
            "url": f"{base_url}/generate_mcp?topic=python",
            "description": "Geração padrão sem personalização"
        },
        {
            "name": "MCP para Iniciantes",
            "url": f"{base_url}/generate_mcp_v2?topic=python&difficulty=beginner",
            "description": "Filtrado por dificuldade: iniciante"
        },
        {
            "name": "MCP com Vídeos",
            "url": f"{base_url}/generate_mcp_v2?topic=python&formats=video",
            "description": "Filtrado por formato: vídeos"
        },
        {
            "name": "MCP Limitado por Tempo",
            "url": f"{base_url}/generate_mcp_v2?topic=python&max_hours=5",
            "description": "Limitado a 5 horas de aprendizagem"
        }
    ]
    
    results = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Testando personalizações...", total=len(tests))
        
        for test in tests:
            console.print(f"[yellow]Testando: {test['name']}[/yellow]")
            console.print(f"[dim]{test['description']}[/dim]")
            
            try:
                response = requests.get(test["url"])
                
                if response.status_code == 200:
                    data = response.json()
                    node_count = len(data.get("nodes", {}))
                    difficulty = data.get("metadata", {}).get("difficulty", "N/A")
                    hours = data.get("metadata", {}).get("estimatedHours", "N/A")
                    
                    results.append({
                        "name": test["name"],
                        "status": "Sucesso",
                        "nodes": node_count,
                        "difficulty": difficulty,
                        "hours": hours
                    })
                    
                    console.print(f"[green]Sucesso: {node_count} nós, dificuldade {difficulty}, {hours} horas[/green]")
                else:
                    results.append({
                        "name": test["name"],
                        "status": f"Erro: {response.status_code}",
                        "nodes": "N/A",
                        "difficulty": "N/A",
                        "hours": "N/A"
                    })
                    
                    console.print(f"[bold red]Erro: {response.status_code}[/bold red]")
            except Exception as e:
                results.append({
                    "name": test["name"],
                    "status": f"Exceção: {str(e)}",
                    "nodes": "N/A",
                    "difficulty": "N/A",
                    "hours": "N/A"
                })
                
                console.print(f"[bold red]Exceção: {str(e)}[/bold red]")
            
            progress.update(task, advance=1)
    
    # Mostrar resultados em tabela
    table = Table(title="Resultados da Personalização")
    table.add_column("Teste", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Nós", style="magenta")
    table.add_column("Dificuldade", style="yellow")
    table.add_column("Horas", style="blue")
    
    for result in results:
        table.add_row(
            result["name"],
            result["status"],
            str(result["nodes"]),
            str(result["difficulty"]),
            str(result["hours"])
        )
    
    console.print(table)

def test_languages(base_url, topic="programming"):
    """Testa o suporte a múltiplos idiomas."""
    console.print(Panel.fit("Testando Suporte a Múltiplos Idiomas", style="bold blue"))
    
    languages = [
        {"code": "en", "name": "Inglês"},
        {"code": "pt", "name": "Português"},
        {"code": "es", "name": "Espanhol"},
        {"code": "fr", "name": "Francês"},
        {"code": "de", "name": "Alemão"}
    ]
    
    results = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Testando idiomas...", total=len(languages))
        
        for lang in languages:
            console.print(f"[yellow]Testando: {lang['name']} ({lang['code']})[/yellow]")
            
            try:
                url = f"{base_url}/generate_mcp_v2?topic={topic}&language={lang['code']}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    node_count = len(data.get("nodes", {}))
                    
                    # Verificar se há recursos
                    resource_count = 0
                    for node in data.get("nodes", {}).values():
                        resource_count += len(node.get("resources", []))
                    
                    results.append({
                        "language": lang["name"],
                        "status": "Sucesso",
                        "nodes": node_count,
                        "resources": resource_count
                    })
                    
                    console.print(f"[green]Sucesso: {node_count} nós, {resource_count} recursos[/green]")
                else:
                    results.append({
                        "language": lang["name"],
                        "status": f"Erro: {response.status_code}",
                        "nodes": "N/A",
                        "resources": "N/A"
                    })
                    
                    console.print(f"[bold red]Erro: {response.status_code}[/bold red]")
            except Exception as e:
                results.append({
                    "language": lang["name"],
                    "status": f"Exceção: {str(e)}",
                    "nodes": "N/A",
                    "resources": "N/A"
                })
                
                console.print(f"[bold red]Exceção: {str(e)}[/bold red]")
            
            progress.update(task, advance=1)
    
    # Mostrar resultados em tabela
    table = Table(title="Resultados do Suporte a Idiomas")
    table.add_column("Idioma", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Nós", style="magenta")
    table.add_column("Recursos", style="yellow")
    
    for result in results:
        table.add_row(
            result["language"],
            result["status"],
            str(result["nodes"]),
            str(result["resources"])
        )
    
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Testa as melhorias do MCP Server")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base do servidor MCP")
    parser.add_argument("--topic", default="python", help="Tópico para usar nos testes")
    parser.add_argument("--test", choices=["all", "cache", "personalization", "languages"], default="all", help="Teste específico a executar")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(f"Testando MCP Server em {args.url}", style="bold green"))
    
    try:
        # Verificar se o servidor está online
        response = requests.get(f"{args.url}/health")
        if response.status_code != 200:
            console.print(f"[bold red]Erro: Servidor não está respondendo corretamente. Status: {response.status_code}[/bold red]")
            return
        
        console.print("[bold green]Servidor está online![/bold green]")
        
        # Executar testes selecionados
        if args.test in ["all", "cache"]:
            test_cache(args.url, args.topic)
            console.print()
        
        if args.test in ["all", "personalization"]:
            test_personalization(args.url)
            console.print()
        
        if args.test in ["all", "languages"]:
            test_languages(args.url, args.topic)
            console.print()
        
        console.print("[bold green]Testes concluídos![/bold green]")
    
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Erro: Não foi possível conectar ao servidor. Verifique se o servidor está em execução.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erro inesperado: {str(e)}[/bold red]")

if __name__ == "__main__":
    main()
