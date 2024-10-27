import os

from crewai import Agent, Crew, Process, Task

class RevisorArtigosSl3V1Crew:
    """
    RevisorArtigosSl3V1Crew - Equipe para ler e revisar PDFs

    Esta classe representa uma equipe (Crew) especializada em ler e revisar PDFs,
    utilizando modelos de linguagem (LLMs) e ferramentas específicas de leitura de PDFs.
    A classe é configurada com agentes e tarefas definidos nos arquivos YAML de configuração.
    """

    def __init__(self, agents_config=None, tasks_config=None, llm=None, pdf_tool=None, serper_tool=None):
        """
        Inicializa a equipe com as configurações necessárias.

        Args:
            agents_config (dict, opcional): Configurações dos agentes do arquivo agents.yaml.
            tasks_config (dict, opcional): Configurações das tarefas do arquivo tasks.yaml.
            llm: Modelo de linguagem a ser usado pelos agentes.
            pdf_tool: Ferramenta para leitura de PDFs, utilizada pelo agente Leitor.
            serper_tool: Ferramenta para buscar informações adicionais, utilizada pelo agente Criador de Artigos.

        Atributos:
            agents_config (dict): Armazena as configurações dos agentes.
            tasks_config (dict): Armazena as configurações das tarefas.
            llm: Instância do modelo de linguagem a ser usada pelos agentes.
            pdf_tool: Instância da ferramenta de leitura de PDFs.
            serper_tool: Instância da ferramenta para buscar informações adicionais.
        """
        self.agents_config = agents_config or {}
        self.tasks_config = tasks_config or {}
        self.llm = llm
        self.pdf_tool = pdf_tool
        self.serper_tool = serper_tool

    def _create_leitor_pdfs(self):
        """
        Cria o agente Leitor de PDFs usando a configuração do agents.yaml.

        Este agente é responsável por ler PDFs e extrair informações conforme
        definido na configuração dos agentes.

        Returns:
            Agent: Instância do agente configurado para leitura de PDFs.
        """
        agent_config = self.agents_config.get('leitor_pdfs', {})

        return Agent(
            role=agent_config.get('role'),
            goal=agent_config.get('goal'),
            backstory=agent_config.get('backstory'),
            tools=[self.pdf_tool] if self.pdf_tool else [],
            llm=self.llm,
            verbose=True
        )

    def _create_revisor_yaml(self):
        """
        Cria o agente Revisor de YAML usando a configuração do agents.yaml.

        Este agente é responsável por revisar o YAML gerado pelo agente Leitor,
        garantindo que esteja em conformidade com o template especificado.

        Returns:
            Agent: Instância do agente configurado para revisão de YAML.
        """
        agent_config = self.agents_config.get('revisor_yaml', {})

        return Agent(
            role=agent_config.get('role'),
            goal=agent_config.get('goal'),
            backstory=agent_config.get('backstory'),
            llm=self.llm,
            verbose=True
        )

    def _create_criador_artigos(self):
        """
        Cria o agente Criador de Artigos LinkedIn usando a configuração do agents.yaml.

        Este agente é responsável por criar um artigo para o LinkedIn, usando informações
        adicionais buscadas com o SerperDevTool.

        Returns:
            Agent: Instância do agente configurado para criar artigos no LinkedIn.
        """
        agent_config = self.agents_config.get('criador_artigos_linkedin', {})

        return Agent(
            role=agent_config.get('role'),
            goal=agent_config.get('goal'),
            backstory=agent_config.get('backstory'),
            tools=[self.serper_tool] if self.serper_tool else [],
            llm=self.llm,
            verbose=True
        )

    def create_crew(self):
        """
        Cria e retorna a equipe configurada usando as definições dos YAMLs.

        A equipe (Crew) é composta por três agentes que trabalham sequencialmente:
        1. Leitor de PDFs: Extrai informações do PDF
        2. Revisor de YAML: Valida o conteúdo extraído
        3. Criador de artigos: Gera conteúdo para LinkedIn

        Returns:
            Crew: Instância da equipe configurada para processamento de PDFs.
        """
        # Criar os agentes
        leitor = self._create_leitor_pdfs()
        revisor = self._create_revisor_yaml()
        criador_artigos = self._create_criador_artigos()

        # Obter configurações
        leitura_config = self.tasks_config.get('leitura_pdfs', {})
        revisao_config = self.tasks_config.get('revisao_yaml', {})
        criar_artigo_config = self.tasks_config.get('criar_artigo_linkedin', {})

        # Tarefa de leitura com output_file especificado
        leitura = Task(
            description=leitura_config.get('description', ''),
            expected_output=leitura_config.get('expected_output', ''),
            agent=leitor,
            output_format="YAML",  # Especifica formato de saída
            output_file=leitura_config.get('output_file')  # Nome do arquivo de saída a partir do YAML
        )

        # Tarefa de revisão com output_file especificado
        revisao = Task(
            description=revisao_config.get('description', ''),
            expected_output=revisao_config.get('expected_output', ''),
            agent=revisor,
            context=[leitura],
            output_format="YAML",  # Especifica formato de saída
            output_file=revisao_config.get('output_file')  # Nome do arquivo de saída a partir do YAML
        )

        # Tarefa de criação de artigo
        criar_artigo = Task(
            description=criar_artigo_config.get('description', ''),
            expected_output=criar_artigo_config.get('expected_output', ''),
            agent=criador_artigos,
            context=[revisao],
            output_format="markdown",  # Especifica formato de saída
            output_file=criar_artigo_config.get('output_file')  # Nome do arquivo de saída a partir do YAML
        )

        # Criar e retornar a equipe com configurações adicionais
        return Crew(
            agents=[leitor, revisor, criador_artigos],
            tasks=[leitura, revisao, criar_artigo],
            process=Process.sequential,
            verbose=True,
            full_output=True,  # Retorna todos os outputs intermediários
            cache=True  # Habilita cache para melhor performance
        )

