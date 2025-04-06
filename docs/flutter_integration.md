# Integração com Flutter

Este documento explica como integrar o MCP Server com aplicações Flutter, considerando as novas funcionalidades implementadas.

## Visão Geral

O MCP Server fornece uma API RESTful que pode ser facilmente consumida por aplicações Flutter. A integração permite que sua aplicação Flutter gere planos de aprendizagem personalizados para qualquer tópico, com suporte para múltiplos idiomas e personalização do número de nós.

## Configuração no Flutter

### 1. Adicionar Dependências

Adicione as seguintes dependências ao seu arquivo `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  json_annotation: ^4.8.1

dev_dependencies:
  json_serializable: ^6.7.1
  build_runner: ^2.4.6
```

Execute `flutter pub get` para instalar as dependências.

### 2. Criar Modelos de Dados

Crie modelos de dados que correspondam à estrutura JSON retornada pelo MCP Server. Aqui está um exemplo simplificado:

```dart
// lib/models/mcp.dart
import 'package:json_annotation/json_annotation.dart';

part 'mcp.g.dart';

@JsonSerializable(explicitToJson: true)
class MCP {
  final String id;
  final String title;
  final String description;
  final String rootNodeId;
  final Metadata metadata;
  final Map<String, Node> nodes;

  MCP({
    required this.id,
    required this.title,
    required this.description,
    required this.rootNodeId,
    required this.metadata,
    required this.nodes,
  });

  factory MCP.fromJson(Map<String, dynamic> json) => _$MCPFromJson(json);
  Map<String, dynamic> toJson() => _$MCPToJson(this);
}

@JsonSerializable()
class Metadata {
  final String difficulty;
  final int estimatedHours;
  final List<String> tags;

  Metadata({
    required this.difficulty,
    required this.estimatedHours,
    required this.tags,
  });

  factory Metadata.fromJson(Map<String, dynamic> json) => _$MetadataFromJson(json);
  Map<String, dynamic> toJson() => _$MetadataToJson(this);
}

@JsonSerializable(explicitToJson: true)
class Node {
  final String id;
  final String title;
  final String description;
  final String type;
  final String state;
  final List<String> prerequisites;
  final List<Resource> resources;
  final Map<String, dynamic> visualPosition;
  final Quiz? quiz;

  Node({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.state,
    required this.prerequisites,
    required this.resources,
    required this.visualPosition,
    this.quiz,
  });

  factory Node.fromJson(Map<String, dynamic> json) => _$NodeFromJson(json);
  Map<String, dynamic> toJson() => _$NodeToJson(this);
}

@JsonSerializable()
class Resource {
  final String id;
  final String title;
  final String url;
  final String type;
  final String? description;
  final int? duration;
  final int? readTime;
  final String? difficulty;

  Resource({
    required this.id,
    required this.title,
    required this.url,
    required this.type,
    this.description,
    this.duration,
    this.readTime,
    this.difficulty,
  });

  factory Resource.fromJson(Map<String, dynamic> json) => _$ResourceFromJson(json);
  Map<String, dynamic> toJson() => _$ResourceToJson(this);
}

@JsonSerializable(explicitToJson: true)
class Quiz {
  final List<Question> questions;
  final int passingScore;

  Quiz({
    required this.questions,
    required this.passingScore,
  });

  factory Quiz.fromJson(Map<String, dynamic> json) => _$QuizFromJson(json);
  Map<String, dynamic> toJson() => _$QuizToJson(this);
}

@JsonSerializable()
class Question {
  final String id;
  final String text;
  final List<String> options;
  final int correctOptionIndex;

  Question({
    required this.id,
    required this.text,
    required this.options,
    required this.correctOptionIndex,
  });

  factory Question.fromJson(Map<String, dynamic> json) => _$QuestionFromJson(json);
  Map<String, dynamic> toJson() => _$QuestionToJson(this);
}
```

Gere os arquivos de serialização executando:

```
flutter pub run build_runner build
```

### 3. Criar Serviço para o MCP Server

Crie um serviço para interagir com o MCP Server:

```dart
// lib/services/mcp_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/mcp.dart';

class MCPService {
  final String baseUrl;
  
  MCPService({required this.baseUrl});
  
  Future<MCP> generateMCP({
    required String topic,
    int? maxResources,
    int? numNodes,
    String? language,
  }) async {
    // Construir a URL com os parâmetros
    final queryParams = {
      'topic': topic,
      if (maxResources != null) 'max_resources': maxResources.toString(),
      if (numNodes != null) 'num_nodes': numNodes.toString(),
      if (language != null) 'language': language,
    };
    
    final uri = Uri.parse('$baseUrl/generate_mcp').replace(
      queryParameters: queryParams,
    );
    
    try {
      final response = await http.get(uri);
      
      if (response.statusCode == 200) {
        final jsonData = json.decode(response.body);
        return MCP.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw Exception('Falha ao gerar MCP: ${errorData['detail'] ?? 'Erro desconhecido'}');
      }
    } catch (e) {
      throw Exception('Erro de conexão: $e');
    }
  }
  
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
```

## Uso no Flutter

### 1. Configurar o Serviço

Configure o serviço no seu aplicativo:

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'services/mcp_service.dart';

void main() {
  // Configurar o serviço com a URL do servidor
  final mcpService = MCPService(
    baseUrl: 'https://reunemacacada.onrender.com',
  );
  
  runApp(MyApp(mcpService: mcpService));
}

class MyApp extends StatelessWidget {
  final MCPService mcpService;
  
  const MyApp({Key? key, required this.mcpService}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MCP Flutter App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: HomePage(mcpService: mcpService),
    );
  }
}
```

### 2. Criar Tela para Gerar MCPs

Crie uma tela para permitir que os usuários gerem MCPs:

```dart
// lib/pages/home_page.dart
import 'package:flutter/material.dart';
import '../services/mcp_service.dart';
import '../models/mcp.dart';
import 'mcp_view_page.dart';

class HomePage extends StatefulWidget {
  final MCPService mcpService;
  
  const HomePage({Key? key, required this.mcpService}) : super(key: key);
  
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _formKey = GlobalKey<FormState>();
  final _topicController = TextEditingController();
  
  String? _selectedLanguage = 'pt';
  int _numNodes = 15;
  int _maxResources = 15;
  bool _isLoading = false;
  String? _errorMessage;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gerador de Planos de Aprendizagem'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _topicController,
                decoration: const InputDecoration(
                  labelText: 'Tópico',
                  hintText: 'Ex: Python, História do Brasil, Fotografia',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor, insira um tópico';
                  }
                  if (value.length < 3) {
                    return 'O tópico deve ter pelo menos 3 caracteres';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              
              DropdownButtonFormField<String>(
                value: _selectedLanguage,
                decoration: const InputDecoration(
                  labelText: 'Idioma',
                ),
                items: const [
                  DropdownMenuItem(value: 'pt', child: Text('Português')),
                  DropdownMenuItem(value: 'en', child: Text('Inglês')),
                  DropdownMenuItem(value: 'es', child: Text('Espanhol')),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedLanguage = value;
                  });
                },
              ),
              
              const SizedBox(height: 16),
              
              Text('Número de nós: $_numNodes'),
              Slider(
                value: _numNodes.toDouble(),
                min: 10,
                max: 30,
                divisions: 20,
                label: _numNodes.toString(),
                onChanged: (value) {
                  setState(() {
                    _numNodes = value.round();
                  });
                },
              ),
              
              const SizedBox(height: 16),
              
              Text('Máximo de recursos: $_maxResources'),
              Slider(
                value: _maxResources.toDouble(),
                min: 5,
                max: 30,
                divisions: 25,
                label: _maxResources.toString(),
                onChanged: (value) {
                  setState(() {
                    _maxResources = value.round();
                  });
                },
              ),
              
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              
              const Spacer(),
              
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _generateMCP,
                  child: _isLoading
                      ? const CircularProgressIndicator()
                      : const Text('Gerar Plano de Aprendizagem'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Future<void> _generateMCP() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
      
      try {
        final mcp = await widget.mcpService.generateMCP(
          topic: _topicController.text,
          maxResources: _maxResources,
          numNodes: _numNodes,
          language: _selectedLanguage,
        );
        
        if (!mounted) return;
        
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MCPViewPage(mcp: mcp),
          ),
        );
      } catch (e) {
        setState(() {
          _errorMessage = e.toString();
        });
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }
  
  @override
  void dispose() {
    _topicController.dispose();
    super.dispose();
  }
}
```

### 3. Criar Tela para Visualizar MCPs

Crie uma tela para visualizar os MCPs gerados:

```dart
// lib/pages/mcp_view_page.dart
import 'package:flutter/material.dart';
import '../models/mcp.dart';

class MCPViewPage extends StatelessWidget {
  final MCP mcp;
  
  const MCPViewPage({Key? key, required this.mcp}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    // Obter o nó raiz
    final rootNode = mcp.nodes[mcp.rootNodeId];
    if (rootNode == null) {
      return Scaffold(
        appBar: AppBar(title: Text(mcp.title)),
        body: const Center(child: Text('Erro: Nó raiz não encontrado')),
      );
    }
    
    // Construir a árvore de nós
    final nodeTree = _buildNodeTree(rootNode, mcp.nodes);
    
    return Scaffold(
      appBar: AppBar(
        title: Text(mcp.title),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              mcp.title,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              mcp.description,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 16),
            
            // Metadados
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Metadados',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text('Dificuldade: ${mcp.metadata.difficulty}'),
                    Text('Tempo estimado: ${mcp.metadata.estimatedHours} horas'),
                    Text('Tags: ${mcp.metadata.tags.join(", ")}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // Árvore de nós
            Text(
              'Plano de Aprendizagem',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            nodeTree,
          ],
        ),
      ),
    );
  }
  
  Widget _buildNodeTree(Node rootNode, Map<String, Node> allNodes) {
    return _buildNodeWidget(rootNode, allNodes, 0);
  }
  
  Widget _buildNodeWidget(Node node, Map<String, Node> allNodes, int depth) {
    // Encontrar nós filhos (nós que têm este nó como pré-requisito)
    final childNodes = allNodes.values
        .where((n) => n.prerequisites.contains(node.id))
        .toList();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Nó atual
        Card(
          margin: EdgeInsets.only(left: depth * 20.0, bottom: 8.0),
          child: ExpansionTile(
            title: Text(node.title),
            subtitle: Text(node.type),
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(node.description),
                    const SizedBox(height: 8),
                    
                    if (node.resources.isNotEmpty) ...[
                      const Text(
                        'Recursos:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      ...node.resources.map((resource) => ListTile(
                        title: Text(resource.title),
                        subtitle: Text('${resource.type} • ${resource.url}'),
                        onTap: () {
                          // Abrir URL (você precisará de um plugin como url_launcher)
                        },
                      )),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
        
        // Nós filhos
        if (childNodes.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(left: 20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: childNodes
                  .map((childNode) => _buildNodeWidget(
                        childNode,
                        allNodes,
                        depth + 1,
                      ))
                  .toList(),
            ),
          ),
      ],
    );
  }
}
```

## Tratamento de Erros

Implemente tratamento de erros adequado para lidar com falhas na API:

```dart
// lib/utils/error_handler.dart
import 'package:flutter/material.dart';

class ErrorHandler {
  static void showErrorDialog(BuildContext context, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Erro'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
  
  static String getErrorMessage(dynamic error) {
    if (error.toString().contains('Could not generate enough nodes')) {
      return 'Não foi possível gerar nós suficientes para este tópico. Tente um tópico mais amplo ou reduza o número mínimo de nós.';
    }
    
    if (error.toString().contains('No resources found')) {
      return 'Não foram encontrados recursos para este tópico. Tente outro tópico ou outro idioma.';
    }
    
    return 'Ocorreu um erro: ${error.toString()}';
  }
}
```

## Considerações de Performance

Para otimizar a experiência do usuário ao integrar com o MCP Server:

1. **Implementar Cache Local**: Armazene MCPs gerados localmente para evitar chamadas repetidas à API.

```dart
// lib/services/mcp_cache_service.dart
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/mcp.dart';

class MCPCacheService {
  static const String _cacheKeyPrefix = 'mcp_cache_';
  
  Future<void> cacheMCP({
    required String topic,
    required int? numNodes,
    required int? maxResources,
    required String? language,
    required MCP mcp,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _generateCacheKey(
      topic: topic,
      numNodes: numNodes,
      maxResources: maxResources,
      language: language,
    );
    
    await prefs.setString(key, json.encode(mcp.toJson()));
  }
  
  Future<MCP?> getCachedMCP({
    required String topic,
    required int? numNodes,
    required int? maxResources,
    required String? language,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _generateCacheKey(
      topic: topic,
      numNodes: numNodes,
      maxResources: maxResources,
      language: language,
    );
    
    final cachedData = prefs.getString(key);
    if (cachedData != null) {
      try {
        return MCP.fromJson(json.decode(cachedData));
      } catch (e) {
        return null;
      }
    }
    
    return null;
  }
  
  String _generateCacheKey({
    required String topic,
    required int? numNodes,
    required int? maxResources,
    required String? language,
  }) {
    return _cacheKeyPrefix +
        '${topic}_${numNodes ?? 15}_${maxResources ?? 15}_${language ?? 'pt'}';
  }
}
```

2. **Implementar Indicadores de Carregamento**: Mostre indicadores de progresso durante chamadas à API.

3. **Implementar Retry Logic**: Adicione lógica de retry para lidar com falhas temporárias de rede.

## Exemplo Completo de Integração

Aqui está um exemplo completo de como usar o serviço MCP em uma tela Flutter:

```dart
// lib/pages/topic_search_page.dart
import 'package:flutter/material.dart';
import '../services/mcp_service.dart';
import '../services/mcp_cache_service.dart';
import '../models/mcp.dart';
import '../utils/error_handler.dart';
import 'mcp_view_page.dart';

class TopicSearchPage extends StatefulWidget {
  final MCPService mcpService;
  final MCPCacheService cacheService;
  
  const TopicSearchPage({
    Key? key,
    required this.mcpService,
    required this.cacheService,
  }) : super(key: key);
  
  @override
  _TopicSearchPageState createState() => _TopicSearchPageState();
}

class _TopicSearchPageState extends State<TopicSearchPage> {
  final _searchController = TextEditingController();
  bool _isLoading = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Buscar Tópico'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                labelText: 'Tópico',
                hintText: 'Ex: Python, História do Brasil',
                suffixIcon: Icon(Icons.search),
              ),
              onSubmitted: (_) => _searchTopic(),
            ),
            const SizedBox(height: 16),
            
            ElevatedButton(
              onPressed: _isLoading ? null : _searchTopic,
              child: _isLoading
                  ? const CircularProgressIndicator()
                  : const Text('Gerar Plano de Aprendizagem'),
            ),
            
            const SizedBox(height: 24),
            
            const Text(
              'Tópicos Populares',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            
            Wrap(
              spacing: 8,
              children: [
                _buildTopicChip('Python'),
                _buildTopicChip('Flutter'),
                _buildTopicChip('História do Brasil'),
                _buildTopicChip('Fotografia'),
                _buildTopicChip('Machine Learning'),
                _buildTopicChip('Culinária'),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildTopicChip(String topic) {
    return ActionChip(
      label: Text(topic),
      onPressed: () {
        _searchController.text = topic;
        _searchTopic();
      },
    );
  }
  
  Future<void> _searchTopic() async {
    final topic = _searchController.text.trim();
    if (topic.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, insira um tópico')),
      );
      return;
    }
    
    setState(() {
      _isLoading = true;
    });
    
    try {
      // Verificar cache primeiro
      final cachedMCP = await widget.cacheService.getCachedMCP(
        topic: topic,
        numNodes: null,
        maxResources: null,
        language: null,
      );
      
      if (cachedMCP != null) {
        if (!mounted) return;
        
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MCPViewPage(mcp: cachedMCP),
          ),
        );
        return;
      }
      
      // Se não estiver em cache, buscar da API
      final mcp = await widget.mcpService.generateMCP(topic: topic);
      
      // Armazenar em cache
      await widget.cacheService.cacheMCP(
        topic: topic,
        numNodes: null,
        maxResources: null,
        language: null,
        mcp: mcp,
      );
      
      if (!mounted) return;
      
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => MCPViewPage(mcp: mcp),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      
      ErrorHandler.showErrorDialog(
        context,
        ErrorHandler.getErrorMessage(e),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
  
  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
```

## Conclusão

A integração do MCP Server com Flutter permite criar aplicativos de aprendizagem ricos e personalizados. Com as novas funcionalidades do servidor, você pode:

1. Gerar planos de aprendizagem para qualquer tema
2. Personalizar o número de nós e recursos
3. Suportar múltiplos idiomas, com foco em português
4. Aproveitar as otimizações de performance para uma experiência de usuário mais fluida

Lembre-se de implementar cache local e tratamento de erros adequado para lidar com as limitações do free tier do Render e proporcionar a melhor experiência possível aos usuários.
