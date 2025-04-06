# Controle de Estrutura da Árvore

Este documento descreve os parâmetros de controle de estrutura da árvore de aprendizagem implementados no MCP Server v1.0.6.

## Visão Geral

O MCP Server agora permite um controle mais preciso sobre a estrutura das árvores de aprendizagem geradas, através de quatro novos parâmetros:

- `min_width`: Largura mínima da árvore (nós no primeiro nível)
- `max_width`: Largura máxima em qualquer nível da árvore
- `min_height`: Altura mínima da árvore (profundidade)
- `max_height`: Altura máxima da árvore (profundidade)

Estes parâmetros permitem gerar árvores com diferentes formas, desde árvores largas e rasas até árvores estreitas e profundas, dependendo do tópico e das preferências do usuário.

## Parâmetros de Controle

### 1. Controle de Largura

#### `min_width` (Largura Mínima)

- **Descrição**: Define o número mínimo de nós no primeiro nível da árvore (filhos diretos do nó raiz).
- **Valor Padrão**: 3
- **Valor Mínimo**: 2
- **Valor Máximo**: 10
- **Uso**: Útil para garantir que a árvore tenha uma diversidade mínima de subtópicos principais.

#### `max_width` (Largura Máxima)

- **Descrição**: Define o número máximo de nós em qualquer nível da árvore.
- **Valor Padrão**: 5
- **Valor Mínimo**: 3
- **Valor Máximo**: 15
- **Uso**: Útil para evitar que a árvore fique muito larga, o que pode dificultar a visualização.

### 2. Controle de Altura

#### `min_height` (Altura Mínima)

- **Descrição**: Define a profundidade mínima da árvore (número mínimo de níveis).
- **Valor Padrão**: 3
- **Valor Mínimo**: 2
- **Valor Máximo**: 8
- **Uso**: Útil para garantir que a árvore tenha uma profundidade mínima, explorando os tópicos em detalhes.

#### `max_height` (Altura Máxima)

- **Descrição**: Define a profundidade máxima da árvore (número máximo de níveis).
- **Valor Padrão**: 7
- **Valor Mínimo**: 3
- **Valor Máximo**: 12
- **Uso**: Útil para evitar que a árvore fique muito profunda, o que pode tornar o caminho de aprendizagem muito longo.

## Exemplos de Uso

### Árvore Larga e Rasa

```
GET /generate_mcp?topic=python&min_width=5&max_width=8&min_height=2&max_height=4
```

Esta configuração gera uma árvore com muitos nós no primeiro nível (5-8) e poucos níveis de profundidade (2-4), resultando em uma árvore larga e rasa. Ideal para tópicos que podem ser divididos em muitos subtópicos independentes.

### Árvore Estreita e Profunda

```
GET /generate_mcp?topic=python&min_width=2&max_width=3&min_height=5&max_height=10
```

Esta configuração gera uma árvore com poucos nós no primeiro nível (2-3) e muitos níveis de profundidade (5-10), resultando em uma árvore estreita e profunda. Ideal para tópicos que seguem uma progressão linear de aprendizagem.

### Árvore Balanceada

```
GET /generate_mcp?topic=python&min_width=3&max_width=5&min_height=3&max_height=7
```

Esta é a configuração padrão, que gera uma árvore balanceada com uma largura e profundidade moderadas. Adequada para a maioria dos tópicos.

## Implementação

A implementação do controle de estrutura da árvore foi feita no arquivo `path_generator.py`, modificando a função `create_node_structure` para usar os novos parâmetros ao criar a estrutura da árvore.

```python
async def create_node_structure(
    topic: str, 
    subtopics: List[str], 
    resources: List[Resource], 
    min_nodes: int = 15, 
    max_nodes: int = 28, 
    min_width: int = 3, 
    max_width: int = 5, 
    min_height: int = 3, 
    max_height: int = 7, 
    language: str = "pt"
) -> Tuple[Dict[str, Node], List[str]]:
    # ...
```

## Integração com Flutter

Para integrar o controle de estrutura da árvore em aplicativos Flutter, você pode adicionar controles na interface do usuário para permitir que os usuários personalizem a estrutura da árvore:

```dart
// Exemplo de interface para controlar a estrutura da árvore
Widget _buildTreeStructureControls() {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text("Estrutura da Árvore", style: TextStyle(fontWeight: FontWeight.bold)),
      Row(
        children: [
          Expanded(
            child: TextField(
              controller: _minWidthController,
              decoration: InputDecoration(labelText: "Largura Mínima"),
              keyboardType: TextInputType.number,
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            child: TextField(
              controller: _maxWidthController,
              decoration: InputDecoration(labelText: "Largura Máxima"),
              keyboardType: TextInputType.number,
            ),
          ),
        ],
      ),
      Row(
        children: [
          Expanded(
            child: TextField(
              controller: _minHeightController,
              decoration: InputDecoration(labelText: "Altura Mínima"),
              keyboardType: TextInputType.number,
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            child: TextField(
              controller: _maxHeightController,
              decoration: InputDecoration(labelText: "Altura Máxima"),
              keyboardType: TextInputType.number,
            ),
          ),
        ],
      ),
    ],
  );
}
```

Ou você pode oferecer opções predefinidas para simplificar a experiência do usuário:

```dart
// Opções predefinidas para a estrutura da árvore
enum TreeStructure {
  balanced,    // Balanceada (padrão)
  wideShallow, // Larga e rasa
  narrowDeep,  // Estreita e profunda
}

// Mapeamento de opções para parâmetros
Map<TreeStructure, Map<String, int>> treeStructureParams = {
  TreeStructure.balanced: {
    'min_width': 3, 'max_width': 5, 'min_height': 3, 'max_height': 7
  },
  TreeStructure.wideShallow: {
    'min_width': 5, 'max_width': 8, 'min_height': 2, 'max_height': 4
  },
  TreeStructure.narrowDeep: {
    'min_width': 2, 'max_width': 3, 'min_height': 5, 'max_height': 10
  },
};
```

## Benefícios

1. **Personalização**: Os usuários podem personalizar a estrutura da árvore de acordo com suas preferências e necessidades.

2. **Adaptação ao Tópico**: Diferentes tópicos podem se beneficiar de diferentes estruturas de árvore.

3. **Melhor Experiência de Aprendizagem**: Uma estrutura de árvore adequada pode facilitar a compreensão e a navegação pelo conteúdo.

4. **Visualização Otimizada**: Controlar a largura e a altura da árvore pode melhorar a visualização em diferentes dispositivos e tamanhos de tela.

## Limitações Atuais

1. **Aleatoriedade**: Ainda há um elemento de aleatoriedade na geração da árvore, o que significa que os parâmetros são usados como guias, mas a estrutura exata pode variar.

2. **Dependência do Tópico**: A estrutura da árvore também depende do tópico e dos recursos disponíveis, o que pode limitar o controle preciso.

## Trabalhos Futuros

1. **Visualização Prévia**: Implementar uma visualização prévia da estrutura da árvore antes de gerar o conteúdo completo.

2. **Mais Opções de Personalização**: Adicionar mais opções de personalização, como controle sobre a distribuição de recursos e quizzes.

3. **Algoritmos de Layout Avançados**: Implementar algoritmos de layout mais avançados para gerar árvores com estruturas específicas.

4. **Feedback do Usuário**: Coletar feedback dos usuários sobre as estruturas de árvore geradas para melhorar os algoritmos.
