#!/usr/bin/env python

# Importações necessárias para o funcionamento do script
import os
import sys
import yaml
from datetime import datetime as dt
from dotenv import load_dotenv
from revisor_artigos_sl3v1.crew import RevisorArtigosSl3V1Crew
from crewai_tools import PDFSearchTool, SerperDevTool
from crewai import LLM

# Caminho da pasta contendo os PDFs a serem processados
pdf_folder = os.path.join(os.path.dirname(__file__), 'resources', 'pdfs')

# Configurar a saída do terminal para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


def generate_linkedin_article(article_data, pdf_file_name, task_config):
    """
    Gera um artigo em formato Markdown para o LinkedIn com base nos dados do YAML e na configuração da tarefa.

    Args:
        article_data (dict): Dados do artigo extraídos do YAML.
        pdf_file_name (str): Nome do arquivo PDF original.
        task_config (dict): Configuração da tarefa do arquivo tasks.yaml.

    Returns:
        str: Conteúdo do artigo em formato Markdown.
    """
    try:
        # Extrair o título do artigo a partir do nome do arquivo PDF
        title = os.path.splitext(pdf_file_name)[0].split(' - ')[1]

        # Construir o artigo em Markdown
        content = []

        # Emoji relevante para o título
        content.append("🔬 #CiênciaNaPrática")

        # Título chamativo
        content.append(f"# {title}: {task_config.get('titulo')}")
        content.append("\n---\n")

        # Hook inicial
        content.append(task_config.get('hook'))
        content.append("\n")

        # Adicionar conteúdo baseado nos dados do YAML
        artigo = article_data.get('ARTIGO', [{}])[0] if isinstance(article_data.get('ARTIGO'), list) else {}

        # Seções principais do artigo
        secoes = task_config.get('secoes', {})
        if 'gap' in secoes and 'GAP' in artigo:
            content.append(f"## {secoes['gap']}")
            content.append(f"\n{artigo['GAP']}\n")

        if 'objetivos' in secoes and 'OBJETIVOS' in artigo:
            content.append(f"## {secoes['objetivos']}")
            content.append(f"\n{artigo['OBJETIVOS']}\n")

        if 'metodologia' in secoes and 'METODOLOGIA' in artigo:
            content.append(f"## {secoes['metodologia']}")
            content.append(f"\n{artigo['METODOLOGIA']}\n")

        if 'resultados' in secoes and 'RESULTADOS' in artigo:
            content.append(f"## {secoes['resultados']}")
            content.append(f"\n{artigo['RESULTADOS']}\n")

        # Provocação para engajamento
        content.append("\n## Sua vez de compartilhar! 💭")
        content.append(f"\n{task_config.get('provocacao')}")
        content.append("\nCompartilhe suas ideias nos comentários! 👇")

        # Hashtags relevantes
        content.append("\n---\n")
        content.append(task_config.get('hashtags'))

        # Juntar todo o conteúdo em uma string Markdown
        article_content = '\n'.join(content)

        return article_content

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
        base_dir = os.path.dirname(__file__)

        # Caminhos completos para os arquivos YAML de configuração
        agents_file_path = os.path.join(base_dir, 'config', 'agents.yaml')
        tasks_file_path = os.path.join(base_dir, 'config', 'tasks.yaml')

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


def save_article(content, file_name="linkedin_article.md"):
    """
    Salva o conteúdo gerado em um arquivo Markdown na pasta 'resources/artigos_markdown'.

    Args:
        content (str): O conteúdo do artigo em formato de string.
        file_name (str): O nome do arquivo para salvar o artigo.
    """
    try:
        # Obter o diretório base do projeto (onde está o main.py)
        base_dir = os.path.dirname(os.path.dirname(__file__))

        # Caminho para o diretório 'artigos_markdown' dentro de src/revisor_artigos_sl3v1/resources
        md_dir = os.path.join(base_dir, 'revisor_artigos_sl3v1', 'resources', 'artigos_markdown')

        # Criar o diretório se não existir
        os.makedirs(md_dir, exist_ok=True)

        # Caminho completo do arquivo Markdown
        md_path = os.path.join(md_dir, file_name)

        # Salvar o conteúdo no arquivo
        with open(md_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Artigo salvo em: {md_path}")

    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")
        print(f"Tentando salvar em caminho alternativo...")

        try:
            # Tentativa alternativa usando caminho relativo
            alt_md_dir = os.path.join('revisor_artigos_sl3v1', 'resources', 'artigos_markdown')
            os.makedirs(alt_md_dir, exist_ok=True)
            alt_md_path = os.path.join(alt_md_dir, file_name)

            with open(alt_md_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Artigo salvo em caminho alternativo: {alt_md_path}")

        except Exception as e2:
            print(f"Erro ao salvar no caminho alternativo: {e2}")


def processar_pdfs():
    """
    Processar cada PDF na pasta pdf_folder e salvar o resultado em um arquivo YAML separado.

    Esta função utiliza as configurações de agentes e tarefas para criar uma equipe
    de agentes que processará cada arquivo PDF encontrado na pasta especificada.
    Os resultados são salvos individualmente em arquivos YAML nomeados de acordo com
    o arquivo PDF correspondente.

    Fluxo de Execução:
        1. Carregar as configurações de agentes e tarefas.
        2. Listar os arquivos PDF na pasta designada.
        3. Para cada PDF:
            a. Criar o caminho completo do PDF.
            b. Instanciar o PDFTool para o PDF atual.
            c. Preparar os inputs para a leitura do PDF.
            d. Criar e executar a equipe com os inputs preparados.
            e. Extrair o resultado em formato YAML.
            f. Salvar o resultado em um arquivo YAML específico.
        4. Continuar para o próximo PDF em caso de erro.

    Exceptions:
        Captura qualquer exceção durante o processamento de cada PDF e continua
        para o próximo arquivo.
    """
    # Carregar as configurações de agentes e tarefas
    agents_config, tasks_config = carregar_configuracoes()

    # Verificar se as configurações foram carregadas corretamente
    if not agents_config or not tasks_config:
        print("Erro: Falha ao carregar as configurações do agents.yaml ou tasks.yaml.")
        return

    # Configurar o LLM usando o modelo OpenAI especificado
    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.environ['OPENAI_API_KEY'],
        temperature=0.7
    )

    # Diretório para salvar os arquivos YAML gerados
    yaml_dir = os.path.join(os.path.dirname(__file__), 'revisor_artigos_sl3v1', 'resources', 'yamls')
    os.makedirs(yaml_dir, exist_ok=True)  # Criar o diretório se não existir

    # Listar todos os arquivos PDF na pasta especificada
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

    # Iterar sobre cada arquivo PDF encontrado
    for pdf_file_name in pdf_files:
        print(f"\nProcessando: {pdf_file_name}")

        try:
            # Criar o caminho completo do arquivo PDF
            pdf_path = os.path.join(pdf_folder, pdf_file_name)

            # Instanciar a ferramenta de busca em PDF para o arquivo atual
            pdf_tool = PDFSearchTool(pdf=pdf_path)

            # Obter as configurações de inputs para a tarefa de leitura de PDFs
            task_config = tasks_config.get('leitura_pdfs', {}).get('inputs', {})

            # Preparar os inputs necessários para a leitura do PDF
            leitura_inputs = {
                'arquivo': pdf_file_name,
                'solicitacoes': task_config.get('solicitacoes', ''),
                'template': task_config.get('template', '').replace('nome do arquivo.pdf', pdf_file_name),
                'controles': task_config.get('controles', ''),
                'restricoes': task_config.get('restricoes', '')
            }

            # Instanciar a ferramenta de busca em Serper para o novo agente
            serper_tool = SerperDevTool()

            # Criar uma instância da equipe para o processamento do PDF atual
            crew_instance = RevisorArtigosSl3V1Crew(
                agents_config=agents_config,
                tasks_config=tasks_config,
                llm=llm,
                pdf_tool=pdf_tool,
                serper_tool=serper_tool
            )

            # Criar a equipe de agentes
            crew = crew_instance.create_crew()

            # Executar a equipe com os inputs preparados
            print("\nExecutando com inputs:")
            print(f"- Arquivo: {pdf_file_name}")
            print("- Solicitações, template, controles e restrições carregados das configurações")

            results = crew.kickoff(inputs=leitura_inputs)

            # Extrair conteúdo YAML do resultado
            yaml_content = None
            if "```yaml" in results:
                yaml_content = results.split("```yaml")[1].split("```")[0].strip()
            elif "ARTIGO:" in results:
                yaml_content = results[results.find("ARTIGO:"):]

            # Salvar o resultado em um arquivo YAML específico para o PDF
            if yaml_content:
                try:
                    article_data = yaml.safe_load(yaml_content)
                    if article_data:
                        yaml_file = os.path.join(yaml_dir, f'output_{os.path.splitext(pdf_file_name)[0]}.yaml')
                        with open(yaml_file, 'w', encoding='utf-8') as file:
                            yaml.dump(article_data, file, default_flow_style=False, allow_unicode=True)
                        print(f"\nYAML salvo em: {yaml_file}")
                    else:
                        print(f"\nErro: YAML vazio para {pdf_file_name}")
                        continue  # Pula para o próximo PDF se o YAML estiver vazio
                except yaml.YAMLError as e:
                    print(f"\nErro ao fazer parse do YAML para {pdf_file_name}: {e}")
                    continue  # Pula para o próximo PDF em caso de erro no parse
            else:
                print(f"\nNenhum resultado encontrado para {pdf_file_name}.")
                continue  # Pula para o próximo PDF se não houver resultado

        except Exception as e:
            print(f"\nErro ao processar {pdf_file_name}: {e}")
            continue


def gerar_artigos_a_partir_de_yaml():
    """
    Itera sobre os arquivos YAML gerados no diretório especificado e cria um artigo
    em Markdown para cada um.

    Para cada arquivo YAML encontrado, esta função extrai os dados do artigo,
    gera um conteúdo em formato Markdown e o salva em um arquivo .md na mesma estrutura
    de diretório.

    Fluxo de Execução:
        1. Listar todos os arquivos YAML gerados no diretório 'src/revisor_artigos_sl3v1/resources/yamls'.
        2. Para cada arquivo YAML:
            a. Ler o conteúdo do arquivo.
            b. Verificar se contém a chave 'ARTIGO'.
            c. Gerar o conteúdo em Markdown usando 'generate_linkedin_article()'.
            d. Salvar o artigo em um arquivo .md no diretório 'src/revisor_artigos_sl3v1/resources/artigos_markdown'.
        3. Em caso de erro, exibir uma mensagem e continuar para o próximo arquivo.

    Exceptions:
        Captura qualquer exceção durante o processamento de um arquivo YAML e
        continua para o próximo, garantindo que a função não seja interrompida.
    """
    # Diretório de leitura dos arquivos YAML
    yaml_dir = os.path.join(os.path.dirname(__file__), 'revisor_artigos_sl3v1', 'resources', 'yamls')
    # Diretório de salvamento dos arquivos Markdown
    markdown_dir = os.path.join(os.path.dirname(__file__), 'revisor_artigos_sl3v1', 'resources', 'artigos_markdown')
    os.makedirs(markdown_dir, exist_ok=True)  # Criar o diretório se não existir

    # Listar todos os arquivos YAML gerados no diretório especificado
    yaml_files = [f for f in os.listdir(yaml_dir) if f.startswith('output_') and f.endswith('.yaml')]

    # Iterar sobre cada arquivo YAML encontrado
    for yaml_file in yaml_files:
        try:
            # Caminho completo do arquivo YAML
            yaml_path = os.path.join(yaml_dir, yaml_file)

            # Ler o conteúdo do arquivo YAML
            with open(yaml_path, 'r', encoding='utf-8') as file:
                article_data = yaml.safe_load(file)

            # Verificar se contém a chave 'ARTIGO' e se está no formato esperado
            if article_data and 'ARTIGO' in article_data:
                artigo = article_data['ARTIGO'][0]

                # Gerar o conteúdo em Markdown usando a função generate_linkedin_article()
                markdown_content, _ = generate_linkedin_article(artigo, yaml_file)

                # Salvar o artigo em um arquivo .md se o conteúdo for gerado com sucesso
                if markdown_content:
                    nome_md = f"{os.path.splitext(yaml_file)[0]}.md"
                    markdown_path = os.path.join(markdown_dir, nome_md)

                    save_article(markdown_content, markdown_path)
                    print(f"Artigo salvo em: {markdown_path}")
                else:
                    print(f"\nErro ao gerar o artigo para {yaml_file}")

        except Exception as e:
            print(f"\nErro ao processar o arquivo YAML {yaml_file}: {e}")
            continue

def run():
    """
    Executar o processamento de PDFs e a geração de artigos.

    Esta função primeiro chama a função 'processar_pdfs()' para iniciar o processamento
    dos PDFs disponíveis na pasta especificada e salvar os resultados em arquivos YAML
    separados. Em seguida, chama a função 'gerar_artigos_a_partir_de_yaml()' para criar
    artigos em Markdown a partir dos arquivos YAML gerados.
    """
    processar_pdfs()
    gerar_artigos_a_partir_de_yaml()


if __name__ == "__main__":
    run()
