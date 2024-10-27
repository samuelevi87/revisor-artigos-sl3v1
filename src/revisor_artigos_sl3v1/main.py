#!/usr/bin/env python

# Importações necessárias para o funcionamento do script
import os
import yaml
from dotenv import load_dotenv
from revisor_artigos_sl3v1.crew import RevisorArtigosSl3V1Crew
from crewai_tools import PDFSearchTool
from crewai import LLM

# Caminho da pasta contendo os PDFs a serem processados
pdf_folder = os.path.join(os.path.dirname(__file__), 'resources', 'pdfs')

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


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


def processar_pdfs():
    """
    Criar uma equipe de agentes para processar cada PDF na pasta pdf_folder.

    Esta função utiliza as configurações de agentes e tarefas para criar uma
    equipe de agentes que processará cada arquivo PDF encontrado na pasta
    especificada. Os resultados são salvos em um arquivo YAML com um timestamp.

    Fluxo de Execução:
        1. Carregar as configurações de agentes e tarefas.
        2. Listar os arquivos PDF na pasta designada.
        3. Para cada PDF:
            a. Criar o caminho completo do PDF.
            b. Instanciar o PDFTool para o PDF atual.
            c. Preparar os inputs para a leitura do PDF.
            d. Criar e executar a equipe com os inputs preparados.
            e. Extrair o resultado em formato YAML.
        4. Salvar os resultados finais em um arquivo YAML.

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

    # Listar todos os arquivos PDF na pasta especificada
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    all_articles = []

    # Iterar sobre cada arquivo PDF encontrado
    for pdf_file_name in pdf_files:
        print(f"\nProcessando: {pdf_file_name}")

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

        # Criar uma instância da equipe para o processamento do PDF atual
        crew_instance = RevisorArtigosSl3V1Crew(
            agents_config=agents_config,
            tasks_config=tasks_config,
            llm=llm,
            pdf_tool=pdf_tool
        )

        # Criar a equipe de agentes
        crew = crew_instance.create_crew()

        try:
            # Executar a equipe com os inputs preparados
            print("\nExecutando com inputs:")
            print(f"- Arquivo: {pdf_file_name}")
            print("- Solicitações, template, controles e restrições carregados das configurações")

            results = crew.kickoff(inputs=leitura_inputs)

            # Converter o resultado para string se necessário
            if not isinstance(results, str):
                results = str(results)

            print("\nResultado obtido:", results)

            # Extrair o conteúdo YAML do resultado
            yaml_content = None
            if "```yaml" in results:
                yaml_content = results.split("```yaml")[1].split("```")[0].strip()
            elif "ARTIGO:" in results:
                yaml_content = results[results.find("ARTIGO:"):]

            # Carregar o conteúdo YAML extraído em um dicionário
            if yaml_content:
                try:
                    article_data = yaml.safe_load(yaml_content)
                    if article_data:
                        print("\nYAML extraído com sucesso!")
                        all_articles.append(article_data)
                    else:
                        print(f"\nErro: YAML vazio para {pdf_file_name}")
                except yaml.YAMLError as e:
                    print(f"\nErro ao fazer parse do YAML para {pdf_file_name}: {e}")
            else:
                print(f"\nNão foi possível extrair YAML do resultado para {pdf_file_name}")

        except Exception as e:
            print(f"\nErro ao processar {pdf_file_name}: {e}")
            continue

    # Salvar os resultados finais em um arquivo YAML
    if all_articles:
        final_output = {'artigos': all_articles}
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'output_{timestamp}.yaml'

        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                yaml.dump(final_output, file, default_flow_style=False, allow_unicode=True)
            print(f"\nDados salvos em {output_file}")
            print(f"Número de artigos processados: {len(all_articles)}")
        except Exception as e:
            print(f"\nErro ao salvar o arquivo de saída: {e}")
    else:
        print("\nNenhum artigo foi processado com sucesso.")


def run():
    """
    Executar o processamento de PDFs.

    Esta função chama a função 'processar_pdfs()' para iniciar o processamento dos
    PDFs disponíveis na pasta especificada.
    """
    processar_pdfs()


if __name__ == "__main__":
    run()
