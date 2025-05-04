from api import MCPServerApp
import config

# Create FastAPI app
app = MCPServerApp(
    title="MCP Server",
    version="1.1.3"
).get_app()





if __name__ == "__main__":
    import uvicorn

    # Use configurações do arquivo config.py
    port = config.PORT
    debug = config.DEBUG

    print(f"Iniciando MCP Server na porta {port}")
    print(f"URL base: {config.BASE_URL}")
    print(f"Modo de depuração: {'Ativado' if debug else 'Desativado'}")
    print("")
    print("O servidor estará disponível em:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Rede: http://0.0.0.0:{port}")
    print("")
    print("Pressione Ctrl+C para encerrar o servidor")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
