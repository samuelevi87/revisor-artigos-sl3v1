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
import sys
import yaml
from typing import Dict, Optional, Union, List, Tuple
from pathlib import Path
from datetime import datetime as dt
from dotenv import load_dotenv
from revisor_artigos_sl3v1.crew import RevisorArtigosSl3V1Crew
from crewai_tools import PDFSearchTool, SerperDevTool
from crewai import LLM

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


def generate_linkedin_article(
        article_data: Dict,
        pdf_file_name: str,
        task_config: Dict
) -> Optional[str]:
    """
    Gera um artigo em formato Markdown para o LinkedIn.

    Args:
        article_data (Dict): Dados do artigo extraídos do YAML
        pdf_file_name (str): Nome do arquivo PDF original
        task_config (Dict): Configurações da tarefa

    Returns:
        Optional[str]: Conteúdo do artigo em Markdown ou None se houver erro

    Raises:
        ValueError: Se os dados do artigo estiverem em formato inválido
        KeyError: Se campos obrigatórios estiverem faltando

    Example:
        >>> data = {"ARTIGO": [{"TITULO": "Exemplo", "OBJETIVOS": "Testar"}]}
        >>> article = generate_linkedin_article(data, "exemplo.pdf", {})
        >>> print(article[:50])
        🔬 #CiênciaNaPrática

        # exemplo.pdf
    """
    try:
        content = []

        # Cabeçalho
        content.append("🔬 #CiênciaNaPrática")
        content.append(f"\n# {pdf_file_name}\n")
        content.append("---\n")

        # Processar dados do YAML
        if isinstance(article_data, dict) and 'ARTIGO' in article_data:
            artigo = article_data['ARTIGO']

            if isinstance(artigo, list) and len(artigo) > 0:
                artigo = artigo[0]

            # Seções principais com emojis
            sections = {
                'GAP': '🎯 Por que isso importa?',
                'OBJETIVOS': '💡 O que descobrimos?',
                'METODOLOGIA': '🔍 Como chegamos lá?',
                'RESULTADOS': '📊 O que encontramos?'
            }

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
        print(f"Erro ao gerar artigo: {e}")
        return None


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


def save_article(content: str, file_name: str) -> None:
    """
    Salva o conteúdo do artigo em um arquivo Markdown.

    Args:
        content (str): Conteúdo do artigo em formato Markdown
        file_name (str): Nome do arquivo a ser salvo

    Raises:
        OSError: Se houver erro ao salvar o arquivo
        PermissionError: Se não houver permissão para salvar o arquivo

    Example:
        >>> content = ""# Título do Artigo\n\nConteúdo do artigo...""
        >>> save_article(content, "artigo_001.md")
        Artigo salvo em: src/revisor_artigos_sl3v1/resources/artigos_markdown/artigo_001.md
    """
    try:
        _, _, base_dir = verificar_estrutura_diretorios()
        articles_dir = base_dir / 'artigos_markdown'

        file_path = articles_dir / file_name

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.info(f"Artigo salvo em: {file_path}")


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


def processar_pdfs() -> bool:
    """
    Processa PDFs e gera análises em YAML usando agentes CrewAI.

    Esta função coordena o processamento de artigos científicos em PDF através de uma equipe
    de agentes especializados, gerando análises estruturadas em formato YAML.

    Fluxo de Execução:
        1. Carregamento de Configurações:
           - Carrega configurações de agentes e tarefas dos arquivos YAML
           - Configura o modelo de linguagem (LLM)

        2. Preparação do Ambiente:
           - Verifica e cria diretórios necessários
           - Lista arquivos PDF disponíveis

        3. Processamento Individual:
           Para cada PDF encontrado:
           - Instancia ferramentas específicas (PDFTool, SerperTool)
           - Prepara inputs baseados nas configurações
           - Cria e executa equipe de agentes
           - Extrai e valida conteúdo YAML
           - Salva resultados

    Returns:
        bool: True se pelo menos um PDF foi processado com sucesso, False caso contrário

    Raises:
        FileNotFoundError: Se o diretório de PDFs não for encontrado
        yaml.YAMLError: Se houver erro na leitura dos arquivos de configuração
        EnvironmentError: Se variáveis de ambiente necessárias não estiverem configuradas

    Example:
        >>> if processar_pdfs():
        ...     print("Processamento concluído com sucesso")
        ... else:
        ...     print("Erro no processamento dos PDFs")
    """
    try:
        # Configurar logging
        logging.info("Iniciando processamento de PDFs")

        # Verificar e obter caminhos dos diretórios
        pdf_dir, yaml_dir, base_dir = verificar_estrutura_diretorios()

        # Carregar configurações
        agents_config, tasks_config = carregar_configuracoes()
        if not agents_config or not tasks_config:
            logging.error("Falha ao carregar configurações dos arquivos YAML")
            return False

        # Listar e verificar PDFs
        pdf_files = list(pdf_dir.glob('*.pdf'))
        logging.info(f"Diretório de PDFs: {pdf_dir}")
        logging.info(f"PDFs encontrados: {len(pdf_files)}")

        if not pdf_files:
            logging.warning(f"Nenhum arquivo PDF encontrado em: {pdf_dir}")
            if pdf_dir.exists():
                files = list(pdf_dir.iterdir())
                logging.info(f"Arquivos no diretório: {[f.name for f in files]}")
            return False

        # Configurar LLM
        try:
            llm = LLM(
                model="gpt-4o-mini",
                api_key=os.environ['OPENAI_API_KEY'],
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

                # Preparar inputs
                task_config = tasks_config.get('leitura_pdfs', {}).get('inputs', {})
                leitura_inputs = {
                    'arquivo': pdf_path.name,
                    'solicitacoes': task_config.get('solicitacoes', ''),
                    'template': task_config.get('template', '').replace('nome do arquivo.pdf', pdf_path.name),
                    'controles': task_config.get('controles', ''),
                    'restricoes': task_config.get('restricoes', '')
                }

                # Criar e executar equipe
                crew_instance = RevisorArtigosSl3V1Crew(
                    agents_config=agents_config,
                    tasks_config=tasks_config,
                    llm=llm,
                    pdf_tool=pdf_tool,
                    serper_tool=serper_tool
                )
                crew = crew_instance.create_crew()

                logging.info(f"Executando processamento para: {pdf_path.name}")
                results = crew.kickoff(inputs=leitura_inputs)

                # Extrair e processar YAML
                yaml_content = None
                if "```yaml" in results:
                    yaml_content = results.split("```yaml")[1].split("```")[0].strip()
                elif "ARTIGO:" in results:
                    yaml_content = results[results.find("ARTIGO:"):]

                if yaml_content:
                    try:
                        article_data = yaml.safe_load(yaml_content)
                        if article_data:
                            yaml_file = yaml_dir / f'output_{pdf_path.stem}.yaml'
                            with open(yaml_file, 'w', encoding='utf-8') as file:
                                yaml.dump(article_data, file, default_flow_style=False, allow_unicode=True)
                            logging.info(f"YAML salvo em: {yaml_file}")
                            processed_successfully = True
                        else:
                            logging.error(f"YAML vazio para {pdf_path.name}")
                    except yaml.YAMLError as e:
                        logging.error(f"Erro ao fazer parse do YAML para {pdf_path.name}: {e}")
                else:
                    logging.warning(f"Nenhum resultado encontrado para {pdf_path.name}")

            except Exception as e:
                logging.error(f"Erro ao processar {pdf_path.name}: {e}", exc_info=True)
                continue

        return processed_successfully

    except Exception as e:
        logging.error(f"Erro não esperado durante o processamento: {e}", exc_info=True)
        return False


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
