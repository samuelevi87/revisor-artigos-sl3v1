#!/usr/bin/env python
"""
Módulo para processamento de artigos científicos e geração de conteúdo para LinkedIn.

Este módulo contém funções para processar arquivos PDF de artigos científicos,
gerar análises em formato YAML e criar artigos formatados para o LinkedIn.

Estrutura de diretórios:
src/revisor_artigos_sl3v1/
├── resources/
│   ├── pdfs/            # PDFs dos artigos científicos
│   ├── yamls/           # Análises geradas em YAML
│   └── artigos_markdown/ # Artigos formatados para LinkedIn

Author: [Samuel Levi Araújo Alves]
Date: 2024-10-27
"""
import logging
# Importações necessárias para o funcionamento do script
import os
import re
import sys
from datetime import datetime as dt
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml
from crewai import LLM
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from revisor_artigos_sl3v1.crew import RevisorArtigosSl3V1Crew

# Configurar a saída do terminal para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


def setup_directories() -> None:
    """
    Verifica a estrutura de diretórios do projeto.

    Verifica a existência dos diretórios necessários usando caminhos absolutos:
    {PROJECT_ROOT}/src/revisor_artigos_sl3v1/resources/{pdfs,yamls,artigos_markdown}

    Raises:
        FileNotFoundError: Se os diretórios não existirem
        PermissionError: Se não houver permissões adequadas

    Example:
        >>> setup_directories()
        Estrutura de diretórios verificada em: .../src/revisor_artigos_sl3v1/resources
    """
    try:
        # Obter caminho absoluto do projeto
        project_root = Path(__file__).resolve().parent.parent.parent  # Sobe até a raiz do projeto
        base_dir = project_root / 'src' / 'revisor_artigos_sl3v1' / 'resources'

        if not base_dir.exists():
            raise FileNotFoundError(f"Diretório base não encontrado: {base_dir}")

        directories = ['pdfs', 'yamls', 'artigos_markdown']

        for dir_name in directories:
            dir_path = base_dir / dir_name

            if not dir_path.exists():
                raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")

            if not os.access(dir_path, os.R_OK | os.W_OK):
                raise PermissionError(f"Sem permissões adequadas para: {dir_path}")

            logging.info(f"Diretório verificado: {dir_path}")

        logging.info(f"Estrutura de diretórios validada em: {base_dir}")

    except Exception as e:
        logging.error(f"Erro ao verificar diretórios: {e}", exc_info=True)
        raise


def verificar_estrutura_diretorios() -> Tuple[Path, Path, Path]:
    """
    Verifica e retorna os caminhos corretos dos diretórios do projeto.

    Utiliza caminhos absolutos para garantir a localização correta dos diretórios:
    {PROJECT_ROOT}/src/revisor_artigos_sl3v1/resources/{pdfs,yamls,artigos_markdown}

    Returns:
        Tuple[Path, Path, Path]: Tupla contendo (pdf_dir, yaml_dir, base_dir)
            - pdf_dir: Diretório de PDFs fonte
            - yaml_dir: Diretório para YAMLs
            - base_dir: Diretório base de resources

    Raises:
        FileNotFoundError: Se os diretórios não forem encontrados
        PermissionError: Se não houver permissões adequadas

    Example:
        >>> pdf_dir, yaml_dir, base_dir = verificar_estrutura_diretorios()
        >>> print(f"PDFs serão lidos de: {pdf_dir}")
    """
    try:
        # Obter caminho absoluto do diretório src/revisor_artigos_sl3v1/resources
        project_root = Path(__file__).resolve().parent.parent.parent  # Sobe até a raiz do projeto
        base_dir = project_root / 'src' / 'revisor_artigos_sl3v1' / 'resources'

        pdf_dir = base_dir / 'pdfs'
        yaml_dir = base_dir / 'yamls'
        artigos_dir = base_dir / 'artigos_markdown'

        # Verificar se os diretórios existem
        for dir_path in [base_dir, pdf_dir, yaml_dir, artigos_dir]:
            if not dir_path.exists():
                logging.error(f"Diretório não encontrado: {dir_path}")
                raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")

            if not os.access(dir_path, os.R_OK | os.W_OK):
                raise PermissionError(f"Sem permissões adequadas para: {dir_path}")

        logging.info(f"Estrutura de diretórios verificada:")
        logging.info(f"- Base: {base_dir}")
        logging.info(f"- PDFs: {pdf_dir}")
        logging.info(f"- YAMLs: {yaml_dir}")

        return pdf_dir, yaml_dir, base_dir

    except Exception as e:
        logging.error(f"Erro ao verificar estrutura de diretórios: {e}", exc_info=True)
        raise


def carregar_configuracoes():
    """
    Carregar as definições de agentes e tarefas dos arquivos YAML.

    Esta função lê as configurações dos agentes e tarefas a partir dos arquivos
    'agents.yaml' e 'tasks.yaml' localizados na pasta 'config'. Se houver algum
    erro durante o carregamento, uma mensagem será exibida.

    Returns:
        Tuple[Dict, Dict]: Retorna dois dicionários contendo as configurações de
        agentes e tarefas, respectivamente.
    """
    agents_config = {}
    tasks_config = {}

    try:
        # Diretório base para localizar os arquivos de configuração
        base_dir = Path(__file__).resolve().parent / 'config'
        agents_file_path = base_dir / 'agents.yaml'
        tasks_file_path = base_dir / 'tasks.yaml'

        # Carregar configurações de agentes
        with open(agents_file_path, 'r', encoding='utf-8', errors='replace') as file:
            agents_config = yaml.safe_load(file) or {}
            print("Configurações de agents.yaml carregadas com sucesso.")

        # Carregar configurações de tarefas
        with open(tasks_file_path, 'r', encoding='utf-8', errors='replace') as file:
            tasks_config = yaml.safe_load(file) or {}
            print("Configurações de tasks.yaml carregadas com sucesso.")

    except Exception as e:
        # Exibir mensagem de erro em caso de falha no carregamento dos arquivos
        print(f"Erro ao carregar as configurações: {e}")

    return agents_config, tasks_config


def construir_caminho_artigo_markdown(pdf_path: Path) -> str:
    """
    Constrói o caminho completo do arquivo Markdown como uma string,
    com base no nome do PDF processado.

    Esta função sanitiza o nome do PDF e cria o caminho para o arquivo Markdown
    dentro do diretório padrão de artigos em Markdown.

    Args:
        pdf_path (Path): Caminho do arquivo PDF sendo processado.

    Returns:
        str: Caminho completo do arquivo Markdown como string.

    Raises:
        ValueError: Se o nome do PDF estiver vazio ou for inválido.

    Exemplo:
        >>> pdf_path = Path("src/revisor_artigos_sl3v1/resources/pdfs/Artigo_Teste.pdf")
        >>> construir_caminho_artigo_markdown(pdf_path)
        'src/revisor_artigos_sl3v1/resources/artigos_markdown/artigo_Artigo_Teste.md'
    """
    try:
        if not pdf_path or not pdf_path.stem:
            raise ValueError("Nome do PDF está vazio ou é inválido")

        # Diretório base de artigos em Markdown
        articles_dir = Path('src/revisor_artigos_sl3v1/resources/artigos_markdown')
        articles_dir.mkdir(parents=True, exist_ok=True)

        # Sanitizar o nome do arquivo PDF
        sanitized_pdf_name = re.sub(r'[^\w\-]', '_', pdf_path.stem)

        # Criar o caminho completo do arquivo Markdown
        markdown_file_path = articles_dir / f'artigo_{sanitized_pdf_name}.md'

        # Retornar o caminho como string
        return str(markdown_file_path)

    except Exception as e:
        logging.error(f"Erro ao construir caminho do arquivo Markdown: {e}")
        raise


def processar_pdfs() -> bool:
    """
    Processa PDFs e gera análises em YAML e artigos em Markdown usando agentes CrewAI.

    Esta função coordena o processamento completo de artigos científicos em PDF através de uma
    equipe de agentes especializados. O processamento ocorre em várias etapas sequenciais,
    cada uma executada por um agente específico com uma responsabilidade única.

    Fluxo de Execução:
        1. Preparação:
           - Verifica e configura diretórios necessários (PDFs, YAMLs, Markdown)
           - Carrega configurações dos agentes e tarefas
           - Configura o modelo de linguagem (LLM)
           - Lista arquivos PDF disponíveis

        2. Para cada PDF:
           a. Leitura (Agente Leitor):
              - Extrai informações estruturadas do PDF
              - Gera conteúdo YAML inicial

           b. Revisão (Agente Revisor):
              - Valida o conteúdo YAML
              - Verifica conformidade com o template
              - Salva o YAML revisado

           c. Pesquisa (Agente Pesquisador):
              - Realiza pesquisas contextuais
              - Enriquece o conteúdo com informações adicionais

           d. Criação de Artigo (Agente Criador):
              - Transforma os dados em artigo para LinkedIn
              - Gera arquivo Markdown formatado

    Returns:
        bool: True se pelo menos um PDF foi processado com sucesso até o final,
              False caso contrário ou em caso de erros críticos.

    Raises:
        FileNotFoundError: Se os diretórios necessários não forem encontrados
        yaml.YAMLError: Se houver erro no processamento dos arquivos YAML
        KeyError: Se configurações essenciais estiverem ausentes
        PermissionError: Se houver problemas de acesso aos arquivos
        EnvironmentError: Se variáveis de ambiente requeridas não estiverem configuradas

    Example:
        >>> # Configurar ambiente e variáveis necessárias
        >>> os.environ['OPENAI_API_KEY'] = 'sua-chave-api'
        >>> # Processar PDFs
        >>> success = processar_pdfs()
        >>> if success:
        ...     print("Processamento concluído com sucesso")
        ... else:
        ...     print("Falha no processamento")
    """
    try:
        # Configuração inicial
        logging.info("Iniciando processamento de PDFs")

        # Verificar e obter caminhos dos diretórios
        pdf_dir, yaml_dir, markdown_dir = verificar_estrutura_diretorios()

        # Carregar configurações de agentes e tarefas
        agents_config, tasks_config = carregar_configuracoes()
        if not agents_config or not tasks_config:
            logging.error("Falha ao carregar configurações dos arquivos YAML")
            return False

        # Listar e verificar PDFs
        pdf_files = list(pdf_dir.glob('*.pdf'))
        if not pdf_files:
            logging.warning(f"Nenhum arquivo PDF encontrado em: {pdf_dir}")
            return False

        # Configurar LLM
        try:
            llm = LLM(
                model="gpt-4o-mini",
                api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.7
            )
        except KeyError:
            logging.error("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
            return False

        processed_successfully = False

        # Processar cada PDF
        for pdf_path in pdf_files:
            logging.info(f"\nProcessando: {pdf_path.name}")

            try:
                # Instanciar ferramentas
                pdf_tool = PDFSearchTool(pdf=str(pdf_path))
                serper_tool = SerperDevTool()

                # Preparar inputs de leitura
                task_config = tasks_config.get('leitura_pdfs', {}).get('inputs', {})
                leitura_inputs = {
                    'arquivo': pdf_path.name,
                    'solicitacoes': task_config.get('solicitacoes', ''),
                    'template': task_config.get('template', '').replace('nome do arquivo.pdf', pdf_path.name),
                    'controles': task_config.get('controles', ''),
                    'restricoes': task_config.get('restricoes', '')
                }

                # Preparar inputs para criação do artigo
                task_config_artigo = tasks_config.get('criar_artigo_linkedin', {}).get('inputs', {})
                artigo_inputs = {
                    'titulo': task_config_artigo.get('titulo', ''),
                    'hook': task_config_artigo.get('hook', ''),
                    'secoes': task_config_artigo.get('secoes', {}),
                    'provocacao': task_config_artigo.get('provocacao', ''),
                    'hashtags': task_config_artigo.get('hashtags', ''),
                    'controles': task_config_artigo.get('controles', ''),
                    'restricoes': task_config_artigo.get('restricoes', ''),
                    'output_file': construir_caminho_artigo_markdown(pdf_path)
                }

                # Remover chaves vazias
                artigo_inputs = {k: v for k, v in artigo_inputs.items() if v}

                # Construir caminho para o arquivo de saída do artigo
                output_file_artigo = construir_caminho_artigo_markdown(pdf_path)

                # Criar e executar equipe
                crew_instance = RevisorArtigosSl3V1Crew(
                    agents_config=agents_config,
                    tasks_config=tasks_config,
                    llm=llm,
                    pdf_tool=pdf_tool,
                    serper_tool=serper_tool
                )
                crew = crew_instance.create_crew(output_file_artigo=artigo_inputs['output_file'])

                # Executar tarefa de leitura
                results = crew.kickoff(inputs=leitura_inputs)
                if results and hasattr(results, 'tasks_output'):
                    yaml_content = processar_resultado_leitura(results.tasks_output)
                    if yaml_content:
                        resultados_revisao = processar_resultado_revisao(results.tasks_output, pdf_path, yaml_dir)
                        if resultados_revisao:
                            pesquisa_content = processar_resultado_pesquisa(results.tasks_output)
                            if pesquisa_content:
                                # Executar tarefa de criação de artigo
                                results_artigo = crew.kickoff(inputs=artigo_inputs)
                                if results_artigo:
                                    processar_resultado_artigo(results_artigo.tasks_output, pdf_path, markdown_dir)
                                    processed_successfully = True
                            else:
                                logging.error(f"Falha na pesquisa adicional para {pdf_path.name}")
                        else:
                            logging.error(f"Falha na revisão do YAML para {pdf_path.name}")
                    else:
                        logging.error(f"Falha na extração do YAML para {pdf_path.name}")

            except Exception as e:
                logging.error(f"Erro ao processar {pdf_path.name}: {e}", exc_info=True)
                continue  # Continua para o próximo PDF em caso de erro

        return processed_successfully

    except Exception as e:
        logging.error(f"Erro inesperado durante o processamento: {e}", exc_info=True)
        return False


def processar_resultado_leitura(tasks_output: list) -> Optional[str]:
    """
    Processa o resultado da tarefa de leitura do PDF, extraindo e validando o conteúdo YAML.

    Esta função identifica o output do agente Leitor de PDFs, extrai o conteúdo YAML
    e realiza validações iniciais antes de passar para o revisor. O conteúdo não é
    salvo nesta etapa, apenas processado e validado.

    Args:
        tasks_output (list): Lista de outputs das tarefas executadas pelos agentes

    Returns:
        Optional[str]: Conteúdo YAML válido ou None se:
            - Nenhum resultado do Leitor for encontrado
            - O YAML extraído for inválido
            - Ocorrer erro no processamento

    Raises:
        yaml.YAMLError: Se o conteúdo extraído não for um YAML válido
        ValueError: Se o conteúdo estiver vazio ou mal formatado
        TypeError: Se tasks_output não for uma lista

    Example:
        >>> outputs = [TaskOutput(agent="Leitor de PDFs", raw="ARTIGO:\\n  - chave: valor")]
        >>> yaml_content = processar_resultado_leitura(outputs)
        >>> if yaml_content:
        ...     print("YAML válido extraído")

    Notes:
        O conteúdo YAML extraído deve seguir o template definido começando com 'ARTIGO:'
        e contendo a estrutura esperada de campos.
    """
    try:
        # Validar input
        if not isinstance(tasks_output, list):
            raise TypeError("tasks_output deve ser uma lista")

        # Procurar resultado do Leitor
        for task_output in tasks_output:
            if "Leitor de PDFs" in task_output.agent:
                content = str(task_output.raw)

                # Extrair e validar YAML
                yaml_content = extrair_yaml_content(content)
                if not yaml_content:
                    logging.warning("Conteúdo YAML não encontrado no resultado do Leitor")
                    continue

                try:
                    # Validar estrutura do YAML
                    parsed_yaml = yaml.safe_load(yaml_content)
                    if not isinstance(parsed_yaml, dict) or 'ARTIGO' not in parsed_yaml:
                        raise ValueError("YAML não contém a estrutura esperada com 'ARTIGO'")

                    logging.info("YAML extraído e validado com sucesso da leitura do PDF")
                    return yaml_content

                except yaml.YAMLError as e:
                    logging.error(f"YAML extraído é inválido: {e}")
                    return None
                except ValueError as e:
                    logging.error(f"Estrutura do YAML inválida: {e}")
                    return None

        logging.warning("Nenhum resultado do Leitor de PDFs encontrado nos outputs")
        return None

    except Exception as e:
        logging.error(f"Erro ao processar resultado da leitura: {e}", exc_info=True)
        return None

def processar_resultado_revisao(tasks_output: list, pdf_path: Path, yaml_dir: Path) -> bool:
    """
    Processa o resultado da tarefa de revisão e salva o YAML validado.

    Esta função processa o output do revisor, que já validou o conteúdo YAML
    gerado pelo leitor, e salva o resultado final em um arquivo YAML.

    Args:
        tasks_output (list): Lista de outputs das tarefas
        pdf_path (Path): Caminho do arquivo PDF processado
        yaml_dir (Path): Diretório para salvar os arquivos YAML

    Returns:
        bool: True se o YAML foi processado e salvo com sucesso

    Example:
        >>> tasks_output = [...]  # Lista de outputs das tarefas
        >>> pdf_path = Path("artigo.pdf")
        >>> yaml_dir = Path("yamls")
        >>> if processar_resultado_revisao(tasks_output, pdf_path, yaml_dir):
        ...     print("YAML revisado e salvo com sucesso")
    """
    try:
        logging.info(f"Iniciando processamento de revisão para: {pdf_path.name}")
        logging.info(f"Diretório destino YAML: {yaml_dir}")

        for task_output in tasks_output:
            logging.info(f"Processando output do agente: {task_output.agent}")

            if "Revisor" in task_output.agent:
                content = str(task_output.raw)
                logging.info("Conteúdo bruto do revisor obtido")

                yaml_content = extrair_yaml_content(content)
                logging.info(f"YAML extraído: {'Sim' if yaml_content else 'Não'}")

                if yaml_content:
                    try:
                        # Validar e carregar o YAML
                        article_data = yaml.safe_load(yaml_content)
                        logging.info("YAML carregado com sucesso")

                        if article_data and isinstance(article_data, dict):
                            # Sanitizar nome do arquivo
                            sanitized_pdf_name = sanitize_filename(pdf_path.stem)
                            logging.info(f"Nome sanitizado: {sanitized_pdf_name}")

                            # Criar o caminho do arquivo YAML
                            yaml_file = yaml_dir / f'output_{sanitized_pdf_name}.yaml'
                            logging.info(f"Caminho do arquivo YAML: {yaml_file}")

                            # Verificar se o diretório existe e tem permissão de escrita
                            if not yaml_dir.exists():
                                logging.error(f"Diretório não existe: {yaml_dir}")
                                return False

                            if not os.access(yaml_dir, os.W_OK):
                                logging.error(f"Sem permissão de escrita em: {yaml_dir}")
                                return False

                            # Salvar YAML
                            with open(yaml_file, 'w', encoding='utf-8') as file:
                                yaml.dump(article_data, file,
                                          default_flow_style=False,
                                          allow_unicode=True,
                                          sort_keys=False)
                                logging.info(f"YAML salvo com sucesso em: {yaml_file}")
                            return True

                    except yaml.YAMLError as e:
                        logging.error(f"Erro no parse do YAML revisado: {e}")
                else:
                    logging.error("Nenhum conteúdo YAML válido encontrado na revisão")

        logging.warning("Nenhum output do Revisor encontrado nos resultados")
        return False

    except Exception as e:
        logging.error(f"Erro ao processar revisão: {e}", exc_info=True)
        return False


# Função para sanitizar o nome do arquivo removendo caracteres inválidos
def sanitize_filename(filename):
    """
    Remove caracteres inválidos do nome do arquivo.
    Substitui caracteres como \ / : * ? " < > | e \n por _.
    """
    return re.sub(r'[\\/*?:"<>|\n]', '_', filename)


def limpar_conteudo_yaml(content: str) -> str:
    """
    Limpa o conteúdo YAML de caracteres e formatações indesejadas.

    Esta função remove delimitadores de código, caracteres especiais e
    formatações que podem interferir no parse do YAML.

    Args:
        content (str): Conteúdo bruto contendo YAML

    Returns:
        str: Conteúdo YAML limpo e pronto para parse

    Example:
        >>> content = "```yaml\\nARTIGO:\\n  - teste: valor\\n```"
        >>> print(limpar_conteudo_yaml(content))
        ARTIGO:
          - teste: valor
    """
    if not content:
        return ""

    # Remover blocos de código markdown
    content = re.sub(r'```+\s*yaml\s*', '', content)
    content = re.sub(r'```+', '', content)

    # Remover caracteres especiais problemáticos
    content = re.sub(r'[`]', '', content)

    # Limpar espaços extras e linhas em branco
    lines = [line.rstrip() for line in content.splitlines()]
    content = '\n'.join(line for line in lines if line.strip())

    return content.strip()


def extrair_yaml_content(content: str) -> Optional[str]:
    """
    Extrai e processa o conteúdo YAML de uma string bruta.

    Esta função identifica o bloco YAML dentro do conteúdo,
    limpa formatações indesejadas e valida a estrutura do YAML.

    Args:
        content (str): String contendo o conteúdo bruto

    Returns:
        Optional[str]: Conteúdo YAML processado ou None se inválido

    Raises:
        yaml.YAMLError: Se o conteúdo YAML for inválido após processamento

    Example:
        >>> content = "Algum texto\\nARTIGO:\\n  - chave: valor"
        >>> yaml_content = extrair_yaml_content(content)
        >>> print(yaml_content)
        ARTIGO:
          - chave: valor
    """
    try:
        if not content:
            return None

        # Primeiro limpar o conteúdo
        content = limpar_conteudo_yaml(content)

        # Extrair seção YAML
        if "ARTIGO:" in content:
            # Pegar do ARTIGO: até o final ou próxima seção
            yaml_content = content[content.find("ARTIGO:"):]

            # Validar se é um YAML válido
            try:
                yaml.safe_load(yaml_content)
                return yaml_content
            except yaml.YAMLError:
                logging.error("Conteúdo extraído não é um YAML válido")
                return None

        return None

    except Exception as e:
        logging.error(f"Erro ao extrair YAML: {e}", exc_info=True)
        return None


def processar_resultado_yaml(tasks_output: list, pdf_path: Path, yaml_dir: Path) -> bool:
    """
    Processa o resultado das tarefas de leitura e revisão de PDFs, salvando o conteúdo em um arquivo YAML.

    Esta função percorre a lista de outputs das tarefas, identifica os agentes responsáveis pela leitura e revisão
    de PDFs, extrai o conteúdo YAML, e salva o resultado em um arquivo no diretório especificado.

    Args:
        tasks_output (list): Lista de outputs das tarefas executadas pela equipe de agentes.
        pdf_path (Path): Caminho do arquivo PDF sendo processado, usado para nomear o arquivo YAML.
        yaml_dir (Path): Diretório onde o arquivo YAML será salvo.

    Returns:
        bool: Retorna True se o YAML for processado e salvo com sucesso, caso contrário, retorna False.

    Raises:
        yaml.YAMLError: Se houver erro no processamento do YAML.
        OSError: Se houver um erro ao salvar o arquivo YAML.

    Example:
        >>> tasks_output = [...]  # Lista de outputs das tarefas
        >>> pdf_path = Path("/caminho/para/arquivo.pdf")
        >>> yaml_dir = Path("/caminho/para/yaml")
        >>> sucesso = processar_resultado_yaml(tasks_output, pdf_path, yaml_dir)
        >>> if sucesso:
        ...     print("Arquivo YAML salvo com sucesso")
    """
    try:
        for task_output in tasks_output:
            if "Leitor de PDFs" in task_output.agent or "Revisor" in task_output.agent:
                content = str(task_output.raw)

                yaml_content = None
                if "```yaml" in content:
                    yaml_content = content.split("```yaml")[1].split("```")[0].strip()
                elif "ARTIGO:" in content:
                    yaml_content = content[content.find("ARTIGO:"):]

                if yaml_content:
                    try:
                        article_data = yaml.safe_load(yaml_content)
                        if article_data and isinstance(article_data, dict):
                            # Sanitizar nome do arquivo PDF e do agente
                            sanitized_pdf_name = sanitize_filename(pdf_path.stem)
                            sanitized_agent_name = sanitize_filename(task_output.agent)

                            # Criar o caminho do arquivo YAML
                            yaml_file = yaml_dir / f'output_{sanitized_pdf_name}_{sanitized_agent_name}.yaml'

                            # Salvar o arquivo YAML
                            with open(yaml_file, 'w', encoding='utf-8') as file:
                                yaml.dump(article_data, file, default_flow_style=False, allow_unicode=True)

                            logging.info(f"YAML salvo em: {yaml_file}")
                            return True

                    except yaml.YAMLError as e:
                        logging.error(f"Erro ao processar YAML: {e}", exc_info=True)

    except OSError as e:
        logging.error(f"Erro ao salvar arquivo YAML: {e}", exc_info=True)

    return False


def processar_resultado_pesquisa(tasks_output: list) -> Optional[str]:
    """
    Processa o resultado da tarefa de pesquisa adicional realizada pelo agente pesquisador.

    Esta função analisa os outputs das tarefas e extrai as informações de contexto e
    dados adicionais obtidos pelo agente pesquisador, que serão utilizados pelo
    agente criador de artigos para enriquecer o conteúdo.

    Args:
        tasks_output (list): Lista de outputs das tarefas executadas pela equipe de agentes

    Returns:
        Optional[str]: Conteúdo processado da pesquisa ou None se não houver
                      resultados válidos

    Raises:
        ValueError: Se o conteúdo da pesquisa estiver em formato inválido

    Example:
        >>> tasks_output = [...]  # Lista de outputs das tarefas
        >>> pesquisa = processar_resultado_pesquisa(tasks_output)
        >>> if pesquisa:
        ...     print("Informações adicionais obtidas com sucesso")
    """
    try:
        for task_output in tasks_output:
            if "Pesquisador" in task_output.agent:
                content = str(task_output.raw)

                if content:
                    # Limpar e validar o conteúdo
                    content = content.strip()

                    # Verificar se há conteúdo substancial
                    if len(content) > 10:  # Critério mínimo arbitrário
                        logging.info("Resultado da pesquisa processado com sucesso")
                        return content
                    else:
                        logging.warning("Conteúdo da pesquisa muito curto ou vazio")
                        return None

        logging.warning("Nenhum resultado do Pesquisador encontrado")
        return None

    except Exception as e:
        logging.error(f"Erro ao processar resultado da pesquisa: {e}", exc_info=True)
        return None


def generate_linkedin_article(article_data: Dict, pdf_file_name: str, task_config: Dict) -> Optional[str]:
    """
    Gera um artigo em formato Markdown para o LinkedIn.

    Esta função recebe os dados extraídos do arquivo YAML, o nome do arquivo PDF
    e as configurações de tarefa, e gera um artigo formatado para o LinkedIn.

    Args:
        article_data (Dict): Dados do artigo extraídos do YAML, contendo as seções e conteúdo.
        pdf_file_name (str): Nome do arquivo PDF original, utilizado para referência no artigo.
        task_config (Dict): Configurações da tarefa, incluindo parâmetros adicionais para o artigo.

    Returns:
        Optional[str]: Conteúdo do artigo em formato Markdown ou None se ocorrer um erro.

    Raises:
        ValueError: Se os dados do artigo estiverem em formato inválido ou faltando informações essenciais.
        KeyError: Se houver ausência de campos obrigatórios no dicionário de dados do artigo.

    Exemplo:
        >>> data = {"ARTIGO": [{"TITULO": "Exemplo", "OBJETIVOS": "Testar"}]}
        >>> article = generate_linkedin_article(data, "exemplo.pdf", {})
        >>> print(article[:50])
        🔬 #CiênciaNaPrática
        # exemplo.pdf
    """
    try:
        content = []

        # Cabeçalho do artigo
        content.append("🔬 #CiênciaNaPrática")
        content.append(f"\n# {pdf_file_name}\n")
        content.append("---\n")

        # Processar dados do YAML
        if isinstance(article_data, dict) and 'ARTIGO' in article_data:
            artigo = article_data['ARTIGO']

            if isinstance(artigo, list) and len(artigo) > 0:
                artigo = artigo[0]

            # Seções principais do artigo
            sections = {
                'GAP': '🎯 Por que isso importa?',
                'OBJETIVOS': '💡 O que descobrimos?',
                'METODOLOGIA': '🔍 Como chegamos lá?',
                'RESULTADOS': '📊 O que encontramos?',
                'LIMITAÇÕES': '⚠️ Quais são os desafios?',
                'FUTURO': '🔮 O que vem a seguir?'
            }

            # Adicionar conteúdo das seções
            for key, title in sections.items():
                if key in artigo:
                    content.append(f"\n## {title}\n")
                    content.append(artigo[key])
                    content.append("\n")

        # Call-to-action
        content.append("\n## 💭 E você, o que acha?\n")
        content.append("Como essas descobertas podem impactar sua área? Compartilhe suas ideias! 👇\n")

        # Hashtags
        content.append("\n---\n")
        content.append("#IA #Pesquisa #Inovação #Tecnologia #Desenvolvimento #Ciência")

        return '\n'.join(content)

    except Exception as e:
        logging.error(f"Erro ao gerar artigo: {e}")
        return None


def gerar_artigos_a_partir_de_yaml() -> None:
    """
    Gera artigos em Markdown a partir dos arquivos YAML existentes.

    Processa todos os arquivos YAML no diretório de YAMLs e gera os artigos
    correspondentes em formato Markdown para o LinkedIn.

    Raises:
        FileNotFoundError: Se o diretório de YAMLs não existir
        yaml.YAMLError: Se houver erro no parse dos arquivos YAML

    Example:
        >>> gerar_artigos_a_partir_de_yaml()
        Processando arquivo YAML: output_artigo_001.yaml
        Artigo gerado com sucesso: artigo_001.md
    """
    try:
        # Usar verificar_estrutura_diretorios para obter caminhos corretos
        _, yaml_dir, _ = verificar_estrutura_diretorios()

        yaml_files = list(yaml_dir.glob('output_*.yaml'))

        for yaml_file in yaml_files:
            try:
                logging.info(f"Processando arquivo YAML: {yaml_file.name}")

                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f)

                if yaml_content and isinstance(yaml_content, dict):
                    md_filename = f"{yaml_file.stem}.md"

                    article_content = generate_linkedin_article(
                        yaml_content,
                        yaml_file.stem,
                        {}
                    )

                    if article_content:
                        save_article(article_content, md_filename)
                        logging.info(f"Artigo gerado com sucesso: {md_filename}")
                    else:
                        logging.error(f"Erro: Conteúdo vazio para {yaml_file.name}")

            except Exception as e:
                logging.error(f"Erro ao processar {yaml_file.name}: {e}")
                continue

    except Exception as e:
        logging.error(f"Erro ao acessar diretório de YAMLs: {e}")
        raise


def limpar_conteudo_markdown(content: str) -> str:
    """
    Limpa o conteúdo markdown de delimitadores e formatações indesejadas.

    Esta função remove blocos de código markdown e outros elementos que possam
    interferir na formatação final do artigo.

    Args:
        content (str): Conteúdo bruto do artigo em markdown

    Returns:
        str: Conteúdo markdown limpo e formatado

    Example:
        >>> content = "```markdown\\n# Título\\n```\\nTexto"
        >>> print(limpar_conteudo_markdown(content))
        # Título
        Texto
    """
    if not content:
        return ""

    # Remover blocos de código markdown
    content = re.sub(r'```+\s*markdown\s*', '', content)
    content = re.sub(r'```+', '', content)

    # Limpar espaços extras e linhas em branco consecutivas
    lines = [line.rstrip() for line in content.splitlines()]
    content = '\n'.join(line for line in lines if line.strip())

    return content.strip()


def processar_resultado_artigo(tasks_output: list, pdf_path: Path, markdown_dir: Path) -> bool:
    """
    Processa o resultado da tarefa de criação do artigo em Markdown.

    Esta função extrai o conteúdo gerado pelo agente Criador de Artigos,
    valida o conteúdo e o salva no diretório de artigos.

    Args:
        tasks_output (list): Lista de outputs das tarefas executadas.
        pdf_path (Path): Caminho do arquivo PDF original, usado para nomear o artigo.
        markdown_dir (Path): Diretório onde o arquivo Markdown será salvo.

    Returns:
        bool: True se o processamento e o salvamento foram bem-sucedidos, False caso contrário.

    Raises:
        ValueError: Se o conteúdo do artigo estiver vazio ou inválido.
        OSError: Se houver falha ao salvar o arquivo.

    Exemplo:
        >>> success = processar_resultado_artigo(tasks_output, Path("artigo.pdf"), Path("artigos_markdown"))
        >>> print("Artigo processado" if success else "Falha no processamento")
    """
    try:
        for task_output in tasks_output:
            if "Criador de Artigos" in task_output.agent:
                content = str(task_output.raw)

                if content:
                    # Gerar nome do arquivo
                    md_filename = f'artigo_{pdf_path.stem}.md'

                    # Salvar artigo
                    save_article(content, md_filename)
                    return True

        logging.error("Nenhum conteúdo de artigo encontrado")
        return False

    except Exception as e:
        logging.error(f"Erro ao processar artigo Markdown: {e}", exc_info=True)
        return False


def save_article(content: str, file_name: str) -> None:
    """
    Salva o conteúdo do artigo em um arquivo Markdown.

    Esta função processa o conteúdo do artigo, sanitiza o nome do arquivo,
    e salva o artigo no diretório especificado na estrutura do projeto.

    Args:
        content (str): Conteúdo do artigo em formato Markdown.
        file_name (str): Nome do arquivo a ser salvo, incluindo extensão.

    Raises:
        OSError: Se houver erro ao salvar o arquivo.
        PermissionError: Se não houver permissão para escrever no diretório.
        ValueError: Se o conteúdo ou nome do arquivo forem inválidos.

    Exemplo:
        >>> content = "# Título do Artigo\\n\\nConteúdo do artigo..."
        >>> save_article(content, "Artigo_Test.md")
        Artigo salvo com sucesso em: .../artigos_markdown/Artigo_Test.md
    """
    try:
        if not content:
            raise ValueError("Conteúdo do artigo está vazio")
        if not file_name:
            raise ValueError("Nome do arquivo está vazio")

        # Limpar e sanitizar nome do arquivo
        sanitized_name = re.sub(r'[^\w\-\.]', '_', file_name)
        sanitized_name = re.sub(r'_+', '_', sanitized_name)

        # Diretório base de artigos
        articles_dir = Path('src/revisor_artigos_sl3v1/resources/artigos_markdown')
        articles_dir.mkdir(parents=True, exist_ok=True)

        # Verificar permissões de escrita
        if not os.access(articles_dir, os.W_OK):
            raise PermissionError(f"Sem permissão de escrita em: {articles_dir}")

        # Criar caminho completo do arquivo
        file_path = articles_dir / sanitized_name

        # Salvar o arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.info(f"Artigo salvo com sucesso em: {file_path}")

    except Exception as e:
        logging.error(f"Erro ao salvar artigo: {e}")
        raise


def setup_logging() -> None:
    """
    Configura o sistema de logging para o aplicativo.

    Cria um logger que escreve tanto no console quanto em um arquivo de log,
    com timestamps e níveis de log apropriados.

    Example:
        >>> setup_logging()
        Logger configurado: logs/revisor_artigos_20241027.log
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'revisor_artigos_{dt.now():%Y%m%d}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info(f"Iniciando processamento de artigos - {dt.now():%Y-%m-%d %H:%M:%S}")


def run() -> None:
    """
    Executa o pipeline completo de processamento de artigos científicos.

    Esta função orquestra o processo completo de:
    1. Configuração inicial de logging e diretórios
    2. Processamento de PDFs e geração de YAMLs
    3. Geração de artigos em Markdown para LinkedIn

    O processo é interrompido se houver falha em alguma etapa crítica.

    Raises:
        SystemExit: Se houver falha em alguma etapa crítica do processo

    Example:
        >>> try:
        ...     run()
        ...     print("Processamento concluído com sucesso")
        ... except SystemExit as e:
        ...     print(f"Erro crítico: {e}")
    """
    try:
        # Configuração inicial
        setup_logging()
        logging.info("Iniciando pipeline de processamento")

        # Processamento dos PDFs
        if not processar_pdfs():
            logging.error("Falha no processamento dos PDFs")
            raise SystemExit("Falha no processamento dos PDFs")

        # Geração dos artigos
        try:
            gerar_artigos_a_partir_de_yaml()
            logging.info("Artigos gerados com sucesso")
        except Exception as e:
            logging.error(f"Erro na geração dos artigos: {str(e)}", exc_info=True)
            raise SystemExit("Falha na geração dos artigos")

        logging.info("Pipeline de processamento concluído com sucesso")

    except Exception as e:
        logging.error(f"Erro não esperado: {str(e)}", exc_info=True)
        raise SystemExit(f"Erro não esperado: {str(e)}")


if __name__ == "__main__":
    """
    Ponto de entrada principal do script.

    Executa o pipeline completo de processamento e trata erros críticos.
    Os logs são salvos tanto no console quanto em um arquivo de log.
    """
    try:
        run()
    except SystemExit as e:
        logging.critical(f"Execução interrompida: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Execução interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Erro fatal não esperado: {e}", exc_info=True)
        sys.exit(1)
