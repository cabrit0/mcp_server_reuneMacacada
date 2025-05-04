# Guia de Integração Flutter para o MCP Server v1.1.3

Este guia fornece instruções detalhadas para integrar o MCP Server com aplicativos Flutter, permitindo a geração e exibição de planos de aprendizagem personalizados.

## Índice

1. [Visão Geral](#visão-geral)
2. [Configuração Inicial](#configuração-inicial)
3. [Modelos de Dados](#modelos-de-dados)
4. [Serviços de API](#serviços-de-api)
5. [Widgets e UI](#widgets-e-ui)
6. [Sistema de Tarefas Assíncronas](#sistema-de-tarefas-assíncronas)
7. [Tratamento de Erros](#tratamento-de-erros)
8. [Exemplos Completos](#exemplos-completos)
9. [Melhores Práticas](#melhores-práticas)

## Visão Geral

O MCP Server fornece uma API para gerar planos de aprendizagem (Master Content Plans ou MCPs) baseados em tópicos. A integração com Flutter permite que você:

- Gere planos de aprendizagem personalizados
- Exiba esses planos em uma interface amigável
- Acompanhe o progresso de geração em tempo real
- Armazene planos localmente para acesso offline

Este guia aborda todos os aspectos da integração, desde a configuração inicial até exemplos completos de implementação.

## Configuração Inicial

### Dependências Necessárias

Adicione as seguintes dependências ao seu arquivo `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^0.13.5
  provider: ^6.0.5
  shared_preferences: ^2.1.0
  flutter_cache_manager: ^3.3.0
  connectivity_plus: ^3.0.3
```

### Configuração do Ambiente

Crie um arquivo de configuração para armazenar as URLs da API:

```dart
// lib/config/api_config.dart
class ApiConfig {
  static const String baseUrl = 'https://reunemacacada.onrender.com';
  static const String localBaseUrl = 'http://localhost:8000';

  // Use a URL de produção por padrão, mas permita alternar para desenvolvimento
  static String currentBaseUrl = baseUrl;

  // Endpoints
  static String get healthEndpoint => '$currentBaseUrl/health';
  static String get generateMcpEndpoint => '$currentBaseUrl/generate_mcp';
  static String get generateMcpAsyncEndpoint => '$currentBaseUrl/generate_mcp_async';
  static String get taskStatusEndpoint => '$currentBaseUrl/status';
  static String get tasksEndpoint => '$currentBaseUrl/tasks';

  // Método para alternar entre produção e desenvolvimento
  static void toggleEnvironment(bool useProduction) {
    currentBaseUrl = useProduction ? baseUrl : localBaseUrl;
  }
}
```

### Verificação de Conectividade

Implemente uma classe para verificar a conectividade com a internet:

```dart
// lib/services/connectivity_service.dart
import 'package:connectivity_plus/connectivity_plus.dart';

class ConnectivityService {
  Future<bool> isConnected() async {
    var connectivityResult = await Connectivity().checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }

  Stream<ConnectivityResult> get connectivityStream =>
      Connectivity().onConnectivityChanged;
}
```

## Modelos de Dados

Para trabalhar com os dados retornados pela API, você precisará criar modelos Dart correspondentes aos modelos JSON da API. Aqui estão os principais modelos necessários:

### Modelo MCP

```dart
// lib/models/mcp.dart
import 'dart:convert';
import 'package:flutter/foundation.dart';

class MCP {
  final String id;
  final String title;
  final String description;
  final String topic;
  final String category;
  final String language;
  final Map<String, Node> nodes;
  final int totalHours;
  final List<String> tags;

  MCP({
    required this.id,
    required this.title,
    required this.description,
    required this.topic,
    required this.category,
    required this.language,
    required this.nodes,
    required this.totalHours,
    required this.tags,
  });

  factory MCP.fromJson(Map<String, dynamic> json) {
    Map<String, Node> nodesMap = {};
    json['nodes'].forEach((key, value) {
      nodesMap[key] = Node.fromJson(value);
    });

    return MCP(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      topic: json['topic'],
      category: json['category'],
      language: json['language'],
      nodes: nodesMap,
      totalHours: json['totalHours'],
      tags: List<String>.from(json['tags']),
    );
  }

  Map<String, dynamic> toJson() {
    Map<String, dynamic> nodesJson = {};
    nodes.forEach((key, value) {
      nodesJson[key] = value.toJson();
    });

    return {
      'id': id,
      'title': title,
      'description': description,
      'topic': topic,
      'category': category,
      'language': language,
      'nodes': nodesJson,
      'totalHours': totalHours,
      'tags': tags,
    };
  }

  // Método para serializar para armazenamento local
  String toJsonString() => jsonEncode(toJson());

  // Método para deserializar do armazenamento local
  static MCP fromJsonString(String jsonString) =>
      MCP.fromJson(jsonDecode(jsonString));
}
```

### Modelo Node

```dart
// lib/models/node.dart
class Node {
  final String id;
  final String title;
  final String description;
  final String type;
  final List<Resource> resources;
  final List<String> prerequisites;
  final VisualPosition visualPosition;
  final Quiz? quiz;

  Node({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.resources,
    required this.prerequisites,
    required this.visualPosition,
    this.quiz,
  });

  factory Node.fromJson(Map<String, dynamic> json) {
    return Node(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      type: json['type'],
      resources: (json['resources'] as List)
          .map((resource) => Resource.fromJson(resource))
          .toList(),
      prerequisites: List<String>.from(json['prerequisites']),
      visualPosition: VisualPosition.fromJson(json['visualPosition']),
      quiz: json['quiz'] != null ? Quiz.fromJson(json['quiz']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'type': type,
      'resources': resources.map((resource) => resource.toJson()).toList(),
      'prerequisites': prerequisites,
      'visualPosition': visualPosition.toJson(),
      'quiz': quiz?.toJson(),
    };
  }
}

class VisualPosition {
  final double x;
  final double y;
  final int level;

  VisualPosition({
    required this.x,
    required this.y,
    required this.level,
  });

  factory VisualPosition.fromJson(Map<String, dynamic> json) {
    return VisualPosition(
      x: json['x'].toDouble(),
      y: json['y'].toDouble(),
      level: json['level'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'x': x,
      'y': y,
      'level': level,
    };
  }
}
```

### Modelo Resource

```dart
// lib/models/resource.dart
class Resource {
  final String id;
  final String title;
  final String url;
  final String type;
  final String? description;
  final int? duration;
  final int? readTime;
  final String? difficulty;
  final String? thumbnail;

  Resource({
    required this.id,
    required this.title,
    required this.url,
    required this.type,
    this.description,
    this.duration,
    this.readTime,
    this.difficulty,
    this.thumbnail,
  });

  factory Resource.fromJson(Map<String, dynamic> json) {
    return Resource(
      id: json['id'],
      title: json['title'],
      url: json['url'],
      type: json['type'],
      description: json['description'],
      duration: json['duration'],
      readTime: json['readTime'],
      difficulty: json['difficulty'],
      thumbnail: json['thumbnail'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'url': url,
      'type': type,
      'description': description,
      'duration': duration,
      'readTime': readTime,
      'difficulty': difficulty,
      'thumbnail': thumbnail,
    };
  }
}
```

### Modelo Quiz

```dart
// lib/models/quiz.dart
class Quiz {
  final List<Question> questions;
  final int passingScore;

  Quiz({
    required this.questions,
    required this.passingScore,
  });

  factory Quiz.fromJson(Map<String, dynamic> json) {
    return Quiz(
      questions: (json['questions'] as List)
          .map((question) => Question.fromJson(question))
          .toList(),
      passingScore: json['passingScore'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'questions': questions.map((question) => question.toJson()).toList(),
      'passingScore': passingScore,
    };
  }
}

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

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json['id'],
      text: json['text'],
      options: List<String>.from(json['options']),
      correctOptionIndex: json['correctOptionIndex'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'options': options,
      'correctOptionIndex': correctOptionIndex,
    };
  }
}
```

### Modelo Task

```dart
// lib/models/task.dart
class Task {
  final String id;
  final String description;
  final String status;
  final int progress;
  final dynamic result;
  final String? error;
  final double createdAt;
  final double updatedAt;
  final double? completedAt;
  final List<TaskMessage> messages;

  Task({
    required this.id,
    required this.description,
    required this.status,
    required this.progress,
    this.result,
    this.error,
    required this.createdAt,
    required this.updatedAt,
    this.completedAt,
    required this.messages,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'],
      description: json['description'],
      status: json['status'],
      progress: json['progress'],
      result: json['result'],
      error: json['error'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
      completedAt: json['completed_at'],
      messages: json['messages'] != null
          ? (json['messages'] as List)
              .map((message) => TaskMessage.fromJson(message))
              .toList()
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'status': status,
      'progress': progress,
      'result': result,
      'error': error,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'completed_at': completedAt,
      'messages': messages.map((message) => message.toJson()).toList(),
    };
  }

  // Método para verificar se a tarefa está concluída
  bool get isCompleted => status == 'completed';

  // Método para verificar se a tarefa falhou
  bool get isFailed => status == 'failed';

  // Método para verificar se a tarefa está em execução
  bool get isRunning => status == 'running';

  // Método para obter o MCP resultante (se a tarefa estiver concluída)
  MCP? getMcpResult() {
    if (isCompleted && result != null) {
      return MCP.fromJson(result);
    }
    return null;
  }
}

class TaskMessage {
  final double time;
  final String message;

  TaskMessage({
    required this.time,
    required this.message,
  });

  factory TaskMessage.fromJson(Map<String, dynamic> json) {
    return TaskMessage(
      time: json['time'],
      message: json['message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'time': time,
      'message': message,
    };
  }
}
```

### Modelo TaskCreationResponse

```dart
// lib/models/task_creation_response.dart
class TaskCreationResponse {
  final String taskId;
  final String? message;

  TaskCreationResponse({
    required this.taskId,
    this.message,
  });

  factory TaskCreationResponse.fromJson(Map<String, dynamic> json) {
    return TaskCreationResponse(
      taskId: json['task_id'],
      message: json['message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'task_id': taskId,
      'message': message,
    };
  }
}
```

Estes modelos fornecem a base para trabalhar com os dados retornados pela API do MCP Server. Na próxima seção, implementaremos os serviços para comunicação com a API.

## Serviços de API

Para comunicação com a API do MCP Server, vamos criar serviços dedicados que encapsulam as chamadas HTTP e o processamento de respostas.

### Serviço Base

Primeiro, crie um serviço base que lida com a lógica comum de requisições HTTP:

```dart
// lib/services/api_service_base.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiServiceException implements Exception {
  final String message;
  final int? statusCode;

  ApiServiceException(this.message, {this.statusCode});

  @override
  String toString() => 'ApiServiceException: $message (Status Code: $statusCode)';
}

class ApiServiceBase {
  final http.Client _client;

  ApiServiceBase({http.Client? client}) : _client = client ?? http.Client();

  // Método para fazer requisições GET
  Future<Map<String, dynamic>> get(String url) async {
    try {
      final response = await _client.get(Uri.parse(url));
      return _processResponse(response);
    } catch (e) {
      throw ApiServiceException('Erro na requisição GET: $e');
    }
  }

  // Método para fazer requisições POST
  Future<Map<String, dynamic>> post(String url, {Map<String, dynamic>? body}) async {
    try {
      final response = await _client.post(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
        body: body != null ? jsonEncode(body) : null,
      );
      return _processResponse(response);
    } catch (e) {
      throw ApiServiceException('Erro na requisição POST: $e');
    }
  }

  // Método para processar respostas HTTP
  Map<String, dynamic> _processResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      try {
        return jsonDecode(response.body);
      } catch (e) {
        throw ApiServiceException('Erro ao decodificar resposta: $e');
      }
    } else {
      String errorMessage;
      try {
        final errorJson = jsonDecode(response.body);
        errorMessage = errorJson['detail'] ?? 'Erro desconhecido';
      } catch (e) {
        errorMessage = response.body;
      }
      throw ApiServiceException(errorMessage, statusCode: response.statusCode);
    }
  }
}
```

### Serviço MCP

Em seguida, crie um serviço específico para operações relacionadas a MCPs:

```dart
// lib/services/mcp_service.dart
import 'dart:convert';
import '../config/api_config.dart';
import '../models/mcp.dart';
import '../models/task_creation_response.dart';
import 'api_service_base.dart';

class McpService extends ApiServiceBase {
  // Verificar a saúde do servidor
  Future<bool> checkHealth() async {
    try {
      final response = await get(ApiConfig.healthEndpoint);
      return response['status'] == 'ok';
    } catch (e) {
      return false;
    }
  }

  // Gerar MCP de forma síncrona
  Future<MCP> generateMcp({
    required String topic,
    int maxResources = 15,
    int numNodes = 15,
    int minWidth = 3,
    int maxWidth = 5,
    int minHeight = 3,
    int maxHeight = 7,
    String language = 'pt',
    String? category,
  }) async {
    final queryParams = {
      'topic': topic,
      'max_resources': maxResources.toString(),
      'num_nodes': numNodes.toString(),
      'min_width': minWidth.toString(),
      'max_width': maxWidth.toString(),
      'min_height': minHeight.toString(),
      'max_height': maxHeight.toString(),
      'language': language,
    };

    if (category != null) {
      queryParams['category'] = category;
    }

    final url = Uri.parse(ApiConfig.generateMcpEndpoint)
        .replace(queryParameters: queryParams)
        .toString();

    final response = await get(url);
    return MCP.fromJson(response);
  }

  // Gerar MCP de forma assíncrona
  Future<TaskCreationResponse> generateMcpAsync({
    required String topic,
    int maxResources = 15,
    int numNodes = 15,
    int minWidth = 3,
    int maxWidth = 5,
    int minHeight = 3,
    int maxHeight = 7,
    String language = 'pt',
    String? category,
  }) async {
    final queryParams = {
      'topic': topic,
      'max_resources': maxResources.toString(),
      'num_nodes': numNodes.toString(),
      'min_width': minWidth.toString(),
      'max_width': maxWidth.toString(),
      'min_height': minHeight.toString(),
      'max_height': maxHeight.toString(),
      'language': language,
    };

    if (category != null) {
      queryParams['category'] = category;
    }

    final url = Uri.parse(ApiConfig.generateMcpAsyncEndpoint)
        .replace(queryParameters: queryParams)
        .toString();

    final response = await post(url);
    return TaskCreationResponse.fromJson(response);
  }
}
```

### Serviço de Tarefas

Crie um serviço para gerenciar tarefas assíncronas:

```dart
// lib/services/task_service.dart
import '../config/api_config.dart';
import '../models/task.dart';
import 'api_service_base.dart';

class TaskService extends ApiServiceBase {
  // Obter o status de uma tarefa
  Future<Task> getTaskStatus(String taskId) async {
    final url = '${ApiConfig.taskStatusEndpoint}/$taskId';
    final response = await get(url);
    return Task.fromJson(response);
  }

  // Listar todas as tarefas
  Future<List<Task>> listTasks() async {
    final response = await get(ApiConfig.tasksEndpoint);
    return (response as List).map((task) => Task.fromJson(task)).toList();
  }

  // Verificar periodicamente o status de uma tarefa
  Stream<Task> pollTaskStatus(String taskId, {Duration interval = const Duration(seconds: 2)}) async* {
    while (true) {
      final task = await getTaskStatus(taskId);
      yield task;

      // Se a tarefa estiver concluída ou falhou, pare de verificar
      if (task.isCompleted || task.isFailed) {
        break;
      }

      await Future.delayed(interval);
    }
  }
}
```

### Serviço de Cache

Crie um serviço para gerenciar o cache local de MCPs:

```dart
// lib/services/cache_service.dart
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/mcp.dart';

class CacheService {
  static const String _mcpCachePrefix = 'mcp_cache_';

  // Salvar um MCP no cache
  Future<bool> cacheMcp(MCP mcp) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = '$_mcpCachePrefix${mcp.topic}_${mcp.language}';
      return await prefs.setString(key, mcp.toJsonString());
    } catch (e) {
      print('Erro ao salvar MCP no cache: $e');
      return false;
    }
  }

  // Obter um MCP do cache
  Future<MCP?> getCachedMcp(String topic, String language) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = '${_mcpCachePrefix}${topic}_$language';
      final jsonString = prefs.getString(key);

      if (jsonString != null) {
        return MCP.fromJsonString(jsonString);
      }
      return null;
    } catch (e) {
      print('Erro ao obter MCP do cache: $e');
      return null;
    }
  }

  // Verificar se um MCP está no cache
  Future<bool> hasCachedMcp(String topic, String language) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = '${_mcpCachePrefix}${topic}_$language';
      return prefs.containsKey(key);
    } catch (e) {
      print('Erro ao verificar cache de MCP: $e');
      return false;
    }
  }

  // Limpar o cache de MCPs
  Future<bool> clearMcpCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final keys = prefs.getKeys().where((key) => key.startsWith(_mcpCachePrefix));

      for (final key in keys) {
        await prefs.remove(key);
      }

      return true;
    } catch (e) {
      print('Erro ao limpar cache de MCPs: $e');
      return false;
    }
  }

  // Listar todos os MCPs em cache
  Future<List<MCP>> listCachedMcps() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final keys = prefs.getKeys().where((key) => key.startsWith(_mcpCachePrefix));
      final mcps = <MCP>[];

      for (final key in keys) {
        final jsonString = prefs.getString(key);
        if (jsonString != null) {
          try {
            mcps.add(MCP.fromJsonString(jsonString));
          } catch (e) {
            print('Erro ao decodificar MCP do cache: $e');
          }
        }
      }

      return mcps;
    } catch (e) {
      print('Erro ao listar MCPs em cache: $e');
      return [];
    }
  }
}
```

### Provedor de MCP

Para facilitar o gerenciamento de estado, crie um provedor usando o pacote Provider:

```dart
// lib/providers/mcp_provider.dart
import 'package:flutter/foundation.dart';
import '../models/mcp.dart';
import '../models/task.dart';
import '../services/mcp_service.dart';
import '../services/task_service.dart';
import '../services/cache_service.dart';

enum McpLoadingStatus {
  idle,
  loading,
  success,
  error,
}

class McpProvider with ChangeNotifier {
  final McpService _mcpService;
  final TaskService _taskService;
  final CacheService _cacheService;

  McpLoadingStatus _status = McpLoadingStatus.idle;
  MCP? _currentMcp;
  String? _error;
  Task? _currentTask;
  bool _isPolling = false;

  McpProvider({
    McpService? mcpService,
    TaskService? taskService,
    CacheService? cacheService,
  }) :
    _mcpService = mcpService ?? McpService(),
    _taskService = taskService ?? TaskService(),
    _cacheService = cacheService ?? CacheService();

  McpLoadingStatus get status => _status;
  MCP? get currentMcp => _currentMcp;
  String? get error => _error;
  Task? get currentTask => _currentTask;
  bool get isPolling => _isPolling;

  // Gerar MCP de forma síncrona
  Future<void> generateMcp({
    required String topic,
    int maxResources = 15,
    int numNodes = 15,
    int minWidth = 3,
    int maxWidth = 5,
    int minHeight = 3,
    int maxHeight = 7,
    String language = 'pt',
    String? category,
    bool useCache = true,
  }) async {
    try {
      _status = McpLoadingStatus.loading;
      _error = null;
      notifyListeners();

      // Verificar cache primeiro
      if (useCache) {
        final cachedMcp = await _cacheService.getCachedMcp(topic, language);
        if (cachedMcp != null) {
          _currentMcp = cachedMcp;
          _status = McpLoadingStatus.success;
          notifyListeners();
          return;
        }
      }

      // Gerar novo MCP
      final mcp = await _mcpService.generateMcp(
        topic: topic,
        maxResources: maxResources,
        numNodes: numNodes,
        minWidth: minWidth,
        maxWidth: maxWidth,
        minHeight: minHeight,
        maxHeight: maxHeight,
        language: language,
        category: category,
      );

      _currentMcp = mcp;
      _status = McpLoadingStatus.success;

      // Salvar no cache
      await _cacheService.cacheMcp(mcp);

    } catch (e) {
      _status = McpLoadingStatus.error;
      _error = e.toString();
    } finally {
      notifyListeners();
    }
  }

  // Gerar MCP de forma assíncrona
  Future<void> generateMcpAsync({
    required String topic,
    int maxResources = 15,
    int numNodes = 15,
    int minWidth = 3,
    int maxWidth = 5,
    int minHeight = 3,
    int maxHeight = 7,
    String language = 'pt',
    String? category,
    bool useCache = true,
  }) async {
    try {
      _status = McpLoadingStatus.loading;
      _error = null;
      _currentTask = null;
      notifyListeners();

      // Verificar cache primeiro
      if (useCache) {
        final cachedMcp = await _cacheService.getCachedMcp(topic, language);
        if (cachedMcp != null) {
          _currentMcp = cachedMcp;
          _status = McpLoadingStatus.success;
          notifyListeners();
          return;
        }
      }

      // Iniciar tarefa assíncrona
      final response = await _mcpService.generateMcpAsync(
        topic: topic,
        maxResources: maxResources,
        numNodes: numNodes,
        minWidth: minWidth,
        maxWidth: maxWidth,
        minHeight: minHeight,
        maxHeight: maxHeight,
        language: language,
        category: category,
      );

      // Iniciar polling para acompanhar o progresso
      _startPolling(response.taskId);

    } catch (e) {
      _status = McpLoadingStatus.error;
      _error = e.toString();
      notifyListeners();
    }
  }

  // Iniciar polling para acompanhar o progresso da tarefa
  void _startPolling(String taskId) {
    if (_isPolling) return;

    _isPolling = true;
    notifyListeners();

    _taskService.pollTaskStatus(taskId).listen(
      (task) {
        _currentTask = task;
        notifyListeners();

        // Se a tarefa estiver concluída, obter o MCP resultante
        if (task.isCompleted && task.result != null) {
          _currentMcp = task.getMcpResult();
          _status = McpLoadingStatus.success;

          // Salvar no cache
          if (_currentMcp != null) {
            _cacheService.cacheMcp(_currentMcp!);
          }
        }

        // Se a tarefa falhou, atualizar o status
        if (task.isFailed) {
          _status = McpLoadingStatus.error;
          _error = task.error ?? 'Erro desconhecido ao gerar MCP';
        }
      },
      onError: (e) {
        _status = McpLoadingStatus.error;
        _error = e.toString();
        _isPolling = false;
        notifyListeners();
      },
      onDone: () {
        _isPolling = false;
        notifyListeners();
      },
    );
  }

  // Limpar o estado atual
  void clear() {
    _status = McpLoadingStatus.idle;
    _currentMcp = null;
    _error = null;
    _currentTask = null;
    _isPolling = false;
    notifyListeners();
  }

  // Carregar um MCP do cache
  Future<bool> loadFromCache(String topic, String language) async {
    try {
      final cachedMcp = await _cacheService.getCachedMcp(topic, language);
      if (cachedMcp != null) {
        _currentMcp = cachedMcp;
        _status = McpLoadingStatus.success;
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      _error = e.toString();
      return false;
    }
  }

  // Listar todos os MCPs em cache
  Future<List<MCP>> listCachedMcps() async {
    return await _cacheService.listCachedMcps();
  }
}
```

Estes serviços fornecem uma camada de abstração para interagir com a API do MCP Server, gerenciar o cache local e acompanhar o progresso de tarefas assíncronas. Na próxima seção, implementaremos widgets para exibir os planos de aprendizagem.
