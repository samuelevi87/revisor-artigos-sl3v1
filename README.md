# RevisorArtigosSl3V1 Crew

## Descrição do Projeto

O projeto **RevisorArtigosSl3V1 Crew** é uma ferramenta desenvolvida para facilitar a leitura e revisão de artigos científicos, utilizando um sistema de agentes do framework CrewAI. Diante do volume crescente de estudos em Inteligência Artificial, torna-se desafiador acompanhar todas as publicações relevantes. Este projeto visa ajudar pesquisadores e entusiastas a se manterem atualizados, gerando relatórios sucintos que permitem uma avaliação rápida do interesse de cada artigo antes de um aprofundamento completo.

## Estrutura de Diretórios

A estrutura de diretórios do projeto é organizada para facilitar o desenvolvimento e a manutenção:

```
revisor_artigos_sl3v1/
│
├── .venv/                         # Ambiente virtual Python (não incluído no repositório)
├── db/                            # Banco de dados ou arquivos relacionados
├── src/                           # Código fonte principal do projeto
│   └── revisor_artigos_sl3v1/     # Módulo do projeto
│       ├── config/                # Arquivos de configuração YAML para agentes e tarefas
│       │   ├── agents.yaml        # Configurações dos agentes
│       │   └── tasks.yaml         # Configurações das tarefas
│       ├── resources/             # Recursos necessários para a execução
│       │   └── pdfs/              # Pasta de armazenamento dos PDFs a serem analisados
│       ├── tools/                 # Ferramentas customizadas para os agentes
│       │   ├── __init__.py        # Inicialização do módulo de ferramentas
│       │   ├── custom_tool.py     # Ferramenta customizada de exemplo
│       ├── crew.py                # Definição da classe da equipe do projeto
│       └── main.py                # Arquivo principal para execução do projeto
├── tests/                         # Testes automatizados do projeto
├── .env                           # Variáveis de ambiente para configuração
├── pyproject.toml                 # Configuração de dependências do projeto
└── README.md                      # Documentação do projeto
```

### Configuração do Ambiente

Antes de executar o projeto, é necessário configurar a chave de API do OpenAI:

1. Crie um arquivo chamado `.env` na raiz do projeto.
2. Adicione a seguinte linha ao arquivo:

   ```
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   ```

   Substitua `YOUR_OPENAI_API_KEY` pela sua chave de API válida.

3. Certifique-se de que o arquivo `.env` está no diretório correto.

### Exemplo de Uso

Siga os passos abaixo para executar o projeto e processar arquivos PDF:

1. **Prepare o Ambiente:**
   - Instale as dependências do projeto:
     ```bash
     pip install -r requirements.txt
     ```
   
2. **Adicione os PDFs à pasta:**
   - Coloque os arquivos PDF que deseja processar na pasta `src/revisor_artigos_sl3v1/resources/pdfs`.

3. **Execute o Projeto:**
   - Use o seguinte comando para iniciar o processamento:
     ```bash
     python src/revisor_artigos_sl3v1/main.py
     ```
   - Durante a execução, o projeto irá:
     - Carregar as configurações de agentes e tarefas.
     - Processar cada PDF encontrado na pasta especificada.
     - Gerar um arquivo YAML de saída com os resultados.

4. **Saída Esperada:**
   - O projeto gera um arquivo de saída em YAML contendo o resumo dos artigos processados. O arquivo é salvo na raiz do projeto e possui o seguinte formato:
     ```
     output_YYYYMMDD_HHMMSS.yaml
     ```

### Contribuição e Manutenção

Contribuir para o projeto é bem-vindo e incentivado! Siga as diretrizes abaixo para enviar suas contribuições:

1. **Faça um Fork do Repositório**:
   - Crie uma cópia do projeto em sua conta GitHub e clone-a localmente.

2. **Crie uma Nova Branch**:
   - Use uma branch separada para suas contribuições:
     ```bash
     git checkout -b feature/minha-nova-funcionalidade
     ```

3. **Teste suas Modificações**:
   - Certifique-se de que as alterações estão funcionando corretamente e não quebram o código existente.

4. **Envie um Pull Request**:
   - Após finalizar as alterações, envie um Pull Request para a branch principal do projeto.

5. **Diretrizes de Código**:
   - Mantenha o código claro e bem documentado.
   - Siga os padrões de codificação do projeto (ex.: pep8 para Python).
   - Inclua testes para novas funcionalidades ou correções de bugs.

### Depuração e Solução de Problemas

Embora o projeto seja projetado para funcionar de maneira robusta, alguns problemas comuns podem surgir devido às dependências:

1. **Verificação de Dependências:**
   - Certifique-se de que todas as dependências estão na versão correta, conforme especificado no arquivo `pyproject.toml`.
   - Se ocorrerem problemas de compatibilidade, tente reinstalar as dependências com o comando:
     ```bash
     pip install -r requirements.txt
     ```

2. **Versões do Python:**
   - Este projeto é testado para funcionar com versões específicas do Python (ex.: Python 3.8+). Certifique-se de estar usando uma versão compatível.

3. **Erro na API do OpenAI:**
   - Caso ocorra um erro ao se conectar à API do OpenAI, verifique se a chave de API está configurada corretamente no arquivo `.env` e se está ativa.

---

Sinta-se à vontade para sugerir melhorias e relatórios de bugs na seção de Issues do repositório.

Esperamos que o projeto seja útil em sua jornada de revisão de artigos científicos!